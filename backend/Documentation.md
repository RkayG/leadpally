# Keyword Monitor Application Documentation

## Overview
The Keyword Monitor application is designed to track keyword mentions across the web. It periodically fetches keywords from a database, processes mentions using web scraping and analysis, and stores the results in a database. The application is built using **FastAPI** for the API layer, **SQLAlchemy** for database interactions, and **APScheduler** for job scheduling.

## Features

### Keyword Tracking
- Fetches keywords from the database that need monitoring.
- Queues keywords for mention processing.

### Mention Processing
- Scrapes mentions for keywords from sources like Google.
- Analyzes mentions for sentiment, topic distribution, and domain statistics.

### Job Scheduling
- Periodic tasks for fetching keywords and processing mentions.
- Daily fetch jobs for comprehensive mention tracking.

### API Endpoints
- Health check endpoint.
- Example endpoint for database interaction.
- Endpoint to manually trigger scheduled jobs.

### Extensibility
- Modular design for adding new jobs or features.

## Project Structure

### `main.py`
- Entry point for the FastAPI application.
- Configures the API, middleware, and lifespan events.
- Includes example endpoints for database interaction and job triggering.

### `database.py`
- Manages database connections using SQLAlchemy.
- Provides a session factory (`SessionLocal`) and ORM base class (`Base`).
- Includes utility functions for initializing the database and managing sessions.

### `jobs`
Contains job modules for periodic tasks:
- **`keyword_fetcher.py`**: Fetches keywords from the database and queues them for mention processing.
- **`mention_processor.py`**: Processes mentions for queued keywords. Scrapes mentions, analyzes them, and stores results.
- **`scheduler.py`**: Manages job scheduling using APScheduler.

### `models`
- Defines database models for keywords, mentions, and analysis results.
- Models include `Keywords`, `Mentions`, `TopicDistribution`, `SentimentAnalysis`, etc.

### `scrapers`
- Contains modules for web scraping.
- Example: `google_scraper.py` for scraping Google search results.

### `analyzers`
- Contains modules for analyzing scraped data.
- Example: `google_analyzer.py` for analyzing Google search results.

### `config`
- Stores configuration files for scheduling, database, and other settings.
- Example: `schedule_config.py` for job intervals and cron schedules.

## API Endpoints

### 1. Health Check
- **Endpoint**: `/health`
- **Method**: GET
- **Description**: Checks the health of the application.

### 2. Example Database Query
- **Endpoint**: `/example`
- **Method**: GET
- **Description**: Demonstrates database interaction by querying all keywords.
- **Response**: List of keywords from the database.

### 3. Trigger Job
- **Endpoint**: `/api/jobs/{job_id}/trigger`
- **Method**: POST
- **Description**: Manually triggers a scheduled job.
- **Path Parameter**: `job_id` - The ID of the job to trigger (`keyword_fetcher`, `mention_processor`, `daily_fetch`).
- **Response**:
  - **Success**: `{ "status": "success", "message": "Job {job_id} triggered successfully" }`
  - **Failure**: HTTP 404 with `{ "detail": "Job {job_id} not found" }`

## Job Scheduling

The application uses **APScheduler** to manage periodic tasks.

### 1. Keyword Fetcher
- **Job ID**: `keyword_fetcher`
- **Trigger**: Interval (every `KEYWORD_FETCH_INTERVAL` minutes).
- **Function**: Fetches keywords from the database and queues them for processing.

### 2. Mention Processor
- **Job ID**: `mention_processor`
- **Trigger**: Interval (every `MENTION_PROCESSOR_INTERVAL` minutes).
- **Function**: Processes mentions for queued keywords.

### 3. Daily Fetch
- **Job ID**: `daily_fetch`
- **Trigger**: Cron (at `DAILY_FETCH_TIME`).
- **Function**: Runs a comprehensive fetch of all mentions.

## Database Models

The database models are defined using **SQLAlchemy ORM**.

### 1. Keywords
- Tracks keywords to be monitored.
- **Fields**: `id`, `text`, `last_checked`, `is_priority`, etc.

### 2. Mentions
- Stores mentions for keywords.
- **Fields**: `id`, `keyword_id`, `source`, `content`, `timestamp`, etc.

### 3. TopicDistribution
- Stores topic analysis results for mentions.
- **Fields**: `id`, `keyword_id`, `topic`, `score`, etc.

### 4. SentimentAnalysis
- Stores sentiment analysis results for mentions.
- **Fields**: `id`, `keyword_id`, `sentiment`, `score`, etc.

## Configuration

### 1. Environment Variables
- `DATABASE_URL`: Connection string for the PostgreSQL database.

### 2. Schedule Config (`schedule_config.py`)
- `KEYWORD_FETCH_INTERVAL`: Interval (in minutes) for the keyword fetcher job.
- `MENTION_PROCESSOR_INTERVAL`: Interval (in minutes) for the mention processor job.
- `DAILY_FETCH_TIME`: Time (hour and minute) for the daily fetch job.

## How to Run

### Set Up Environment
```bash
pip install -r requirements.txt
```
Set up the `.env` file with the `DATABASE_URL`.

### Run the Application
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the API
Open [http://localhost:8000](http://localhost:8000) in your browser or use tools like Postman.

### Run Jobs
- Jobs run automatically based on their schedule.
- Use the `/api/jobs/{job_id}/trigger` endpoint to manually trigger jobs.

## Extending the Application

### Add New Jobs
- Define the job function in a new or existing module.
- Add the job to the scheduler in `scheduler.py`.

### Add New API Endpoints
- Define the endpoint in `main.py` or a new router module.
- Use FastAPI's dependency injection for database access.

### Add New Models
- Define the model in `models.py`.
- Run migrations to update the database schema.

## Known Issues
- Ensure the `DATABASE_URL` is correctly configured in `.env`.
- Verify that all required dependencies are installed.
- Scheduler jobs must be properly configured with unique IDs.
