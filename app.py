import streamlit as st
import requests

# Use Render backend URL
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Air Quality Chatbot", layout="centered")
st.title("🌍 Air Quality Health Chatbot")

# --- User Profile ---
st.sidebar.header("Set Your Profile")
name = st.sidebar.text_input("Name")
condition = st.sidebar.selectbox("Condition", ["none", "general", "asthma", "heart", "pregnant", "children", "senior", "copd"])
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

# --- Chat ---
st.subheader("💬 Chat with AI")
city = st.text_input("Enter your city", "Chennai")
query = st.text_area("Ask your question")

if st.button("Send"):
    if not name or not condition or not age_group:
        st.warning("⚠️ Set your profile first!")
    else:
        try:
            resp = requests.post(f"{BACKEND_URL}/chat/", json={
                "name": name, "query": query, "city": city
            })
            if resp.status_code == 200:
                st.write("🤖", resp.json().get("response", "No response."))
            else:
                st.error(f"❌ Backend error {resp.status_code}")
                st.text(resp.text)
        except Exception as e:
            st.error(f"⚠️ Connection error: {e}")
