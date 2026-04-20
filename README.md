# 🏛️ Smart Citizen Complaint Analyzer

An AI-powered full-stack system that allows citizens to submit complaints (text or voice), classifies them using NLP, assigns priority scores, and provides a dedicated admin dashboard for authorities to monitor and analyze all complaints.

## ✨ Features

### Citizen Portal (`/user`)
- **Complaint Submission** — Text input or voice recording
- **AI Classification** — Auto-categorizes into: Water, Electricity, Road, Sanitation, Traffic
- **Priority Feedback** — Instantly shows category and priority after submission
- **My Complaints** — View your own submitted complaints and their status

### Admin Dashboard (`/admin`)
- **All Complaints Table** — View, filter, and sort every submitted complaint
- **Statistics Charts** — Category distribution (bar) & priority distribution (doughnut)
- **Live Stats** — Total, High, Medium, Low complaint counts in the header
- **Filter Controls** — Filter by category and priority

### Authentication
- **JWT-based auth** — Secure token stored in localStorage
- **Role-based access** — `user` role sees only their portal; `admin` role sees the full dashboard
- **Register & Login** — Citizens can self-register; admin account is pre-created on startup

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy |
| ML / NLP | scikit-learn (TF-IDF + Naive Bayes), TextBlob |
| Speech | SpeechRecognition, pydub |
| Auth | PyJWT, bcrypt |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Database | SQLite |

---

## 🚀 Setup & Run

### Prerequisites
- Python 3.9+
- pip

### 1. Create & activate virtual environment

```bash
python -m venv venv
source venv/bin/activate      # macOS/Linux
venv\Scripts\activate         # Windows
```

### 2. Install dependencies

```bash
cd backend
pip install -r requirements.txt
python -c "import textblob; textblob.download_corpora()"
```

### 3. Start the server

```bash
python main.py
```

### 4. Open in browser

| URL | Description |
|-----|-------------|
| http://localhost:8000 | Login / Register page |
| http://localhost:8000/user | Citizen complaint portal |
| http://localhost:8000/admin | Admin dashboard |
| http://localhost:8000/docs | Interactive API docs |

---

## 🔑 Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Citizen | Register via the UI | — |

> **Note:** Change the admin password in production by updating the `create_default_admin` function in `main.py`.

---

## 📁 Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app, API endpoints & auth
│   ├── models.py            # User & Complaint database models
│   ├── database.py          # SQLite setup
│   ├── nlp_processor.py     # Text classification & sentiment analysis
│   ├── priority.py          # Priority scoring system
│   ├── speech.py            # Speech-to-text conversion
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── login.html           # Login / Register page
│   ├── user.html            # Citizen complaint portal
│   ├── user.js              # Citizen portal logic
│   ├── admin.html           # Admin dashboard
│   ├── admin.js             # Admin dashboard logic & charts
│   └── style.css            # Light theme styling
├── data/
│   └── complaints.db        # SQLite database (auto-created)
└── README.md
```

---

## 🌐 API Endpoints

### Auth (Public)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Register a new citizen account |
| POST | `/login` | Login and receive a JWT token |
| GET | `/me` | Get current authenticated user info |

### Citizen (Authenticated)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submit_complaint` | Submit a text or audio complaint |
| GET | `/my_complaints` | Get the current user's own complaints |
| POST | `/speech_to_text` | Convert audio recording to text |

### Admin Only
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/get_complaints` | Get all complaints (filter by category/priority) |
| GET | `/analyze` | Get aggregate statistics & charts data |

---

## 🧠 Priority Scoring

```
priority_score = urgency_score (0–4) + frequency_score (0–3) + sentiment_score (0–3)
```

| Component | Logic |
|-----------|-------|
| **Urgency** | Keyword matching — e.g. "emergency", "danger" → higher score |
| **Frequency** | Count of similar complaints in the same category |
| **Sentiment** | More negative sentiment → higher priority |

| Score | Priority |
|-------|----------|
| ≥ 6.5 | 🔴 High |
| ≥ 4.0 | 🟡 Medium |
| < 4.0 | 🟢 Low |
