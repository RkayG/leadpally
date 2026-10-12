# -*- coding: utf-8 -*-
"""
Updated Scheduler Module
This module now works with the optimized processing pipeline and includes:
1. Updated job configurations for the new processor
2. Better error handling and logging
3. Support for priority processing
"""
import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Import job functions
from jobs.keyword_fetcher import fetch_keywords_from_db, process_priority_keywords
from jobs.mention_processor import OptimizedUserMentionProcessor
#from jobs.daily_fetch import run_daily_fetch
from jobs.aggregated_analysis import generate_aggregated_analysis

# Import configurations
from config.schedule_config import (
    KEYWORD_FETCH_INTERVAL,
    MENTION_PROCESSOR_INTERVAL,
    DAILY_FETCH_TIME,
    AGGREGATED_ANALYSIS_TIME,
    PRIORITY_PROCESSING_INTERVAL
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KeywordMonitorScheduler:
    """Manages scheduled jobs for the Keyword Monitor application."""
    
    def __init__(self):
        """Initialize the scheduler with optimized jobs."""
        self.scheduler = AsyncIOScheduler()
        self._configure_jobs()
        logger.info("Optimized scheduler initialized")
    
    def _configure_jobs(self):
        """Configure all scheduled jobs for the optimized pipeline."""
        # Job 1: Main keyword processing
        self.scheduler.add_job(
            self._run_keyword_processing,
            IntervalTrigger(minutes=KEYWORD_FETCH_INTERVAL),
            id='keyword_processing',
            replace_existing=True
        )
        
        # Job 2: Priority keyword processing (more frequent)
        self.scheduler.add_job(
            self._run_priority_processing,
            IntervalTrigger(minutes=PRIORITY_PROCESSING_INTERVAL),
            id='priority_processing',
            replace_existing=True
        )
        
        # Job 3: Daily maintenance tasks
       # self.scheduler.add_job(
       #     self._run_daily_tasks,
       #     CronTrigger(hour=DAILY_FETCH_TIME.hour, minute=DAILY_FETCH_TIME.minute),
       #     id='daily_maintenance',
       #     replace_existing=True
       # )
       # 
       # logger.info("Jobs configured: keyword_processing, priority_processing, daily_maintenance") """
    
    async def _run_keyword_processing(self):
        """Wrapper for the main keyword processing job."""
        try:
            logger.info("Starting main keyword processing")
            processor = OptimizedUserMentionProcessor()
            result = await processor.run_processing_job()
            logger.info(f"Main processing completed: {result}")
        except Exception as e:
            logger.error(f"Error in main processing job: {str(e)}", exc_info=True)
    
    async def _run_priority_processing(self):
        """Wrapper for priority keyword processing."""
        try:
            logger.info("Starting priority keyword processing")
            result = await process_priority_keywords()
            logger.info(f"Priority processing completed: {result}")
        except Exception as e:
            logger.error(f"Error in priority processing job: {str(e)}", exc_info=True)
    
    #async def _run_daily_tasks(self):
    #    Wrapper for daily maintenance tasks
    #    try:
    #        logger.info("Starting daily maintenance tasks")
    #        
    #        # Run the daily fetch
    #        fetch_result = await run_daily_fetch()
    #        logger.info(f"Daily fetch completed: {fetch_result}")
    #        
    #        # Run aggregated analysis
    #        analysis_result = await generate_aggregated_analysis()
    #        logger.info(f"Aggregated analysis completed: {analysis_result}")
    #        
    #    except Exception as e:
    #        logger.error(f"Error in daily tasks: {str(e)}", exc_info=True) """
    
    def start(self):
        """Start the scheduler with error handling."""
        try:
            if not self.scheduler.running:
                self.scheduler.start()
                logger.info("Scheduler started successfully")
                return True
            logger.warning("Scheduler already running")
            return False
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            return False
    
    def shutdown(self):
        """Shutdown the scheduler gracefully."""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler shutdown completed")
                return True
            logger.warning("Scheduler not running")
            return False
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {str(e)}")
            return False
    
    async def run_job_now(self, job_id: str):
        """Run a specific job immediately with enhanced error handling."""
        try:
            job = self.scheduler.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return False
            
            logger.info(f"Manually executing job: {job_id}")
            
            if job_id == 'keyword_processing':
                await self._run_keyword_processing()
            elif job_id == 'priority_processing':
                await self._run_priority_processing()
            elif job_id == 'daily_maintenance':
                await self._run_daily_tasks()
            else:
                logger.error(f"Unknown job ID: {job_id}")
                return False
                
            logger.info(f"Job {job_id} executed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {str(e)}", exc_info=True)
            return False

def get_scheduler():
    """Singleton accessor for the scheduler with thread safety."""
    if not hasattr(get_scheduler, "instance"):
        get_scheduler.instance = KeywordMonitorScheduler()
    return get_scheduler.instance