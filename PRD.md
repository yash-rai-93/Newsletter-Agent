# 📰 Newsletter Agent — Product Requirements Document

**Version:** 1.0.0  
**Author:** AI Developer Assignment  
**Status:** Active Development  
**Platform:** Antigravity

---

## 1. Executive Summary

Newsletter Agent is a **fully autonomous, multi-step AI agent** that researches the latest AI industry news, summarizes top articles, generates a polished HTML newsletter, critiques its own output, and simulates delivery — all from a single natural-language goal. It supports both a **Fully Autonomous** mode and a **Human-in-the-Loop (HITL)** mode, with a real-time streaming frontend for live interaction.

---

## 2. Problem Statement

Creating a high-quality, timely newsletter requires:
- Hours of manual research across dozens of sources
- Content curation and summarization
- Writing and formatting expertise
- Editing and quality review

Newsletter Agent automates this entire pipeline using an orchestrated AI agent with specialized tools, multi-step reasoning, and self-reflection capabilities.

---

## 3. Goals & Success Metrics

| Goal | Metric |
|------|--------|
| Fully autonomous end-to-end pipeline | Single `run_newsletter_agent(goal)` call produces newsletter |
| Research quality | ≥ 5 unique, relevant articles per run |
| Newsletter quality score | Agent self-scores ≥ 7/10 before finalizing |
| Latency | Full pipeline completes in < 90 seconds |
| HITL mode | Human can inject feedback at 3 checkpoints |
| Output formats | HTML + plain text + subject line |

---

## 4. Users & Use Cases

### Primary Users
- **Developers / Students**: Building and demonstrating agentic AI systems
- **Content Marketers**: Automating weekly newsletter creation
- **Researchers**: Tracking AI news trends autonomously

### Core Use Cases
1. **UC-01**: Run fully autonomous newsletter generation from a topic goal
2. **UC-02**: Run HITL mode — review and approve agent plan, draft, and final output
3. **UC-03**: View real-time agent reasoning steps in the frontend
4. **UC-04**: Preview and download the generated HTML newsletter
5. **UC-05**: Export newsletter to file for simulated sending

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     FRONTEND (React + Vite)              │
│  ┌──────────────┐  ┌────────────────┐  ┌─────────────┐  │
│  │  Goal Input  │  │  Agent Steps   │  │  Newsletter │  │
│  │  + Mode      │  │  Live Stream   │  │  Preview    │  │
│  │  Toggle      │  │  (SSE)         │  │  + Export   │  │
│  └──────────────┘  └────────────────┘  └─────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP + SSE
┌────────────────────────▼────────────────────────────────┐
│                   BACKEND (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────┐ │
│  │              LangGraph Agent Pipeline                │ │
│  │                                                     │ │
│  │  ┌──────┐  ┌────────┐  ┌───────┐  ┌────────────┐  │ │
│  │  │ Plan │→ │Research│→ │ Write │→ │   Review   │  │ │
│  │  └──────┘  └────────┘  └───────┘  └─────┬──────┘  │ │
│  │     ↑ HITL    ↑ HITL       ↑ HITL       │         │ │
│  │  checkpoint checkpoint  checkpoint       ↓         │ │
│  │                                    ┌─────────┐     │ │
│  │                                    │ Improve │     │ │
│  │                                    └────┬────┘     │ │
│  │                                         ↓          │ │
│  │                                    ┌─────────┐     │ │
│  │                                    │ Output  │     │ │
│  │                                    └─────────┘     │ │
│  └─────────────────────────────────────────────────────┘ │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  Web Search  │  │  HTML        │  │  File Output   │  │
│  │  Tool        │  │  Generator   │  │  Tool          │  │
│  │  (Tavily)    │  │  Tool        │  │                │  │
│  └──────────────┘  └──────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────-┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              LLM (Gemini gemini-2.5-flash)              │
└─────────────────────────────────────────────────────────┘
```

---

## 6. Agent Pipeline (Detailed)

### Step 1: Plan
- **Input**: Natural language goal
- **Process**: LLM extracts topic, identifies audience, creates research plan with 4-6 targeted search queries
- **Output**: Structured plan + search query list
- **HITL Checkpoint**: Human can modify plan or add/remove queries

### Step 2: Research
- **Input**: Search queries from plan
- **Process**: Parallel web searches via Tavily API, deduplication, relevance ranking
- **Output**: Raw articles with titles, URLs, snippets
- **Tool**: `web_search_tool`

### Step 3: Fetch & Summarize
- **Input**: Top 5-7 articles
- **Process**: Fetch full content, LLM summarizes each article (150-200 words), extracts key points
- **Output**: Enriched article list with summaries
- **Tool**: `fetch_article_tool`, `summarize_tool`

### Step 4: Write Draft
- **Input**: Summarized articles, plan
- **Process**: LLM generates full newsletter — intro, article sections, conclusion, CTA
- **Output**: Markdown newsletter draft
- **HITL Checkpoint**: Human can edit draft, add/remove sections

### Step 5: Generate HTML
- **Input**: Markdown draft
- **Process**: Convert to beautiful, responsive HTML newsletter
- **Output**: Production-ready HTML
- **Tool**: `html_generator_tool`

### Step 6: Review & Critique
- **Input**: HTML newsletter
- **Process**: LLM acts as editor — evaluates structure, quality, relevance, tone. Scores 1-10.
- **Output**: Critique + quality score + improvement flag
- **HITL Checkpoint**: Human sees critique, can override approve/reject

### Step 7: Improve (Conditional)
- **Trigger**: Score < 7 OR human rejected
- **Process**: LLM rewrites based on critique (max 2 iterations)
- **Output**: Improved newsletter

### Step 8: Output
- **Process**: Save HTML file, generate plain text version, log subject line
- **Output**: Final newsletter file + metadata

---

## 7. Tools Specification

| Tool | Description | API |
|------|-------------|-----|
| `web_search_tool` | Search for latest news articles | Tavily API |
| `fetch_article_tool` | Fetch and parse article content | httpx + BeautifulSoup |
| `html_generator_tool` | Convert markdown to HTML newsletter | Template engine |
| `file_output_tool` | Save newsletter to disk | Python stdlib |
| `quality_scorer_tool` | Score newsletter quality 1-10 | LLM-based |

---

## 8. Human-in-the-Loop (HITL) Mode

HITL mode adds three interactive checkpoints using **LangGraph's interrupt mechanism**:

1. **After Plan**: Show research plan → Human can approve, modify queries, or add context
2. **After Draft**: Show newsletter draft → Human can edit content, tone, length
3. **After Review**: Show critique → Human can override quality score, force finalize

In **Autonomous Mode**, all checkpoints are skipped and the agent self-decides at each step.

---

## 9. Frontend Features

| Feature | Description |
|---------|-------------|
| Goal Input | Rich text input for natural language goal |
| Topic Presets | Quick-select buttons for common newsletter topics |
| Mode Toggle | Animated toggle between Autonomous / HITL |
| Live Agent Steps | Real-time streaming of each agent step with icons and status |
| Step Expansion | Click any step to see full reasoning/output |
| Newsletter Preview | Live HTML preview panel |
| Export Options | Download HTML, copy plain text |
| Run History | Last 5 newsletter runs stored in session |
| Human Review Modal | Clean review interface for HITL checkpoints |

---

## 10. API Specification

### POST `/api/run`
Start newsletter agent run.

**Request:**
```json
{
  "goal": "Create a weekly newsletter on latest AI agent news",
  "mode": "autonomous | hitl",
  "topic_override": "optional topic string"
}
```

**Response:** Server-Sent Events stream
```
data: {"type": "step_start", "step": "plan", "message": "Creating research plan..."}
data: {"type": "step_complete", "step": "plan", "data": {"plan": "...", "queries": [...]}}
data: {"type": "hitl_checkpoint", "step": "plan", "data": {...}}  // HITL only
data: {"type": "newsletter_ready", "data": {"html": "...", "subject": "...", "path": "..."}}
data: {"type": "complete"}
```

### POST `/api/feedback`
Submit human feedback for HITL checkpoint.

**Request:**
```json
{
  "run_id": "abc123",
  "checkpoint": "plan | draft | review",
  "approved": true,
  "feedback": "optional modification text"
}
```

### GET `/api/output/{run_id}`
Download final newsletter file.

---

## 11. Tech Stack

| Layer | Technology | Reason |
|-------|-----------|--------|
| LLM | Gemini gemini-2.5-flash (Google) | Fast reasoning + instruction following |
| Agent Framework | LangGraph | Native HITL support, stateful graph, production-grade |
| LLM Integration | LangChain Google GenAI | Seamless Gemini integration |
| Web Search | Tavily API | Purpose-built for AI agents |
| Backend | FastAPI + uvicorn | Async SSE streaming, fast |
| Frontend | React + Vite + Tailwind CSS | Fast iteration, beautiful UI |
| State Store | LangGraph MemorySaver | In-memory checkpointing for HITL |

---

## 12. Project Structure

```
newsletter-agent/
├── PRD.md                          # This document
├── README.md                       # Setup and usage guide
├── .env.example                    # Required environment variables
├── .gitignore                      
├── requirements.txt                # Python dependencies
├── docker-compose.yml              # Optional Docker setup
│
├── backend/
│   ├── main.py                     # FastAPI app + SSE endpoints
│   ├── agent/
│   │   ├── state.py                # LangGraph AgentState TypedDict
│   │   ├── tools.py                # Tool definitions (search, fetch, HTML)
│   │   ├── prompts.py              # All LLM prompts
│   │   ├── nodes.py                # Individual agent node functions
│   │   └── graph.py                # LangGraph StateGraph construction
│   └── utils/
│       └── html_generator.py       # HTML newsletter template
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       └── components/
│           ├── GoalInput.jsx       # Goal + mode input panel
│           ├── AgentSteps.jsx      # Real-time step visualization
│           ├── NewsletterPreview.jsx # HTML preview panel
│           └── HumanReview.jsx     # HITL checkpoint modal
│
└── outputs/                        # Generated newsletters saved here
    └── .gitkeep
```

---

## 13. Environment Variables

```bash
GEMINI_API_KEY=           # Gemini API key (required)
TAVILY_API_KEY=              # Tavily search API key (required)
BACKEND_PORT=8000            # FastAPI port (default: 8000)
FRONTEND_PORT=5173           # Vite dev server port (default: 5173)
MAX_ARTICLES=7               # Max articles to research (default: 7)
MAX_IMPROVE_ITERATIONS=2     # Max self-improvement loops (default: 2)
MIN_QUALITY_SCORE=7          # Minimum score before improvement (default: 7)
```

---

## 14. Non-Functional Requirements

| NFR | Requirement |
|-----|-------------|
| Performance | Pipeline completes in < 90s on average |
| Reliability | Graceful error handling, retry on API failures |
| Scalability | Stateless backend, each run is independent |
| Security | API keys in env vars, never in code |
| Code Quality | Type hints, docstrings, modular functions |
| Observability | Full step logging, error tracing |

---

## 15. Out of Scope (v1.0)

- Actual email sending (SMTP integration)
- Persistent database for newsletter history
- Multiple subscriber management
- Scheduled/automated runs
- Multi-language support
- Custom templates via UI

---

## 16. Future Roadmap

- **v1.1**: SMTP sending + subscriber list management
- **v1.2**: Custom newsletter templates in UI
- **v1.3**: Scheduled autonomous runs (cron/celery)
- **v2.0**: Multi-agent setup (Researcher, Writer, Editor agents)
- **v2.1**: Memory across runs (personalization based on past newsletters)
