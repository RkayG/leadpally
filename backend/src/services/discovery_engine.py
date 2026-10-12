"""
Full Discovery Pipeline Orchestrator
Coordinates Search (Serper) -> Webpage Fetch -> LLM Qualification -> DB Storage -> Notifications
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from scrapers.serper_google_scraper import SerperScraper
from scrapers.htmlrequest import ContentExtractor
from services.qualifier import LeadQualifier
from services.notifier import NotificationService
from utils.stripUrl import strip_url_to_domain
from models import Lead, LeadEvidence, MonitorTask

logger = logging.getLogger(__name__)

class DiscoveryEngine:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.extractor = ContentExtractor()
        self.qualifier = LeadQualifier()
        self.notifier = NotificationService()

    async def run_discovery_for_goal(
        self, 
        user_goal: str, 
        regions: Optional[List[str]] = None, 
        monitor_task_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes a complete end-to-end discovery cycle for a given user objective.
        """
        # 1. Generate search queries with LLM
        queries = await self.qualifier.generate_search_queries(user_goal, regions)
        logger.info(f"Generated queries for discovery: {queries}")

        # 2. Gather candidates via Serper
        candidate_results: Dict[str, Dict[str, Any]] = {}
        for query in queries:
            try:
                scraper = SerperScraper(query=query)
                results = await scraper.search_serper(num_results=15)
                for res in results:
                    url = res.get("url") or res.get("link")
                    if not url:
                        continue
                    domain = strip_url_to_domain(url)
                    # Filter out major social / public platforms that are not startups
                    if any(ignored in domain for ignored in [
                        "google.", "youtube.", "linkedin.", "github.", "twitter.", 
                        "x.com", "medium.", "reddit.", "ycombinator.", "wikipedia."
                    ]):
                        continue

                    if domain not in candidate_results:
                        candidate_results[domain] = {
                            "domain": domain,
                            "url": url,
                            "title": res.get("title", ""),
                            "snippet": res.get("description", res.get("snippet", "")),
                        }
            except Exception as e:
                logger.error(f"Error executing search query '{query}': {e}")

        logger.info(f"Found {len(candidate_results)} unique candidate domains.")

        qualified_leads: List[Dict[str, Any]] = []

        # 3. Check existing database leads and qualify new ones
        for domain, info in list(candidate_results.items())[:10]: # Batch first 10 candidates
            existing = self.db.query(Lead).filter(Lead.domain == domain).first()
            if existing:
                continue

            # Fetch target page content
            page_data = await self.extractor.fetch_page_text(info["url"])
            page_text = page_data["body_text"] if page_data else info["snippet"]

            # Qualify with LLM
            qualification = await self.qualifier.qualify_lead(
                company_name=info["title"],
                domain=domain,
                page_content=page_text,
                search_snippet=info["snippet"]
            )

            if qualification.get("is_match"):
                new_lead = Lead(
                    monitor_task_id=monitor_task_id,
                    company_name=qualification.get("company_name", domain),
                    domain=domain,
                    website_url=info["url"],
                    stage=qualification.get("stage", "Early-stage"),
                    location=qualification.get("location", "Unknown"),
                    summary=qualification.get("summary", ""),
                    development_needs=qualification.get("development_needs", []),
                    why_qualifies=qualification.get("why_qualifies", ""),
                    confidence_score=float(qualification.get("confidence_score", 0.7)),
                    status="new",
                    first_seen_at=datetime.utcnow()
                )
                self.db.add(new_lead)
                self.db.flush()

                # Add evidence item
                evidence = LeadEvidence(
                    lead_id=new_lead.id,
                    signal_type="discovery_search",
                    source_url=info["url"],
                    title=info["title"],
                    snippet=info["snippet"]
                )
                self.db.add(evidence)
                self.db.commit()

                lead_dict = {
                    "id": new_lead.id,
                    "company_name": new_lead.company_name,
                    "domain": new_lead.domain,
                    "website_url": new_lead.website_url,
                    "stage": new_lead.stage,
                    "summary": new_lead.summary,
                    "development_needs": new_lead.development_needs,
                    "why_qualifies": new_lead.why_qualifies,
                    "confidence_score": new_lead.confidence_score,
                }
                qualified_leads.append(lead_dict)

                # Send real-time notification
                await self.notifier.notify_new_lead(lead_dict)

        return qualified_leads
