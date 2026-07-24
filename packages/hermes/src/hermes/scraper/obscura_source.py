"""
Obscura Headless Browser Scraper Source.

Uses Obscura (https://github.com/h4ckf0r0day/obscura) — an ultra-lightweight
headless browser written in Rust — for stealthy, high-performance web scraping.

Obscura advantages over Playwright/Chromium:
  - 30MB memory vs 200MB+ for Chrome
  - 85ms page load vs ~500ms for Chrome
  - Built-in stealth mode (anti-fingerprinting + tracker blocking)
  - Native CDP support (drop-in for Puppeteer/Playwright)
  - Ships MCP server for AI agent integration

This source uses Obscura via three strategies:
  1. CLI subprocess (obscura fetch) — quick single-page extraction
  2. CDP WebSocket (obscura serve) — full Puppeteer/Playwright automation
  3. MCP server (obscura mcp) — AI agent tool integration

Install: Download binary from https://github.com/h4ckf0r0day/obscura/releases
"""

import json
import logging
import os
import random
import subprocess
import shutil
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class ObscuraScraper:
    """Scrape property listings using Obscura headless browser.

    Falls back gracefully if Obscura binary is not found.
    """

    def __init__(self, binary_path: str = "", stealth: bool = True):
        self.binary_path = binary_path or self._find_binary()
        self.stealth = stealth
        self._available = None

    def _find_binary(self) -> str:
        """Find the obscura binary on the system."""
        # Check common locations
        candidates = [
            shutil.which("obscura"),
            os.path.expanduser("~/.local/bin/obscura"),
            "/usr/local/bin/obscura",
            "/usr/bin/obscura",
            "./obscura",
        ]
        # Check OBSCURA_PATH env var
        env_path = os.environ.get("OBSCURA_PATH")
        if env_path:
            candidates.insert(0, env_path)
        for c in candidates:
            if c and os.path.isfile(c) and os.access(c, os.X_OK):
                return c
        return "obscura"  # hope it's on PATH

    def is_available(self) -> bool:
        """Check if Obscura binary is installed and working."""
        if self._available is not None:
            return self._available
        try:
            result = subprocess.run(
                [self.binary_path, "--version"],
                capture_output=True, text=True, timeout=5,
            )
            self._available = result.returncode == 0
        except FileNotFoundError:
            self._available = False
        except Exception:
            self._available = False
        return self._available

    def search(self, location: str = "Edmonton, AB", max_results: int = 25) -> list[dict]:
        """Search property listings using Obscura headless browser.

        Uses obscura fetch with JS evaluation to extract listings from the
        rendered DOM.

        Returns the same schema as ZillowScraper.search().
        """
        if not self.is_available():
            logger.warning("Obscura binary not found; use requests-based scraper instead")
            return []

        # Try Zillow first, then Realtor.com
        results = self._obscura_fetch_zillow(location, max_results)
        if not results:
            results = self._obscura_fetch_realtor(location, max_results)
        return results

    def _obscura_fetch_zillow(self, location: str, max_results: int) -> list[dict]:
        """Use obscura fetch to scrape Zillow with full JS rendering."""
        search_slug = location.lower().replace(" ", "-").replace(",", "")
        url = f"https://www.zillow.com/homes/{search_slug}_rb/"

        # JavaScript to extract listing data from rendered DOM
        eval_js = json.dumps(f"""
        (() => {{
            const listings = [];
            const cards = document.querySelectorAll('[data-test="property-card"], .list-card, article:has(.list-card-info), .photo-card');
            cards.forEach(card => {{
                const addrEl = card.querySelector('[data-test="property-card-addr"], .list-card-addr, address');
                const priceEl = card.querySelector('[data-test="property-card-price"], .list-card-price');
                const infoEl = card.querySelector('[data-test="property-card-details"], .list-card-details');
                const imgEl = card.querySelector('img[data-test="property-card-img"], img');
                const statusEl = card.querySelector('[data-test="property-card-status"], .list-card-status');

                const addr = addrEl ? addrEl.textContent.trim() : '';
                const price = priceEl ? priceEl.textContent.trim().replace(/[^0-9]/g, '') : '0';
                const info = infoEl ? infoEl.textContent.trim() : '';
                const img = imgEl ? imgEl.src : '';
                const status = statusEl ? statusEl.textContent.trim() : 'For Sale';

                // Parse beds/baths/sqft from info string like "3 bds | 2 ba | 1,500 sqft"
                const bedMatch = info.match(/(\\d+)\\s*bd/);
                const bathMatch = info.match(/(\\d+)\\s*ba/);
                const sqftMatch = info.match(/([\\d,]+)\\s*sqft/);

                listings.push({{
                    address: addr,
                    price: parseInt(price) || 0,
                    beds: bedMatch ? parseInt(bedMatch[1]) : 0,
                    baths: bathMatch ? parseInt(bathMatch[1]) : 0,
                    sqft: sqftMatch ? parseInt(sqftMatch[1].replace(/,/g, '')) : 0,
                    status: status,
                    image: img,
                }});
            }});
            return JSON.stringify({{listings, count: listings.length}});
        }})()
        """)

        try:
            cmd = [
                self.binary_path, "fetch", url,
                "--eval", eval_js,
                "--wait-until", "networkidle0",
                "--timeout", "30",
                "--dump", "text",
                "--quiet",
            ]
            if self.stealth:
                cmd.append("--stealth")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

            if result.returncode != 0:
                logger.warning(f"Obscura fetch failed: {result.stderr[:200]}")
                return []

            # Try to parse the JSON output
            output = result.stdout.strip()
            # obscura wraps --eval output — find the JSON
            if "{" in output:
                json_start = output.index("{")
                json_end = output.rindex("}") + 1
                data = json.loads(output[json_start:json_end])
                listings = data.get("listings", [])
            else:
                listings = []

            if not listings:
                logger.info("No listings found via Obscura on Zillow")
                return []

            # Normalize with ZillowScraper normalizer
            from .zillow import ZillowScraper
            normalizer = ZillowScraper()
            parsed = []
            for raw in listings[:max_results]:
                # Map Obscura fields to zillow format
                normalized_raw = {
                    "address": raw.get("address", ""),
                    "price": raw.get("price", 0),
                    "beds": raw.get("beds", 0),
                    "baths": raw.get("baths", 0),
                    "sqft": raw.get("sqft", 0),
                    "status": raw.get("status", "FOR_SALE"),
                    "imgSrc": raw.get("image", ""),
                }
                prop = normalizer._normalize(normalized_raw, location)
                if prop:
                    prop["source"] = "obscura-zillow"
                    parsed.append(prop)

            logger.info(f"Obscura extracted {len(parsed)} properties from Zillow")
            return parsed

        except subprocess.TimeoutExpired:
            logger.warning("Obscura fetch timed out")
            return []
        except Exception as e:
            logger.warning(f"Obscura fetch error: {e}")
            return []

    def _obscura_fetch_realtor(self, location: str, max_results: int) -> list[dict]:
        """Fallback: try Realtor.com via Obscura."""
        search_slug = location.lower().replace(" ", "-").replace(",", "")
        url = f"https://www.realtor.com/real-estate/{search_slug}"

        eval_js = json.dumps(f"""
        (() => {{
            const listings = [];
            const cards = document.querySelectorAll('[data-testid="card-content"], .component_property_card');
            cards.forEach(card => {{
                const addr = card.querySelector('[data-testid="card-address"], .card-address');
                const price = card.querySelector('[data-testid="card-price"], .card-price');
                const meta = card.querySelector('[data-testid="card-meta"], .card-meta');
                listings.push({{
                    address: addr ? addr.textContent.trim() : '',
                    price: price ? price.textContent.trim().replace(/[^0-9]/g, '') : '0',
                    info: meta ? meta.textContent.trim() : '',
                }});
            }});
            return JSON.stringify(listings);
        }})()
        """)

        try:
            cmd = [self.binary_path, "fetch", url, "--eval", eval_js, "--timeout", "20", "--quiet"]
            if self.stealth:
                cmd.append("--stealth")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return []

            output = result.stdout.strip()
            if output.startswith("["):
                listings = json.loads(output)
            else:
                # Find JSON array
                start = output.find("[")
                end = output.rfind("]") + 1
                listings = json.loads(output[start:end]) if start >= 0 else []

            from .zillow import ZillowScraper
            normalizer = ZillowScraper()
            parsed = []
            for raw in listings[:max_results]:
                info = raw.get("info", "")
                bed_match = __import__("re").search(r"(\\d+)\\s*bd", info)
                bath_match = __import__("re").search(r"(\\d+)\\s*ba", info)
                sqft_match = __import__("re").search(r"([\\d,]+)\\s*sqft", info)
                normalized_raw = {
                    "address": raw.get("address", ""),
                    "price": int(raw.get("price", 0)) if raw.get("price") else 0,
                    "beds": int(bed_match.group(1)) if bed_match else 0,
                    "baths": int(bath_match.group(1)) if bath_match else 0,
                    "sqft": int(sqft_match.group(1).replace(",", "")) if sqft_match else 0,
                }
                prop = normalizer._normalize(normalized_raw, location)
                if prop:
                    prop["source"] = "obscura-realtor"
                    parsed.append(prop)

            logger.info(f"Obscura extracted {len(parsed)} properties from Realtor.com")
            return parsed

        except Exception as e:
            logger.warning(f"Obscura Realtor.com fetch error: {e}")
            return []

    def fetch_page_text(self, url: str) -> str:
        """Fetch a web page and return its readable text content.

        Used by Athena's browse_web_page tool.
        """
        if not self.is_available():
            return ""

        try:
            cmd = [self.binary_path, "fetch", url, "--dump", "text", "--timeout", "20", "--quiet"]
            if self.stealth:
                cmd.append("--stealth")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return result.stdout.strip()[:8000]  # limit size
            return f"Error: {result.stderr[:200]}"
        except subprocess.TimeoutExpired:
            return "Request timed out"
        except Exception as e:
            return f"Error: {e}"

    def start_mcp_server(self, port: int = 8080) -> subprocess.Popen:
        """Start Obscura MCP server for AI agent tool integration.

        Returns the process handle. Caller must manage lifecycle.
        """
        cmd = [self.binary_path, "mcp", "--http", "--port", str(port)]
        if self.stealth:
            cmd.append("--stealth")
        return subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)