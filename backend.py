from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
import requests
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load .env for local testing
load_dotenv()

# --- API KEYS ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not set")
if not OPENWEATHER_API_KEY:
    raise ValueError("❌ OPENWEATHER_API_KEY not set")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# --- FastAPI app ---
app = FastAPI()

# Enable CORS for all origins (frontend access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    try:
        geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url)
        geo_data = geo_resp.json()
        if not geo_data:
            return {"error": f"City '{city}' not found."}
        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}"
        resp = requests.get(aqi_url)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"Failed to fetch AQI: {resp.text}"}
    except Exception as e:
        return {"error": str(e)}

# --- Chat Endpoint ---
@app.post("/chat/")
def chat(query: ChatQuery):
    # Fetch user profile from DB
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT condition, age_group FROM users WHERE name=?", (query.name,))
    row = cursor.fetchone()
    conn.close()

    # If user profile not found, ask them to register
    if not row:
        return {
            "response": f"⚠️ Hi {query.name}, I don’t have your medical history yet. "
                        f"Please set it by calling the /profile/ endpoint with your "
                        f"condition (e.g., asthma, heart disease) and age group."
        }

    # Extract saved medical history
    condition, age_group = row

    # Fetch AQI data
    aqi_data = get_aqi(query.city)

    # Default precaution
    precaution = "General guidance."
    try:
        with open("rules.json", "r") as f:
            rules = json.load(f)
        if "list" in aqi_data and len(aqi_data["list"]) > 0:
            aqi_value = aqi_data["list"][0]["main"].get("aqi", 1) * 50
            for rule in rules:
                if rule["condition"] == condition and rule["min_aqi"] <= aqi_value <= rule["max_aqi"]:
                    precaution = rule["precaution"]
    except Exception as e:
        precaution = f"(⚠️ rules.json error: {str(e)})"

    # --- Gemini Prompt ---
    prompt = f"""
   You are an Air Quality Health Assistant.

   User Details:
   - Name: {query.name}
   - Age Group: {age_group}
   - Health Condition: {condition}

   Location & Air Quality:
   - City: {query.city}
   - AQI Data (pollutants in ppm): {aqi_data}

   Precautions to Follow: {precaution}

   User Question: {query.query}

   Instructions:
   1. List each pollutant from the AQI data with its value in ppm.
   2. Explain clearly whether the level of each pollutant is safe, moderate, or hazardous.
   3. Highlight which pollutants are most relevant to the user's health condition.
   4. Give practical advice based on the current levels and the user's condition.
   5. Respond conversationally and make it easy to understand, using simple language.

   Provide the output in a structured way like this:
   - Pollutant: Value ppm — Status (Safe/Moderate/Hazardous)
   - Impact on you: [Explain how it affects the user's condition]
   - Advice: [Practical guidance based on current levels]
   """


    try:
        response = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        reply = response.text
    except Exception as e:
        reply = f"⚠️ Gemini API Error: {e}"

    return {"response": reply}

# --- Render port ---
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend:app", host="0.0.0.0", port=port)
