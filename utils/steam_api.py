import requests
import os
from dotenv import load_dotenv
load_dotenv()

class SteamAPI:
    BASE_URL = "https://store.steampowered.com/api/appdetails"
    SEARCH_URL = "https://store.steampowered.com/api/storesearch/"
    FEATURED_URL = "https://store.steampowered.com/api/featuredcategories/"
    API_KEY = os.getenv("STEAM_API_KEY")
    
    @staticmethod
    def search_game(query: str, country: str = "us"):
        try:
            params = {"term": query, "l": "english", "cc": country}
            resp = requests.get(SteamAPI.SEARCH_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if data.get("total", 0) > 0:
                return data["items"][0]["id"]
            return None
        except Exception as e:
            print(f"Steam search error: {e}")
            return None

    @staticmethod
    def get_game_details(appid: str):
        try:
            url = f"{SteamAPI.BASE_URL}?appids={appid}&cc=us&l=english"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Steam API error: {e}")
            return None

    @staticmethod
    def format_steam_info(appid: str, data: dict) -> str:
        try:
            if not data or str(appid) not in data or not data[str(appid)]["success"]:
                return "❌ ไม่พบข้อมูลเกมใน Steam Store."

            game_data = data[str(appid)]["data"]
            name = game_data.get("name", "Unknown Game")
            price = game_data.get("price_overview", {}).get("final_formatted", "N/A")
            genres = ", ".join([g["description"] for g in game_data.get("genres", [])])
            release = game_data.get("release_date", {}).get("date", "N/A")
            url = f"https://store.steampowered.com/app/{appid}/"
            desc = game_data.get("short_description", "")

            return (
                f"🎮 **{name}**\n"
                f"💰 ราคา: {price}\n"
                f"🗓️ วันที่วางจำหน่าย: {release}\n"
                f"🏷️ แนวเกม: {genres}\n"
                f"📝 คำอธิบาย: {desc}\n"
                f"🔗 [ดูบน Steam]({url})"
            )
        except Exception as e:
            return f"⚠️ Error formatting data: {e}"

    @staticmethod
    def get_top_games(count=10):
        """ดึง Top Games จาก Steam"""
        try:
            resp = requests.get(SteamAPI.FEATURED_URL, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            top = data.get("top_sellers", {}).get("items", [])[:count]
            return [{"name": g.get("name"), "appid": g.get("id")} for g in top]
        except Exception as e:
            print(f"Steam API error (get_top_games): {e}")
            return []
