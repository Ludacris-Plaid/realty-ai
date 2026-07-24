"""
Unified Multi-Source Scraper Orchestrator.

Combines all available scraping sources into a single pipeline:
  1. ZillowScraper (requests-based — existing)
  2. BrowserUseScraper (browser-use library — JS rendering)
  3. ObscuraScraper (Rust headless browser — stealth + speed)
  4. AgentReachConnector (platform connectivity — web reading)

The orchestrator tries sources in order of speed:
  - Static requests (fastest, already works for most pages)
  - Obscura fetch (85ms, lightweight headless)
  - Browser-use (slower but most capable, full browser)
  - Agent-Reach (platform-specific, web search fallback)

Strategy:
  1. Try the existing ZillowScraper first (static requests)
  2. If results are empty or too few, try Obscura (stealth headless)
  3. If still insufficient, try Browser-Use (full JS rendering)
  4. Finally, use Agent-Reach for web search fallback
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SuperScraper:
    """Unified orchestrator over all available scraping sources."""

    def __init__(self):
        self.zillow = None  # lazy import
        self.browser_use = None
        self.obscura = None
        self.agent_reach = None
        self._sources_checked = {}

    def _get_zillow(self):
        if self.zillow is None:
            from .zillow import ZillowScraper
            self.zillow = ZillowScraper(delay=0.5)
        return self.zillow

    def _get_browser_use(self):
        if self.browser_use is None:
            from .browser_use_source import BrowserUseScraper
            self.browser_use = BrowserUseScraper(headless=True)
        return self.browser_use

    def _get_obscura(self):
        if self.obscura is None:
            from .obscura_source import ObscuraScraper
            self.obscura = ObscuraScraper(stealth=True)
        return self.obscura

    def _get_agent_reach(self):
        if self.agent_reach is None:
            from .agent_reach_source import AgentReachConnector
            self.agent_reach = AgentReachConnector()
        return self.agent_reach

    def search(self, location: str, max_results: int = 25) -> list[dict]:
        """Search property listings using the best available source.

        Tries sources in order: Zillow (requests) → Obscura → Browser-Use
        → Agent-Reach web search.

        Returns the union of all results (deduplicated by address).
        """
        all_results = []
        seen_addresses = set()

        # Phase 1: Static Zillow scraper (fastest)
        logger.info("Phase 1: Static Zillow scraper")
        try:
            z_results = self._get_zillow().search(location, max_results)
            for p in z_results:
                addr = p.get("address_street", "")
                if addr and addr not in seen_addresses:
                    seen_addresses.add(addr)
                    all_results.append(p)
            logger.info(f"  → Zillow returned {len(z_results)} results")
        except Exception as e:
            logger.warning(f"  → Zillow failed: {e}")

        # Phase 2: Obscura (stealth headless, 85ms pages)
        if len(all_results) < max_results:
            logger.info("Phase 2: Obscura headless browser")
            try:
                o_results = self._get_obscura().search(location, max_results - len(all_results))
                for p in o_results:
                    addr = p.get("address_street", "")
                    if addr and addr not in seen_addresses:
                        seen_addresses.add(addr)
                        all_results.append(p)
                logger.info(f"  → Obscura returned {len(o_results)} results")
            except Exception as e:
                logger.warning(f"  → Obscura failed: {e}")

        # Phase 3: Browser-Use (full JS rendering, slowest but most capable)
        if len(all_results) < max_results:
            logger.info("Phase 3: Browser-Use full JS rendering")
            try:
                bu = self._get_browser_use()
                if bu.is_available():
                    b_results = bu.search(location, max_results - len(all_results))
                    for p in b_results:
                        addr = p.get("address_street", "")
                        if addr and addr not in seen_addresses:
                            seen_addresses.add(addr)
                            all_results.append(p)
                    logger.info(f"  → Browser-Use returned {len(b_results)} results")
                else:
                    logger.info("  → Browser-Use not available (install browser-use + playwright)")
            except Exception as e:
                logger.warning(f"  → Browser-Use failed: {e}")

        # Phase 4: Agent-Reach web search (general fallback)
        if len(all_results) < max_results // 2:
            logger.info("Phase 4: Agent-Reach web search fallback")
            try:
                arc = self._get_agent_reach()
                if arc.is_available():
                    results = arc.search_property_listings(location)
                    all_results.append({
                        "source": "agent-reach",
                        "web_search_results": results,
                        "address_street": "Web Search Results",
                        "address_city": location.split(",")[0].strip(),
                        "note": f"Found {len(results)} listing sources via web search",
                    })
                    logger.info(f"  → Agent-Reach returned {len(results)} sources")
            except Exception as e:
                logger.warning(f"  → Agent-Reach failed: {e}")

        logger.info(f"SuperScraper total: {len(all_results)} results from "
                     f"{len(set(p.get('source', 'unknown') for p in all_results))} sources")
        return all_results[:max_results]

    def web_read(self, url: str) -> str:
        """Read any web page using best available tool.

        Tries: Obscura fetch → Agent-Reach Jina → direct HTTP.
        """
        # Try Obscura (fastest, cleanest output)
        try:
            obs = self._get_obscura()
            if obs.is_available():
                text = obs.fetch_page_text(url)
                if text and len(text) > 100 and "Error" not in text[:20]:
                    return text
        except Exception:
            pass

        # Try Agent-Reach / Jina Reader
        try:
            arc = self._get_agent_reach()
            text = arc.read_web_page(url)
            if text and len(text) > 100 and "Error" not in text[:20]:
                return text
        except Exception:
            pass

        # Direct HTTP fallback
        try:
            import httpx
            resp = httpx.get(url, timeout=15, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text[:8000]
        except Exception:
            pass

        return ""

    def check_availability(self) -> dict:
        """Check which sources are available on this system."""
        status = {}

        # Zillow (always available, requests-based)
        status["zillow_requests"] = True

        # Obscura
        try:
            obs = self._get_obscura()
            status["obscura"] = obs.is_available()
        except Exception:
            status["obscura"] = False

        # Browser-Use
        try:
            bu = self._get_browser_use()
            status["browser_use"] = bu.is_available()
        except Exception:
            status["browser_use"] = False

        # Agent-Reach
        try:
            arc = self._get_agent_reach()
            status["agent_reach"] = arc.is_available()
        except Exception:
            status["agent_reach"] = False

        return status