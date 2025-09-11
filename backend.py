from fastapi import FastAPI
from pydantic import BaseModel
import sqlite3
import requests
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai  # Gemini SDK

load_dotenv()  # Load .env file

# --- API KEYS ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not set in .env")

genai.configure(api_key=GEMINI_API_KEY)

# --- FastAPI app ---
app = FastAPI()

# --- DB Setup ---
def init_db():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        condition TEXT,
                        age_group TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- Models ---
class UserProfile(BaseModel):
    name: str
    condition: str
    age_group: str

class ChatQuery(BaseModel):
    name: str
    query: str
    city: str

# --- Save/Update User Profile ---
@app.post("/profile/")
def save_profile(profile: UserProfile):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (name, condition, age_group) VALUES (?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET condition=excluded.condition, age_group=excluded.age_group
    """, (profile.name, profile.condition, profile.age_group))
    conn.commit()
    conn.close()
    return {"message": "✅ Profile saved/updated successfully"}

# --- Fetch AQI Data from OpenWeather ---
def get_aqi(city: str):
    # OpenWeather Air Pollution API requires lat/lon
    coords = {
        "Chennai": (13.0827, 80.2707),
        # Add other cities here if needed
    }
    lat, lon = coords.get(city, (13.0827, 80.2707))  # default to Chennai

    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
    try:
        resp = requests.get(url)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"Failed to fetch AQI: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}

# --- Chat Endpoint ---
@app.post("/chat/")
def chat(query: ChatQuery):
    # Fetch user profile
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT condition, age_group FROM users WHERE name=?", (query.name,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return {"response": "⚠️ I don’t know your health profile yet. Please set it in the sidebar."}

    condition, age_group = row
    aqi_data = get_aqi(query.city)

    # Load rules
    precaution = "General guidance."
    try:
        with open("rules.json", "r") as f:
            rules = json.load(f)
        if "list" in aqi_data and len(aqi_data["list"]) > 0:
            aqi_value = aqi_data["list"][0]["main"].get("aqi", 1) * 50  # scale AQI 1-5 → approx 50-250
            for rule in rules:
                if rule["condition"] == condition and rule["min_aqi"] <= aqi_value <= rule["max_aqi"]:
                    precaution = rule["precaution"]
    except Exception as e:
        precaution = f"(⚠️ rules.json error: {str(e)})"

    # --- Construct Prompt for Gemini ---
    prompt = f"""
You are an Air Quality Health Assistant.
User: {query.name}, Condition: {condition}, Age: {age_group}
City: {query.city}, AQI Data: {aqi_data}
Health Guidance Rule: {precaution}
User Question: {query.query}

Answer conversationally and provide practical health advice.
"""

    try:
           response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
           reply = response.text
    except Exception as e:
          reply = f"⚠️ Gemini API Error: {e}"


    return {"response": reply}
