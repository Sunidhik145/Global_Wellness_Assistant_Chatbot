# Global_Wellness_Assistant_Chatbot - Task 1

## Project Idea
The Global Wellness Assistant Chatbot is an AI-powered assistant designed to help users with wellness guidance.  
Task 1 includes **backend APIs and frontend UI for user registration, login, profile management, and basic chat**.

## Features Implemented (Task 1)
- User registration with username, password, age, gender, and preferred language.
- JWT-based authentication and login.
- Profile management (view/update).
- Basic chat endpoint to test bot responses.
- Streamlit frontend for user interaction.

## How it Works (Task 1)
1. **Register User:** `/register` endpoint creates a new user in SQLite DB.
2. **Login:** `/token` endpoint authenticates user and provides JWT token.
3. **Profile Management:** `/profile/{user_id}` to view/update profile.
4. **Chat:** `/chat` endpoint echoes user message (prototype for chatbot).
5. **Frontend:** `ui.py` provides Streamlit interface to interact with backend.

## Tech Stack
- Python, FastAPI, Streamlit
- SQLite + SQLAlchemy
- JWT authentication (python-jose)
- Requests library for API calls

## How to Run (Task 1)
1. Install dependencies:
```bash
pip install -r requirements.txt


## Run backend:
uvicorn app:app --reload

## Run frontend:
streamlit run ui.py

## Open browser and interact with the chatbot via Streamlit UI.
