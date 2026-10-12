# -*- coding: utf-8 -*-
"""
Optimized User-Specific Mention Processor Job Module (Complete Version)
"""
import logging
import asyncio
import json
import hashlib
import pickle
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass
from sqlalchemy import cast, Integer, text

#import redis
from sqlalchemy import select, and_, or_, update, func
from sqlalchemy.orm import Session, selectinload

# Internal imports
from database import get_db_session
from models import (
    Keywords, UserKeywords, UserMentions, UserTopicDistribution, 
    UserTopicKeywords, UserSentimentAnalysis, UserDomainStatistics,
    JobHistory, UserSourceTypeStatistics
)
from scrapers.google_scraper import GoogleScraper
from scrapers.serper_google_scraper import SerperScraper
from analyzers.google_analyzer import GoogleResultAnalyzer
from config.schedule_config import (
    MAX_RESULTS_PER_SEARCH, DEFAULT_USE_GOOGLE_API, 
    DEFAULT_USE_SERPER_API, MAX_KEYWORDS_PER_BATCH,
    USER_KEYWORD_CHECK_FREQUENCY_HOURS
)
from utils.map_topic_ids import map_topic_ids_from_db

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Data class for search results."""
    position: int
    url: str
    title: str
    description: str
    display_link: str
    source_type: str = "web"
    thumbnail_url: Optional[str] = None
    author: Optional[str] = None
    age: Optional[str] = None
    published_date: Optional[datetime] = None
    content_fingerprint: Optional[str] = None
    raw_data: Dict = None

@dataclass
class UserConfig:
    """User keyword configuration."""
    user_keyword_id: str
    user_id: str
    display_text: Optional[str]
    associated_keywords: List[str]
    excluded_keywords: List[str]
    project_type: str	
    is_active: bool
    check_frequency_hours: int = USER_KEYWORD_CHECK_FREQUENCY_HOURS

class CacheManager:
    """Manages caching of search results."""
    
    def __init__(self):
        try:
            import redis
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=False)
            self.redis_client.ping()  # Test connection
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory cache: {e}")
            self.redis_client = None
        
        self.memory_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
    
    def get_cache_key(self, keyword_text: str, search_date: str = None) -> str:
        """Generate cache key for search results."""
        if not search_date:
            search_date = datetime.now().strftime('%Y-%m-%d')
        
        cache_data = {
            'keyword': keyword_text.lower().strip(),
            'max_results': MAX_RESULTS_PER_SEARCH,
            'date': search_date
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return f"search_results:{hashlib.md5(cache_string.encode()).hexdigest()}"
    
    def get_cached_results(self, cache_key: str) -> Optional[List[Dict]]:
        """Retrieve cached search results."""
        try:
            if self.redis_client:
                cached_data = self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_hits += 1
                    return pickle.loads(cached_data)
            elif cache_key in self.memory_cache:
                self.cache_hits += 1
                return self.memory_cache[cache_key]
            
            self.cache_misses += 1
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            self.cache_misses += 1
            return None
    
    def set_cached_results(self, cache_key: str, results: List[Dict], expiry_hours: int = 24):
        """Cache search results."""
        try:
            if self.redis_client:
                self.redis_client.setex(
                    cache_key, 
                    expiry_hours * 3600, 
                    pickle.dumps(results)
                )
            else:
                self.memory_cache[cache_key] = results
                # Simple cleanup for memory cache
                if len(self.memory_cache) > 100:
                    oldest_keys = sorted(self.memory_cache.keys(), 
                                      key=lambda k: self.memory_cache[k]['timestamp'])[:20]
                    for key in oldest_keys:
                        self.memory_cache.pop(key, None)
        except Exception as e:
            logger.error(f"Error caching results: {e}")

class SearchResultFetcher:
    """Handles fetching of search results from various sources."""
    
    def __init__(self):
        self.cache_manager = CacheManager()
        self.last_fetch_time = {}
    
    async def fetch_search_results(self, keyword: Keywords, force_fresh: bool = False) -> Optional[List[Dict]]:
        """Fetch search results for a keyword, using cache when possible."""
        cache_key = self.cache_manager.get_cache_key(keyword.text)
        
        # Try cache first unless forced fresh
        if not force_fresh:
            cached_results = self.cache_manager.get_cached_results(cache_key)
            if cached_results:
                logger.info(f"Using cached results for keyword: {keyword.text}")
                return cached_results
        
        # Fetch fresh results
        logger.info(f"Fetching fresh results for keyword: {keyword.text}")
        self.last_fetch_time[keyword.id] = datetime.utcnow()
        
        try:
            # Determine search parameters
            now = datetime.utcnow()
            is_new_keyword = keyword.created_at > (now - timedelta(hours=24))
            last_checked_at = None if is_new_keyword else keyword.last_checked
            time_period = None if is_new_keyword else 'd'
            
            # Perform search based on configuration
            raw_results = await self._perform_search(
                keyword.text, 
                last_checked_at, 
                time_period
            )
            
            if raw_results:
                # Cache the results
                self.cache_manager.set_cached_results(cache_key, raw_results)
                logger.info(f"Cached {len(raw_results)} results for keyword: {keyword.text}")
            
            return raw_results
            
        except Exception as e:
            logger.error(f"Error fetching search results for '{keyword.text}': {e}", exc_info=True)
            return None
    
    async def _perform_search(self, keyword_text: str, last_checked_at: datetime = None, 
                            time_period: str = None) -> Optional[List[Dict]]:
        """Perform the actual search using configured scraper."""
        try:
            if DEFAULT_USE_SERPER_API:
                scraper = SerperScraper(keyword_text)
                search_data = await scraper.search_serper(
                    num_results=MAX_RESULTS_PER_SEARCH,
                    last_checked_at=last_checked_at
                )
            elif DEFAULT_USE_GOOGLE_API:
                scraper = GoogleScraper(keyword_text)
                search_data = await scraper.search_google(
                    num_results=MAX_RESULTS_PER_SEARCH,
                    use_google_api=True
                )
            else:
                scraper = GoogleScraper(keyword_text)
                search_data = await scraper.search_google(
                    num_results=MAX_RESULTS_PER_SEARCH,
                    use_google_api=False,
                    time_period=time_period
                )
            
            if not search_data or not search_data.get("organic_results"):
                logger.warning(f"No organic results found for keyword: {keyword_text}")
                return None
            
            return search_data["organic_results"]
            
        except Exception as e:
            logger.error(f"Search failed for '{keyword_text}': {e}")
            raise

class UserFilterProcessor:
    """Handles user-specific filtering and processing of search results."""
    
    @staticmethod
    def generate_content_fingerprint(result: Dict) -> str:
        """Generate a unique fingerprint for a search result."""
        title = result.get("title", "").strip().lower()
        description = (result.get("description", "") or result.get("snippet", "")).strip().lower()
        
        # For short content, include URL for better uniqueness
        if len(title) < 20 and len(description) < 50:
            url = result.get("link", "").lower()
            content = f"{title}|{description}|{url}"
        else:
            content = f"{title}|{description}"
        
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def apply_user_filters(results: List[Dict], user_config: UserConfig) -> List[Dict]:
        """Apply user-specific include/exclude filters to search results."""
        if not results:
            return []
        
        filtered_results = []
        
        for result in results:
            title = result.get("title", "").lower()
            description = result.get("description", "").lower()
            url = result.get("link", "").lower()
            full_text = f"{title} {description} {url}"
            
            # Apply exclusion filters
            if user_config.excluded_keywords:
                should_exclude = any(
                    excluded.lower() in full_text 
                    for excluded in user_config.excluded_keywords
                    if excluded.strip()
                )
                if should_exclude:
                    continue
            
            # Apply inclusion filters (if specified, at least one must match)
            if user_config.associated_keywords:
                has_required = any(
                    associated.lower() in full_text
                    for associated in user_config.associated_keywords
                    if associated.strip()
                )
                # Also check for the primary keyword
                primary_keyword = (user_config.display_text or "").lower().strip()
                if not has_required and primary_keyword:
                    has_required = primary_keyword in full_text
                if not has_required:
                    continue
            
            # Add fingerprint
            result["content_fingerprint"] = UserFilterProcessor.generate_content_fingerprint(result)
            filtered_results.append(result)
        
        return filtered_results
    
    async def get_existing_fingerprints(self, session: Session, user_keyword_id: str, 
                                     days_back: int = 30) -> Set[str]:
        """Get existing content fingerprints for deduplication."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        
        stmt = select(UserMentions.content_fingerprint).where(
            and_(
                UserMentions.user_keyword_id == user_keyword_id,
                UserMentions.created_at >= cutoff_date,
                UserMentions.content_fingerprint.isnot(None)
            )
        )
        
        result = session.execute(stmt)
        return {row[0] for row in result.fetchall()}
    
    async def deduplicate_results(self, session: Session, user_keyword_id: str, 
                                results: List[Dict]) -> Tuple[List[Dict], int]:
        """Remove duplicate results based on content fingerprints."""
        existing_fingerprints = await self.get_existing_fingerprints(session, user_keyword_id)
        
        new_results = []
        duplicate_count = 0
        
        for result in results:
            fingerprint = result.get("content_fingerprint")
            if fingerprint in existing_fingerprints:
                duplicate_count += 1
                continue
            
            new_results.append(result)
            existing_fingerprints.add(fingerprint)  # Prevent intra-batch duplicates
        
        return new_results, duplicate_count

class MentionDataProcessor:
    """Handles analysis and storage of mention data."""
    
    async def analyze_results(self, results: List[Dict], keyword_text: str, user_config: UserConfig,
                            last_checked_at: datetime = None) -> Optional[Dict]:
        """Analyze search results using the Google analyzer."""
        if not results:
            return None
        
        try:
            analyzer = GoogleResultAnalyzer(
                results, 
                keyword=keyword_text, 
                excluded_keywords=user_config.excluded_keywords,
                associated_keywords=user_config.associated_keywords,    
                project_type=user_config.project_type,
                last_checked_at=last_checked_at
            )
            analysis = analyzer.analyze()
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing results for '{keyword_text}': {e}")
            return None
    
    async def store_user_mentions(self, session: Session, user_config: UserConfig, 
                                results: List[Dict], keyword_id: str):
        """Store user-specific mentions."""
        mentions_to_add = []
        
        for result in results:
            mention = UserMentions(
                user_keyword_id=user_config.user_keyword_id,
                keyword_id=keyword_id,
                user_id=user_config.user_id,
                position=result.get("position", 0),
                url=result.get("link", "")[:2000],  # Truncate long URLs
                title=result.get("title", "")[:500],  # Truncate long titles
                description=result.get("description", "")[:1000],  # Truncate long descriptions
                display_link=result.get("display_link", "")[:255],
                source_type=result.get("source_type", "web"),
                sentiment=result.get("sentiment", "neutral"),
                topic_id=result.get("topic_id"),
                topic_name=result.get("topic_name", "")[:255] if result.get("topic_name") else None,
                thumbnail_url=result.get("thumbnail"),
                author=result.get("author", "")[:255] if result.get("author") else None,
                age=result.get("age", "")[:100] if result.get("age") else None,
                keyword_count_title=result.get("keyword_count_title", 0),
                keyword_count_description=result.get("keyword_count_description", 0),
                content_fingerprint=result.get("content_fingerprint"),
                created_at=datetime.utcnow()
            )
            #print("mention topics:", mention.topic_name)
            # Parse published date if available
            if result.get("date_published"):
                try:
                    published_str = result["date_published"].replace("Z", "+00:00")
                    mention.published_date = datetime.fromisoformat(published_str)
                except (ValueError, TypeError, AttributeError):
                    pass
            
            mentions_to_add.append(mention)
        
        # Bulk insert for better performance
        if mentions_to_add:
            session.add_all(mentions_to_add)
    
    async def store_analysis_data(self, session: Session, user_keyword_id: str, 
                                analysis: Dict, results: List[Dict]):
        """Store topic distribution, sentiment analysis, and domain statistics."""
        try:
            # Store topic distribution
            await self._store_topic_distribution(session, user_keyword_id, analysis, results)
            
            # Store sentiment analysis
            sentiment_data = analysis.get("topic_analysis", {}).get("sentiment_distribution", {})
            await self._store_sentiment_analysis(session, user_keyword_id, sentiment_data)
            
            # Store domain statistics
            domain_data = analysis.get("top_domains", [])
            domain_source_types = analysis.get("domain_source_types", {})
            await self._store_domain_statistics(session, user_keyword_id, domain_data, domain_source_types)
            
            # Store source types
            await self._store_source_type_statistics(session, user_keyword_id, analysis["source_types"])

        
        except Exception as e:
            logger.error(f"Error storing analysis data for user_keyword {user_keyword_id}: {e}")
    
    async def _store_topic_distribution(self, session: Session, user_keyword_id: str, 
                                      analysis: Dict, results: List[Dict]):
        """Store user-specific topic distribution."""
        topics = analysis.get("topic_analysis", {}).get("topics", [])
        
        # Create topic name to UUID mapping
        topic_name_to_uuid = {}
        for result in results:
            topic_name = result.get("topic_name", "").strip().lower()
            topic_id = result.get("topic_id")
            if topic_name and topic_id:
                topic_name_to_uuid[topic_name] = topic_id
        
        # Handle uncategorized results
        uncategorized_count = sum(1 for r in results if r.get("topic_name", "").strip().lower() == "uncategorized")
        total_results = len(results) if results else 1
        
        if uncategorized_count > 0:
            uncategorized_topic = UserTopicDistribution(
                id=str(uuid.UUID("00000000-0000-0000-0000-000000000000")),
                user_keyword_id=user_keyword_id,
                topic_name="Uncategorized",
                percentage=round((uncategorized_count / total_results) * 100, 2)
            )
            session.merge(uncategorized_topic)
        
        # Store categorized topics
        for topic in topics:
            topic_name = topic.get("topic_name", "").strip().lower()
            topic_uuid = topic_name_to_uuid.get(
                topic_name, 
                str(uuid.uuid5(uuid.NAMESPACE_DNS, topic_name))
            )
            
            topic_dist = UserTopicDistribution(
                id=topic_uuid,
                user_keyword_id=user_keyword_id,
                topic_name=topic.get("topic_name", ""),
                percentage=round(topic.get("percentage", 0.0), 2)
            )
            
            session.merge(topic_dist)
            session.flush()
            
            # Store topic keywords
            for keyword in topic.get("keywords", []):
                topic_keyword = UserTopicKeywords(
                    topic_distribution_id=topic_dist.id,
                    user_keyword_id=user_keyword_id,
                    keyword=keyword[:255]  # Truncate if too long
                )
                session.merge(topic_keyword)
    
    async def _store_sentiment_analysis(self, session: Session, user_keyword_id: str, 
                                      sentiment_data: Dict):
        """Store user-specific sentiment analysis."""
        for sentiment_type, percentage in sentiment_data.items():
            sentiment = UserSentimentAnalysis(
                user_keyword_id=user_keyword_id,
                sentiment_type=sentiment_type,
                percentage=round(percentage, 2)
            )
            session.add(sentiment)
    
    async def _store_domain_statistics(self, session: Session, user_keyword_id: str, 
                                     domain_data: List[Tuple], domain_source_types: Dict):
        """Store user-specific domain statistics."""
        for domain, count in domain_data:
            domain_stat = UserDomainStatistics(
                user_keyword_id=user_keyword_id,
                domain=domain,
                source_type=domain_source_types.get(domain, "web"),
                count=count
            )
            session.add(domain_stat)
    
    async def _store_source_type_statistics(self, session: Session, user_keyword_id: str,
                                          source_types: Dict):
        """Store source type statistics in the database."""
        for source_type, count in source_types.items():
            source_stat = UserSourceTypeStatistics(
                user_keyword_id=user_keyword_id,
                source_type=source_type,
                count=count
            )
            session.add(source_stat)

    async def store_signals(self, session, user_config: UserConfig, signals: List[Dict]):
        """
        Store signals in the database.

        :param session: Database session
        :param user_keyword_id: ID of the user_keywords row
        :param user_id: ID of the user
        :param keyword_id: ID of the keyword
        :param project_type: Project type string
        :param signals: List of signal dictionaries to store
        """
        from models import UserSignals, SignalTypeEnum
        import json
        from datetime import datetime
        print(f"Storing {len(signals)} signals for user_keyword_id={user_config.user_keyword_id}")
        for signal_dict in signals:
            # Convert Enum to string if needed
            project_type = user_config.project_type
            if hasattr(project_type, "value"):
                project_type = project_type.value
                
            signal_type = signal_dict.get("signal_type")
            if isinstance(signal_type, str):
                signal_type = SignalTypeEnum(signal_type.lower())

            signal = UserSignals(
                user_keyword_id=user_config.user_keyword_id,
                user_id=user_config.user_id,
                project_type=project_type,  # <-- Now always a string
                signal_type=signal_type,
                title=signal_dict.get("title"),
                description=signal_dict.get("description"),
                url=signal_dict.get("url"),
                confidence=signal_dict.get("confidence", 0.0),
                impact_score=signal_dict.get("impact_score", 0.0),
                extra_data=json.dumps(signal_dict.get("extra_data", {})),
                detected_at=datetime.utcnow()
            )
            session.add(signal)
        try:
            session.commit()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error storing signals: {str(e)}")
            session.rollback()

class OptimizedUserMentionProcessor:
    """Main processor that orchestrates the entire user-specific mention processing workflow."""
    
    def __init__(self):
        self.fetcher = SearchResultFetcher()
        self.filter_processor = UserFilterProcessor()
        self.data_processor = MentionDataProcessor()
        self.keyword_last_processed = {}
    
    async def get_user_keywords_to_process(self, session: Session, limit: int = MAX_KEYWORDS_PER_BATCH) -> List[Tuple[Keywords, UserConfig]]:
        """Get user keyword configurations that need processing based on individual schedules."""
        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)

        stmt = (
            select(UserKeywords)
            .join(Keywords, UserKeywords.keyword_id == Keywords.id)
            .where(
                and_(
                    UserKeywords.is_active == True,
                    Keywords.auto_scan == True,
                    or_(
                        UserKeywords.last_processed_at.is_(None),
                        UserKeywords.last_processed_at <= twenty_four_hours_ago
                    )
                )
            )
            .order_by(
                UserKeywords.last_processed_at.asc().nulls_first(),
                Keywords.last_checked.asc().nulls_first()
            )
            .limit(limit)
            .options(
                selectinload(UserKeywords.keyword),
                selectinload(UserKeywords.user)
            )
        )
        result = session.execute(stmt)
        user_keywords = result.scalars().all()
        
        print(f"Found {len(user_keywords)} user keywords to process")
        print(f"User keywords: {[uk.keyword.text for uk in user_keywords]}")
        print(f"User keyword IDs: {[uk.id for uk in user_keywords]}")
        
        configs = []
        for uk in user_keywords:
            config = UserConfig(
                user_keyword_id=uk.id,
                user_id=uk.user_id,
                display_text=uk.display_text,
                associated_keywords=uk.associated_keywords or [],
                excluded_keywords=uk.excluded_keywords or [],
                project_type=uk.project_type,
                is_active=uk.is_active,
                check_frequency_hours=uk.check_frequency or USER_KEYWORD_CHECK_FREQUENCY_HOURS
            )
            configs.append((uk.keyword, config))
        
        return configs
    
    async def process_user_keyword(self, session: Session, keyword: Keywords, user_config: UserConfig) -> int:
        """Process a single user keyword configuration."""
        logger.info(f"Processing keyword '{keyword.text}' for user {user_config.user_id}")
        
        # Determine if we need fresh results
        need_fresh_results = (
            keyword.last_checked is None or
            keyword.last_checked < datetime.utcnow() - timedelta(hours=user_config.check_frequency_hours)
        )
        
        # 1. Fetch results (fresh or cached based on need)
        raw_results = await self.fetcher.fetch_search_results(
            keyword, 
            force_fresh=need_fresh_results
        )
        
        if not raw_results:
            logger.warning(f"No search results for keyword: {keyword.text}")
            return 0
        
        # 2. Process the user configuration
        try:
            user_mention_count = await self._process_user_configuration(
                session, keyword, raw_results, user_config
            )
            
            # Update processing timestamps
            current_time = datetime.utcnow()
            
            # Update user keyword last processed time
            stmt = (
                update(UserKeywords)
                .where(UserKeywords.id == user_config.user_keyword_id)
                .values(
                    last_processed_at=current_time,
                    processing_status='completed'
                )
            )
            session.execute(stmt)
            
            # Update keyword's last checked time if we fetched fresh results
            if need_fresh_results:
                keyword.last_checked = current_time
                keyword.is_priority = False
            
            return user_mention_count
            
        except Exception as e:
            logger.error(f"Error processing user config {user_config.user_keyword_id}: {e}")
            
            # Mark as failed
            stmt = (
                update(UserKeywords)
                .where(UserKeywords.id == user_config.user_keyword_id)
                .values(
                    processing_status='failed',
                    #last_error=str(e)[:500]  # Truncate long error messages
                )
            )
            session.execute(stmt)
            
            return 0
    
    async def _process_user_configuration(self, session: Session, keyword: Keywords, 
                                        raw_results: List[Dict], user_config: UserConfig) -> int:
        """Process a single user configuration against raw search results."""

        # 1. Apply user-specific filters
        filtered_results = self.filter_processor.apply_user_filters(raw_results, user_config)
        if not filtered_results:
            logger.debug(f"No results after filtering for user {user_config.user_id}")
            return 0
        
        # 2. Deduplicate against existing user mentions
        new_results, duplicate_count = await self.filter_processor.deduplicate_results(
            session, user_config.user_keyword_id, filtered_results
        )
        
        logger.info(f"User {user_config.user_id} - {keyword.text}: "
                   f"{len(new_results)} new, {duplicate_count} duplicates")
        
        if not new_results:
            return 0
        
        # 3. Analyze the new results
        analysis = await self.data_processor.analyze_results(
            new_results, keyword.text, user_config,  keyword.last_checked
        )
        
        if not analysis:
            logger.warning(f"No analysis results for user keyword: {user_config.user_keyword_id}")
            return 0
        
        enhanced_results = analysis.get("enhanced_results", new_results)
        if not enhanced_results:
            logger.warning(f"No enhanced results after analysis for user keyword: {user_config.user_keyword_id}")
            return 0
        
        # Ensure all results have a content fingerprint
        for result in enhanced_results:
            if "content_fingerprint" not in result:
                result["content_fingerprint"] = self.filter_processor.generate_content_fingerprint(result)
        # Deduplicate again after analysis
        enhanced_results, analysis_duplicate_count = await self.filter_processor.deduplicate_results( 
            session, user_config.user_keyword_id, enhanced_results
        )
    
        # Store the analysis data
        await self.data_processor.store_analysis_data(
            session, user_config.user_keyword_id, analysis, enhanced_results
        )

        # 4. Map topic IDs and enhance results
        
        map_topic_ids_from_db(session, user_config.user_keyword_id, enhanced_results)
        
        # 5. Store all user-specific data
        await self.data_processor.store_user_mentions(
            session, user_config, enhanced_results, keyword.id
        )

        # 6, Store signals if available
        signals = analysis.get("topic_analysis", {}).get("signals", [])
        print('storing signals:', signals)
        await self.data_processor.store_signals(
            session, user_config, signals
        )
        
        
        return len(enhanced_results)
    
    async def run_processing_job(self) -> Dict[str, Any]:
        """Main entry point for the processing job."""
        logger.info("Starting optimized user-specific mention processing job")
        
        session = next(get_db_session())
        job_history = JobHistory(
            job_name="optimized_user_mention_processor",
            start_time=datetime.utcnow(),
            status="in_progress"
        )
        session.add(job_history)
        session.commit()
        
        stats = {
            "user_keywords_processed": 0,
            "keywords_processed": 0,
            "total_mentions_stored": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "errors": []
        }
        
        try:
            # Get user keyword configurations that need processing
            user_keyword_configs = await self.get_user_keywords_to_process(session)
            
            if not user_keyword_configs:
                logger.info("No user keyword configurations need processing at this time")
                job_history.status = "success"
                job_history.items_processed = 0
                job_history.end_time = datetime.utcnow()
                session.commit()
                return stats
            
            logger.info(f"Processing {len(user_keyword_configs)} user keyword configurations")
            
            # Group by keyword to optimize processing
            keyword_groups = defaultdict(list)
            for keyword, config in user_keyword_configs:
                keyword_groups[keyword].append(config)
            
            # Process each keyword group
            processed_keywords = set()
            for keyword, configs in keyword_groups.items():
                try:
                    # Process all user configs for this keyword
                    for config in configs:
                        mention_count = await self.process_user_keyword(
                            session, keyword, config
                        )
                        
                        stats["user_keywords_processed"] += 1
                        stats["total_mentions_stored"] += mention_count
                    
                    stats["keywords_processed"] += 1
                    processed_keywords.add(keyword.id)
                    
                    # Commit after each keyword group
                    session.commit()
                    
                except Exception as e:
                    error_msg = f"Error processing keyword {keyword.text}: {str(e)}"
                    logger.error(error_msg, exc_info=True)
                    stats["errors"].append(error_msg)
                    session.rollback()
                    continue
            
            # Add cache statistics
            stats["cache_hits"] = self.fetcher.cache_manager.cache_hits
            stats["cache_misses"] = self.fetcher.cache_manager.cache_misses
            
            # Update job history
            job_history.status = "success"
            job_history.items_processed = stats["user_keywords_processed"]
            job_history.end_time = datetime.utcnow()
            session.commit()
            
            logger.info(f"Job completed successfully. Stats: {stats}")
            
        except Exception as e:
            error_msg = f"Fatal error in processing job: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            job_history.status = "failure"
            job_history.error_message = error_msg
            job_history.end_time = datetime.utcnow()
            session.commit()
            
            stats["errors"].append(error_msg)
            
        finally:
            session.close()
        
        return stats

# Public API functions for job scheduling
#async def run_optimized_user_mention_processing():
#    """Entry point for the optimized user mention processing job."""
#    processor = OptimizedUserMentionProcessor()
#    return await processor.run_processing_job()
#
#async def process_priority_keywords():
#    """Process only keywords marked as priority."""
#    session = next(get_db_session())
#    try:
#        # Mark some keywords as priority for immediate processing
#        stmt = (
#            update(Keywords)
#            .where(
#                and_(
#                    Keywords.auto_scan == True,
#                    Keywords.last_checked.is_(None)
#            )
#            .values(is_priority=True)
#            .limit(10)
#        )
#        session.execute(stmt)
#        session.commit()
#        
#        # Run the normal processing job which will prioritize these keywords
#        return await run_optimized_user_mention_processing()
#        
#    finally:
#        session.close()