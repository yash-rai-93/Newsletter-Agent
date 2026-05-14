"""
FastAPI Server
--------------
Main API server for the Newsletter Agent.

Endpoints:
  POST /api/run        — Start agent run, stream events via SSE
  POST /api/feedback   — Submit human feedback for HITL checkpoints
  GET  /api/status/{run_id}  — Get current run status
  GET  /api/output/{run_id}  — Download generated newsletter
  GET  /health         — Health check
"""

import os
import json
import uuid
import asyncio
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .agent.graph import build_graph, stream_newsletter_agent

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# App Setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Newsletter Agent API",
    description="Autonomous AI agent for newsletter generation",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for active runs (in production, use Redis)
active_runs: dict[str, dict] = {}
run_graphs: dict[str, any] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class RunRequest(BaseModel):
    goal: str
    mode: str = "autonomous"  # "autonomous" | "hitl"
    topic_override: Optional[str] = None

class FeedbackRequest(BaseModel):
    run_id: str
    checkpoint: str  # "plan" | "write"
    approved: bool
    feedback: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# SSE Helper
# ─────────────────────────────────────────────────────────────────────────────

def sse_event(data: dict) -> str:
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data)}\n\n"


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Simple health check."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/run")
async def run_agent(request: RunRequest):
    run_id = str(uuid.uuid4())[:8]
    
    active_runs[run_id] = {
        "goal": request.goal,
        "mode": request.mode,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "final_state": None
    }
    
    async def event_generator():
        yield sse_event({"type": "run_started", "run_id": run_id})
        
        try:
            async for event in _run_graph_stream(request.goal, request.mode, run_id):
                yield sse_event(event)
                
                if event.get("type") == "hitl_checkpoint":
                    active_runs[run_id]["status"] = f"waiting_hitl_{event.get('step')}"
                    active_runs[run_id]["checkpoint_data"] = event.get("data", {})
                    active_runs[run_id]["checkpoint_step"] = event.get("step")
                elif event.get("type") == "complete":
                    active_runs[run_id]["status"] = "complete"
                    
        except Exception as e:
            active_runs[run_id]["status"] = "error"
            yield sse_event({"type": "error", "message": str(e)})
            
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"}
    )

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    run_id = request.run_id
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
    run_data = active_runs[run_id]
    if not run_data["status"].startswith("waiting_hitl"):
        raise HTTPException(status_code=400, detail="Run is not awaiting human feedback")
        
    active_runs[run_id]["feedback"] = {
        "approved": request.approved,
        "text": request.feedback,
        "checkpoint": request.checkpoint
    }
    active_runs[run_id]["status"] = "running"
    
    async def feedback_stream():
        try:
            async for event in _run_graph_stream(run_data["goal"], run_data["mode"], run_id, feedback=active_runs[run_id]["feedback"]):
                yield sse_event(event)
                if event.get("type") == "hitl_checkpoint":
                    active_runs[run_id]["status"] = f"waiting_hitl_{event.get('step')}"
                elif event.get("type") == "complete":
                    active_runs[run_id]["status"] = "complete"
        except Exception as e:
            yield sse_event({"type": "error", "message": str(e)})
            
    return StreamingResponse(
        feedback_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.get("/api/status/{run_id}")
async def get_run_status(run_id: str):
    """Get the current status of a run."""
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    run = active_runs[run_id]
    return {
        "run_id": run_id,
        "status": run["status"],
        "goal": run["goal"],
        "mode": run["mode"],
        "started_at": run["started_at"],
    }


@app.get("/api/output/{run_id}")
async def get_output(run_id: str):
    """Download the final newsletter HTML file."""
    if run_id not in active_runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    final_state = active_runs[run_id].get("final_state", {})
    output_path = final_state.get("output_path", "")
    
    if not output_path or not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_path,
        media_type="text/html",
        filename=os.path.basename(output_path)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Internal Streaming Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _run_graph_stream(goal: str, mode: str, run_id: str, feedback: Optional[dict] = None):
    import threading
    import queue
    from .agent.graph import build_graph
    
    event_queue = queue.Queue()
    app = build_graph(mode)
    config = {"configurable": {"thread_id": run_id}}
    
    def run_sync():
        try:
            if feedback:
                app.update_state(config, {
                    "human_approved": feedback["approved"],
                    "human_feedback": feedback["text"],
                    "improvement_needed": bool(feedback["text"]) if feedback["checkpoint"] == "write" else False
                })
                stream = app.stream(None, config, stream_mode="values")
            else:
                initial_state = {
                    "goal": goal, "mode": mode, "run_id": run_id, 
                    "topic": "", "audience": "", "plan": "",
                    "search_queries": [], "articles": [], "raw_search_results": [],
                    "newsletter_draft": "", "newsletter_html": "", "subject_line": "", "preview_text": "",
                    "critique": "", "quality_score": 0, "improvement_needed": False, "iteration_count": 0,
                    "awaiting_human": False, "human_checkpoint": "", "human_feedback": None, "human_approved": True,
                    "output_path": "", "plain_text_output": "", "steps_log": [], "current_step": "start", "error": None
                }
                stream = app.stream(initial_state, config, stream_mode="values")
                
            step_labels = {
                "plan": "Creating research plan",
                "research": "Searching the web for articles",
                "summarize": "Summarizing top articles",
                "write": "Writing the newsletter",
                "review": "Self-reviewing quality",
                "improve": "Improving the draft",
                "output": "Generating final output",
            }
            
            prev_step = "start" if not feedback else feedback["checkpoint"]
            
            for event in stream:
                current_step = event.get("current_step", "")
                if current_step and current_step != prev_step and current_step != "start":
                    step_data = {
                        "type": "step_complete",
                        "step": current_step,
                        "label": step_labels.get(current_step, current_step),
                        "data": _extract_step_data(current_step, event)
                    }
                    event_queue.put(step_data)
                    if current_step == "output":
                        active_runs[run_id]["final_state"] = event
                    prev_step = current_step
                    
            state = app.get_state(config)
            if state.next:
                current_step = state.values.get("current_step", "")
                checkpoint_data = {
                    "type": "hitl_checkpoint",
                    "step": current_step,
                    "data": _extract_step_data(current_step, state.values)
                }
                event_queue.put(checkpoint_data)
            else:
                event_queue.put({"type": "complete", "run_id": run_id})
                
        except Exception as e:
            event_queue.put({"type": "error", "message": str(e)})
        finally:
            event_queue.put(None)
            
    thread = threading.Thread(target=run_sync, daemon=True)
    thread.start()
    
    loop = asyncio.get_event_loop()
    while True:
        event = await loop.run_in_executor(None, event_queue.get, True, 120)
        if event is None:
            break
        yield event


def _extract_step_data(step: str, event: dict) -> dict:
    """Extract relevant data for each step type."""
    if step == "plan":
        return {
            "topic": event.get("topic"),
            "audience": event.get("audience"),
            "plan": event.get("plan"),
            "search_queries": event.get("search_queries", [])
        }
    elif step == "research":
        articles = event.get("raw_search_results", [])
        return {
            "article_count": len(articles),
            "titles": [a.get("title", "")[:70] for a in articles]
        }
    elif step == "summarize":
        articles = event.get("articles", [])
        return {
            "article_count": len(articles),
            "articles": [
                {"title": a["title"], "summary": a["summary"], "url": a["url"]}
                for a in articles
            ]
        }
    elif step == "write":
        return {
            "subject_line": event.get("subject_line"),
            "preview_text": event.get("preview_text"),
            "draft_length": len(event.get("newsletter_draft", ""))
        }
    elif step == "review":
        return {
            "quality_score": event.get("quality_score"),
            "critique": event.get("critique"),
            "improvement_needed": event.get("improvement_needed"),
        }
    elif step == "improve":
        return {"iteration": event.get("iteration_count")}
    elif step == "output":
        return {
            "output_path": event.get("output_path"),
            "newsletter_html": event.get("newsletter_html", ""),
            "subject_line": event.get("subject_line"),
            "quality_score": event.get("quality_score"),
            "article_count": len(event.get("articles", [])),
            "plain_text": event.get("plain_text_output", "")
        }
    return {}
