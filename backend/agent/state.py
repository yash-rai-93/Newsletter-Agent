"""
Agent State Definition
----------------------
Defines the shared state that flows through all nodes in the LangGraph pipeline.
Every node reads from and writes to this state.
"""

from typing import TypedDict, List, Optional, Literal


class Article(TypedDict):
    """Represents a researched article."""
    title: str
    url: str
    snippet: str
    content: str
    summary: str
    key_points: List[str]


class StepLog(TypedDict):
    """Represents a single step in the agent's execution log."""
    step: str
    status: Literal["running", "complete", "error", "waiting"]
    message: str
    data: Optional[dict]


class AgentState(TypedDict):
    """
    Central state object for the Newsletter Agent pipeline.
    Passed between all LangGraph nodes.
    """

    # ── Input ─────────────────────────────────────────────────────────────────
    goal: str                          # Natural language goal from user
    mode: Literal["autonomous", "hitl"] # Execution mode
    run_id: str                        # Unique ID for this run

    # ── Planning ──────────────────────────────────────────────────────────────
    topic: str                         # Extracted newsletter topic
    audience: str                      # Inferred target audience
    plan: str                          # Full research & writing plan
    search_queries: List[str]          # Generated search queries

    # ── Research ──────────────────────────────────────────────────────────────
    articles: List[Article]            # Fetched + summarized articles
    raw_search_results: List[dict]     # Raw Tavily search results

    # ── Writing ───────────────────────────────────────────────────────────────
    newsletter_draft: str              # Markdown draft
    newsletter_html: str               # Final HTML newsletter
    subject_line: str                  # Email subject line
    preview_text: str                  # Email preview text

    # ── Review & Improvement ──────────────────────────────────────────────────
    critique: str                      # Agent's self-critique
    quality_score: int                 # 1-10 quality score
    improvement_needed: bool           # Whether to rewrite
    iteration_count: int               # How many improvement loops done

    # ── Human-in-the-Loop ─────────────────────────────────────────────────────
    awaiting_human: bool               # Currently paused for human input
    human_checkpoint: str              # Which checkpoint we're at
    human_feedback: Optional[str]      # Feedback text from human
    human_approved: bool               # Whether human approved

    # ── Output ────────────────────────────────────────────────────────────────
    output_path: str                   # Path to saved HTML file
    plain_text_output: str             # Plain text version

    # ── Logging ───────────────────────────────────────────────────────────────
    steps_log: List[StepLog]           # All steps taken
    current_step: str                  # Current active step name
    error: Optional[str]               # Error message if any
