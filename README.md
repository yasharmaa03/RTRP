# 🏛️ Smart Citizen Complaint Analyzer

An AI-powered full-stack system that takes citizen complaints (text or voice), classifies them into categories, assigns priority, and displays them on a dashboard for authorities.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLAlchemy |
| ML/NLP | scikit-learn (TF-IDF + Naive Bayes), TextBlob |
| Speech | SpeechRecognition, pydub |
| Frontend | HTML, CSS, JavaScript, Chart.js |
| Database | SQLite |

## Features

- **Complaint Submission** — Text input or voice recording
- **AI Classification** — Automatically categorizes into: Water, Electricity, Road, Sanitation, Traffic
- **Priority Scoring** — Assigns High/Medium/Low based on urgency keywords, sentiment, and frequency
- **Dashboard** — Color-coded complaints table with filters
- **Statistics** — Bar chart (categories) and doughnut chart (priorities)

## Setup & Run

### Prerequisites
- Python 3.9+
- pip

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
python -c "import textblob; textblob.download_corpora()"
```

### 2. Start the Server

```bash
cd backend
python main.py
```

### 3. Open in Browser

Navigate to **http://localhost:8000**

## Project Structure

```
├── backend/
│   ├── main.py              # FastAPI app & API endpoints
│   ├── models.py            # Database models
│   ├── database.py          # SQLite setup
│   ├── nlp_processor.py     # Text classification & sentiment
│   ├── priority.py          # Priority scoring system
│   ├── speech.py            # Speech-to-text
│   └── requirements.txt     # Dependencies
├── frontend/
│   ├── index.html           # Main page
│   ├── style.css            # Styling
│   └── app.js               # Frontend logic & charts
├── data/
│   └── complaints.db        # SQLite database (auto-created)
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/submit_complaint` | Submit text/audio complaint |
| GET | `/get_complaints` | Get complaints (filter by category/priority) |
| GET | `/analyze` | Get aggregate statistics |
| POST | `/speech_to_text` | Convert audio to text |

Visit **http://localhost:8000/docs** for interactive API documentation.

## Priority Scoring

```
priority_score = urgency + frequency + sentiment
```

- **Urgency**: Keyword matching (emergency, danger → high score)
- **Frequency**: Count of similar complaints in DB
- **Sentiment**: Negative sentiment → higher priority
- Score ≥ 7 → **High** 🔴 | Score ≥ 4 → **Medium** 🟡 | Score < 4 → **Low** 🟢
