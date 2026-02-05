# Next.js Frontend

This folder contains a starter Next.js frontend for the SaaS Blog API.

## Run locally

```bash
cd frontend
npm install
npm run dev
```

The app will run on `http://localhost:3000` and expects backend API on `http://localhost:8000`.

## Environment variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```
