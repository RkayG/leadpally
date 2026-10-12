"""
# Aggregated Analysis Job Module
This module defines a job that performs daily aggregation of mentions stored in the database.
It calculates aggregated statistics over different time periods (3 days, 7 days, 30 days)
to provide pre-computed data for faster access and visualization.
"""
import logging
import asyncio
from datetime import datetime, timedelta
from sqlalchemy import select, func, and_, desc, distinct
from typing import Dict, List, Set, Tuple, Optional
import json
import uuid

# Internal imports
from database import get_db_session
from models import (
    UserMentions, 
    UserKeywords, 
    JobHistory,
    AggregatedAnalysis
)
from analyzers.google_analyzer import GoogleResultAnalyzer

# Configure logging
logger = logging.getLogger(__name__)

async def generate_aggregated_analysis():
    """
    Main function to generate aggregated analysis for different time periods.
    This job runs daily to pre-compute analytical data for faster access.
    """
    logger.info("Starting aggregated analysis job")
    session = next(get_db_session())
    
    # Record job start in history
    job_history = JobHistory(
        job_name="generate_aggregated_analysis",
        start_time=datetime.utcnow(),
        status="in_progress"
    )
    session.add(job_history)
    session.commit()
    
    try:
        # Time periods for aggregation (in days)
        time_periods = [7, 30]
        
        # Get all active user keywords
        user_keywords = session.execute(
            select(UserKeywords).where(UserKeywords.is_active == True)
        ).scalars().all()
        
        processed_count = 0
        for user_keyword in user_keywords:
            user_keyword_id = user_keyword.id
            keyword_text = user_keyword.display_text or (user_keyword.keyword.text if user_keyword.keyword else "")
            
            logger.info(f"Generating aggregated analysis for user_keyword: {user_keyword_id} ({keyword_text})")
            
            # Process each time period
            for period in time_periods:
                # Generate and store aggregated analysis
                await aggregate_for_period(session, user_keyword_id, keyword_text, period)
                processed_count += 1
        
        # Update job history
        job_history.status = "success"
        job_history.items_processed = processed_count
        job_history.end_time = datetime.utcnow()
        session.commit()
        
        logger.info(f"Aggregated analysis job completed successfully. Processed {processed_count} user_keyword-period combinations.")
        
    except Exception as e:
        logger.error(f"Error in aggregated analysis job: {str(e)}", exc_info=True)
        session.rollback()
        
        # Update job history with error
        job_history.status = "failure"
        job_history.error_message = str(e)
        job_history.end_time = datetime.utcnow()
        session.commit()
    finally:
        session.close()

async def aggregate_for_period(session, user_keyword_id: str, keyword_text: str, days: int):
    """
    Generate aggregated analysis for a specific user keyword and time period,
    re-extracting topics and mapping them to mention IDs.
    Args:
        session: SQLAlchemy session
        user_keyword_id: ID of the user keyword config
        keyword_text: Text of the keyword
        days: Number of days to include in the analysis

    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Get all user mentions for this user keyword in the specified period
    mentions_query = select(UserMentions).where(
        and_(
            UserMentions.user_keyword_id == user_keyword_id,
            UserMentions.created_at >= cutoff_date
        )
    )
    mentions = session.execute(mentions_query).scalars().all()

    if not mentions:
        logger.info(f"No mentions found for user_keyword '{user_keyword_id}' in the last {days} days.")
        empty_analysis = {
            "topic_distribution": {},
            "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 100},
            "top_domains": [],
            "source_types": {},
            "mention_count": 0,
            "period_days": days,
            "topic_to_mention_ids": []
        }
        store_aggregated_analysis(session, user_keyword_id, days, empty_analysis)
        return

    # Prepare results for analyzer (LLM or GoogleResultAnalyzer)
    results = []
    mention_id_map = {}
    for mention in mentions:
        result = {
            "title": mention.title,
            "description": mention.description,
            "link": mention.url,
            "display_link": mention.display_link,
            "source_type": mention.source_type,
            "sentiment": mention.sentiment,
            "position": mention.position,
            "domain": mention.display_link.split('/')[0] if mention.display_link else None,
            "keyword_count_title": mention.keyword_count_title,
            "keyword_count_description": mention.keyword_count_description,
            "content_fingerprint": mention.content_fingerprint,
            "original_mention_id": str(mention.id)
        }
        results.append(result)
        mention_id_map[result["link"]] = str(mention.id)  # or another unique field

    # Run topic extraction (LLM or GoogleResultAnalyzer)
    analyzer = GoogleResultAnalyzer(results, keyword=keyword_text)
    analysis = analyzer.analyze()
    topic_analysis = analysis["topic_analysis"]
    topics = topic_analysis.get("topics", [])

    # Build mapping: topic_id -> {topic_name, mention_ids}
    topic_to_mention_ids = {}
    for result in results:
        for topic in topics:
            topic_name = topic.get("topic_name", "").strip().lower()
            topic_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, topic_name))
            logger.info(f"Topic name: {topic_name}, Topic ID: {topic_id}")
            if topic_id not in topic_to_mention_ids:
                logger.info(f"Creating new entry for topic ID: {topic_id}")
                topic_to_mention_ids[topic_id] = {
                    "topic_id": topic_id,
                    "topic_name": topic_name,
                    "mention_ids": []
                }
            topic_to_mention_ids[topic_id]["mention_ids"].append(result["original_mention_id"])
            logger.info(f"Appending mention ID: {result['original_mention_id']} to topic ID: {topic_id}")
    topic_to_mention_ids_list = list(topic_to_mention_ids.values())
    logger.info(f"Topic to mention IDs mapping: {topic_to_mention_ids_list}")
    # Calculate topic and sentiment distribution as before
    topic_distribution = {}
    total_mentions = len(results)
    for topic in topic_to_mention_ids_list:
        topic_distribution[topic["topic_name"]] = round(
            (len(topic["mention_ids"]) / total_mentions) * 100, 1
        )

    sentiment_distribution = await calculate_sentiment_distribution(session, user_keyword_id, cutoff_date)

    aggregated_analysis = {
        "topic_distribution": topic_distribution,
        "sentiment_distribution": sentiment_distribution,
        "top_domains": analyzer.source_counter.most_common(10),
        "source_types": dict(analyzer.source_type_counter),
        "mention_count": total_mentions,
        "period_days": days,
        "topic_to_mention_ids": topic_to_mention_ids_list
    }

    store_aggregated_analysis(session, user_keyword_id, days, aggregated_analysis)
    logger.info(f"Completed aggregated analysis for user_keyword '{user_keyword_id}' - {days} days period")

async def calculate_sentiment_distribution(session, user_keyword_id: str, cutoff_date: datetime) -> Dict[str, float]:
    """
    Calculate sentiment distribution for a user keyword within a specific time period.
    
    Args:
        session: SQLAlchemy session
        user_keyword_id: ID of the user keyword config
        cutoff_date: Only include mentions created after this date
        
    Returns:
        Dict: Sentiment distribution with sentiment types as keys and percentages as values
    """
    # Get mention counts per sentiment
    sentiment_counts_query = select(
        UserMentions.sentiment, 
        func.count(UserMentions.id).label('count')
    ).where(
        and_(
            UserMentions.user_keyword_id == user_keyword_id,
            UserMentions.created_at >= cutoff_date
        )
    ).group_by(UserMentions.sentiment)
    
    sentiment_counts = session.execute(sentiment_counts_query).all()
    
    # Calculate percentages
    total_mentions = sum(count for _, count in sentiment_counts)
    
    if total_mentions == 0:
        return {"positive": 0, "negative": 0, "neutral": 100}
    
    return {
        sentiment: round((count / total_mentions) * 100, 1)
        for sentiment, count in sentiment_counts
    }

def store_aggregated_analysis(session, user_keyword_id: str, period_days: int, analysis: Dict):
    """
    Store the aggregated analysis in the database.
    
    Args:
        session: SQLAlchemy session
        user_keyword_id: ID of the user keyword config
        period_days: The time period in days
        analysis: The aggregated analysis data
    """
    # Convert data to serializable format
    serializable_analysis = analysis.copy()
    
    # Convert top_domains to a serializable format if needed
    if "top_domains" in serializable_analysis:
        serializable_analysis["top_domains"] = [
            {"domain": domain, "count": count}
            for domain, count in serializable_analysis["top_domains"]
        ]
    
    # Check if there's an existing record
    existing_query = select(AggregatedAnalysis).where(
        and_(
            AggregatedAnalysis.user_keyword_id == user_keyword_id,
            AggregatedAnalysis.period_days == period_days
        )
    )
    existing = session.execute(existing_query).scalar_one_or_none()
    
    if existing:
        # Update existing record
        existing.data = json.dumps(serializable_analysis)
        existing.updated_at = datetime.utcnow()
    else:
        # Create new record
        new_analysis = AggregatedAnalysis(
            id=str(uuid.uuid4()),
            user_keyword_id=user_keyword_id,
            period_days=period_days,
            data=json.dumps(serializable_analysis),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        session.add(new_analysis)
    
    session.commit()

if __name__ == "__main__":
    # For testing purposes
    asyncio.run(generate_aggregated_analysis())
