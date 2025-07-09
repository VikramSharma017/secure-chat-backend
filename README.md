# 🚀 FastAPI Chat Messaging API

A backend API for a chat messaging app built with FastAPI, PostgreSQL, and JWT authentication.

---

## ✨ Features

- 🔐 User registration and login with JWT authentication  
- 💬 Create and list chat rooms  
- 📝 Post and retrieve messages in chat rooms  
- 🔒 Secure password hashing with bcrypt  
- ⚡ Async database interactions with databases and SQLAlchemy  

---

## 🛠 Technologies Used

- 🐍 Python 3.11  
- ⚡ FastAPI  
- 🐘 PostgreSQL  
- 🗄️ SQLAlchemy  
- 🌐 databases (async DB support)  
- 🔑 JWT (via `python-jose`)  
- 🔐 Passlib (for password hashing)  
- 🚀 Uvicorn (ASGI server)  

---

## ⚙️ Setup and Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/VikramSharma017/secure-chat-backend.git
   cd secure-chat-backend
2. Create and activate a virtual environment:
    ```bash
   python -m venv venv
   source venv/bin/activate
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
4. Run the FastAPI app:
   ```bash
   uvicorn main:app --reload
5. Access the API docs at
   ```bash
   http://127.0.0.1:8000/docs.
  --- 
## 🚀 Usage

- Register a new user via the /register endpoint.  
- Login via /token endpoint to get a JWT access token.
- Use the token to authenticate and access protected endpoints like /rooms and /messages.

---

## 👤 Author

Vikram Sharma
