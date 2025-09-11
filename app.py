import streamlit as st
import requests

BACKEND_URL = "https://air-quality-chatbot-n17y.onrender.com"

st.set_page_config(page_title="Air Quality Chatbot", layout="centered")
st.title("🌍 Air Quality Health Chatbot")

# --- User Profile Setup ---
st.sidebar.header("Set Your Profile")
name = st.sidebar.text_input("Name")
condition = st.sidebar.selectbox("Condition", ["none", "asthma", "heart", "pregnant", "children", "senior", "copd", "general"])
age_group = st.sidebar.selectbox("Age Group", ["child", "adult", "senior"])

if st.sidebar.button("Save Profile"):
    try:
        resp = requests.post(f"{BACKEND_URL}/profile/", json={
            "name": name, "condition": condition, "age_group": age_group
        })
        if resp.status_code == 200:
            st.sidebar.success(resp.json().get("message", "Saved."))
        else:
            st.sidebar.error(f"Error: {resp.text}")
    except Exception as e:
        st.sidebar.error(f"⚠️ Backend error: {e}")

# --- Chat Section ---
st.subheader("💬 Chat with AI")
city = st.text_input("Enter your city", "Chennai")
query = st.text_area("Ask your question")

if st.button("Send"):
    try:
        resp = requests.post(f"{BACKEND_URL}/chat/", json={
            "name": name, "query": query, "city": city
        })
        if resp.status_code == 200:
            data = resp.json()
            st.write("🤖", data.get("response", "No response field."))
        else:
            st.error(f"❌ Backend error {resp.status_code}")
            st.text(resp.text)
    except Exception as e:
        st.error(f"⚠️ Connection error: {e}")
