"""
LangGraph Agent Pipeline
------------------------
Constructs the StateGraph for the Newsletter Agent.

Flow:
  START → plan → research → summarize → write → review
                                                   ↓
                                            [should_improve?]
                                            ↙           ↘
                                        improve        output
                                            ↓             ↓
                                         review          END

Human-in-the-Loop mode adds interrupt_after=["plan", "write"]
allowing human review at those checkpoints.
"""

import uuid
from typing import Optional, AsyncIterator
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import (
    plan_node,
    research_node,
    summarize_node,
    write_node,
    review_node,
    improve_node,
    output_node,
    should_improve
)


# Global checkpointer so state persists across API requests
global_checkpointer = MemorySaver()

def build_graph(mode: str = "autonomous"):
    """
    Build and compile the LangGraph StateGraph.
    
    Args:
        mode: "autonomous" or "hitl"
        
    Returns:
        Compiled LangGraph app
    """
    # Create graph builder
    builder = StateGraph(AgentState)
    
    # ── Add all nodes ──────────────────────────────────────────────────────
    builder.add_node("planner", plan_node)
    builder.add_node("research", research_node)
    builder.add_node("summarize", summarize_node)
    builder.add_node("write", write_node)
    builder.add_node("review", review_node)
    builder.add_node("improve", improve_node)
    builder.add_node("output", output_node)
    
    # ── Define edges (pipeline flow) ───────────────────────────────────────
    builder.add_edge(START, "planner")
    builder.add_edge("planner", "research")
    builder.add_edge("research", "summarize")
    builder.add_edge("summarize", "write")
    builder.add_edge("write", "review")
    
    # Conditional: after review, either improve or output
    builder.add_conditional_edges(
        "review",
        should_improve,
        {
            "improve": "improve",
            "output": "output"
        }
    )
    
    # After improve, go back to review (self-improvement loop)
    builder.add_edge("improve", "review")
    
    # Output is the terminal node
    builder.add_edge("output", END)
    
    # ── Compile with appropriate settings ──────────────────────────────────
    
    if mode == "hitl":
        # HITL: pause after plan and write for human review
        app = builder.compile(
            checkpointer=global_checkpointer,
            interrupt_after=["planner", "write"]
        )
    else:
        # Autonomous: run to completion without interruption
        app = builder.compile(checkpointer=global_checkpointer)
    
    return app


def run_newsletter_agent(
    goal: str,
    mode: str = "autonomous",
    topic_override: Optional[str] = None
) -> dict:
    """
    Main entry point — run the newsletter agent pipeline.
    
    This is the single function call that does everything:
    research → write → review → improve → output
    
    Args:
        goal: Natural language goal (e.g. "Create a weekly newsletter on AI agents")
        mode: "autonomous" or "hitl" (terminal-based HITL prompts)
        topic_override: Optional manual topic override
        
    Returns:
        Final AgentState with newsletter_html, output_path, quality_score, etc.
    """
    run_id = str(uuid.uuid4())[:8]
    
    # Initial state
    initial_state: AgentState = {
        "goal": goal,
        "mode": mode,
        "run_id": run_id,
        "topic": topic_override or "",
        "audience": "",
        "plan": "",
        "search_queries": [],
        "articles": [],
        "raw_search_results": [],
        "newsletter_draft": "",
        "newsletter_html": "",
        "subject_line": "",
        "preview_text": "",
        "critique": "",
        "quality_score": 0,
        "improvement_needed": False,
        "iteration_count": 0,
        "awaiting_human": False,
        "human_checkpoint": "",
        "human_feedback": None,
        "human_approved": False,
        "output_path": "",
        "plain_text_output": "",
        "steps_log": [],
        "current_step": "start",
        "error": None,
    }
    
    config = {"configurable": {"thread_id": run_id}}
    
    if mode == "hitl":
        return _run_hitl(goal, initial_state, config)
    else:
        return _run_autonomous(initial_state, config)


def _run_autonomous(initial_state: AgentState, config: dict) -> dict:
    """Run in fully autonomous mode — no interruptions."""
    app = build_graph("autonomous")
    
    print("\n🤖 Newsletter Agent — AUTONOMOUS MODE")
    print("=" * 50)
    
    final_state = None
    for event in app.stream(initial_state, config, stream_mode="values"):
        final_state = event
        step = event.get("current_step", "")
        if step:
            print(f"  ✅ Step complete: {step}")
    
    return final_state or {}


def _run_hitl(goal: str, initial_state: AgentState, config: dict) -> dict:
    """
    Run in Human-in-the-Loop mode.
    Pauses after 'plan' and 'write' for human review.
    This version uses terminal prompts (for CLI usage).
    """
    app = build_graph("hitl")
    
    print("\n👥 Newsletter Agent — HUMAN-IN-THE-LOOP MODE")
    print("=" * 50)
    
    # ── Phase 1: Run until first interrupt (after plan) ────────────────────
    print("\n📋 Phase 1: Planning...")
    for event in app.stream(initial_state, config, stream_mode="values"):
        current_step = event.get("current_step", "")
        if current_step:
            print(f"  ✅ {current_step}")
    
    state_after_plan = app.get_state(config).values
    
    print(f"\n📋 PLAN REVIEW:")
    print(f"Topic: {state_after_plan.get('topic')}")
    print(f"Search Queries: {state_after_plan.get('search_queries')}")
    print(f"\nPlan:\n{state_after_plan.get('plan')}")
    
    # Human review
    feedback = input("\n👤 Approve plan? (y/n) and optional feedback: ").strip()
    approved = feedback.lower().startswith("y") or feedback == ""
    human_feedback = feedback[2:].strip() if len(feedback) > 2 else None
    
    # Update state with human decision
    app.update_state(config, {
        "human_approved": approved,
        "human_feedback": human_feedback
    })
    
    if not approved:
        print("❌ Plan rejected. Stopping.")
        return app.get_state(config).values
    
    # ── Phase 2: Continue until next interrupt (after write) ───────────────
    print("\n✍️  Phase 2: Researching and writing...")
    for event in app.stream(None, config, stream_mode="values"):
        current_step = event.get("current_step", "")
        if current_step:
            print(f"  ✅ {current_step}")
    
    state_after_write = app.get_state(config).values
    
    print(f"\n📧 DRAFT REVIEW:")
    print(f"Subject: {state_after_write.get('subject_line')}")
    print(f"\nDraft Preview (first 500 chars):")
    print(state_after_write.get('newsletter_draft', '')[:500])
    print("...")
    
    # Human review of draft
    feedback2 = input("\n👤 Approve draft? (y/n) and optional feedback: ").strip()
    approved2 = feedback2.lower().startswith("y") or feedback2 == ""
    human_feedback2 = feedback2[2:].strip() if len(feedback2) > 2 else None
    
    app.update_state(config, {
        "human_approved": approved2,
        "human_feedback": human_feedback2,
        # If they gave feedback, trigger improvement
        "improvement_needed": bool(human_feedback2)
    })
    
    # ── Phase 3: Run to completion ─────────────────────────────────────────
    print("\n🏁 Phase 3: Reviewing, improving, and finalizing...")
    for event in app.stream(None, config, stream_mode="values"):
        current_step = event.get("current_step", "")
        if current_step:
            print(f"  ✅ {current_step}")
    
    return app.get_state(config).values


async def stream_newsletter_agent(
    goal: str,
    mode: str = "autonomous",
    run_id: Optional[str] = None
) -> AsyncIterator[dict]:
    """
    Async generator that streams agent events for the FastAPI SSE endpoint.
    
    Yields dicts with:
      - type: "step_start" | "step_complete" | "hitl_checkpoint" | "error" | "complete"
      - step: step name
      - data: step-specific data
    """
    if not run_id:
        run_id = str(uuid.uuid4())[:8]
    
    initial_state: AgentState = {
        "goal": goal,
        "mode": mode,
        "run_id": run_id,
        "topic": "",
        "audience": "",
        "plan": "",
        "search_queries": [],
        "articles": [],
        "raw_search_results": [],
        "newsletter_draft": "",
        "newsletter_html": "",
        "subject_line": "",
        "preview_text": "",
        "critique": "",
        "quality_score": 0,
        "improvement_needed": False,
        "iteration_count": 0,
        "awaiting_human": False,
        "human_checkpoint": "",
        "human_feedback": None,
        "human_approved": True,
        "output_path": "",
        "plain_text_output": "",
        "steps_log": [],
        "current_step": "start",
        "error": None,
    }
    
    config = {"configurable": {"thread_id": run_id}}
    app = build_graph(mode)
    
    step_labels = {
        "plan": "Creating research plan",
        "research": "Searching the web",
        "summarize": "Summarizing articles",
        "write": "Writing newsletter",
        "review": "Self-reviewing quality",
        "improve": "Improving draft",
        "output": "Generating final output",
    }
    
    prev_step = None
    
    try:
        for event in app.stream(initial_state, config, stream_mode="values"):
            current_step = event.get("current_step", "")
            
            if current_step and current_step != prev_step and current_step != "start":
                # Step completed
                step_data = {
                    "step": current_step,
                    "label": step_labels.get(current_step, current_step),
                }
                
                # Add relevant data for each step
                if current_step == "plan":
                    step_data["data"] = {
                        "topic": event.get("topic"),
                        "audience": event.get("audience"),
                        "plan": event.get("plan"),
                        "search_queries": event.get("search_queries", [])
                    }
                elif current_step == "research":
                    articles = event.get("raw_search_results", [])
                    step_data["data"] = {
                        "article_count": len(articles),
                        "titles": [a.get("title", "")[:60] for a in articles]
                    }
                elif current_step == "summarize":
                    articles = event.get("articles", [])
                    step_data["data"] = {
                        "article_count": len(articles),
                        "articles": [{"title": a["title"], "summary": a["summary"], "url": a["url"]}
                                    for a in articles]
                    }
                elif current_step == "write":
                    step_data["data"] = {
                        "subject_line": event.get("subject_line"),
                        "preview_text": event.get("preview_text"),
                        "draft_length": len(event.get("newsletter_draft", ""))
                    }
                elif current_step == "review":
                    step_data["data"] = {
                        "quality_score": event.get("quality_score"),
                        "critique": event.get("critique"),
                        "improvement_needed": event.get("improvement_needed"),
                    }
                elif current_step == "improve":
                    step_data["data"] = {
                        "iteration": event.get("iteration_count"),
                    }
                elif current_step == "output":
                    step_data["data"] = {
                        "output_path": event.get("output_path"),
                        "newsletter_html": event.get("newsletter_html"),
                        "subject_line": event.get("subject_line"),
                        "quality_score": event.get("quality_score"),
                        "article_count": len(event.get("articles", [])),
                    }
                
                yield {"type": "step_complete", **step_data}
                
                # Check for HITL checkpoint
                if mode == "hitl" and current_step in ("plan", "write"):
                    checkpoint_data = {
                        "plan": {
                            "topic": event.get("topic"),
                            "plan": event.get("plan"),
                            "search_queries": event.get("search_queries", []),
                        },
                        "write": {
                            "subject_line": event.get("subject_line"),
                            "newsletter_draft": event.get("newsletter_draft", "")
                        }
                    }
                    yield {
                        "type": "hitl_checkpoint",
                        "step": current_step,
                        "data": checkpoint_data.get(current_step, {})
                    }
                    # In API mode, we wait for the /feedback endpoint to continue
                    # The graph is interrupted here automatically
                    return
                
                prev_step = current_step
        
        yield {"type": "complete", "run_id": run_id}
        
    except Exception as e:
        yield {"type": "error", "message": str(e)}
