# Multitenant SaaS Blog API

Backend API for a Medium-like blogging platform, built to support **multi-tenant** architecture. This project is currently in early development, and **contributions are welcome**!

## ⚙️ Tech Stack

- **FastAPI** – Fast, modern Python web framework
- **SQLModel** – ORM built on SQLAlchemy and Pydantic
- **OAuth2** – For authentication
- **uv** – Blazing fast Python package manager

## 🚀 Features (Planned)

- ⏳ User Authentication (OAuth2)
- ⏳ Multi-Tenant Support (per-user/blog separation)
- ⏳ Blog CRUD APIs
- ⏳ Custom domains and subdomains per tenant
- ⏳ Role-based access control (Admin, Author, Reader)
- ⏳ Pagination, search, and tags
- ⏳ Upload thumbnails/images

> **Note:** This project is a work in progress. Feel free to explore, suggest features, or contribute via PRs!

## 🛠️ Getting Started

### 1. Install `uv`

```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

Make sure `uv` is available in your path. You can check:

```bash
uv --version
```

### 2. Clone and set up the project

```bash
git clone https://github.com/sanjivthapasvt/saas-blog-api.git
cd saas-blog-api
uv venv
source .venv/bin/activate
uv pip install -r pyproject.toml
```

### 3. Run the project

```bash
fastapi dev main.py
#or
uvicorn main:app --reload
```

## 🤝 Contributing

Contributions, ideas, suggestions, and feedback are always welcome!

1. Fork the repo
2. Create your feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a pull request 🚀


---
