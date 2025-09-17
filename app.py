import streamlit as st
import requests

# --- Backend URL ---
BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Air Quality Chatbot", layout="centered")
st.title("🌍 Air Quality Health Chatbot")

# --- Sidebar: User Profile ---
st.sidebar.header("Set Your Profile")
name = st.sidebar.text_input("Name")
condition = st.sidebar.selectbox(
    "Condition",
    ["none", "general", "asthma", "heart", "pregnant", "children", "senior", "copd"]
)
age_group = st.sidebar.selectbox(
    "Age Group",
    ["child", "adult", "senior"]
)

# Save profile to backend
if st.sidebar.button("Save Profile"):
    if not name:
        st.sidebar.warning("⚠️ Please enter your name")
    else:
        try:
            resp = requests.post(
                f"{BACKEND_URL}/profile/",
                json={"name": name, "condition": condition, "age_group": age_group}
            )
            if resp.status_code == 200:
                st.sidebar.success(resp.json().get("message", "✅ Profile saved."))
            else:
                st.sidebar.error(f"❌ Error: {resp.text}")
        except Exception as e:
            st.sidebar.error(f"⚠️ Backend error: {e}")

# --- Main Chat Section ---
st.subheader("💬 Ask About Air Quality & Health")
city = st.text_input("Enter your city", "Chennai")
query = st.text_area("Your question")

if st.button("Send"):
    if not name:
        st.warning("⚠️ Please set your profile first in the sidebar!")
    elif not query.strip():
        st.warning("⚠️ Please type a question!")
    else:
        try:
            resp = requests.post(
                f"{BACKEND_URL}/chat/",
                json={"name": name, "query": query, "city": city}
            )
            if resp.status_code == 200:
                st.markdown("**🤖 AI Response:**")
                st.info(resp.json().get("response", "No response from AI."))
            else:
                st.error(f"❌ Backend error {resp.status_code}")
                st.text(resp.text)
        except Exception as e:
            st.error(f"⚠️ Connection error: {e}")
