# -*- coding: utf-8 -*-
"""
Updated Keyword Fetcher Job Module
This module now works with the optimized user-specific mention processor to:
1. Fetch keywords that need processing
2. Queue them for processing with all their user configurations
3. Track processing status at both keyword and user-keyword levels
"""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import selectinload

# Internal imports
from database import get_db_session
from models import Keywords, JobHistory, UserKeywords
from config.schedule_config import MAX_KEYWORDS_PER_BATCH
from jobs.mention_processor import OptimizedUserMentionProcessor

# Configure logging
logger = logging.getLogger(__name__)

async def fetch_keywords_from_db():
    """
    Fetch keywords from the database and initiate processing for all their user configurations.
    """
    logger.info("Starting keyword fetch job")
    session = next(get_db_session())
    job_history = JobHistory(
        job_name="fetch_keywords_from_db",
        start_time=datetime.now(),
        status="in_progress"
    )
    session.add(job_history)
    session.commit()

    try:
        processor = OptimizedUserMentionProcessor()
        
        # Get keywords that need processing
        keywords = await processor.get_keywords_to_process(session)
        
        if not keywords:
            logger.info("No keywords pending for processing")
            job_history.status = "success"
            job_history.items_processed = 0
            job_history.end_time = datetime.now()
            session.commit()
            return {"status": "success", "processed": 0}
        
        logger.info(f"Found {len(keywords)} keywords for processing")
        
        # Process each keyword and track statistics
        stats = {
            "keywords_processed": 0,
            "users_processed": 0,
            "mentions_stored": 0
        }
        
        for keyword in keywords:
            try:
                # Process the keyword for all its users
                result = await processor.process_keyword_for_all_users(session, keyword)
                
                stats["keywords_processed"] += 1
                stats["users_processed"] += result["processed_users"]
                stats["mentions_stored"] += result["total_mentions"]
                
                # Commit after each keyword
                session.commit()
                
                logger.info(
                    f"Processed keyword '{keyword.text}': "
                    f"{result['processed_users']} users, "
                    f"{result['total_mentions']} mentions"
                )
                
            except Exception as e:
                logger.error(f"Error processing keyword {keyword.text}: {str(e)}")
                session.rollback()
                continue
        
        # Update job history
        job_history.status = "success"
        job_history.items_processed = stats["keywords_processed"]
        job_history.end_time = datetime.now()
        job_history.metadata = {
            "users_processed": stats["users_processed"],
            "mentions_stored": stats["mentions_stored"]
        }
        session.commit()
        
        logger.info(
            f"Job completed: {stats['keywords_processed']} keywords, "
            f"{stats['users_processed']} users, "
            f"{stats['mentions_stored']} mentions"
        )
        
        return {
            "status": "success",
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error in keyword fetch job: {str(e)}", exc_info=True)
        session.rollback()
        job_history.status = "failure"
        job_history.error_message = str(e)
        job_history.end_time = datetime.now()
        session.commit()
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        session.close()

async def process_priority_keywords():
    """
    Special job to process only priority keywords immediately.
    """
    logger.info("Starting priority keyword processing job")
    session = next(get_db_session())
    job_history = JobHistory(
        job_name="process_priority_keywords",
        start_time=datetime.now(),
        status="in_progress"
    )
    session.add(job_history)
    session.commit()

    try:
        # First mark some keywords as priority
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        stmt = (
            update(Keywords)
            .where(
                and_(
                    Keywords.auto_scan == True,
                    or_(
                        Keywords.last_checked.is_(None),
                        Keywords.last_checked <= cutoff_time
                    ),
                    Keywords.is_priority == False  # Only mark non-priority keywords
                )
            )
            .values(is_priority=True)
        )
        
        result = session.execute(stmt)
        marked_count = result.rowcount
        session.commit()
        
        logger.info(f"Marked {marked_count} keywords as priority")
        
        if marked_count == 0:
            logger.info("No keywords needed priority marking")
            job_history.status = "success"
            job_history.items_processed = 0
            job_history.end_time = datetime.now()
            session.commit()
            return {"status": "success", "marked": 0}
        
        # Now process the priority keywords
        processor = OptimizedUserMentionProcessor()
        keywords = await processor.get_user_keywords_to_process(session)
        
        stats = {
            "keywords_processed": 0,
            "users_processed": 0,
            "mentions_stored": 0
        }
        
        for keyword in keywords:
            try:
                result = await processor.process_user_keyword(session, keyword)
                
                stats["keywords_processed"] += 1
                stats["users_processed"] += result["processed_users"]
                stats["mentions_stored"] += result["total_mentions"]
                
                session.commit()
                
            except Exception as e:
                logger.error(f"Error processing priority keyword {keyword.text}: {str(e)}")
                session.rollback()
                continue
        
        # Update job history
        job_history.status = "success"
        job_history.items_processed = stats["keywords_processed"]
        job_history.end_time = datetime.now()
        job_history.metadata = {
            "users_processed": stats["users_processed"],
            "mentions_stored": stats["mentions_stored"]
        }
        session.commit()
        
        return {
            "status": "success",
            "marked": marked_count,
            **stats
        }
        
    except Exception as e:
        logger.error(f"Error in priority keyword job: {str(e)}", exc_info=True)
        session.rollback()
        job_history.status = "failure"
        job_history.error_message = str(e)
        job_history.end_time = datetime.now()
        session.commit()
        return {
            "status": "failed",
            "error": str(e)
        }
    finally:
        session.close()