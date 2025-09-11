🌍 Air Quality Chatbot

An interactive chatbot that provides personalized health guidance based on air quality (AQI) data.
✨ Features

✅ User Profiles → Save your name, age group, and health conditions (e.g., asthma, heart issues).
✅ Real-time AQI Data → Fetches live AQI from OpenWeather API.
✅ Personalized Precautions → Matches user health conditions with AQI rules from rules.json.
✅ AI-Powered Chat → Uses Google Gemini API to generate conversational health advice.
✅ Frontend with Streamlit → Easy-to-use interface for interacting with the chatbot.
✅ Backend with FastAPI → Handles user profiles, AQI fetching, and AI responses.

🛠️ Tech Stack
Backend: FastAPI, SQLite, Uvicorn
Frontend: Streamlit
AI: Google Gemini (via google-generativeai)
APIs: OpenWeather AQI API
Environment: Python, dotenv

🚀 Getting Started

1. Clone the repository
git clone https://github.com/SHAGANTI-NANDHITHA/Air-Quality-ChatBot.git
cd air-quality-chatbot

2. Setup environment
python3 -m venv .venv
source .venv/bin/activate   # macOS/Linux
.venv\Scripts\activate      # Windows
pip install -r requirements.txt

3. Add API keys
Create a .env file in the project root:
GEMINI_API_KEY=your_google_gemini_api_key
OPENWEATHER_API_KEY=your_openweather_api_key

4. Run backend (FastAPI)
Backend : python backend.py 

5. Run frontend (Streamlit)
Frontend : streamlit run app.py

Developed by Shaganti Nandhitha

