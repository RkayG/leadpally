# -*- coding: utf-8 -*-
# """
# Schedule Configuration Module
# This module defines the scheduling configuration for various jobs in the application.
# It includes settings for cron jobs, processing limits, and API preferences.
# """
from datetime import time

# Cron job configurations
KEYWORD_FETCH_INTERVAL = 15  # Minutes between keyword fetch operations
MENTION_PROCESSOR_INTERVAL = 15  # Minutes between processing batches
DAILY_FETCH_TIME = time(hour=1, minute=0)  # Run daily fetch at 1:00 AM
AGGREGATED_ANALYSIS_TIME = time(hour=4, minute=0)  # Run at 4:00 AM (after daily fetch)
# New configuration for priority processing
PRIORITY_PROCESSING_INTERVAL = 500000  # minutes

# Processing limits
MAX_KEYWORDS_PER_BATCH = 100
MAX_RESULTS_PER_SEARCH = 100

USER_KEYWORD_CHECK_FREQUENCY_HOURS  = 24

# Default search engines to use
DEFAULT_SEARCH_ENGINES = ["google"]

# API preferences 
# Uses ScrapingBee if both are set to False
DEFAULT_USE_GOOGLE_API = False  # Set to False to use ScrapingBee or True to use Google API
DEFAULT_USE_SERPER_API = True # Set to True to use Serper API 

# Retry configurations
MAX_RETRIES = 3
RETRY_DELAY = 300  # seconds (5 minutes)


# Time periods for aggregated analysis (in days)
ANALYSIS_PERIODS = [7, 30]  #7 days, 30 days
OLDER_CONTENT_WEIGHT = 0.5  # Weight multiplier for older content in trend analysis