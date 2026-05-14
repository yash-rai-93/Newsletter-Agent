---
title: Newsletter Agent
emoji: 📰
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# 📰 Newsletter Agent

> A fully autonomous AI agent that researches, writes, critiques, and delivers newsletters — powered by Gemini + LangGraph.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green.svg)](https://langchain-ai.github.io/langgraph/)
[![Gemini](https://img.shields.io/badge/LLM-Gemini%202.5%20Flash-blue.svg)](https://ai.google.dev/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-teal.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/Frontend-React%2018-blue.svg)](https://react.dev)

---

## ✨ What It Does

One function call. Full newsletter. No hand-holding.

```python
run_newsletter_agent("Create a weekly newsletter on latest AI agent news")
```

The agent autonomously:
1. 🧠 **Plans** — Extracts topic, creates research strategy, generates search queries
2. 🔍 **Researches** — Searches and fetches top 5-7 articles via Tavily
3. ✍️ **Writes** — Generates a polished newsletter with intro, articles, and CTA
4. 🎨 **Designs** — Converts to beautiful responsive HTML
5. 🔎 **Reviews** — Self-critiques and scores its own output (1-10)
6. 🔄 **Improves** — Rewrites if quality score < 7 (max 2 iterations)
7. 💾 **Outputs** — Saves HTML file + logs subject line

## 🎛️ Two Modes

| Autonomous | Human-in-the-Loop |
|-----------|-------------------|
| Zero intervention | 3 review checkpoints |
| Fastest path to output | You control quality |
| Great for automation | Great for learning |

---

## 🏗️ Architecture

```
React Frontend (SSE live updates)
       ↕ HTTP + Server-Sent Events
FastAPI Backend
       ↕
LangGraph Agent Pipeline
  Plan → Research → Write → Review → [Improve] → Output
       ↕
Gemini gemini-2.5-flash (LLM) + Tavily (Search)
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key
- Tavily API key (free tier works: [tavily.com](https://tavily.com))

### 1. Clone & Setup

```bash
git clone https://github.com/yourusername/newsletter-agent.git
cd newsletter-agent
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd frontend
npm install
```

### 4. Run

**Terminal 1 — Backend:**
```bash
cd newsletter-agent
source venv/bin/activate
uvicorn backend.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```bash
cd newsletter-agent/frontend
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) 🎉

---

## 🐍 Python-Only Usage (No Frontend)

```python
from backend.agent.graph import run_newsletter_agent

# Fully autonomous
result = run_newsletter_agent(
    goal="Create a weekly newsletter on latest AI agent news",
    mode="autonomous"
)

print(result["subject_line"])
print(f"Newsletter saved to: {result['output_path']}")
print(f"Quality score: {result['quality_score']}/10")

# Human-in-the-loop (terminal prompts)
result = run_newsletter_agent(
    goal="Create a weekly newsletter on latest AI agent news",
    mode="hitl"
)
```

---

## 📁 Project Structure

```
newsletter-agent/
├── PRD.md                    # Full product requirements
├── README.md                 # This file
├── .env.example              # Environment variables template
├── requirements.txt          # Python dependencies
│
├── backend/
│   ├── main.py               # FastAPI server + SSE streaming
│   ├── agent/
│   │   ├── state.py          # Agent state definition
│   │   ├── tools.py          # Web search, fetch, HTML tools
│   │   ├── prompts.py        # All LLM prompts
│   │   ├── nodes.py          # Agent node functions
│   │   └── graph.py          # LangGraph pipeline
│   └── utils/
│       └── html_generator.py # HTML newsletter template
│
├── frontend/
│   └── src/
│       ├── App.jsx           # Main app
│       └── components/       # UI components
│
└── outputs/                  # Generated newsletters
```

---

## 🔧 Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Gemini API key | Required |
| `TAVILY_API_KEY` | Tavily search key | Required |
| `MAX_ARTICLES` | Articles to research | 7 |
| `MIN_QUALITY_SCORE` | Minimum before rewrite | 7 |
| `MAX_IMPROVE_ITERATIONS` | Max self-improvement loops | 2 |

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Gemini gemini-2.5-flash (Google) |
| Agent Framework | LangGraph |
| LLM Integration | LangChain Google GenAI |
| Web Search | Tavily API |
| Backend | FastAPI + uvicorn |
| Frontend | React 18 + Vite + Tailwind CSS |
| Streaming | Server-Sent Events (SSE) |

---

## 📸 Features Showcase

- **Real-time step visualization** — watch the agent think, search, and write live
- **HTML newsletter preview** — rendered inline in the browser
- **HITL modal** — clean review interface with approval/rejection flow
- **Export** — download HTML, copy subject line
- **Quality scores** — see the agent's self-evaluation

---

## 📄 License

MIT License — use freely, attribution appreciated.

---

## 🐳 Docker / Hugging Face Spaces Deployment

### Build & run locally with Docker

```bash
# Copy your env vars into the build
cp .env.example .env
# Edit .env with real API keys

docker build -t newsletter-agent .
docker run -p 7860:7860 \
  -e GEMINI_API_KEY=your_key \
  -e TAVILY_API_KEY=your_key \
  newsletter-agent
# → Open http://localhost:7860
```

### Deploy to Hugging Face Spaces

1. Create a new Space → **Docker** SDK
2. Push this repo:
   ```bash
   git remote add hf https://huggingface.co/spaces/YOUR_USER/newsletter-agent
   git push hf main
   ```
3. In Space **Settings → Variables**, add:
   - `GEMINI_API_KEY`
   - `TAVILY_API_KEY`
4. Space builds automatically and goes live on port 7860.

> The single Docker image builds the React frontend, then serves it  
> via FastAPI (`backend/main_hf.py`) alongside the `/api/*` endpoints.
