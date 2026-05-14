# Newsletter Agent — Autonomous AI Research & Delivery

Newsletter Agent is a fully autonomous, multi-step AI agentic system designed to research industry news, curate content, and generate professional-grade HTML newsletters. Built with LangGraph and Gemini, it supports both fully autonomous operation and Human-in-the-Loop (HITL) checkpoints for quality control.

## Features

- **Autonomous Research**: Generates targeted search queries and scrapes the web for the latest industry updates using the Tavily API.
- **Smart Summarization**: Extracts key insights and value propositions from multiple articles using Gemini's large context window.
- **Self-Critique & Improvement**: An internal "Editor" node scores drafts and triggers automatic rewrites if quality standards are not met.
- **Human-in-the-Loop (HITL)**: Optional checkpoints to review and modify research plans, content drafts, or final outputs before delivery.
- **Real-time Streaming**: A React-based frontend that visualizes the agent's reasoning steps and progress via Server-Sent Events (SSE).
- **One-Click Deployment**: Dockerized setup optimized for Hugging Face Spaces.

## The Agent Pipeline

The core logic is orchestrated as a stateful graph where each node represents a specialized task:

1. **Plan**: LLM analyzes the goal and creates a research strategy with 4-6 search queries.
2. **Research**: Parallel web searching and content fetching (scraping).
3. **Summarize**: Distilling long articles into concise, actionable summaries.
4. **Write**: Drafting the newsletter in Markdown (Intro, Content, Conclusion).
5. **Review**: Self-scoring (1-10) based on relevance and tone.
6. **Improve**: (Conditional) Automatic revision if the score is <7.
7. **Generate HTML**: Conversion of Markdown into a responsive, styled email template.

## Tech Stack

| Layer | Technology |
| --- | --- |
| LLM | Google Gemini (1.5 Flash / Pro) |
| Agent Framework | LangGraph (Stateful, HITL support) |
| Search Engine | Tavily AI |
| Backend | FastAPI (Python) |
| Frontend | React + Vite + Tailwind CSS |
| Deployment | Docker / Hugging Face Spaces |

## Installation & Setup

### 1. Prerequisites

- Python 3.11+
- Node.js 18+
- Google Gemini API Key
- Tavily API Key

### 2. Backend Configuration

```bash
# Clone the repository
git clone https://github.com/your-username/newsletter-agent.git
cd newsletter-agent

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and TAVILY_API_KEY
```

### 3. Frontend Configuration

```bash
cd frontend
npm install
npm run dev
```

## Deployment (Hugging Face Spaces)

The project includes a multi-stage Dockerfile that builds the React frontend and serves it via the FastAPI backend in a single container.

1. Create a new Docker Space on Hugging Face.
2. Upload the repository files.
3. In the Space Settings, add the following Secrets:
   - `GOOGLE_API_KEY`
   - `TAVILY_API_KEY`
4. The Space will automatically build and deploy to port 7860.

## Project Structure

```plaintext
newsletter-agent/
├── backend/
│   ├── agent/             # LangGraph nodes, state, and tools
│   ├── utils/             # HTML templates and formatting
│   └── main.py            # FastAPI entry point & SSE logic
├── frontend/
│   ├── src/               # React components and UI logic
│   └── dist/              # Compiled frontend (for production)
├── outputs/               # Saved newsletter files
├── Dockerfile             # Multi-stage build for HF deployment
└── PRD.md                 # Product Requirements Document
```

## License

Distributed under the MIT License. See LICENSE for more information.
