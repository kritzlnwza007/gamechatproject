import streamlit as st
import sys
import os
import json
import random 
from pathlib import Path
from typing import Tuple
from dotenv import load_dotenv
load_dotenv()

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.llm_client import LLMClient, get_available_models
from utils.search_tools import WebSearchTool, format_search_results
from utils.steam_api import SteamAPI

MEMORY_DIR = Path("data")
MEMORY_FILE = MEMORY_DIR / "chat_memory.json"

REFUSALS_TH = [
    "ผมตอบเฉพาะเรื่องเกมนะครับ 🙂 ลองถามชื่อเกม แนวเกม ราคา หรือสเปคได้เลย",
    "โฟกัสที่เกมเท่านั้นน้าา 🎮 ลองถามเรื่อง GTA, Elden Ring, ราคา, DLC, รีวิวได้เลยครับ",
    "ขอโทษนะครับ ผมตอบเฉพาะเรื่องเกม 🙏 ช่วยถามเกี่ยวกับเกมอีกครั้งได้ไหม",
    "บอทนี้เป็นผู้ช่วยเรื่องเกมเท่านั้นจ้า 😅 ชวนคุยเรื่องเกมมาเลย เช่น ราคา/ข่าว/แนว",
    "ขอจำกัดที่หัวข้อเกมเท่านั้นครับ 🤝 ถามเรื่องแพลตฟอร์ม ราคา หรือรีวิวเกมได้เลย",
    "ขอเป็นเรื่องเกมเท่านั้นนะครับ 🎯 ลองถามชื่อเกมหรือแนวเกมที่สนใจดูได้เลย",
]
def random_refusal() -> str:
    return random.choice(REFUSALS_TH)

GAME_HINTS = [
    "เกม","game","video game","steam","playstation","ps4","ps5",
    "xbox","switch","nintendo","pc","mobile","android","ios",
    "dlc","mod","patch","fps","rpg","moba","open world","survival",
    "multiplayer","singleplayer","esports","rank","รีวิว","แนว","สเปค","ราคา",
    "gta","elden ring","valorant","dota","lol","cs2","minecraft","roblox","cyberpunk",
]
def is_game_query(text: str) -> bool:
    t = text.lower()
    return any(k in t for k in GAME_HINTS)

def load_memory():
    """Load chat memory if file exists, but clear on new session"""
    memory_file = Path("data/chat_memory.json")

    # ถ้ามีการรันใหม่
    if not st.session_state.get("initialized", False):
        if memory_file.exists():
            memory_file.unlink()
        st.session_state.initialized = True

    # โหลดไฟล์ใหม่
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

def get_steam_game_info(game_name: str) -> str:
    """ดึงข้อมูลเกมจริงจาก Steam"""
    appid = SteamAPI.search_game(game_name)
    if not appid:
        return "❌ ไม่พบเกมนี้ใน Steam Store."

    data = SteamAPI.get_game_details(appid)
    if data:
        return SteamAPI.format_steam_info(appid, data)

    return "⚠️ ไม่สามารถดึงข้อมูลเกมจาก Steam ได้."

def handle_tool_calls(message_content: str, llm_client=None) -> Tuple[str, bool]:
    if llm_client is None:
        return message_content, False

    message_lower = message_content.lower()

    # คีย์เวิร์ด
    game_name_keywords = [
        "gta", "fortnite", "valorant", "call of duty", "cod", "pubg",
        "elden ring", "cyberpunk", "palworld", "counter strike", "cs2",
        "roblox", "minecraft", "overwatch", "apex", "dota", "league of legends",
        "lol", "genshin", "starfield", "battlefield", "red dead", "hollow knight"
    ]
    steam_keywords = ["ราคา", "price", "ลดราคา", "sale", "discount", "cost", "ซื้อ", "steam", "ข้อมูล", "เพิ่มเติม", "สนใจ", "download","โหลด","โหลดได้ที่ไหน","ดาวน์โหลด","download link"]
    general_game_keywords = ["คืออะไร", "รู้จัก", "แนว", "เกี่ยวกับ", "review", "รีวิว", "สนุกไหม", "ดีไหม"]

    search_triggers = [
        "top games", "เกมมาแรง", "ยอดนิยม", "popular", "trending", "best selling",
        "most played", "update", "news", "ออกใหม่", "เปิดตัว", "เกมใหม่"
    ]

    #ตรวจจับชื่อเกม
    game_name = None
    for g in game_name_keywords:
        if g in message_lower:
            game_name = g
            break

    #ราคา
    if game_name and any(k in message_lower for k in steam_keywords):
        steam_info = get_steam_game_info(game_name)
        steam_info = steam_info.replace("ราคา: N/A", "ราคา: Free").replace("\n", "  \n")

        final_answer = f"""\
🟨 **นี่คือข้อมูลของเกม:**

{steam_info}
    <-- หากสนใจสามารถกด Link นี้ได้ครับ 
"""
        return final_answer, True
    
    # อธิบายเกมllmตอบ
    if game_name and any(k in message_lower for k in general_game_keywords):
        enhanced_prompt = f"""
ผู้ใช้ถามเกี่ยวกับเกม: {message_content}

ให้ตอบโดยไม่ต้องใช้ Steam API  
อธิบายว่าเกมนี้คือเกมอะไร แนวไหน และเนื้อหาคร่าว ๆ เป็นภาษาไทย อ่านเข้าใจง่าย
"""
        return enhanced_prompt, False

    #คำถามที่ไม่เกี่ยวกับราคา
    if any(trigger in message_lower for trigger in search_triggers):
        search_results = execute_search(message_content, 5)
        enhanced_prompt = f"""
User Query: {message_content}

I searched the web and found:
{format_search_results(search_results)}

สรุปข้อมูลนี้เป็นภาษาไทยให้อ่านเข้าใจง่าย เหมือนข่าวเกม
"""
        return enhanced_prompt, True

    # ไม่เข้าเงื่อนไข ให้ไปที่ llm
    return message_content, False

def execute_search(query: str, num_results: int = 5):
    api = st.session_state.get("search_api", "serper")
    results = st.session_state.search_tool.search(query, num_results, preferred_api=api)
    return results

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message.get("search_used", False):
                st.markdown("🔍 *Used search or Steam API*")
            st.markdown(message["content"])

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

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        available_models = get_available_models()
        selected_model = st.selectbox("Select Model", available_models, index=0)

        st.subheader("🔍 Search Settings")
        st.session_state.search_api = st.selectbox("Search API", ["serper", "tavily"], index=0)

        st.divider()
        if st.button("🧠 Initialize Model"):
            with st.spinner("Initializing..."):
                st.session_state.llm_client = LLMClient(model=selected_model)
            st.success("✅ Model initialized!")

        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            save_memory([])
            st.rerun()

        if st.button("🧹 Clear Memory"):
            clear_memory()
            st.session_state.messages = []
            st.rerun()

    # Display history
    display_chat_messages()

    prompt = st.chat_input("Ask about any game or topic... 🎮")

    if prompt:
        #ข้อข่าวล่าสุด
        with st.chat_message("user"):
            st.markdown(prompt)

        #ถ้ามันไม่ใช่เรื่องเกม ให้จบ
        if not is_game_query(prompt):
            refusal = random_refusal()
            st.session_state.messages.append({"role": "user", "content": prompt})
            st.session_state.messages.append({"role": "assistant", "content": refusal, "search_used": False})
            save_memory(st.session_state.messages)

            with st.chat_message("assistant"):
                st.markdown(refusal)
            st.stop()

        # เพิ่มลง history หลังผ่าน gatekeeper
        st.session_state.messages.append({"role": "user", "content": prompt})
        save_memory(st.session_state.messages)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                enhanced_prompt, search_used = handle_tool_calls(prompt, st.session_state.llm_client)
                response = enhanced_prompt

                # promptบอก Ai
                SYSTEM_PROMPT = """
You are a professional Game Assistant 🎮.
You must ONLY answer questions related to *video games*.
Topics you can talk about include:
- Game details (story, gameplay, mechanics, reviews, genres)
- Platforms (PC, PlayStation, Xbox, Nintendo, Mobile)
- Game recommendations, comparisons, or similar titles
- Game prices, updates, DLCs, mods, esports, or hardware for gaming
- Game industry news, trends, or game development concepts

If the user asks about anything unrelated to games:
Politely refuse in Thai with a short friendly sentence.
"""
                if not search_used:
                    history = [
                        {"role": msg["role"], "content": msg["content"]}
                        for msg in st.session_state.messages[:-1]
                    ]
                    messages = (
                        [{"role": "system", "content": SYSTEM_PROMPT}]
                        + history
                        + [{"role": "user", "content": enhanced_prompt}]
                    )
                    response = st.session_state.llm_client.chat(messages)

                st.markdown(response)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response, "search_used": search_used}
                )
                save_memory(st.session_state.messages)
if __name__ == "__main__":
    main()
