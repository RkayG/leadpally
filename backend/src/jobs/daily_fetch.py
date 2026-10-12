# -*- coding: utf-8 -*-
"""
Updated Daily Fetch Job Module
This version works with the optimized mention processor while maintaining daily full refresh capability.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

# Internal imports
from database import get_db_session
from models import Keywords, JobHistory, UserKeywords
from jobs.mention_processor import OptimizedUserMentionProcessor
from config.schedule_config import MAX_KEYWORDS_PER_BATCH

# Configure logging
logger = logging.getLogger(__name__)

async def run_daily_fetch():
    """
    Run a daily fetch of all active keywords using the optimized processor.
    Forces a full refresh by marking keywords as priority and resetting last_checked.
    """
    logger.info("Starting optimized daily fetch job")
    session = next(get_db_session())
    job_history = JobHistory(
        job_name="run_daily_fetch",
        start_time=datetime.utcnow(),
        status="in_progress"
    )
    session.add(job_history)
    session.commit()

    try:
        # Initialize the optimized processor
        processor = OptimizedUserMentionProcessor()
        
        # Get all active keywords with their user configurations
        stmt = (
            select(Keywords)
            .where(Keywords.is_active == True)
            .options(selectinload(Keywords.user_keywords))
            .order_by(Keywords.last_checked.asc().nulls_first())
        )
        result = session.execute(stmt)
        keywords = result.scalars().all()
        
        if not keywords:
            logger.info("No active keywords found for daily fetch")
            job_history.status = "success"
            job_history.items_processed = 0
            job_history.end_time = datetime.utcnow()
            session.commit()
            return {
                "status": "success",
                "keywords_processed": 0,
                "users_processed": 0,
                "mentions_stored": 0
            }
        
        logger.info(f"Found {len(keywords)} active keywords for daily fetch")
        
        # Mark all keywords as priority and reset last_checked
        for keyword in keywords:
            keyword.is_priority = True
            keyword.last_checked = None
            for user_keyword in keyword.user_keywords:
                user_keyword.last_processed_at = None
        
        session.commit()
        
        # Process in batches using the optimized processor
        batch_size = MAX_KEYWORDS_PER_BATCH
        total_stats = {
            "keywords_processed": 0,
            "users_processed": 0,
            "mentions_stored": 0
        }
        
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]
            for keyword in batch:
                try:
                    result = await processor.process_keyword_for_all_users(session, keyword)
                    total_stats["keywords_processed"] += 1
                    total_stats["users_processed"] += result["processed_users"]
                    total_stats["mentions_stored"] += result["total_mentions"]
                    session.commit()
                except Exception as e:
                    logger.error(f"Error processing keyword {keyword.text} in daily fetch: {str(e)}")
                    session.rollback()
                    continue
            
            # Small delay between batches
            await asyncio.sleep(1)
        
        logger.info(
            f"Daily fetch completed: {total_stats['keywords_processed']} keywords, "
            f"{total_stats['users_processed']} users, "
            f"{total_stats['mentions_stored']} mentions"
        )
        
        # Update job history
        job_history.status = "success"
        job_history.items_processed = total_stats["keywords_processed"]
        job_history.metadata = {
            "users_processed": total_stats["users_processed"],
            "mentions_stored": total_stats["mentions_stored"]
        }
        job_history.end_time = datetime.utcnow()
        session.commit()
        
        return {
            "status": "success",
            **total_stats
        }

    except Exception as e:
        logger.error(f"Error in daily fetch job: {str(e)}", exc_info=True)
        session.rollback()
        job_history.status = "failure"
        job_history.error_message = str(e)
        job_history.end_time = datetime.utcnow()
        session.commit()
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        session.close()