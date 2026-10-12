from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import datetime
from datetime import timedelta
import logging
from collections import defaultdict, Counter
from urllib.parse import urlparse
from typing import List, Dict, Optional, Union
import re
import json
import random

# INTERNAL IMPORTS
from .source_type_map import SOURCE_TYPE_MAP  # Import the source type map

# Configure logging
logger = logging.getLogger(__name__)

class GoogleResultAnalyzer:
    """A class to analyze search results and extract insights."""


    def __init__(self, results: List[Dict[str, Union[str, int]]], keyword: str = None, excluded_keywords: List[str] = None, associated_keywords: List[str] = None, project_type: str = None,  last_checked_at: Optional[datetime.datetime] = None):
        """
        Initialize the analyzer with search results.

        :param results: List of search result dictionaries.
        :param keyword: The main keyword being searched for.
        :param excluded_words: List of words to exclude from results.
        """
        self.results = results
        self.keyword = keyword.lower() if keyword else None
        self.project_type = (
            project_type.value.lower() if hasattr(project_type, "value") else str(project_type).lower()
        ) if project_type else 'brand monitoring'
        self.excluded_keywords = [word.lower() for word in excluded_keywords] if excluded_keywords else []
        self.associated_keywords = [word.lower() for word in associated_keywords] if associated_keywords else []	
        self.enhanced_results = []
        self.filtered_results = []
        self.timeline = defaultdict(int)
        self.source_counter = Counter()
        self.source_type_counter = Counter()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()  # Initialize VADER sentiment analyzer
        self.last_checked_at = last_checked_at
        
    def filter_results(self) -> List[Dict]:
        """
        Filter results based on keyword and excluded words with improved handling for URLs, multi-word keywords,
        and enhanced date detection.
        
        Returns:
            List[Dict]: Filtered list of search results
        """
        if not self.results:
            logger.info("No results to filter")
            return []
            
        filtered = []
        skipped_count = 0
        excluded_count = 0
        date_filtered_count = 0
        
        # Handle the keyword more intelligently
        if self.keyword:
            # Keep the original keyword (including dots for domains)
            original_keyword = self.keyword.lower()
            
            # Also create word-split version for regular content matching
            cleaned_keyword = re.sub(r'[^\w\s]', ' ', self.keyword)
            keywords = [k for k in cleaned_keyword.lower().split() if k]
        else:
            original_keyword = ""
            keywords = []
        
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

            # Date filtering
            if self.last_checked_at is not None:
                should_skip = False

                # Combine description and age for pattern matching
                date_sources = [description, age]

                # Check for relative time indicators in both description and age
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

                # Check for standard date formats anywhere in the description or age
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
                                logger.info(f"Found date pattern: {date_str}")
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
            
            # Check for keyword match with special handling for domains and URLs
            if self.keyword:
                url_content = f"{url} {displayed_url} {domain}"
                keyword_found = False

                # 1. Check for main keyword in URL content (with dots)
                if original_keyword in url_content:
                    keyword_found = True
                elif keywords:
                    # 2. Check if ALL individual main keywords are present in content
                    all_keywords_present = True
                    for keyword in keywords:
                        pattern = rf"\b{re.escape(keyword)}\b"
                        if not re.search(pattern, content):
                            # Special case for plurals and common variations
                            if keyword.endswith('s') and re.search(rf"\b{re.escape(keyword[:-1])}\b", content):
                                continue
                            elif not keyword.endswith('s') and re.search(rf"\b{re.escape(keyword)}s\b", content):
                                continue
                            elif keyword in url or keyword in displayed_url or keyword in domain:
                                continue
                            all_keywords_present = False
                            break
                    if all_keywords_present:
                        keyword_found = True

                # 3. If main keyword not found, check for associated keywords
                if not keyword_found and self.associated_keywords:
                    for assoc_kw in self.associated_keywords:
                        if assoc_kw and assoc_kw in content:
                            keyword_found = True
                            break

                if not keyword_found:
                    logger.debug(f"Skipped: missing keyword and associated keywords -> {title[:40]}...")
                    skipped_count += 1
                    continue
            # Check for excluded words
           # if self.excluded_keywords:
           #     excluded = False
           #     for word in self.excluded_keywords:
           #         exclude_pattern = rf"\b{re.escape(word.lower())}\b"
           #         if re.search(exclude_pattern, content):
           #             logger.debug(f"Excluded due to word '{word}': {title[:40]}...")
           #             excluded_count += 1
           #             excluded = True
           #             break
           #             
           #     if excluded:
           #         continue
            
            # Add to filtered results if it passed all checks
            filtered.append(result)
        
        # Summarize filtering results
        logger.info(f"Filtering summary: {len(self.results)} total, {skipped_count} skipped, "
                    f"(of which {date_filtered_count} were filtered by date), "
                    f"{excluded_count} excluded (excluded words), {len(filtered)} kept")
        
        return filtered

    def infer_source_type(self, domain: str) -> str:
        """Infer the source type based on the domain."""
        for source_type, domains in SOURCE_TYPE_MAP.items():
            if any(domain.endswith(d) for d in domains):
                return source_type
        return "web"

    # Add to GoogleResultAnalyzer class in google_analyzer.py:

    def get_domain_to_source_type_mapping(self):
        """
        Creates a mapping of domains to their source types from the analyzed results.
        
        :return: Dictionary mapping domain names to their source types
        """
        domain_source_types = {}
        
        # First, use the explicit mapping from the enhanced results
        for result in self.enhanced_results:
            # Skip None and non-dictionary values
            if not result or not isinstance(result, dict):
                continue
                
            # Get the domain and source type from the result
            domain = result.get("domain")
            source_type = result.get("source_type", "web")
            if domain:
                domain_source_types[domain] = source_type
        
        # Then add any domains from top_domains that might be missing
        for domain, _ in self.source_counter.most_common():
            if domain not in domain_source_types:
                # Use our infer_source_type method to determine the type
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
        # First, ensure we have result data to work with
        if not result:
            logger.debug(f"Skipped: empty result object")
            return None  # Return None instead of False
        
        domain = result.get("display_link") or urlparse(result.get("link", "")).netloc
        source_type = self.infer_source_type(domain)
        
        # Make sure we have text to analyze for sentiment
        snippet = result.get("snippet", "")
        description = result.get("description", "")
        
        # Only proceed if we have some text to analyze
        if not snippet and not description:
            logger.debug(f"Skipped: no text content for sentiment analysis")
            # Still return the result with basic info, just without sentiment
            result.update({
                "domain": domain,
                "source_type": source_type,
                "vader_sentiment": "neutral",  # Default
                "sentiment": "neutral"  # Default
            })
            return result  # Return the result object with basic info
        
        # Perform sentiment analysis if we have text
        initial_sentiment = self.get_sentiment(snippet or description)
        
        date_obj = self.parse_date(result.get("date_published", ""))

        # Update timeline if date is valid
        if date_obj:
            self.timeline[date_obj.isoformat()] += 1

        # Update counters
        self.source_counter[domain] += 1
        self.source_type_counter[source_type] += 1

        # Add processed fields to the result
        result.update({
            "domain": domain,
            "source_type": source_type,
            "vader_sentiment": initial_sentiment,
            "sentiment": initial_sentiment  # Will be updated by LLM later
        })

        # Count keyword occurrences in title and description
        if self.keyword:
            title = result.get("title", "").lower()
            description = result.get("description", "").lower() or result.get("snippet", "").lower()
            
            result["keyword_count_title"] = title.count(self.keyword)
            result["keyword_count_description"] = description.count(self.keyword)

        return result

    def analyze_topics_and_sentiment_with_llm(self):
        """
        Enhanced version with better topic matching and debugging.
        Key improvements:
        1. More robust LLM prompt for topic extraction
        2. Fuzzy keyword matching
        3. Default topic fallback
        4. Detailed debug logging
        """
        import json
        import re
        import random
        from fuzzywuzzy import fuzz
        from google import genai
        import os
        import uuid
        from typing import List, Dict

        client = genai.Client(api_key=os.getenv("GEN_AI_API_KEY"))

        if not self.filtered_results:
            logger.warning('No results for LLM analysis')
            return {
                "topics": [],
                "topic_distribution": {},
                "sentiment_distribution": {"positive": 0, "negative": 0, "neutral": 100}
            }

        # --- Sampling Logic ---
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
            middle_indices = random.sample(middle_range, middle_count)
            
            sampled_indices = top_indices + middle_indices + bottom_indices

        # --- LLM Analysis ---
        sampled_results = [self.filtered_results[i] for i in sampled_indices]
        docs = [f"Title: {r.get('title', '')}\nDescription: {r.get('description', '') or r.get('snippet', '')}" 
                for r in sampled_results]
        sample_text = "\n\n---\n\n".join(docs)

        prompt = f"""
        Analyze these search results for '{self.keyword}' and identify:
        User project type: {self.project_type}
        Associated keywords: {self.associated_keywords}
        Excluded keywords: {self.excluded_keywords}

        PART 1 - Detect Signals/Leads:
        1. You are an intelligent analyst reviewing online content for a business user. The user has initiated a project of type '{self.project_type}' and is tracking the keyword '{self.keyword}' with the following configuration:
        - Associated keywords: {self.associated_keywords}
        - Excluded keywords: {self.excluded_keywords}

        Your job is to:
        Identify relevant signals from the search results.  
        Tailor insights to the selected project type.  
        Distinguish clearly between leads, opportunities, crises, trends, and anomalies.  
        Justify each classification using real-world reasoning, based on what such signals typically mean in each project context.

        2. Context Definitions by Project Type

        Use these guidelines to classify and detect signals appropriately:

        1. Brand Monitoring
        - Opportunity: Positive mentions of the brand or favorable customer sentiment.
        - Crisis: Negative reviews, complaints, or PR issues.
        - Lead: An individual or organization expressing intent to buy, partner, or inquire.
        - Trend: A rise in keyword mentions or common sentiment patterns.
        - Anomaly: Unexpected spikes or dips in attention or sentiment.

        2. Market Research
        - Opportunity: Market gaps, user needs, or underserved demands.
        - Trend: Industry-wide movements or evolving customer preferences.
        - Lead: New customer segments or influencers expressing interest in related products.
        - Anomaly: Surprising market feedback or irregular demand signals.
        - Crisis: Negative perception of the general market category.

        3. Competitor Analysis
        - Opportunity: Weaknesses in competitor products, bad reviews, or user churn.
        - Lead: Users looking for alternatives to a competitor.
        - Crisis: Sudden surge in competitor reputation or product strength.
        - Trend: New product launches, feature rollouts, pricing shifts.
        - Anomaly: Unexpected user behavior or drastic sentiment changes around a competitor.
        - If a "competitor comparison" is mentioned or implied, extract and highlight competitive advantages, positioning, or pain points.

        ---

        3 - Signal Extraction

        Analyze the search results and extract any item that qualifies as a signal according to the user's project type. For each valid signal, return the following fields:

        - Title
        - Description
        - URL
        - Signal Type (lead, opportunity, crisis, trend, anomaly)
        - Confidence (0-100): How confident are you in this classification?
        - Impact Score (1-10): How significant is this signal for the user's current project?
        - Extra Data:
        - reason: Explain why this was categorized this way, referencing the project type and real-world context.
        - summary: A concise, 1-sentence professional summary for dashboard display.

        ---

        Output Format (JSON):
        {{
        "signals": [
            {{
            "signal_type": "opportunity",
            "title": "Competitor's App Lacks Key Feature",
            "description": "Users on Reddit discuss how CompetitorX doesn't support integration with ToolY.",
            "url": "...",
            "confidence": 88,
            "impact_score": 9,
            "extra_data": {{
                "reason": "This is an opportunity under 'competitor analysis' because a weakness in CompetitorX presents a chance to highlight our product's strengths.",
                "summary": "Reddit thread shows users frustrated by missing feature in CompetitorX, signaling a strong opportunity."
            }}
            }}
        ]
        }}

        PART 2 - TOPICS:
        1. Extract 3-10 MAIN topics (general, 1-4 word names)
        2. For each topic:
        - List 5-7 KEYWORDS (include synonyms/variations)
        - Estimate percentage coverage (0-100)
        3. Topics should be:
        - Broad enough to cover multiple results
        - Specific enough to be meaningful
        - Include the keyword itself as a topic if relevant

        PART 3 - SENTIMENT:
        1. For each result, classify sentiment as:
        - 'positive' (clearly favorable)
        - 'negative' (critical/negative)
        - 'neutral' (factual/balanced)
        2. Include confidence score (50-100)
        
        FORMAT:
        {{
            "topics": [
                {{
                    "topic_name": "Topic 1",
                    "keywords": ["kw1", "kw2", ...],
                    "percentage": 30
                }}
            ],
            "sentiments": [
                {{
                    "sentiment": "positive",
                    "confidence": 80
                }}
            ]
        }}

        Results:
        {sample_text}
        """
        
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt
            )
            llm_output = response.candidates[0].content.parts[0].text.strip()
            clean_output = re.sub(r"^```json|```$", "", llm_output).strip()
            try:
                analysis = json.loads(clean_output)
                print(f"LLM output: {clean_output}")
            except Exception as e:
                logger.error(f"Failed to parse LLM output as JSON: {str(e)}")
                logger.debug(f"LLM output was: {clean_output}")
                analysis = {}
            
            # Ensure we have at least the keyword itself as a topic
            topics = analysis.get("topics", [])
            if not topics:
                topics = [{
                    "topic_name": self.keyword,
                    "keywords": [self.keyword.lower()],
                    "percentage": 100
                }]
                
            sentiments = analysis.get("sentiments", [])
            signals = analysis.get("signals", []) 
            #print(f"LLM analysis signals: {signals}")
            logger.debug(f"LLM extracted topics: {topics}")
            
        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            topics = [{
                "topic_name": self.keyword,
                "keywords": [self.keyword.lower()],
                "percentage": 100
            }]
            sentiments = []
            signals = []

        # --- Topic Assignment ---
        NO_TOPIC_UUID = "00000000-0000-0000-0000-000000000000"
        sentiment_map = {idx: sentiments[i] for i, idx in enumerate(sampled_indices) 
                        if i < len(sentiments)}

        for i, result in enumerate(self.filtered_results):
            if not result or not isinstance(result, dict):
                continue
                
            title = result.get("title", "")
            description = result.get("description", "") or result.get("snippet", "")
            doc_text = (title + " " + description).lower()

            # Skip if no meaningful content
            if len(doc_text.strip()) < 20:
                result.update({
                    "topic_id": NO_TOPIC_UUID,
                    "topic_name": "Uncategorized",
                    "sentiment": "neutral",
                    "sentiment_confidence": 50
                })
                continue

            # Find best matching topic using fuzzy matching
            best_match = {
                "topic_id": NO_TOPIC_UUID,
                "topic_name": "Uncategorized",
                "score": 0
            }
            
            for topic in topics:
                # Score based on keyword matches (fuzzy)
                keywords = [k.lower() for k in topic.get("keywords", [])]
                score = sum(
                    fuzz.partial_ratio(kw, doc_text) >= 75
                    for kw in keywords
                )
                
                # Bonus if topic name appears directly
                if topic["topic_name"].lower() in doc_text:
                    score += 2

                if score > best_match["score"]:
                    best_match = {
                        "topic_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, topic["topic_name"])),
                        "topic_name": topic["topic_name"],
                        "score": score
                    }

            result["topic_id"] = best_match["topic_id"]
            result["topic_name"] = best_match["topic_name"]
            
            # Debug logging for questionable assignments
            if best_match["score"] <= 1 and best_match["topic_name"] != "Uncategorized":
                logger.debug(f"Low confidence assignment ({best_match['score']}):")
                logger.debug(f"  Text: {doc_text[:200]}...")
                logger.debug(f"  Topic: {best_match['topic_name']}")
                logger.debug(f"  Keywords: {topic.get('keywords', [])}")

            # Assign sentiment
            if i in sentiment_map:
                result.update({
                    "sentiment": sentiment_map[i].get("sentiment", "neutral"),
                    "sentiment_confidence": sentiment_map[i].get("confidence", 50)
                })
            else:
                # Find similar results with same topic for sentiment
                same_topic_sentiments = [
                    self.filtered_results[idx].get("sentiment")
                    for idx in sampled_indices
                    if idx < len(self.filtered_results) and
                    self.filtered_results[idx].get("topic_id") == result["topic_id"]
                ]
                
                result["sentiment"] = max(
                    set(same_topic_sentiments),
                    key=same_topic_sentiments.count,
                    default="neutral"
                )
                result["sentiment_confidence"] = 50

        # --- Statistics ---
        sentiment_counts = defaultdict(int)
        topic_counts = defaultdict(int)
        
        for result in self.filtered_results:
            if isinstance(result, dict):
                sentiment_counts[result.get("sentiment", "neutral")] += 1
                topic_counts[result.get("topic_name", "Uncategorized")] += 1

        total = sum(sentiment_counts.values()) or 1
        sentiment_distribution = {
            k: round((v / total) * 100, 1)
            for k, v in sentiment_counts.items()
        }
        
        logger.info("Final topic distribution:")
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
            logger.info(f"  {topic}: {count} mentions")
        #print('final signal', signals)
        return {
            "topics": topics,
            "topic_distribution": {
                t["topic_name"]: t["percentage"] for t in topics
            },
            "sentiment_distribution": sentiment_distribution,
            "signals": signals,  # Include detected signals
            "debug": {
                "sampled_count": len(sampled_indices),
                "total_mentions": len(self.filtered_results)
            }
        }

    def analyze(self) -> Dict[str, Union[List[Dict], Dict, List]]:
        """
        Analyze search results to extract insights such as sentiment, source types, and timeline.

        :return: A dictionary containing enhanced results, timeline, top domains, and source types.
        """
        # Check if results are empty
        if not self.results:
            logger.warning('No results to analyze')
            return {
                "enhanced_results": [],
                "timeline": {},
                "top_domains": [],
                "source_types": {},
                "domain_source_types": {},
                "topic_analysis": {"topics": [], "topic_distribution": {}, "sentiment_distribution": {}}
            }
        
        # First filter the results
        self.filtered_results = self.filter_results()
        
        if not self.filtered_results:
            logger.warning(f'No filtered results for keyword: {self.keyword}')
            return {
                "enhanced_results": [],
                "timeline": {},
                "top_domains": [],
                "source_types": {},
                "domain_source_types": {},
                "topic_analysis": {"topics": [], "topic_distribution": {}, "sentiment_distribution": {}}
            }
        
        self.enhanced_results = []
        for result in self.filtered_results:
            processed_result = self.process_result(result)
            # Only add non-None results to the enhanced_results list
            if processed_result is not None:
                self.enhanced_results.append(processed_result)

        # Generate basic analysis
        analysis = {
            "enhanced_results": self.enhanced_results,
            "timeline": dict(sorted(self.timeline.items())),
            "top_domains": self.source_counter.most_common(10),
            "source_types": dict(self.source_type_counter)
        }
        
        # Add domain to source type mapping
        analysis["domain_source_types"] = self.get_domain_to_source_type_mapping()
        
        # Add topic analysis
        analysis["topic_analysis"] = self.analyze_topics_and_sentiment_with_llm()

        return analysis