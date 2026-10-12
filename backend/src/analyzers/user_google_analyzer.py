from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime
from datetime import timedelta
import logging
from collections import defaultdict, Counter
from urllib.parse import urlparse
from typing import List, Dict, Optional, Union, Set
import re
import json
import random
import hashlib

# INTERNAL IMPORTS
from .source_type_map import SOURCE_TYPE_MAP  # Import the source type map

# Configure logging
logger = logging.getLogger(__name__)

class UserSpecificResultAnalyzer:
    """A class to analyze search results with user-specific filtering and caching."""

    def __init__(self, results: List[Dict[str, Union[str, int]]], keyword: str = None, 
                 user_id: int = None, associated_keywords: List[str] = None, 
                 excluded_keywords: List[str] = None, last_checked_at: Optional[datetime.datetime] = None):
        """
        Initialize the analyzer with search results and user-specific parameters.

        :param results: List of search result dictionaries.
        :param keyword: The main keyword being searched for.
        :param user_id: ID of the user for user-specific filtering.
        :param associated_keywords: List of keywords that should be present (user-specific).
        :param excluded_keywords: List of keywords to exclude (user-specific).
        :param last_checked_at: Last time this keyword was checked.
        """
        self.results = results
        self.keyword = keyword.lower() if keyword else None
        self.user_id = user_id
        self.associated_keywords = [kw.lower() for kw in associated_keywords] if associated_keywords else []
        self.excluded_keywords = [kw.lower() for kw in excluded_keywords] if excluded_keywords else []
        self.last_checked_at = last_checked_at
        
        # Analysis results
        self.enhanced_results = []
        self.filtered_results = []
        self.timeline = defaultdict(int)
        self.source_counter = Counter()
        self.source_type_counter = Counter()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        
        # Cache key for this specific user configuration
        self.cache_key = self._generate_cache_key()
        
    def _generate_cache_key(self) -> str:
        """Generate a unique cache key based on user filtering criteria."""
        filter_data = {
            'keyword': self.keyword,
            'user_id': self.user_id,
            'associated_keywords': sorted(self.associated_keywords),
            'excluded_keywords': sorted(self.excluded_keywords)
        }
        cache_string = json.dumps(filter_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()

    def filter_results_for_user(self) -> List[Dict]:
        """
        Filter results based on user-specific criteria including associated and excluded keywords.
        
        Returns:
            List[Dict]: Filtered list of search results for this specific user
        """
        if not self.results:
            logger.info("No results to filter")
            return []
            
        filtered = []
        skipped_count = 0
        excluded_count = 0
        associated_missing_count = 0
        date_filtered_count = 0
        
        # Handle the main keyword
        if self.keyword:
            original_keyword = self.keyword.lower()
            cleaned_keyword = re.sub(r'[^\w\s]', ' ', self.keyword)
            main_keywords = [k for k in cleaned_keyword.lower().split() if k]
        else:
            original_keyword = ""
            main_keywords = []
        
        for result in self.results:
            # Safely get title, description, and URLs with fallbacks
            title = (result.get("title") or "").lower()
            
            description = ""
            age = ""
            if result.get("age"):
                age = result["age"].lower()
            if result.get("description"):
                description = result["description"].lower()
            elif result.get("snippet"):
                description = result["snippet"].lower()
            elif result.get("html_snippet"):
                description = re.sub(r'<[^>]+>', '', result.get("html_snippet", "")).lower()
            
            # Get URLs for checking
            url = (result.get("url") or "").lower()
            displayed_url = (result.get("displayed_url") or "").lower()
            domain = (result.get("domain") or "").lower()
            
            # If there's still no content to search, skip this result
            if not title and not description and not url and not displayed_url:
                logger.debug(f"Skipped: no searchable content found in result")
                skipped_count += 1
                continue

            # Date filtering (same as before)
            if self.last_checked_at is not None:
                should_skip = False
                date_sources = [description, age]

                # Check for relative time indicators
                if any(re.search(r"(\d{1,2})\s+hours?\s+ago", src) for src in date_sources):
                    match = next((re.search(r"(\d{1,2})\s+hours?\s+ago", src) for src in date_sources if re.search(r"(\d{1,2})\s+hours?\s+ago", src)), None)
                    hours_ago = int(match.group(1))
                    if hours_ago > 24:
                        logger.info(f"Skipped: too old (more than 24 hours) -> {title[:40]}...")
                        skipped_count += 1
                        date_filtered_count += 1
                        should_skip = True

                elif any(re.search(r"(day|days|week|month|year)\s+ago", src) or re.search(r"\d+\s+(day|days|week|weeks|month|months|year|years)\s+ago", src) for src in date_sources):
                    logger.info(f"Skipped: too old (days/weeks/months/years) -> {title[:40]}...")
                    skipped_count += 1
                    date_filtered_count += 1
                    should_skip = True

                # Check for standard date formats
                else:
                    date_patterns = [
                        r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}',
                        r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{4}',
                        r'\d{4}[/\-\.]\d{1,2}[/\-\.]\d{1,2}',
                        r'\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}'
                    ]
                    for src in date_sources:
                        for pattern in date_patterns:
                            date_match = re.search(pattern, src, re.IGNORECASE)
                            if date_match:
                                date_str = date_match.group(0)
                                parsed_date = None
                                try:
                                    from dateutil import parser as date_parser
                                    parsed_date = date_parser.parse(date_str, fuzzy=True)
                                except (ValueError, ImportError):
                                    date_formats = [
                                        "%b %d, %Y", "%B %d, %Y", 
                                        "%d/%m/%Y", "%Y/%m/%d", 
                                        "%d-%m-%Y", "%Y-%m-%d",
                                        "%d %b %Y", "%d %B %Y"
                                    ]
                                    for fmt in date_formats:
                                        try:
                                            parsed_date = datetime.datetime.strptime(date_str, fmt)
                                            break
                                        except ValueError:
                                            continue
                                if parsed_date:
                                    if (datetime.datetime.now() - parsed_date) > datetime.timedelta(days=1):
                                        logger.info(f"Skipped: date too old ({date_str}) -> {title[:40]}...")
                                        skipped_count += 1
                                        date_filtered_count += 1
                                        should_skip = True
                                        break
                        if should_skip:
                            break

                if should_skip:
                    continue
            
            # Combine all searchable content
            content = f"{title} {description} {url} {displayed_url} {domain}"
            
            # Check for main keyword match (same logic as before)
            if self.keyword:
                url_content = f"{url} {displayed_url} {domain}"
                if original_keyword in url_content:
                    pass
                elif main_keywords:
                    all_keywords_present = True
                    for keyword in main_keywords:
                        pattern = rf"\b{re.escape(keyword)}\b"
                        if not re.search(pattern, content):
                            if keyword.endswith('s') and re.search(rf"\b{re.escape(keyword[:-1])}\b", content):
                                continue
                            elif not keyword.endswith('s') and re.search(rf"\b{re.escape(keyword)}s\b", content):
                                continue
                            elif keyword in url or keyword in displayed_url or keyword in domain:
                                continue
                            
                            all_keywords_present = False
                            break
                            
                    if not all_keywords_present:
                        logger.debug(f"Skipped: missing main keyword component -> {title[:40]}...")
                        skipped_count += 1
                        continue
            
            # NEW: Check for user-specific associated keywords (ALL must be present)
            if self.associated_keywords:
                missing_associated = False
                for associated_kw in self.associated_keywords:
                    pattern = rf"\b{re.escape(associated_kw)}\b"
                    if not re.search(pattern, content):
                        # Check for plurals and variations
                        if associated_kw.endswith('s') and re.search(rf"\b{re.escape(associated_kw[:-1])}\b", content):
                            continue
                        elif not associated_kw.endswith('s') and re.search(rf"\b{re.escape(associated_kw)}s\b", content):
                            continue
                        elif associated_kw in url or associated_kw in displayed_url or associated_kw in domain:
                            continue
                        
                        logger.debug(f"Skipped: missing associated keyword '{associated_kw}' -> {title[:40]}...")
                        associated_missing_count += 1
                        missing_associated = True
                        break
                
                if missing_associated:
                    continue
            
            # NEW: Check for user-specific excluded keywords (ANY present = exclude)
            if self.excluded_keywords:
                excluded = False
                for excluded_kw in self.excluded_keywords:
                    pattern = rf"\b{re.escape(excluded_kw)}\b"
                    if re.search(pattern, content):
                        logger.debug(f"Excluded due to keyword '{excluded_kw}': {title[:40]}...")
                        excluded_count += 1
                        excluded = True
                        break
                        
                if excluded:
                    continue
            
            # Add to filtered results if it passed all checks
            filtered.append(result)
        
        # Summarize filtering results
        logger.info(f"User {self.user_id} filtering summary: {len(self.results)} total, "
                   f"{skipped_count} skipped, {date_filtered_count} date-filtered, "
                   f"{associated_missing_count} missing associated keywords, "
                   f"{excluded_count} excluded, {len(filtered)} kept")
        
        return filtered

    def infer_source_type(self, domain: str) -> str:
        """Infer the source type based on the domain."""
        for source_type, domains in SOURCE_TYPE_MAP.items():
            if any(domain.endswith(d) for d in domains):
                return source_type
        return "web"

    def get_domain_to_source_type_mapping(self):
        """Creates a mapping of domains to their source types from the analyzed results."""
        domain_source_types = {}
        
        for result in self.enhanced_results:
            if not result or not isinstance(result, dict):
                continue
                
            domain = result.get("domain")
            source_type = result.get("source_type", "web")
            if domain:
                domain_source_types[domain] = source_type
        
        for domain, _ in self.source_counter.most_common():
            if domain not in domain_source_types:
                source_type = self.infer_source_type(domain)
                domain_source_types[domain] = source_type
        
        return domain_source_types
 
    def get_sentiment(self, text: str) -> str:
        """Analyze the sentiment of a given text using VADER."""
        if not text:
            return "neutral"
        sentiment_scores = self.sentiment_analyzer.polarity_scores(text)
        compound_score = sentiment_scores["compound"]
        if compound_score > 0.05:
            return "positive"
        elif compound_score < -0.05:
            return "negative"
        else:
            return "neutral"

    def parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse a date string into a datetime.date object."""
        if not date_str:
            return None
        try:
            return datetime.datetime.fromisoformat(date_str).date()
        except (ValueError, TypeError):
            return None

    def process_result(self, result: Dict[str, Union[str, int]]) -> Dict[str, Union[str, int]]:
        """Process a single search result to add domain, source type, and sentiment."""
        if not result:
            logger.debug(f"Skipped: empty result object")
            return None
        
        domain = result.get("display_link") or urlparse(result.get("link", "")).netloc
        source_type = self.infer_source_type(domain)
        
        snippet = result.get("snippet", "")
        description = result.get("description", "")
        
        if not snippet and not description:
            logger.debug(f"Skipped: no text content for sentiment analysis")
            result.update({
                "domain": domain,
                "source_type": source_type,
                "vader_sentiment": "neutral",
                "sentiment": "neutral"
            })
            return result
        
        initial_sentiment = self.get_sentiment(snippet or description)
        date_obj = self.parse_date(result.get("date_published", ""))

        if date_obj:
            self.timeline[date_obj.isoformat()] += 1

        self.source_counter[domain] += 1
        self.source_type_counter[source_type] += 1

        result.update({
            "domain": domain,
            "source_type": source_type,
            "vader_sentiment": initial_sentiment,
            "sentiment": initial_sentiment
        })

        # Count keyword occurrences
        if self.keyword:
            title = result.get("title", "").lower()
            description = result.get("description", "").lower() or result.get("snippet", "").lower()
            
            result["keyword_count_title"] = title.count(self.keyword)
            result["keyword_count_description"] = description.count(self.keyword)

        return result

    def analyze_topics_and_sentiment_with_llm(self):
        """Use an LLM to identify topics and sentiment in search results with intelligent sampling."""
        import json
        from google import genai
        import os

        client = genai.Client(api_key=os.getenv("GEN_AI_API_KEY"))

        if not self.filtered_results:
            logger.warning(f'No result to feed to LLM for topic matching and sentiment analysis')
            return {
                "topics": [],
                "topic_distribution": {},
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 100}
            }
            
        print(f"Filtered results for user {self.user_id}: {len(self.filtered_results)}")
        
        # Determine how many results to sample
        total_results = len(self.filtered_results)
        sample_size = min(100, total_results)
        
        if total_results <= sample_size:
            sampled_indices = list(range(total_results))
        else:
            # Stratified sampling
            top_count = sample_size // 3
            bottom_count = sample_size // 3
            middle_count = sample_size - top_count - bottom_count
            
            top_indices = list(range(top_count))
            bottom_indices = list(range(total_results - bottom_count, total_results))
            
            middle_range = list(range(top_count, total_results - bottom_count))
            middle_indices = random.sample(middle_range, min(middle_count, len(middle_range)))
            
            sampled_indices = top_indices + middle_indices + bottom_indices
        
        sampled_results = [self.filtered_results[i] for i in sampled_indices]
        docs = []
        for result in sampled_results:
            title = result.get("title", "")
            description = result.get("description", "") or result.get("snippet", "")
            docs.append(f"Title: {title}\nDescription: {description}")

        sample_text = "\n\n---\n\n".join(docs)

        # Updated prompt to include user-specific context
        prompt = f"""
        Analyze the following search results for the keyword '{self.keyword}' and identify the main topics discussed and the sentiment of each result.
        
        User Context:
        - User ID: {self.user_id}
        - Associated keywords: {', '.join(self.associated_keywords) if self.associated_keywords else 'None'}
        - Excluded keywords: {', '.join(self.excluded_keywords) if self.excluded_keywords else 'None'}
        
        Part 1 - For each topic:
        1. Provide a short, descriptive name (2-4 words)
        2. List 5-7 keywords associated with this topic
        3. Estimate what percentage of the content relates to this topic

        Part 2 - For each search result, determine the sentiment:
        1. Classify as ONLY ONE of: 'positive', 'negative', or 'neutral'
        2. Use the following strict criteria:
        - 'positive': Clearly positive language, endorsements, success stories, benefits
        - 'negative': Criticisms, problems, warnings, risks, failures
        - 'neutral': Factual information, balanced viewpoints, educational content
        3. If in doubt, classify as 'neutral'
        4. Include a confidence score (0-100) for the sentiment classification
        
        Format your response as a JSON object with:
        1. A "topics" field containing a list of topic objects (each with "topic_name", "keywords", and "percentage")
        2. A "sentiments" field containing a list of sentiment objects in the same order as the provided search results (each with "sentiment" and "confidence")

        Search results:
        {sample_text}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
        
            llm_output = response.candidates[0].content.parts[0].text.strip()
            clean_output = re.sub(r"^```json|```$", "", llm_output).strip()
            
            analysis = json.loads(clean_output)
            topics = analysis.get("topics", [])
            sentiments = analysis.get("sentiments", [])
            logger.info(f"LLM response for user {self.user_id}: {len(topics)} topics, {len(sentiments)} sentiments")
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response for user {self.user_id}: {str(e)}")
            return {
                "topics": [], 
                "topic_distribution": {}, 
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 100},
                "error": f"Failed to parse LLM response: {str(e)}"
            }
            
        # Create sentiment map for sampled results
        sentiment_map = {}
        for i, idx in enumerate(sampled_indices):
            if i < len(sentiments):
                sentiment_map[idx] = sentiments[i]
        
        NO_TOPIC_UUID = "00000000-0000-0000-0000-000000000000"
        
        # Assign topics and sentiments to all results
        for i, result in enumerate(self.filtered_results):
            if not result or not isinstance(result, dict):
                logger.debug(f"Skipped: result is not a dictionary at index {i}")
                continue
                
            title = result.get("title", "")
            description = result.get("description", "") or result.get("snippet", "")

            if not title or not description:
                logger.debug(f"Skipped: no searchable content found in result")
                result["topic_id"] = NO_TOPIC_UUID
                result["topic_name"] = "Uncategorized"
                result["sentiment"] = "neutral"
                result["sentiment_confidence"] = 50
                continue

            # Topic assignment
            doc_text = (title + " " + description).lower()
            
            best_match = {"topic_id": NO_TOPIC_UUID, "topic_name": "Uncategorized", "score": 0}
            for t, topic in enumerate(topics):
                keywords = topic.get("keywords", [])
                score = sum(1 for keyword in keywords if keyword.lower() in doc_text)

                if score > best_match["score"]:
                    import uuid
                    topic_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, topic.get("topic_name", "")))
                    best_match = {
                        "topic_id": topic_uuid, 
                        "topic_name": topic.get("topic_name", ""), 
                        "score": score
                    }

            result["topic_id"] = best_match["topic_id"]
            result["topic_name"] = best_match["topic_name"]
            
            # Add sentiment
            if i in sentiment_map:
                result["sentiment"] = sentiment_map[i].get("sentiment", "neutral")
                result["sentiment_confidence"] = sentiment_map[i].get("confidence", 0)
            else:
                # Use sentiment from similar topic
                if result["topic_id"] != NO_TOPIC_UUID:
                    same_topic_results = [
                        idx for idx in sampled_indices 
                        if idx < len(self.filtered_results) and 
                        isinstance(self.filtered_results[idx], dict) and
                        self.filtered_results[idx].get("topic_id") == result["topic_id"]
                    ]
                    
                    if same_topic_results:
                        result["sentiment"] = self.filtered_results[same_topic_results[0]].get("sentiment", "neutral")
                        result["sentiment_confidence"] = self.filtered_results[same_topic_results[0]].get("sentiment_confidence", 0)
                    else:
                        result["sentiment"] = "neutral"
                        result["sentiment_confidence"] = 50
                else:
                    result["sentiment"] = "neutral"
                    result["sentiment_confidence"] = 50
        
        # Calculate sentiment distribution
        sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
        for result in self.filtered_results:
            if isinstance(result, dict):
                sentiment = result.get("sentiment", "neutral")
                sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        total = sum(sentiment_counts.values()) or 1
        sentiment_distribution = {k: round((v / total) * 100, 1) for k, v in sentiment_counts.items()}
        
        return {
            "topics": topics,
            "topic_distribution": {
                topic.get("topic_name"): topic.get("percentage") for topic in topics
            },
            "sentiment_distribution": sentiment_distribution
        }

    def analyze(self) -> Dict[str, Union[List[Dict], Dict, List]]:
        """
        Analyze search results with user-specific filtering to extract insights.

        :return: A dictionary containing enhanced results, timeline, top domains, and source types.
        """
        if not self.results:
            logger.warning(f'No results to analyze for user {self.user_id}')
            return {
                "enhanced_results": [],
                "timeline": {},
                "top_domains": [],
                "source_types": {},
                "domain_source_types": {},
                "topic_analysis": {"topics": [], "topic_distribution": {}, "sentiment_distribution": {}},
                "cache_key": self.cache_key,
                "user_id": self.user_id
            }
        
        # Filter results based on user-specific criteria
        self.filtered_results = self.filter_results_for_user()
        
        if not self.filtered_results:
            logger.warning(f'No filtered results for keyword: {self.keyword}, user: {self.user_id}')
            return {
                "enhanced_results": [],
                "timeline": {},
                "top_domains": [],
                "source_types": {},
                "domain_source_types": {},
                "topic_analysis": {"topics": [], "topic_distribution": {}, "sentiment_distribution": {}},
                "cache_key": self.cache_key,
                "user_id": self.user_id
            }
        
        self.enhanced_results = []
        for result in self.filtered_results:
            processed_result = self.process_result(result)
            if processed_result is not None:
                self.enhanced_results.append(processed_result)

        # Generate analysis
        analysis = {
            "enhanced_results": self.enhanced_results,
            "timeline": dict(sorted(self.timeline.items())),
            "top_domains": self.source_counter.most_common(10),
            "source_types": dict(self.source_type_counter),
            "cache_key": self.cache_key,
            "user_id": self.user_id
        }
        
        analysis["domain_source_types"] = self.get_domain_to_source_type_mapping()
        analysis["topic_analysis"] = self.analyze_topics_and_sentiment_with_llm()

        return analysis


# Backwards compatibility - keep the old class as a wrapper
class GoogleResultAnalyzer(UserSpecificResultAnalyzer):
    """Backwards compatible wrapper for the original GoogleResultAnalyzer."""
    
    def __init__(self, results: List[Dict[str, Union[str, int]]], keyword: str = None, 
                 excluded_words: List[str] = None, last_checked_at: Optional[datetime.datetime] = None):
        # Convert old excluded_words to new excluded_keywords format
        super().__init__(
            results=results,
            keyword=keyword,
            user_id=None,  # No specific user
            associated_keywords=[],
            excluded_keywords=excluded_words or [],
            last_checked_at=last_checked_at
        )
    
    def filter_results(self) -> List[Dict]:
        """Backwards compatible filter method."""
        return super().filter_results_for_user()