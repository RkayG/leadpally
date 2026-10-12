# -*- coding: utf-8 -*-
"""
GoogleScraper Module
This module provides a class to scrape Google search results using either the Google API or ScrapingBee.
It includes methods for performing searches, processing results, and saving data in various formats.
"""
import os
import json
import aiohttp
import logging
import requests
from typing import List, Dict, Optional
from rich import print_json
from dotenv import load_dotenv

# INTERNAL IMPORTS
from utils.save_json_cv import parse_and_write_to_csv, save_to_json

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
GOOGLE_API_URL = os.getenv("GOOGLE_API_URL")
SCRAPINGBEE_API_URL = os.getenv("SCRAPINGBEE_API_URL")
SCRAPINGBEE_API_KEY = os.getenv("SCRAPINGBEE_API_KEY") 
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CX = os.getenv("GOOGLE_CX")

class GoogleScraper:
    """A class to scrape Google search results using Google API or ScrapingBee."""

    def __init__(self, query: str):
        """
        Initialize the GoogleScraper with a search query.
        
        :param query: The search query string.
        """
        self.query = query

    async def search_google(self, num_results: int = 100, use_google_api: bool = True, time_period: str = "d" ) -> List[Dict[str, str]]:
        """
        Perform a Google search using the preferred method and return processed results.
        
        :param num_results: Number of results to fetch.
        :param use_google_api: Whether to use Google API (True) or ScrapingBee (False).
        :param time_period: Time period for results (d1=last 24h, w1=last week, m1=last month, y1=last year)
        :return: A list of processed search results.
        """
        if use_google_api:
            raw_results = await self.search_google_with_google(self.query, num_results, time_period)
            if raw_results:
                # Save the full rich data to a JSON file for further analysis
                #parse_and_write_to_csv(raw_results, f"google_results_{self.query.replace(' ', '_')}.csv")
                save_to_json(raw_results, f"google_results_{self.query.replace(' ', '_')}.json")
                logger.info(f"Complete search results saved to google_results_{self.query.replace(' ', '_')}")
        else:
            print(f"ScrapingBee results: {self.query}")
            raw_results = await self.search_google_with_scrapingbee(self.query, num_results, time_period)
             # Save the full rich data to a JSON file for further analysis
            if raw_results:
                #parse_and_write_to_csv(raw_results, f"scrapingbee_results_{self.query.replace(' ', '_')}.csv")
                save_to_json(raw_results, f"scrapingbee_results_{self.query.replace(' ', '_')}.json")
                logger.info(f"Complete search results saved to scrapingbee_results_{self.query.replace(' ', '_')}")
            
        if raw_results:
            return self.process_search_results(raw_results)
        return []

    async def search_google_with_google(self, query: str, num_results: int, time_period: str) -> Optional[Dict]:
        """
        Perform a Google search using the Google Custom Search API with pagination.

        :param query: The search query string.
        :param num_results: Number of results to fetch (max 100).
        :param time_period: Time period for results (d1=last 24h, w1=last week, etc.)
        :return: Combined JSON response from the Google API or None if an error occurs.
        """
        # Limit num_results to maximum 100 allowed by Google API
        num_results = min(100, num_results)
        
        all_results = {"items": []}  # To store combined results
        start_index = 1  # Start with the first page
        
        # Calculate number of pages needed (10 results per page)
        pages_needed = (num_results + 9) // 10  # Ceiling division to get number of pages
        
        for page in range(pages_needed):
            # Calculate the number of results to fetch in this request (always 10 per API limitation)
            results_to_fetch = 10
            
            # Construct the API URL with the start index
            url = f"{GOOGLE_API_URL}?key={GOOGLE_API_KEY}&cx={GOOGLE_CX}&q={query}&num={results_to_fetch}&start={start_index}&dateRestrict={time_period}"
            
            try:
                logger.info(f"Fetching page {page+1} of {pages_needed}, starting at index {start_index}")
                response = requests.get(url)
                
                if response.status_code == 403:
                    logger.warning("Google API quota exceeded, switching to ScrapingBee.")
                    return await self.search_google_with_scrapingbee(query, num_results, time_period)
                    
                elif response.status_code == 200:
                    results = response.json()
                    
                    # Append the current page's results to the combined results
                    if "items" in results:
                        all_results["items"].extend(results["items"])
                        
                        # Store the rest of the response structure if this is the first page
                        if page == 0:
                            for key, value in results.items():
                                if key != "items":
                                    all_results[key] = value
                    
                    # Check if there are more pages to fetch
                    if "queries" in results and "nextPage" in results["queries"]:
                        start_index = results["queries"]["nextPage"][0]["startIndex"]
                    else:
                        logger.info("No more pages available")
                        break  # No more pages available
                        
                else:
                    logger.error(f"Google API error: {response.status_code} - {response.text}")
                    return None
                    
            except requests.RequestException as e:
                logger.error(f"Google API request failed: {e}")
                return None
                
            # If we've collected enough results, stop making additional API calls
            if len(all_results["items"]) >= num_results:
                # Trim to exact number requested
                all_results["items"] = all_results["items"][:num_results]
                break
        
        return all_results if all_results["items"] else None

    async def search_google_with_scrapingbee(self, query: str, num_results: int, time_period: str) -> Optional[Dict]:
        """
        Perform a Google search using ScrapingBee and return parsed results.

        :param query: The search query string.
        :param num_results: Number of results to fetch.
        :param time_period: Time period for results (d1=last 24h, w1=last week, m1=last month, y1=last year)
        :return: JSON response from ScrapingBee or None if an error occurs.
        """
         # Validate required environment variables
        if not SCRAPINGBEE_API_URL:
            logger.error("SCRAPINGBEE_API_URL is not set or is empty")
            raise ValueError("SCRAPINGBEE_API_URL environment variable is required")
        
        if not isinstance(SCRAPINGBEE_API_URL, str):
            logger.error(f"SCRAPINGBEE_API_URL must be a string, got {type(SCRAPINGBEE_API_URL)}")
            raise TypeError("SCRAPINGBEE_API_URL environment variable must be a string")
        
        params = {
            "api_key": SCRAPINGBEE_API_KEY,
            "search": query,
            "nb_results": num_results,
            "language": "en",
            "country_code": "us",
            "tbs": f"qdr:{time_period}", 
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(SCRAPINGBEE_API_URL, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_message = await response.text()
                        logger.error(f"ScrapingBee error: {response.status} - {error_message}")
                        return None
            except aiohttp.ClientError as e:
                logger.error(f"HTTP request failed: {e}")
                return None

    @staticmethod
    def process_search_results(search_data: Dict) -> Dict[str, str]:
        """
        Process the search results from either ScrapingBee or Google API with enhanced data extraction.

        :param search_data: The JSON response containing search results.
        :return: A dictionary containing enriched search results and metadata.
        """

        processed_data = {
            "organic_results": [],
            "related_searches": [],
            "search_metadata": {}
        }
        
        # Add search metadata if available
        if "searchInformation" in search_data:
            processed_data["search_metadata"] = {
                "total_results": search_data["searchInformation"].get("totalResults", "0"),
                "search_time": search_data["searchInformation"].get("searchTime", 0),
                "query": search_data.get("queries", {}).get("request", [{}])[0].get("searchTerms", "")
            }
        
        # Process ScrapingBee format
        if "organic_results" in search_data:
            for i, result in enumerate(search_data["organic_results"]):
                processed_result = {
                    "title": result.get("title", ""),
                    "link": result.get("url", ""),
                    "description": result.get("description", ""),
                    "position": result.get("position", i + 1),
                    "display_link": result.get("displayed_link", ""),
                    "html_snippet": result.get("snippet", ""),
                    "date_published": result.get("date", ""),
                    "source_type": result.get("source", "web")
                }
                
                # Extract rich data if available
                if "rich_snippet" in result:
                    processed_result["rich_data"] = result["rich_snippet"]
                    
                # Extract images if available
                if "thumbnail" in result:
                    processed_result["thumbnail"] = result["thumbnail"]
                    
                processed_data["organic_results"].append(processed_result)
        
        # Process Google API format
        elif "items" in search_data:
            for i, item in enumerate(search_data["items"]):
                # Basic data
                processed_result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "description": item.get("snippet", ""),
                    "position": i + 1,
                    "display_link": item.get("displayLink", ""),
                    "html_snippet": item.get("htmlSnippet", ""),
                    "formatted_url": item.get("formattedUrl", "")
                }
                
                # Extract page map data (rich metadata)
                if "pagemap" in item:
                    pagemap = item["pagemap"]
                    processed_result["pagemap"] = {}
                    
                    # Extract thumbnail images
                    if "cse_thumbnail" in pagemap and pagemap["cse_thumbnail"]:
                        processed_result["thumbnail"] = pagemap["cse_thumbnail"][0].get("src", "")
                        processed_result["thumbnail_width"] = pagemap["cse_thumbnail"][0].get("width", "")
                        processed_result["thumbnail_height"] = pagemap["cse_thumbnail"][0].get("height", "")
                    
                    # Extract larger images
                    if "cse_image" in pagemap and pagemap["cse_image"]:
                        processed_result["image"] = pagemap["cse_image"][0].get("src", "")
                    
                    # Extract metatags for rich data
                    if "metatags" in pagemap and pagemap["metatags"]:
                        metatags = pagemap["metatags"][0]
                        processed_result["metatags"] = {}
                        
                        # Extract important metatags
                        key_metatags = [
                            "og:title", "og:description", "og:image", "og:url", "og:type", "og:site_name",
                            "twitter:card", "twitter:title", "twitter:description", "twitter:image",
                            "twitter:site", "twitter:creator", "author", "viewport", "article:published_time"
                        ]
                        
                        for tag in key_metatags:
                            if tag in metatags:
                                processed_result["metatags"][tag] = metatags[tag]
                        
                        # Extract social media handles
                        if "twitter:site" in metatags:
                            processed_result["twitter_handle"] = metatags["twitter:site"]
                        if "twitter:creator" in metatags:
                            processed_result["twitter_creator"] = metatags["twitter:creator"]
                        
                        # Extract publication date
                        if "article:published_time" in metatags:
                            processed_result["date_published"] = metatags["article:published_time"]
                        elif "datePublished" in metatags:
                            processed_result["date_published"] = metatags["datePublished"]
                        
                        # Extract author information
                        if "author" in metatags:
                            processed_result["author"] = metatags["author"]
                
                processed_data["organic_results"].append(processed_result)

        # Process related searches
        if "related_searches" in search_data:
            # ScrapingBee format
            processed_data["related_searches"] = search_data["related_searches"]
        elif "queries" in search_data and "request" in search_data["queries"]:
            # Google API format for related searches
            if "relatedSearch" in search_data["queries"]:
                for item in search_data["queries"]["relatedSearch"]:
                    processed_data["related_searches"].append({
                        "query": item.get("title", ""),
                        "link": item.get("link", "")
                    })

        # Add keyword analysis
        if processed_data["organic_results"]:
            search_term = (processed_data["search_metadata"].get("query", "") or 
                        search_data.get("queries", {}).get("request", [{}])[0].get("searchTerms", ""))
            
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
