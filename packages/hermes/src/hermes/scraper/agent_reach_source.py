"""
Agent-Reach Platform Connector.

Integrates Agent-Reach (https://github.com/Panniantong/Agent-Reach) — a
capability layer that gives AI agents access to 15+ platforms: web pages,
YouTube, GitHub, Twitter/X, Reddit, Bilibili, RSS, web search (Exa),
LinkedIn, Instagram, Facebook, Xiaohongshu, and more.

Agent-Reach handles:
  - Platform selection (chooses the best CLI/tool for each platform)
  - Automatic installation and configuration
  - Health checks (agent-reach doctor)
  - Credential management (local-only, never exfiltrated)
  - Transparent backend routing (swaps dead CLIs for working ones)

This source integrates Agent-Reach into the scraper system, giving Athena
the ability to:
  1. Read any web page (via Jina Reader, no API key needed)
  2. Search the web via Exa (free MCP, no API key needed)
  3. Read YouTube video transcripts
  4. Search/read GitHub repos
  5. Read tweets and Twitter timelines
  6. Search/read Reddit (with login)
  7. Search/read Bilibili videos
  8. Read RSS feeds
  9. Get LinkedIn profiles
  10. Read Instagram posts

Install: pip install agent-reach && agent-reach install --env=auto
"""

import json
import logging
import os
import shutil
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


class AgentReachConnector:
    """Platform connectivity layer via Agent-Reach.

    Provides access to web, social media, video, and news platforms
    through a unified interface.

    Install:
        pip install agent-reach
        agent-reach install --env=auto
    """

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        """Check if agent-reach CLI is installed."""
        if self._available is not None:
            return self._available
        try:
            result = subprocess.run(
                ["agent-reach", "--version"],
                capture_output=True, text=True, timeout=5,
            )
            self._available = result.returncode == 0
        except FileNotFoundError:
            self._available = False
        except Exception:
            self._available = False
        return self._available

    def doctor(self) -> str:
        """Run agent-reach doctor to check all platform channels."""
        if not self.is_available():
            return "Agent-Reach not installed. Run: pip install agent-reach && agent-reach install --env=auto"
        try:
            result = subprocess.run(
                ["agent-reach", "doctor"],
                capture_output=True, text=True, timeout=30,
            )
            return result.stdout if result.returncode == 0 else result.stderr
        except Exception as e:
            return f"Doctor check failed: {e}"

    def read_web_page(self, url: str) -> str:
        """Read any web page and return clean text content.

        Uses Jina Reader (built into Agent-Reach, free, no API key).
        """
        if not self.is_available():
            # Fallback to direct Jina Reader call
            return self._jina_read(url)

        # Use Agent-Reach's web channel
        try:
            result = subprocess.run(
                ["curl", "-s", f"https://r.jina.ai/{url}"],
                capture_output=True, text=True, timeout=20,
            )
            if result.returncode == 0 and result.stdout:
                return result.stdout[:8000]
        except Exception:
            pass
        return self._jina_read(url)

    def _jina_read(self, url: str) -> str:
        """Direct Jina Reader fallback (free, no API key)."""
        try:
            import httpx
            resp = httpx.get(f"https://r.jina.ai/{url}", timeout=20, follow_redirects=True)
            if resp.status_code == 200:
                return resp.text[:8000]
            return f"Error: HTTP {resp.status_code}"
        except Exception as e:
            return f"Error reading page: {e}"

    def search_web(self, query: str, count: int = 10) -> list[dict]:
        """Search the web using Exa (via Agent-Reach MCP integration).

        Exa is a semantic search engine optimized for AI agents.
        Free tier available, no API key needed when accessed via MCP.
        """
        if not self.is_available():
            return self._exa_direct(query, count)

        # Use Agent-Reach's search channel (Exa via mcporter MCP)
        try:
            result = subprocess.run(
                ["agent-reach", "search", query, "--count", str(count)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return [{"title": "Result", "url": "", "snippet": result.stdout[:500]}]
        except Exception:
            pass
        return self._exa_direct(query, count)

    def _exa_direct(self, query: str, count: int) -> list[dict]:
        """Direct Exa search via their API (free tier)."""
        try:
            import httpx
            resp = httpx.post(
                "https://api.exa.ai/search",
                json={"query": query, "numResults": count},
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                return [
                    {
                        "title": r.get("title", ""),
                        "url": r.get("url", ""),
                        "snippet": r.get("snippet", r.get("text", ""))[:300],
                    }
                    for r in results
                ]
            return [{"error": f"Exa search failed: HTTP {resp.status_code}"}]
        except ImportError:
            return [{"error": "httpx not installed for direct Exa search"}]
        except Exception as e:
            return [{"error": f"Search error: {e}"}]

    def read_youtube_transcript(self, video_url: str) -> str:
        """Extract transcript from a YouTube video.

        Uses yt-dlp (bundled with Agent-Reach).
        """
        try:
            result = subprocess.run(
                ["yt-dlp", "--write-auto-sub", "--sub-lang", "en",
                 "--skip-download", "--print", "subtitle",
                 video_url, "--sub-format", "vtt"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode == 0:
                return result.stdout[:5000]
            return f"Transcript extraction failed: {result.stderr[:200]}"
        except FileNotFoundError:
            return "yt-dlp not installed (pip install yt-dlp)"
        except subprocess.TimeoutExpired:
            return "Transcript extraction timed out"
        except Exception as e:
            return f"Error: {e}"

    def read_github(self, repo_path: str) -> str:
        """Read GitHub repository info.

        Uses gh CLI (installed by Agent-Reach).
        Example: read_github("owner/repo")
        """
        try:
            result = subprocess.run(
                ["gh", "repo", "view", repo_path],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode == 0:
                return result.stdout[:3000]
            return f"GitHub error: {result.stderr[:200]}"
        except FileNotFoundError:
            return "gh CLI not installed (install via 'gh' or agent-reach install)"
        except Exception as e:
            return f"Error: {e}"

    def read_rss(self, feed_url: str) -> list[dict]:
        """Read an RSS/Atom feed.

        Uses feedparser (bundled with Agent-Reach).
        """
        try:
            import feedparser
            feed = feedparser.parse(feed_url)
            entries = []
            for entry in feed.entries[:10]:
                entries.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", "")[:300],
                })
            return entries
        except ImportError:
            return [{"error": "feedparser not installed"}]
        except Exception as e:
            return [{"error": f"RSS error: {e}"}]

    def search_property_listings(self, location: str) -> list[dict]:
        """Search for property listings by reading real estate sites.

        Uses Agent-Reach web reading to extract listings from:
          - Realtor.com
          - Zillow (as fallback)
          - Local MLS board sites
        """
        results = []

        # Try Realtor.com via Agent-Reach web reader
        url = f"https://www.realtor.com/real-estate/{location.lower().replace(' ', '-').replace(',', '')}"
        page_text = self.read_web_page(url)
        if page_text and "Error" not in page_text[:20]:
            results.append({
                "source": "realtor.com",
                "url": url,
                "content_preview": page_text[:2000],
            })

        # Also try a general web search for listings
        search_results = self.search_web(
            f"real estate listings for sale {location} 2026",
            count=5,
        )
        if search_results:
            results.append({
                "source": "web-search",
                "query": f"real estate listings {location}",
                "results": search_results,
            })

        return results


class HermesBrowserExtension:
    """Integration with Hermes Browser Extension.

    The Hermes Browser Extension (https://github.com/abundantbeing/hermes-browser-extension)
    is a Chrome/Edge side panel that connects browser context to a local Hermes
    Agent runtime. This class documents the integration pattern.

    Architecture:
      - The extension runs as a Chrome side panel
      - It connects to a local Hermes gateway (http://127.0.0.1:8642)
      - It sends active tab context (page text, URL, metadata) to Hermes
      - Responses are streamed back to the side panel

    To integrate with Athena:
      1. Run Hermes gateway alongside the FastAPI backend
      2. Configure the extension to connect to the local gateway
      3. Athena exposes the same tools via the Hermes API

    Connection:
      - Gateway URL: http://127.0.0.1:8642
      - API key: configured in .env as HERMES_API_KEY
      - The extension auto-syncs providers, models, and tools

    Capabilities the extension provides to Athena:
      - Real-time browser context capture (what the user is looking at)
      - Page-level data extraction (selected text, forms, links)
      - Tab management (open tabs, pinned tabs)
      - Voice dictation
      - Site-aware drafting (Hermes Assist)
    """

    @staticmethod
    def integration_guide() -> str:
        return """
=== Hermes Browser Extension Integration ===

To enable real-time browser context for Athena:

1. Install the extension:
   git clone https://github.com/abundantbeing/hermes-browser-extension.git
   cd hermes-browser-extension
   npm install && npm run build
   # Load dist/ as unpacked extension in Chrome

2. Configure Hermes gateway:
   # In .env on the backend machine:
   HERMES_GATEWAY_ENABLED=true
   HERMES_GATEWAY_PORT=8642
   HERMES_API_KEY=<your-api-key>

3. Connect the extension to Athena's backend:
   - Open extension side panel
   - Settings → Manual setup → Local gateway
   - URL: http://<athena-backend-url>:8642
   - Paste the API key

4. Athena gains real-time browser reading capability:
   - "What page am I looking at?" → extension sends tab context
   - "Extract the listing prices from this page" → Athena reads via extension
"""

    @staticmethod
    def athena_tool_integration() -> str:
        return """
Athena can expose these Hermes Browser Extension capabilities as tools:

- `read_browser_context()` — Get the current page URL, title, and text
- `capture_selected_text()` — Get text the user has selected on the page
- `list_open_tabs()` — See what tabs the user has open
- `analyze_current_page()` — Full analysis of the page the user is viewing

These tools require the Hermes gateway to be running and the extension to
be connected. They are passive read-only tools — the extension never
navigates or controls the browser autonomously.
"""