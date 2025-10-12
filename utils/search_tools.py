"""
Web search utilities for tool calling functionality
"""
import os
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class WebSearchTool:
    """Web search tool using Serper API"""

    def __init__(self):
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")

    def search_serper(self, query: str, num_results: int = 5):
        """
        Search using Serper API
        """
        if not self.serper_api_key:
            return [{"error": "Serper API key not configured"}]

        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "q": query,
            "num": num_results
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return [
                {
                    "title": r.get("title", ""),
                    "link": r.get("link", ""),
                    "snippet": r.get("snippet", ""),
                    "source": "serper",
                }
                for r in data.get("organic", [])
            ]
        except Exception as e:
                return [{"error": f"Search failed: {e}"}]
        
    def search_tavily(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using Tavily API

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        if not self.tavily_api_key:
            return [{"error": "Tavily API key not configured"}]

        url = "https://api.tavily.com/search"
        headers = {
            "Content-Type": "application/json"
        }

        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "max_results": num_results,
            "search_depth": "basic"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            results = []

            if "results" in data:
                for result in data["results"]:
                    results.append({
                        "title": result.get("title", ""),
                        "link": result.get("url", ""),
                        "snippet": result.get("content", ""),
                        "source": "tavily"
                    })

            return results
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]


    def search_steam(self, query: str, num_results: int = 5):
        """Search games on Steam"""
        try:
            resp = requests.get(
                "https://store.steampowered.com/api/storesearch/",
                params={"term": query, "l": "english", "cc": "us"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            return [
                {
                    "title": g.get("name"),
                    "link": f"https://store.steampowered.com/app/{g.get('id')}",
                    "snippet": f"Price: {g.get('price', {}).get('final_formatted', 'N/A')}",
                    "source": "steam",
                }
                for g in data.get("items", [])[:num_results]
            ]
        except Exception as e:
            return [{"error": f"Steam search failed: {e}"}]
        
    def search(self, query: str, num_results: int = 5, preferred_api: str = "serper"):
        """
        Search using preferred API with fallback
        """

        """Unified search"""
        if preferred_api == "steam":
            return self.search_steam(query, num_results)
        return self.search_serper(query, num_results)


def format_search_results(results):
    """Format search results"""
    if not results:
        return "No search results found."
    text = "Search Results:\n\n"
    for i, r in enumerate(results, 1):
        if "error" in r:
            text += f"❌ {r['error']}\n"
        else:
            text += f"{i}. **{r['title']}**\n   {r['snippet']}\n   🔗 {r['link']}\n\n"
    return text
