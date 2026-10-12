# Keyword Monitor

A tool to track keyword mentions across various platforms.

## Setup
1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the environment: `venv\Scripts\activate` or `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`

## Usage
Run `python src/main.py --keywords "your keywords here"`

update 22-04-2025
c:/Users/DELL/Desktop/brandtrack/KeywordMonitor/src/
├── analyzers/
├── commands/
├── database.py
├── main.py
├── middleware/
├── models.py
├── routes/
├── scrapers/
├── tests/
├── utils.py
├── jobs/                     # New directory for scheduled jobs
│   ├── __init__.py
│   ├── scheduler.py          # Scheduler configuration
│   ├── keyword_fetcher.py    # Job to gather keywords from DB
│   └── mention_processor.py  # Job to process mentions asynchronously
├── config/                   # New directory for configuration
│   ├── __init__.py
│   └── schedule_config.py    # Cron job configuration
└── workers/                  # For handling async processing
    ├── __init__.py
    └── queue_manager.py      # Manages async task queues