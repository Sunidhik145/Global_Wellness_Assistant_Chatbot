import streamlit as st
import requests
import re

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="🌿 Global Wellness Chatbot", page_icon="💬", layout="wide")

# ----------------- Session state -----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "profile_completed" not in st.session_state:
    st.session_state.profile_completed = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "gender" not in st.session_state:
    st.session_state.gender = ""

# ----------------- Sidebar menu -----------------
menu = ["Login", "Register", "Forgot Password"] if not st.session_state.logged_in else ["Profile", "Chat", "Logout"]
choice = st.sidebar.selectbox("⚙ Menu", menu)

# ----------------- Theme toggle -----------------
theme = st.sidebar.radio("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("<style>body{background-color:#222;color:#eee}</style>", unsafe_allow_html=True)
else:
    st.markdown("<style>body{background-color:#fff;color:#000}</style>", unsafe_allow_html=True)

# ----------------- Title -----------------
st.title("🌿 Global Wellness Chatbot")
st.subheader("Your Personal AI Wellness Companion")

# ----------------- Register -----------------
if choice == "Register":
    st.subheader("📝 Register")
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    age_group = st.selectbox("Age Group", ["15-20", "21-26", "27-35", "36-50", "51+"])
    gender = st.selectbox("Gender", ["Male", "Female", "Other"])  
    preferred_language = st.selectbox("Preferred Language", ["English", "Hindi"])

    if st.button("Register"):
        if name and email and password:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Please enter a valid email address")
            else:
                response = requests.post(
                    f"{BASE_URL}/register",
                    json={
                        "username": email,
                        "password": password,
                        "name": name,
                        "age_group": age_group,
                        "gender": gender,
                        "preferred_language": preferred_language
                    }
                )
                try:
                    data = response.json()
                except ValueError:
                    data = {"detail": response.text or "Server returned invalid response"}

                if response.status_code == 201:
                    st.success("User registered successfully! Please login.")
                else:
                    st.error(data.get("detail") or "Registration failed")
        else:
            st.error("Please fill all fields.")

# ----------------- Login -----------------
elif choice == "Login":
    st.subheader("🔑 Login")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if email and password:
            if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                st.error("Please enter a valid email address")
            else:
                response = requests.post(
                    f"{BASE_URL}/token",
                    data={"username": email, "password": password}
                )
                try:
                    data = response.json()
                except ValueError:
                    data = {"detail": response.text or "Server returned invalid response"}

                if response.status_code == 200 and data:
                    st.session_state.logged_in = True
                    st.session_state.user_id = data.get("user_id")
                    st.session_state.username = data.get("name")
                    st.session_state.gender = data.get("gender") or "Not set"
                    st.session_state.access_token = data.get("access_token")
                    st.session_state.profile_completed = True
                    st.success(f"Welcome {st.session_state.username} ({st.session_state.gender})!")
                else:
                    st.error(data.get("detail") or "Login failed")
        else:
            st.error("Please fill all fields.")

# ----------------- Forgot Password -----------------
elif choice == "Forgot Password":
    st.subheader("🔄 Forgot Password")
    email = st.text_input("Enter your registered email")

    if st.button("Send Reset Link"):
        if email:
            response = requests.post(f"{BASE_URL}/forgot-password", json={"email": email})
            try:
                data = response.json()
            except ValueError:
                data = {"message": response.text or "Server returned invalid response"}
            st.success(data.get("message") or "Reset link sent if email exists")
        else:
            st.error("Please enter your email.")

# ----------------- Profile Management -----------------
elif choice == "Profile" and st.session_state.logged_in:
    st.subheader(f"👤 Manage Your Profile, {st.session_state.username}")

    headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
    response = requests.get(f"{BASE_URL}/profile/{st.session_state.user_id}", headers=headers)
    try:
        profile = response.json() if response.status_code == 200 else {}
    except ValueError:
        profile = {}

    name = st.text_input("Full Name", value=profile.get("name", ""))
    age_group = st.selectbox(
        "Age Group",
        ["15-20", "21-26", "27-35", "36-50", "51+"],
        index=["15-20", "21-26", "27-35", "36-50", "51+"].index(profile.get("age_group", "15-20"))
    )
    gender = st.selectbox(
        "Gender",
        ["Male", "Female", "Other"],
        index=["Male", "Female", "Other"].index(profile.get("gender", "Male"))
    )
    preferred_language = st.selectbox(
        "Preferred Language",
        ["English", "Hindi"],
        index=["English", "Hindi"].index(profile.get("preferred_language", "English"))
    )

    if st.button("Save Profile"):
        payload = {
            "name": name,
            "age_group": age_group,
            "gender": gender,
            "preferred_language": preferred_language
        }

        response = requests.put(
            f"{BASE_URL}/profile/{st.session_state.user_id}",
            json=payload,
            headers=headers
        )

        try:
            data = response.json()
        except ValueError:
            data = {"detail": response.text or "Server returned invalid response"}

        if response.status_code == 200:
            st.success("Profile updated successfully!")
        else:
            st.error(data.get("detail") or "Failed to update profile.")

# ----------------- Chat -----------------
elif choice == "Chat" and st.session_state.logged_in:
    st.subheader(f"💬 Chat with Bot, {st.session_state.username} ({st.session_state.gender})")

    for msg in st.session_state.messages:
        st.markdown(f"You: {msg['user']}")
        st.markdown(f"Bot: {msg['bot']}")

    user_message = st.text_input("Type your message here:")

    if st.button("Send"):
        if user_message:
            headers = {"Authorization": f"Bearer {st.session_state.access_token}"}
            response = requests.get(
                f"{BASE_URL}/chat",
                params={"message": user_message},
                headers=headers
            )
            try:
                bot_reply = response.json().get("response")
            except ValueError:
                bot_reply = "Error: No response from server"
            st.session_state.messages.append({"user": user_message, "bot": bot_reply})
        else:
            st.error("Please type a message.")

# ----------------- Logout -----------------
elif choice == "Logout":
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.username = ""
    st.session_state.gender = ""
    st.session_state.profile_completed = False
    st.session_state.messages = []
    st.session_state.access_token = None
    st.success("You have logged out successfully!")
