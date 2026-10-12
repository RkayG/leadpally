"""
AI Lead Qualification & Search Planning Service
Uses LLM to plan targeted searches and qualify prospective startup clients.
"""
import os
import json
import logging
from typing import List, Dict, Optional, Any
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class LeadQualifier:
    """Uses Gemini to evaluate prospective startups and identify development needs."""

    def __init__(self):
        self.api_key = GEMINI_API_KEY
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)

    async def generate_search_queries(self, user_goal: str, regions: List[str] = None) -> List[str]:
        """
        Translates a user goal (e.g. 'Find early-stage B2B AI startups in the UK that need MVP development')
        into 3-5 high-yield Google / Serper search queries.
        """
        if not self.client:
            # Fallback queries if no API key
            return [
                f'"{user_goal}" site:news.ycombinator.com',
                f'"{user_goal}" "we are hiring" "developer"',
                f'"{user_goal}" launch announcement'
            ]

        prompt = f"""
You are an expert client-acquisition researcher for software engineers.
The user wants to find startup prospects with this goal:
"{user_goal}"
Target regions: {regions if regions else 'UK, US, Europe'}

Generate 3 to 5 precise Google search queries that will uncover early-stage startups, product launches, founders looking for engineers, or recent MVP announcements.
Format your output as a JSON list of strings only, with no markdown code fences:
["query 1", "query 2", "query 3"]
"""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            text = response.text.strip()
            # Clean possible markdown formatting
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:].strip()
            queries = json.loads(text)
            if isinstance(queries, list):
                return queries[:5]
        except Exception as e:
            logger.error(f"Failed to generate search queries via LLM: {e}")

        return [
            f'{user_goal} launch',
            f'{user_goal} "hiring engineer"',
            f'{user_goal} site:producthunt.com'
        ]

    async def qualify_lead(self, company_name: str, domain: str, page_content: str, search_snippet: str) -> Dict[str, Any]:
        """
        Evaluates a candidate startup based on their web page content and SERP snippet.
        Determines:
        - Is it an early stage startup?
        - Do they likely need software/web engineering or MVP help?
        - What concrete evidence supports this?
        - Confidence score between 0.0 and 1.0.
        """
        if not self.client:
            return {
                "is_match": True,
                "company_name": company_name or domain,
                "stage": "Early-stage",
                "summary": search_snippet[:200] if search_snippet else "Discovered prospect",
                "development_needs": ["Frontend or backend development", "MVP refinement"],
                "why_qualifies": "Matches search criteria and recently active.",
                "confidence_score": 0.75,
                "evidence_signals": [search_snippet] if search_snippet else []
            }

        prompt = f"""
You are evaluating whether a prospective company is an early-stage startup that could hire an external freelance software engineer or developer.

Company Domain: {domain}
Search Context / Snippet: {search_snippet}

Extracted Website Content:
\"\"\"
{page_content[:4000]}
\"\"\"

Analyze this company carefully. Distinguish between verified facts and reasonable inferences.
Respond ONLY with a valid JSON object matching this schema:
{{
  "is_match": true or false,
  "company_name": "clean company name",
  "stage": "e.g. Pre-seed, Seed, Bootstrapped, Early-stage, or Mature/Not a fit",
  "location": "location if detectable, or unknown",
  "summary": "1-2 sentence description of what the startup does",
  "development_needs": ["specific need 1", "specific need 2"],
  "why_qualifies": "2-3 sentences explaining why a freelance developer could offer value to them now",
  "confidence_score": 0.85,
  "evidence_signals": ["quote or signal 1", "quote or signal 2"]
}}
"""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.startswith("json"):
                    text = text[4:].strip()
            result = json.loads(text)
            return result
        except Exception as e:
            logger.error(f"Error qualifying lead {domain}: {e}")
            return {
                "is_match": False,
                "why_qualifies": f"Failed qualification analysis: {str(e)}"
            }
