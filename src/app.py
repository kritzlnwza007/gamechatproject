"""
Chat Application with Web Search Tool Calling
Demonstrates function calling with web search capabilities
"""
# main

import streamlit as st

import sys
import os
import json
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv

# โหลด environment variables (รวมถึง STEAM_API_KEY)
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_client import LLMClient, get_available_models
from utils.search_tools import WebSearchTool, format_search_results
from utils.steam_api import SteamAPI



# ------------------------------------------------------------
# 📁 Memory Path
# ------------------------------------------------------------
MEMORY_DIR = Path("data")
MEMORY_FILE = MEMORY_DIR / "chat_memory.json"


# ------------------------------------------------------------
# 💾 Memory Functions
# ------------------------------------------------------------
def load_memory():
    """Load chat memory if file exists, but clear on new session"""
    memory_file = Path("data/chat_memory.json")

    # ถ้ามีการรันใหม่ (session ใหม่) → ลบไฟล์เก่าเลย
    if not st.session_state.get("initialized", False):
        if memory_file.exists():
            memory_file.unlink()  # ลบไฟล์
        st.session_state.initialized = True  # ตั้ง flag ว่าถูกเริ่มแล้ว

    # โหลดไฟล์ใหม่ถ้ามี (หลังจากลบแล้วก็จะไม่มี)
    if memory_file.exists():
        with open(memory_file, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_memory(messages):
    """บันทึกประวัติแชตลงไฟล์"""
    MEMORY_DIR.mkdir(exist_ok=True)
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)


def clear_memory():
    """ล้างหน่วยความจำ"""
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()


# ------------------------------------------------------------
# 🔧 INITIALIZATION
# ------------------------------------------------------------
def init_session_state():
    """Initialize Streamlit session state"""
    if "messages" not in st.session_state:
        st.session_state.messages = load_memory()

    if "llm_client" not in st.session_state or st.session_state.llm_client is None:
        st.session_state.llm_client = LLMClient(
            model=os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo"),
            temperature=float(os.getenv("TEMPERATURE", 0.7)),
            max_tokens=int(os.getenv("MAX_TOKENS", 1000))
        )

    if "search_tool" not in st.session_state:
        st.session_state.search_tool = WebSearchTool()

    if "search_api" not in st.session_state:
        st.session_state.search_api = "serper"


# ------------------------------------------------------------
# 🎮 Steam Game Info (ใช้ API จริง)
# ------------------------------------------------------------
def get_steam_game_info(game_name: str) -> str:
    """ดึงข้อมูลเกมจริงจาก Steam"""
    appid = SteamAPI.search_game(game_name)
    if not appid:
        return "❌ ไม่พบเกมนี้ใน Steam Store."

    data = SteamAPI.get_game_details(appid)
    if data:
        return SteamAPI.format_steam_info(appid, data)

    return "⚠️ ไม่สามารถดึงข้อมูลเกมจาก Steam ได้."


# ------------------------------------------------------------
# 🔍 HANDLE TOOL CALLS
# ------------------------------------------------------------
def handle_tool_calls(message_content: str, llm_client=None) -> Tuple[str, bool]:
    """
    วิเคราะห์ข้อความของผู้ใช้:
    - ถามทั่วไป (รู้จักไหม / คืออะไร / แนวเกมอะไร) → ใช้ LLM ปกติ
    - ถามเรื่องราคา / การขาย → ใช้ Steam API
    - ถามแนวกว้าง (top games, เกมมาแรง) → ใช้ Web Search
    """
    if llm_client is None:
        return message_content, False

    message_lower = message_content.lower()

    # 🔹 คีย์เวิร์ดต่าง ๆ
    game_name_keywords = [
        "gta", "fortnite", "valorant", "call of duty", "cod", "pubg",
        "elden ring", "cyberpunk", "palworld", "counter strike", "cs2",
        "roblox", "minecraft", "overwatch", "apex", "dota", "league of legends",
        "lol", "genshin", "starfield", "battlefield", "red dead", "hollow knight"
    ]
    price_keywords = ["ราคา", "price", "ลดราคา", "sale", "discount", "cost", "ซื้อ", "steam"]
    general_game_keywords = ["คืออะไร", "รู้จัก", "แนว", "เกี่ยวกับ", "review", "รีวิว", "สนุกไหม", "ดีไหม"]

    search_triggers = [
        "top games", "เกมมาแรง", "ยอดนิยม", "popular", "trending", "best selling",
        "most played", "update", "news", "ออกใหม่", "เปิดตัว", "เกมใหม่"
    ]

    # 🔎 ตรวจจับชื่อเกม
    game_name = None
    for g in game_name_keywords:
        if g in message_lower:
            game_name = g
            break

    # 🎮 ถ้ามีชื่อเกมและถามเรื่องราคา → Steam API
    if game_name and any(k in message_lower for k in price_keywords):
        steam_info = get_steam_game_info(game_name)
        
         # แปลง "N/A" → "Free" และใช้ Markdown-friendly line breaks
        steam_info = steam_info.replace("ราคา: N/A", "ราคา: Free")
        steam_info = steam_info.replace("\n", "  \n")  # Markdown: 2 spaces + \n = new line

        enhanced_prompt = f"""
ผู้ใช้ถามเกี่ยวกับราคาเกม: {message_content}

ข้อมูลล่าสุดจาก Steam API:
{steam_info}
"""
        return enhanced_prompt, True

    # 🧠 ถ้ามีชื่อเกมแต่เป็นคำถามทั่วไป → ให้ LLM อธิบายเอง
    if game_name and any(k in message_lower for k in general_game_keywords):
        enhanced_prompt = f"""
ผู้ใช้ถามเกี่ยวกับเกม: {message_content}

ให้ตอบโดยไม่ต้องใช้ Steam API  
อธิบายว่าเกมนี้คือเกมอะไร แนวไหน และเนื้อหาคร่าว ๆ เป็นภาษาไทย อ่านเข้าใจง่าย
"""
        return enhanced_prompt, False

    # 🌐 ถามเรื่องแนวโน้ม / อันดับ / ข่าว → ใช้ Web Search
    if any(trigger in message_lower for trigger in search_triggers):
        query = message_content
        search_results = execute_search(query, 5)
        enhanced_prompt = f"""
User Query: {message_content}

I searched the web and found:
{format_search_results(search_results)}

สรุปข้อมูลนี้เป็นภาษาไทยให้อ่านเข้าใจง่าย เหมือนข่าวเกม
"""
        return enhanced_prompt, True

    # 🔸 ถ้าไม่เข้าเงื่อนไขใดเลย → ใช้ LLM ปกติ
    return message_content, False



# ------------------------------------------------------------
# 🌐 SEARCH FUNCTION
# ------------------------------------------------------------
def execute_search(query: str, num_results: int = 5):
    api = st.session_state.get("search_api", "serper")
    results = st.session_state.search_tool.search(query, num_results, preferred_api=api)
    return results


# ------------------------------------------------------------
# 💬 DISPLAY CHAT
# ------------------------------------------------------------
def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("search_used", False):
                st.markdown("🔍 *Used search or Steam API*")
            st.markdown(message["content"])


# ------------------------------------------------------------
# 🧠 MAIN APP
# ------------------------------------------------------------
def main():
    st.set_page_config(
        page_title="🎮 Game & Info Chat Assistant",
        page_icon="🕹️",
        layout="wide"
    )

    st.markdown(
    """
    <h1 style='text-align: center;'>
        🎮 Game Chat Assistant
    </h1>
    """,
    unsafe_allow_html=True
    )


    init_session_state()

    # Sidebar Configuration
    with st.sidebar:
        st.header("⚙️ Settings")
        available_models = get_available_models()
        selected_model = st.selectbox("Select Model", available_models, index=0)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.7, 0.1)
        max_tokens = st.slider("Max Tokens", 50, 4000, 2000, 50)

        st.subheader("🔍 Search Settings")
        st.session_state.search_api = st.selectbox("Search API", ["serper", "tavily"], index=0)

        st.divider()
        if st.button("🧠 Initialize Model"):
            with st.spinner("Initializing..."):
                st.session_state.llm_client = LLMClient(
                    model=selected_model,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            st.success("✅ Model initialized!")

        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            save_memory([])
            st.rerun()

        if st.button("🧹 Clear Memory"):
            clear_memory()
            st.session_state.messages = []
            st.rerun()

    # Display Chat
    display_chat_messages()

    prompt = st.chat_input("Ask about any game or topic... 🎮")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_memory(st.session_state.messages)

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                enhanced_prompt, search_used = handle_tool_calls(prompt, st.session_state.llm_client)
                response = enhanced_prompt

                # ถ้าไม่ใช่ Steam หรือ Search → ใช้ LLM ตอบ
                if not search_used:
                    messages = [{"role": msg["role"], "content": msg["content"]} for msg in st.session_state.messages[:-1]]
                    messages.append({"role": "user", "content": enhanced_prompt})
                    response = st.session_state.llm_client.chat(messages)

                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response, "search_used": search_used})
                save_memory(st.session_state.messages)

if __name__ == "__main__":
    main()
