# -*- coding: utf-8 -*-
"""
BaseResultAnalyzer Module
This module provides a base class for analyzing search results from various sources.
It includes methods for processing individual results, inferring source types, and performing sentiment analysis.
It also provides a method for generating a comprehensive analysis report.
"""
from collections import defaultdict, Counter
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class BaseResultAnalyzer:
    """
    Base class for result analyzers.
    """

     # Map domains to source types
    SOURCE_TYPE_MAP = {
        "news": [
            "cnn.com", "bbc.com", "nytimes.com", "reuters.com", "theguardian.com", "washingtonpost.com",
            "forbes.com", "bloomberg.com", "usatoday.com", "wsj.com", "aljazeera.com", "npr.org"
        ],
        "blog": [
            "medium.com", "wordpress.com", "blogspot.com", "substack.com", "tumblr.com", "livejournal.com",
            "dev.to", "hashnode.com", "ghost.io"
        ],
        "forum": [
            "reddit.com", "quora.com", "stackexchange.com", "stackoverflow.com", "discord.com", "4chan.org",
            "5ch.net", "tapatalk.com", "vbulletin.com"
        ],
        "video": [
            "youtube.com", "vimeo.com", "dailymotion.com", "twitch.tv", "metacafe.com", "bitchute.com",
            "veoh.com", "vidyard.com"
        ],
        "social": [
            "twitter.com", "x.com", "facebook.com", "linkedin.com", "instagram.com", "pinterest.com",
            "snapchat.com", "tiktok.com", "weibo.com", "wechat.com", "mastodon.social"
        ],
        "ecommerce": [
            "amazon.com", "ebay.com", "etsy.com", "aliexpress.com", "walmart.com", "target.com",
            "flipkart.com", "bestbuy.com", "shopify.com", "rakuten.com", "mercadolibre.com"
        ],
        "education": [
            "coursera.org", "edx.org", "udemy.com", "khanacademy.org", "academia.edu", "researchgate.net",
            "mit.edu", "harvard.edu", "stanford.edu", "ox.ac.uk", "cam.ac.uk"
        ],
        "technology": [
            "techcrunch.com", "wired.com", "arstechnica.com", "theverge.com", "gizmodo.com", "engadget.com",
            "cnet.com", "zdnet.com", "slashdot.org", "venturebeat.com"
        ],
        "health": [
            "webmd.com", "mayoclinic.org", "healthline.com", "nih.gov", "cdc.gov", "who.int",
            "medlineplus.gov", "clevelandclinic.org", "verywellhealth.com", "everydayhealth.com"
        ],
        "finance": [
            "investopedia.com", "marketwatch.com", "bloomberg.com", "forbes.com", "wsj.com", "cnbc.com",
            "seekingalpha.com", "fool.com", "morningstar.com", "bankrate.com"
        ],
        "entertainment": [
            "imdb.com", "rottentomatoes.com", "metacritic.com", "variety.com", "hollywoodreporter.com",
            "buzzfeed.com", "tmz.com", "etonline.com", "eonline.com", "rollingstone.com"
        ],
        "sports": [
            "espn.com", "bleacherreport.com", "cbssports.com", "foxsports.com", "nbcsports.com",
            "skysports.com", "goal.com", "fifa.com", "nba.com", "mlb.com", "nfl.com"
        ],
        "government": [
            "usa.gov", "gov.uk", "europa.eu", "nasa.gov", "whitehouse.gov", "senate.gov", "house.gov",
            "un.org", "state.gov", "justice.gov"
        ],
        "shopping": [
            "shopify.com", "bigcommerce.com", "woocommerce.com", "magento.com", "prestashop.com",
            "opencart.com", "squarespace.com", "wix.com", "weebly.com"
        ],
        "travel": [
            "tripadvisor.com", "expedia.com", "booking.com", "airbnb.com", "kayak.com", "skyscanner.net",
            "lonelyplanet.com", "travelocity.com", "agoda.com", "hotels.com"
        ],
        "gaming": [
            "ign.com", "gamespot.com", "pcgamer.com", "polygon.com", "kotaku.com", "gameinformer.com",
            "nintendo.com", "playstation.com", "xbox.com", "steamcommunity.com"
        ]
    }

    def __init__(self, results=None, name="BaseAnalyzer"):
        """
        Initialize the base analyzer.
        
        :param results: List of result dictionaries
        :param name: Name of the analyzer
        """
        self.name = name
        self.results = results or []
        self.enhanced_results = []
        self.timeline = defaultdict(int)
        self.source_counter = Counter()
        self.source_type_counter = Counter()
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
    
   
    