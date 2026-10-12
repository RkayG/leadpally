# -*- coding: utf-8 -*-
"""
# Google Search Command Module
This module provides a command-line interface to perform Google searches using the GoogleScraper class.
It includes functions to run searches, analyze results, and present insights in a user-friendly format.
"""
import logging
from collections import defaultdict

# INTERNAL IMPORTS
from scrapers.google_scraper import GoogleScraper
from analyzers.google_analyzer import GoogleResultAnalyzer

# Set up loggin
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_google_search(query: str, num_results: int, use_google_api: bool):
    """
    Perform a Google search using the GoogleScraper, analyze results and display insights.

    :param query: The search query string.
    :param num_results: Number of results to fetch.
    :param use_google_api: Whether to use the Google API or ScrapingBee.
    :param brand_keywords: List of brand-related keywords to track for relevance
    :param industry_keywords: List of industry-related keywords for relevance
    """
    try:
        print(f"Searching Google for: '{query}' using {'Google API' if use_google_api else 'ScrapingBee'}...")
        scraper = GoogleScraper(query)
        search_data = await scraper.search_google(num_results, use_google_api)
        print("Search completed. Processing results...")
        
        # In run_google_search function, right after the search completes
        print(f"Type of search_data: {type(search_data)}")
        print(f"Content of search_data: {search_data[:100] if isinstance(search_data, list) else search_data.keys()}")

        # Display search metadata
        if "search_metadata" in search_data and search_data["search_metadata"]:
            meta = search_data["search_metadata"]
            print(f"\nSearch Metadata:")
            print(f"Query: {meta.get('query', query)}")
            print(f"Total Results: {meta.get('total_results', 'N/A')}")
            print(f"Search Time: {meta.get('search_time', 'N/A')} seconds")
            print("-" * 50)

        # Analyze results with TextBlob
        organic_results = search_data["organic_results"]
        if organic_results:
            analyzer = GoogleResultAnalyzer(organic_results)
            analysis = analyzer.analyze()
            # Access topic information
            topics = analysis["topic_analysis"]["topics"]
            present_topic_summary(analysis, analysis["enhanced_results"])            
            print("-" * 50)
            
            # Display source type breakdown
            print(f"\nSource Types:")
            for source_type, count in analysis["source_types"].items():
                print(f"{source_type}: {count}")
            print("-" * 50)

            # Only display relevant results if filtering is applied
            results_to_display = analysis["enhanced_results"]
            
            print(f"\nDisplaying {len(results_to_display)} results:")
            for result in results_to_display:
                print(f"Position {result['position']}: {result['title']}")
                print(f"URL: {result['link']}")
                print(f"Display Link: {result.get('display_link', 'N/A')}")
                print(f"Source Type: {result['source_type']}")
                print(f"Sentiment: {result['sentiment']}")
                #print(f"Topic: {result['topic_id']} - {result['topic_words']}")

                print(f"Description: {result['description']}")
                # Display enhanced data if available
                if "thumbnail" in result:
                    print(f"Thumbnail: {result['thumbnail']}")

                if "twitter_handle" in result:
                    print(f"Twitter: {result['twitter_handle']}")

                if "author" in result:
                    print(f"Author: {result['author']}")

                if "date_published" in result:
                    print(f"Published: {result['date_published']}")

                if "keyword_count_title" in result:
                    print(f"Keyword Count (Title): {result['keyword_count_title']}")
                    print(f"Keyword Count (Description): {result['keyword_count_description']}")

                print("-" * 50)

            print(f"\nTimeline:")
            for date, count in analysis["timeline"].items():
                print(f"{date}: {count} results")
            print("-" * 50)
            print(f"Top Domains: {analysis['top_domains']}")
            print(f"Source Types: {analysis['source_types']}")
            print("-" * 50)
            print(f"Topic Analysis: {topics}")
            print("-" * 50)
            
        else:
            print("No organic results returned from the search.")
            
        # Display related searches
        related_searches = search_data["related_searches"]
        if related_searches:
            print(f"\nRelated searches ({len(related_searches)}):")
            for i, search in enumerate(related_searches):
                print(f"{i+1}. {search.get('query', '')}")
            print("-" * 50)
            
        return search_data, analysis if 'analysis' in locals() else None
            
    except Exception as e:
        logger.error(f"An error occurred during the search: {e}", exc_info=True)
        print(f"An error occurred during the search: {e}")
        return None, None
    
def present_topic_summary(analysis_results, enhanced_results):
    """
    Create a user-friendly presentation of topic and sentiment analysis results.

    :param analysis_results: Results from the analyze() method
    :param enhanced_results: The enhanced search results with assigned topics and sentiments
    :return: String with formatted topic and sentiment summary
    """
    topic_analysis = analysis_results.get("topic_analysis", {})
    topics = topic_analysis.get("topics", [])
    sentiment_distribution = topic_analysis.get("sentiment_distribution", {})

    if not topics:
        return "No clear topics were identified in the search results."

    output = "========== Topic Distribution and Mentions===========: \n\n"

    # Group mentions under their topic
    topic_mentions = defaultdict(list)
    for result in enhanced_results:
        topic_name = result.get("topic_name", "Uncategorized")
        topic_mentions[topic_name].append(result)

    for topic in topics:
        name = topic["topic_name"]
        output += f"====> {topic['percentage']}% about **{name}** (keywords: {', '.join(topic['keywords'])})\n"
        
        # Display mentions under the topic
        mentions = topic_mentions.get(name, [])
        for mention in mentions:
            title = mention.get("title", "Untitled")
            url = mention.get("link", "")
            snippet = mention.get("snippet", "")[:200]  # Trim for readability
            sentiment = mention.get("sentiment", "neutral")
            confidence = mention.get("sentiment_confidence", 0)
            output += f"   - 🔗 [{title}]({url}) ({sentiment}, {confidence}%)\n"
            output += f"     > {snippet}\n"

        output += "\n"

    # Handle outliers/miscellaneous
    if topic_analysis.get("outliers", 0) > 0:
        outlier_pct = (topic_analysis["outliers"] / topic_analysis["total_documents"]) * 100
        output += f"====> {round(outlier_pct, 1)}% were miscellaneous (uncategorized)\n\n"

    # Sentiment Summary
    if sentiment_distribution:
        output += "===> Sentiment Distribution:\n"
        for sentiment, percentage in sentiment_distribution.items():
            output += f"- {percentage}% {sentiment}\n"

    print(output)
    print("-" * 60)
