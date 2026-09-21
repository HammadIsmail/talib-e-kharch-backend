# 🎓 Talib-e-Kharch — Backend API

> **High-performance FastAPI backend for Talib-e-Kharch**, the student expense tracker designed for Pakistani university students. Features envelope budgeting, Roman Urdu voice logging, Google Gemini 3.6 Flash AI financial advisory, and serverless deployment on Vercel with Neon PostgreSQL.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Neon](https://img.shields.io/badge/Database-Neon_PostgreSQL-00E599.svg?style=flat&logo=postgresql&logoColor=white)](https://neon.tech)
[![Gemini](https://img.shields.io/badge/AI-Google_Gemini_3.6_Flash-4285F4.svg?style=flat&logo=google&logoColor=white)](https://aistudio.google.com)
[![Vercel](https://img.shields.io/badge/Deploy-Vercel_Serverless-000000.svg?style=flat&logo=vercel&logoColor=white)](https://vercel.com)

---

## ⚡ Tech Stack

- **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python REST API)
- **Database:** [Neon Serverless PostgreSQL](https://neon.tech/) with [asyncpg](https://github.com/MagicStack/asyncpg) & [SQLAlchemy 2.0 (asyncio)](https://docs.sqlalchemy.org/)
- **Authentication:** Custom Email + 4-6 digit numeric PIN with `passlib[bcrypt]` and `python-jose` (JWT)
- **AI Engine:** [Google Gemini 3.6 Flash](https://aistudio.google.com/) for Roman Urdu natural language expense parsing and Student Affordability Mentor
- **Voice Engine:** [Uplift AI](https://upliftai.org/) (`prime-time-anchor` voice) for Urdu/English STT/TTS
- **Monetization Sync:** [RevenueCat](https://www.revenuecat.com/) Webhook integration for $1/mo student pro subscription
- **Deployment:** [Vercel Serverless Functions](https://vercel.com/docs/functions/serverless-functions/runtimes/python) via `@vercel/python`

---

## 📁 Project Structure

```
backend/
├── api/
│   └── index.py            # Vercel serverless entry point
├── app/
│   ├── api/
│   │   ├── deps.py         # DB session, JWT user auth, premium gates
│   │   └── v1/
│   │       ├── auth.py     # Register, login, refresh, profile
│   │       ├── expenses.py # Expense CRUD, filtering & pagination
│   │       ├── budgets.py  # Monthly stipend envelope allocation
│   │       ├── categories.py # Default & user categories
│   │       ├── ai.py       # Gemini parsing & affordability checks
│   │       ├── analytics.py # Dashboard cash compass & safe daily spend
│   │       └── webhooks.py # RevenueCat subscription webhook handler
│   ├── core/
│   │   ├── config.py       # Pydantic Settings environment configuration
│   │   ├── database.py     # Async SQLAlchemy engine & connection pooler
│   │   └── security.py     # Bcrypt PIN hashing & JWT tokens
│   ├── models/             # SQLAlchemy ORM models (User, Expense, Category, Budget)
│   ├── schemas/            # Pydantic validation & response schemas
│   ├── services/
│   │   ├── gemini_service.py # Gemini 3.6 Flash parsing & affordability
│   │   └── uplift_service.py # Uplift AI STT/TTS session generator
│   └── main.py             # FastAPI app initialization, CORS, lifespan
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore rules (protects .env and .venv)
├── requirements.txt        # Python production dependencies
└── vercel.json             # Vercel serverless route rewrites
```

---

## 🚀 Quickstart (Local Development)

### 1. Prerequisites
- Python 3.11+
- Virtual environment tool (`venv`)

### 2. Setup Environment
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux / macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```env
# Neon PostgreSQL Connection String
DATABASE_URL=postgresql://neondb_owner:password@ep-xxx-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require

# Google Gemini API Key (Free tier from aistudio.google.com)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.6-flash

# Uplift AI Voice
UPLIFTAI_API_KEY=your_upliftai_key_here
UPLIFTAI_VOICE_ID=prime-time-anchor

# Security
SECRET_KEY=generate_a_random_secret_string_here
```

### 4. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

- API Base: `http://localhost:8000/api`
- Interactive Swagger Docs: `http://localhost:8000/api/docs`
- Health Check: `http://localhost:8000/api/health`

---

## ☁️ Deploy to Vercel

1. Push this repository to GitHub.
2. Go to [Vercel Dashboard](https://vercel.com) → **New Project**.
3. Import your GitHub repository.
4. Set **Root Directory** to `backend` (if repo contains only backend, leave as `./`).
5. Add the environment variables from your `.env` in the Vercel Project Settings:
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`
   - `UPLIFTAI_API_KEY`
   - `UPLIFTAI_VOICE_ID`
   - `REVENUECAT_WEBHOOK_AUTH_TOKEN`
6. Click **Deploy**. Vercel will automatically build the serverless Python bundle using `vercel.json`.

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Health probe | No |
| `POST` | `/api/auth/register` | Register new student with PIN | No |
| `POST` | `/api/auth/login` | Login with email and PIN | No |
| `POST` | `/api/auth/refresh` | Refresh access token | No |
| `GET` | `/api/auth/me` | Current user profile | Yes |
| `PATCH` | `/api/auth/me` | Update settings (Parda, benchmark, PIN) | Yes |
| `GET` | `/api/analytics/dashboard` | Cash compass, safe daily spend & pace | Yes |
| `GET` | `/api/expenses` | List expenses (search, date filter, pages) | Yes |
| `POST` | `/api/expenses` | Log new expense | Yes |
| `DELETE`| `/api/expenses/{id}` | Delete expense | Yes |
| `GET` | `/api/budgets/current` | Active monthly envelope budget | Yes |
| `POST` | `/api/budgets` | Set stipend total & envelopes | Yes |
| `POST` | `/api/ai/parse-expense` | Roman Urdu NLP expense parser (Gemini) | Yes (Trial/Pro) |
| `POST` | `/api/ai/affordability` | "Can I afford this?" AI mentor check | Yes (Trial/Pro) |
| `POST` | `/api/ai/voice-session` | Uplift AI STT/TTS realtime token | Yes (Trial/Pro) |
| `POST` | `/api/webhooks/revenuecat` | Google Play subscription sync webhook | Header Auth |

---

## 📄 License
This project is licensed under the MIT License.
