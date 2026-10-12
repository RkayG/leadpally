"""
SerperScraper Module
This module extends the GoogleScraper class to add support for the Serper.dev API.
It maintains the same interface as the existing GoogleScraper methods.
"""
import os
import json
import aiohttp
import logging
from typing import Dict, Optional, List
from dotenv import load_dotenv

# INTERNAL IMPORTS
from utils.save_json_cv import save_to_json
from utils.stripUrl import strip_url_to_domain

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SERPER_API_URL = "https://google.serper.dev/search"
SERPER_API_KEY = os.getenv("SERPER_API_KEY") 
class SerperScraper:
    """A class to scrape Google search results using Serper.dev API."""

    def __init__(self, query: str):
        """
        Initialize the SerperScraper with a search query.
        
        :param query: The search query string.
        """
        self.query = query

    async def search_serper(self, num_results: int = 100, last_checked_at: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Perform a Google search using Serper.dev API and return processed results.
        
        :param num_results: Number of results to fetch.
        :param last_checked_at: Timestamp of last check. If None, don't apply time filter.
        :return: A list of processed search results.
        """
        raw_results = await self.search_google_with_serper(self.query, num_results, last_checked_at)
        
        if raw_results:
            # Save the full rich data to a JSON file for further analysis
            save_to_json(raw_results, f"serper_results_{self.query.replace(' ', '_')}.json")
            logger.info(f"Complete search results saved to serper_results_{self.query.replace(' ', '_')}.json")
            
            return self.process_search_results(raw_results)
        return []

    async def search_google_with_serper(self, query: str, num_results: int, last_checked_at: Optional[str] = None) -> Optional[Dict]:
        """
        Perform a Google search using the Serper.dev API.

        :param query: The search query string.
        :param num_results: Number of results to fetch (max 100).
        :param last_checked_at: Timestamp of last check. If None, don't apply time filter.
        :return: JSON response from Serper API or None if an error occurs.
        """
        # Limit num_results to maximum 100
        num_results = min(100, num_results)
        
        # Create payload for Serper API
        payload = {
            "q": query,
            "num": num_results,
            "engine": "google"
        }
        
        # Add time filter if last_checked_at is provided
        if last_checked_at is not None:
            #payload["tbs"] = "qdr:d"  # last 24 hours
            payload["tbs"] = "qdr:d"
        
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(SERPER_API_URL, json=payload, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_message = await response.text()
                        logger.error(f"Serper API error: {response.status} - {error_message}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"HTTP request failed: {e}")
                return None

    @staticmethod
    def process_search_results(search_data: Dict) -> Dict[str, str]:
        """
        Process the search results from Serper API with enhanced data extraction.

        :param search_data: The JSON response containing search results.
        :return: A dictionary containing enriched search results and metadata.
        """
        processed_data = {
            "organic_results": [],
            "related_searches": [],
            "search_metadata": {}
        }
        
        # Add search metadata if available
        if "searchParameters" in search_data:
            processed_data["search_metadata"] = {
                "query": search_data["searchParameters"].get("q", ""),
                "engine": search_data["searchParameters"].get("engine", "google"),
                "num_results": search_data["searchParameters"].get("num", 0),
                "time_filter": search_data["searchParameters"].get("tbs", "")
            }
        
        # Process organic results
        if "organic" in search_data:
            for i, result in enumerate(search_data["organic"]):
                processed_result = {
                    "title": result.get("title", ""),
                    "link": result.get("link", ""),
                    "description": result.get("snippet", ""),
                    "position": result.get("position", i + 1),
                    "display_link": strip_url_to_domain(result.get("link", "")),
                    "html_snippet": result.get("snippet", ""),  # Serper doesn't provide HTML snippet
                    "age": result.get("date", "")
                }
                
                # Extract sitelinks if available
                if "sitelinks" in result:
                    processed_result["sitelinks"] = result["sitelinks"]
                
                processed_data["organic_results"].append(processed_result)
        
        # Process related searches
        if "relatedSearches" in search_data:
            for item in search_data["relatedSearches"]:
                processed_data["related_searches"].append({
                    "query": item.get("query", "")
                })
        
        # Process answer box if available
        if "answerBox" in search_data:
            processed_data["answer_box"] = search_data["answerBox"]
        
        # Process knowledge graph if available
        if "knowledgeGraph" in search_data:
            processed_data["knowledge_graph"] = search_data["knowledgeGraph"]
        
        # Process top stories if available
        if "topStories" in search_data:
            processed_data["top_stories"] = search_data["topStories"]
        
        # Process images if available
        if "images" in search_data:
            processed_data["images"] = search_data["images"]
        
        # Process places if available
        if "places" in search_data:
            processed_data["places"] = search_data["places"]
        
        # Add keyword analysis
        if processed_data["organic_results"] and "search_metadata" in processed_data:
            search_term = processed_data["search_metadata"].get("query", "")
            
            if search_term:
                for result in processed_data["organic_results"]:
                    # Calculate keyword appearance in title and description
                    result["keyword_in_title"] = search_term.lower() in result["title"].lower()
                    result["keyword_in_description"] = search_term.lower() in result["description"].lower()
                    
                    # Add simple frequency count
                    result["keyword_count_title"] = result["title"].lower().count(search_term.lower())
                    result["keyword_count_description"] = result["description"].lower().count(search_term.lower())

        if not processed_data["organic_results"]:
            logger.warning("No organic results found in the search data.")
            

        return processed_data
