# 📝 SaaS Blog API  

Backend API for a Medium-like blogging platform. It provides authentication, blog CRUD, comments, likes, notifications, and user management.  

This project is designed for **scalability**, **security**, and **extensibility**, with 90%+ **test coverage** to ensure reliability.  

---

## ⚙️ Tech Stack  

- **FastAPI** – High-performance async Python web framework  
- **SQLModel** – SQLAlchemy + Pydantic ORM 
- **Redis** - Store expired JWTs for token blacklisting
- **Alembic** – Database migrations  
- **OAuth2 + JWT** – Authentication & authorization  
- **Google OAuth** – Social login support  
- **uv** – Modern Python package/dependency manager  
- **Pytest** – Test framework with 90%+ coverage  

---

## 🚀 Features  

### ✅ Implemented  
- 🔑 User Authentication (JWT, Refresh Tokens, Logout)  
- 🌍 Google OAuth login  
- 📝 Blog CRUD (create, update, delete, search, paginate)  
- ❤️ Blog likes & unlikes  
- 💬 Comments (CRUD on blogs)  
- 🔔 Notifications (likes, follows)
- ⚡ Rate-limiting  
- 👥 User system (follow/unfollow, profiles, password change)  
- 🔎 Pagination & search everywhere  
- 🖼️ File uploads (thumbnails, profile pictures)  
- 🏷️ Tags & categorization  
- 🔔 Push notifications for likes/follows/new blogs from following
- 📌 Bookmarks (save posts for later)

### 🛠 Planned  
- ⚡ Caching  
- 📧 Email verification & password reset
- 📊 Popular blogs (trending posts based on likes/views)
- ⚡ Celery – Asynchronous background task
- 🔍 Content suggestions & related blogs (recommendation engine)
- 🗂️ Heavy background tasks (image processing, analytics, etc.)
- ⏰ Scheduled periodic tasks (cleanup expired tokens, cache updates)

---

## 🛠️ Getting Started  

### 1. Install `uv`  

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
uv --version
```

### 2. Clone & setup  

```bash
git clone https://github.com/sanjivthapasvt/SaaS-Blog-API.git
cd SaaS-Blog-API
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
```

### 3. Environment Variables

Create a `.env` file in the root directory with the following required variables:

```env
SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

#### Environment Variable Details:
- **`SECRET_KEY`** – Used for JWT token signing and encryption. Generate a strong random string.
- **`GOOGLE_CLIENT_ID`** – Google OAuth client ID from Google Cloud Console
- **`GOOGLE_CLIENT_SECRET`** – Google OAuth client secret from Google Cloud Console  
- **`GOOGLE_REDIRECT_URI`** – Callback URL for Google OAuth (must match Google Cloud Console settings)

### 4. Run the project  

```bash
# Development
fastapi dev app/main.py

# or with Uvicorn
uvicorn app.main:app --reload
```

---

## 📚 API Documentation  

- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  

### Example Endpoints  
- `POST /api/auth/register` – Register new user  
- `POST /api/auth/login` – Login & get tokens  
- `POST /api/auth/logout` – Logout (blacklist token)  
- `POST /api/auth/google` – Google login flow  
- `GET /api/blogs` – List blogs (with pagination/search)  
- `POST /api/blogs/{id}/like` – Like/unlike blog  
- `POST /api/blogs/{id}/comments` – Add comment  
- `GET /api/notifications` – Get notifications  
- `GET /api/users/me` – Current user profile  

(See full docs in Swagger UI for all routes.)  

---

## 🧪 Tests  

This project is **well-tested** with **90%+ coverage**.  
Run tests with:  

```bash
pytest tests/
```

---

## 📂 Project Structure  

```
.
├── app/
│   ├── alembic/             # DB migrations
│   ├── auth/                # Authentication & security
│   ├── blogs/               # Blog CRUD & comments
│   ├── core/                # Core configs & database
│   ├── models/              # Shared models
│   ├── notifications/       # Notification system
│   ├── users/               # User management
│   ├── utils/               # Helpers (logging, rate-limiters, etc.)
│   └── main.py              # Entry point
├── tests/                   # Pytest test suite
├── .env                     # Environment variables (create this)
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 🤝 Contributing  

Contributions, ideas, suggestions, and feedback are always welcome!  

1. Fork the repo  
2. Create a feature branch: `git checkout -b feature/your-feature`  
3. Commit changes: `git commit -m "Add new feature"`  
4. Push: `git push origin feature/your-feature`  
5. Open a PR 🚀  

---

## 📜 License  

MIT License – feel free to use and contribute.
