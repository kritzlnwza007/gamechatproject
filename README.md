# 🎮 Game Chat Assistant

Game Chat Assistant เป็นเว็บแอปที่ช่วยตอบคำถามเกี่ยวกับเกมโดยใช้ **Streamlit + Large Language Model (LLM)**  
ร่วมกับ **Steam API** และ **Web Search API** เพื่อให้ผู้ใช้ได้รับข้อมูลเกมที่อัปเดตและเข้าใจง่าย เช่น  
- เกมนี้ราคาเท่าไหร่  
- เกมแนวนี้คืออะไร  
- เกมไหนมาแรงตอนนี้  

---

## ✨ Features / ฟีเจอร์หลัก

- 💬 พูดคุยกับ AI เกี่ยวกับเกมได้ทุกเกม  
- 🎮 ดึงข้อมูลจริงจาก **Steam API** (ราคา แนวเกม วันที่ออก)  
- 🌐 ค้นหาเกมมาแรงและข่าวจากเว็บ (ผ่าน Serper หรือ Tavily API)  
- 🧠 มีระบบจำบทสนทนาเก็บไว้ใน `chat_memory.json`  
- 🔍 รองรับระบบ **RAG (Retrieval-Augmented Generation)** สำหรับอ้างอิงข้อมูลจากเอกสาร  

---

## 🧱 Project Structure / โครงสร้างโปรเจกต์

```
.
├── src/
│   ├── app.py                # Main Streamlit app (เว็บหลัก)
│   ├── utils/
│   │   ├── __init__.py       # รวมการ import ของทุกโมดูล
│   │   ├── llm_client.py     # เชื่อมต่อโมเดล LLM ผ่าน LiteLLM
│   │   ├── search_tools.py   # ค้นหาข่าวหรือข้อมูลเกมจากเว็บ
│   │   ├── steam_api.py      # ดึงข้อมูลจริงจาก Steam Store
│   │   └── rag_system.py     # ระบบ RAG สำหรับค้นหาข้อมูลภายใน
│
├── data/
│   └── chat_memory.json      # เก็บประวัติการแชต
│
├── .env                      # เก็บ API keys
├── requirements.txt           # รายชื่อ dependencies
├── devcontainer.json          # ตั้งค่าสภาพแวดล้อมใน VS Code
└── README.md
```

---

## ⚙️ How to Run / วิธีรันโปรแกรม

### 1️⃣ ติดตั้ง dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ ตั้งค่า Environment Variables
สร้างไฟล์ชื่อ `.env` แล้วใส่ข้อมูล API key ของคุณ:
```bash
OPENAI_API_KEY=your_key_here
STEAM_API_KEY=your_key_here
SERPER_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here
```

### 3️⃣ รันแอป
```bash
streamlit run src/app.py
```

จากนั้นเปิดเบราว์เซอร์ที่  
👉 https://gamechatprojectdemo.streamlit.app/

---

## 🧠 Example Questions / ตัวอย่างคำถาม

- “เกม Palworld ราคาเท่าไหร่”  
- “Elden Ring คือเกมแนวอะไร”  
- “Top 5 trending games right now”  
- “เกมแนว survival ที่กำลังมาแรงมีอะไรบ้าง”  

---

## 🧩 Technologies Used / เทคโนโลยีที่ใช้

- 🐍 **Python 3.11**
- 💻 **Streamlit** — สำหรับสร้างหน้าเว็บ
- 🧠 **LiteLLM** — สำหรับเชื่อมต่อโมเดล AI
- 🎮 **Steam API** — สำหรับดึงข้อมูลเกมจริง
- 🌐 **Serper / Tavily API** — สำหรับค้นหาข้อมูลจากเว็บ
- 📚 **FAISS + SentenceTransformer** — สำหรับระบบ RAG

---

## 🧾 Summary / สรุป

> โปรเจกต์นี้เป็นระบบ “ผู้ช่วยแชตเกี่ยวกับเกม” ที่ผสมผสาน AI เข้ากับข้อมูลจริงจาก Steam และเว็บต่าง ๆ  
> ผู้ใช้สามารถถามเกี่ยวกับเกมใดก็ได้ แล้วระบบจะตอบแบบเข้าใจง่ายและอิงข้อมูลจริง 💬🎮

---

👥 Team Members / สมาชิกกลุ่ม
ชื่อ-นามสกุล	รหัสนักศึกษา
ณัฐนนท์ ทวีทรัพย์นวกุล	670510655
ธนกฤต วรรณ์ประเสริฐ	670510659
รัตนนรินทร์ ยอดเรือน	670510676
ปัญญาณัฏฐ์ พาเขียว	670510667
สรวิศ สิงห์แก้ว	670510730

---

