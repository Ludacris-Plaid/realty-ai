"""
Browser-Use Scraper Source.

Uses the browser-use library (https://github.com/browser-use/browser-use)
to control a real browser for JS-rendered property listings from Zillow,
Realtor.com, MLS listings, and other dynamic real estate pages.

browser-use gives AI agents full browser control — clicks, types, scrolls,
reads rendered DOM after JavaScript execution. This source uses it as a
drop-in for pages where plain HTTP requests fail (Zillow catZillow fallback,
Realtor.com search pages, local MLS portals).

Install: pip install browser-use
Requires: playwright install chromium (first-time setup)
"""

import json
import logging
import random
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class BrowserUseScraper:
    """Scrape property listings using browser-use for JS-rendered pages.

    Falls back gracefully if browser-use is not installed or Playwright
    browsers are not available.
    """

    def __init__(self, headless: bool = True, delay: float = 2.0):
        self.headless = headless
        self.delay = delay
        self._available = None

    def is_available(self) -> bool:
        """Check if browser-use + Playwright are installed."""
        if self._available is not None:
            return self._available
        try:
            import browser_use  # noqa: F401
            # Quick Playwright check
            import subprocess
            result = subprocess.run(
                ["python", "-m", "playwright", "install", "--dry-run", "chromium"],
                capture_output=True, text=True, timeout=10,
            )
            self._available = result.returncode == 0 or "already" in result.stdout
        except Exception:
            self._available = False
        return self._available

    def search(self, location: str = "Edmonton, AB", max_results: int = 25) -> list[dict]:
        """Search property listings using browser automation.

        Uses browser-use to load Zillow search pages (or Realtor.com) with
        full JavaScript rendering, then extracts listing data from the
        rendered DOM.

        Returns the same schema as ZillowScraper.search().
        """
        if not self.is_available():
            logger.warning("browser-use not available; use requests-based scraper instead")
            return []

        try:
            return self._browser_use_search(location, max_results)
        except Exception as e:
            logger.warning(f"browser-use search failed: {e}")
            return []

    def _browser_use_search(self, location: str, max_results: int) -> list[dict]:
        """Execute a browser-use agent to scrape property listings."""
        import asyncio
        from browser_use import Agent as BUAgent
        from browser_use.controller.service import Browser
        from langchain_openai import ChatOpenAI

        # Parse location
        search_slug = location.lower().replace(" ", "-").replace(",", "")
        url = f"https://www.zillow.com/homes/{search_slug}_rb/"

        # Build extraction task for browser-use
        task = f"""
        1. Go to {url}
        2. Wait for the page to fully load (including JavaScript rendering)
        3. Wait for property cards to appear (look for class names containing 'card', 'listing', 'photo-card')
        4. Scroll down slowly to trigger lazy loading, up to {max_results} listings
        5. Extract for EACH property listing:
           - address (street, city, state, zip)
           - price (as a number)
           - beds, baths, sqft
           - property type (Single Family, Condo, Townhouse, etc.)
           - status (For Sale, Pending, Sold)
           - a direct image URL if visible
        6. Return the data as a JSON array of objects with keys:
           address_street, address_city, address_state, address_zip,
           list_price, beds, baths, sqft, property_type, status, images
        """

        # Run browser-use in a new event loop
        llm = ChatOpenAI(
            model="deepseek-v4-flash-free",
            base_url="https://opencode.ai/zen/v1",
            api_key="sk-zen-free",
            temperature=0.1,
        )

        async def _run():
            browser = Browser(headless=self.headless)
            agent = BUAgent(
                task=task,
                llm=llm,
                browser=browser,
                use_vision=False,  # text extraction is faster
                max_actions_per_step=10,
            )
            history = await agent.run(max_steps=15)
            await browser.close()

            # Try to parse structured JSON from the final result
            if history and history.final_result():
                try:
                    data = json.loads(history.final_result())
                    if isinstance(data, list):
                        return data
                except (json.JSONDecodeError, TypeError):
                    pass
            return []

        # Run async in a sync context
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(_run())
            loop.close()
        except Exception as e:
            logger.warning(f"browser-use async execution failed: {e}")
            return []

        # Normalize results
        from .zillow import ZillowScraper
        normalizer = ZillowScraper()
        parsed = []
        for raw in results[:max_results]:
            if not isinstance(raw, dict):
                continue
            prop = normalizer._normalize(raw, location)
            if prop:
                prop["source"] = "browser-use"
                parsed.append(prop)

        logger.info(f"browser-use extracted {len(parsed)} properties from {location}")
        return parsed

    def search_realtor(self, location: str, max_results: int = 25) -> list[dict]:
        """Search Realtor.com using browser automation."""
        import asyncio
        from browser_use import Agent as BUAgent
        from browser_use.controller.service import Browser

        search_slug = location.lower().replace(" ", "-").replace(",", "")
        url = f"https://www.realtor.com/real-estate/{search_slug}"

        task = f"""
        1. Go to {url}
        2. Wait for property listing cards to appear
        3. Scroll to load up to {max_results} listings
        4. For each listing, extract:
           - address
           - price
           - beds, baths, sqft
           - property type
        5. Return as JSON array
        """

        async def _run():
            browser = Browser(headless=self.headless)
            agent = BUAgent(task=task, llm=None, browser=browser, use_vision=False)
            history = await agent.run(max_steps=10)
            await browser.close()
            if history and history.final_result():
                try:
                    data = json.loads(history.final_result())
                    return data if isinstance(data, list) else []
                except (json.JSONDecodeError, TypeError):
                    pass
            return []

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(_run())
            loop.close()
        except Exception as e:
            logger.warning(f"browser-use realtor search failed: {e}")
            return []

        from .zillow import ZillowScraper
        normalizer = ZillowScraper()
        parsed = []
        for raw in results[:max_results]:
            if not isinstance(raw, dict):
                continue
            prop = normalizer._normalize(raw, location)
            if prop:
                prop["source"] = "browser-use-realtor"
                parsed.append(prop)

        logger.info(f"browser-use realtor extracted {len(parsed)} properties")
        return parsed