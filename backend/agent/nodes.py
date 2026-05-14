"""
Agent Nodes
-----------
Each function here is a LangGraph node — it receives the full AgentState,
performs one step of the pipeline, and returns updated state fields.

Pipeline order:
  plan_node → research_node → write_node → review_node → improve_node → output_node
"""

import os
import json
import asyncio
import uuid
from datetime import datetime
from typing import Any
from dotenv import load_dotenv

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from .state import AgentState, Article, StepLog
from .prompts import (
    SYSTEM_PROMPT, PLAN_PROMPT, SUMMARIZE_PROMPT,
    WRITE_PROMPT, CRITIQUE_PROMPT, IMPROVE_PROMPT
)
from .tools import (
    web_search_tool, fetch_article_tool, fetch_articles_parallel,
    html_generator_tool, file_output_tool, deduplicate_articles
)

load_dotenv()

MAX_ARTICLES = int(os.getenv("MAX_ARTICLES", 7))
MIN_QUALITY_SCORE = int(os.getenv("MIN_QUALITY_SCORE", 7))
MAX_IMPROVE_ITERATIONS = int(os.getenv("MAX_IMPROVE_ITERATIONS", 2))


# ─────────────────────────────────────────────────────────────────────────────
# LLM Factory
# ─────────────────────────────────────────────────────────────────────────────

def get_llm() -> ChatGroq:
    """Create and return a Groq LLM instance."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        max_tokens=4096,
        api_key=os.getenv("GROQ_API_KEY")
    )


def call_llm_json(llm: ChatGroq, system: str, user: str) -> dict:
    """
    Call the LLM and parse JSON response.
    Returns empty dict on parse failure.
    """
    try:
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=user)
        ]
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()
        
        return json.loads(content, strict=False)
    except json.JSONDecodeError as e:
        print(f"[Node] JSON parse error: {e}")
        print(f"[Node] Raw content: {response.content[:200]}")
        return {}
    except Exception as e:
        print(f"[Node] LLM call error: {e}")
        return {}


def log_step(state: AgentState, step: str, status: str, message: str, data: Any = None) -> list:
    """Create an updated steps_log with a new entry."""
    logs = list(state.get("steps_log", []))
    logs.append({
        "step": step,
        "status": status,
        "message": message,
        "data": data,
        "timestamp": datetime.now().isoformat()
    })
    return logs


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: Plan
# ─────────────────────────────────────────────────────────────────────────────

def plan_node(state: AgentState) -> dict:
    """
    STEP 1 — PLAN
    Extract topic from goal, create research plan, generate search queries.
    """
    print(f"\n[plan_node] 🧠 Planning for goal: {state['goal'][:80]}...")
    
    llm = get_llm()
    
    result = call_llm_json(
        llm,
        SYSTEM_PROMPT,
        PLAN_PROMPT.format(goal=state["goal"])
    )
    
    if not result:
        # Fallback
        result = {
            "topic": state["goal"],
            "audience": "tech-savvy professionals",
            "plan": "Research and summarize top AI news",
            "search_queries": [
                "latest AI agent news 2025",
                "AI automation developments 2025",
                "large language model news this week",
                "AI startup funding 2025",
                "AI agent framework releases 2025"
            ]
        }
    
    logs = log_step(state, "plan", "complete", 
                    f"Created plan with {len(result.get('search_queries', []))} search queries",
                    {"topic": result.get("topic"), "queries": result.get("search_queries")})
    
    print(f"[plan_node] ✅ Topic: {result.get('topic')}")
    print(f"[plan_node] 🔍 Queries: {result.get('search_queries')}")
    
    return {
        "topic": result.get("topic", state["goal"]),
        "audience": result.get("audience", "professionals"),
        "plan": result.get("plan", ""),
        "search_queries": result.get("search_queries", []),
        "current_step": "plan",
        "steps_log": logs,
        "iteration_count": 0,
        "improvement_needed": False,
        "awaiting_human": False,
        "human_approved": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 2: Research
# ─────────────────────────────────────────────────────────────────────────────

async def research_node_async(state: AgentState) -> dict:
    """Async implementation of research node."""
    queries = state.get("search_queries", [])
    print(f"\n[research_node] 🔍 Running {len(queries)} searches...")
    
    # Run all searches in parallel
    search_tasks = [web_search_tool(q, max_results=4) for q in queries]
    all_results = await asyncio.gather(*search_tasks)
    
    # Flatten and deduplicate
    flat_results = []
    for results in all_results:
        flat_results.extend(results)
    
    unique_results = deduplicate_articles(flat_results)
    
    # Sort by score, take top MAX_ARTICLES
    unique_results.sort(key=lambda x: x.get("score", 0), reverse=True)
    top_results = unique_results[:MAX_ARTICLES]
    
    print(f"[research_node] 📰 Found {len(unique_results)} unique articles, using top {len(top_results)}")
    
    # Fetch article content in parallel
    urls = [r["url"] for r in top_results]
    contents = await fetch_articles_parallel(urls)
    
    # Merge content into results
    for i, result in enumerate(top_results):
        result["content"] = contents[i] if i < len(contents) else ""
    
    logs = log_step(state, "research", "complete",
                    f"Fetched {len(top_results)} articles",
                    {"article_titles": [r.get("title", "")[:60] for r in top_results]})
    
    return {
        "raw_search_results": top_results,
        "current_step": "research",
        "steps_log": logs,
    }


def research_node(state: AgentState) -> dict:
    """STEP 2 — RESEARCH: Search and fetch articles."""
    return asyncio.run(research_node_async(state))


# ─────────────────────────────────────────────────────────────────────────────
# Node 3: Summarize
# ─────────────────────────────────────────────────────────────────────────────

def summarize_node(state: AgentState) -> dict:
    """
    STEP 3 — SUMMARIZE
    Use LLM to summarize each article and extract key points.
    """
    print(f"\n[summarize_node] 📝 Summarizing articles...")
    
    llm = get_llm()
    raw_results = state.get("raw_search_results", [])
    articles: list[Article] = []
    
    for i, result in enumerate(raw_results):
        print(f"[summarize_node]   Summarizing {i+1}/{len(raw_results)}: {result.get('title', '')[:50]}")
        
        # Use content if available, fallback to snippet
        content = result.get("content") or result.get("snippet", "")
        if len(content) < 100:
            content = result.get("snippet", "No content available")
        
        summary_result = call_llm_json(
            llm,
            SYSTEM_PROMPT,
            SUMMARIZE_PROMPT.format(
                title=result.get("title", ""),
                url=result.get("url", ""),
                content=content[:2000]  # Cap to avoid token overflow
            )
        )
        
        article: Article = {
            "title": result.get("title", "Untitled"),
            "url": result.get("url", ""),
            "snippet": result.get("snippet", ""),
            "content": content[:500],
            "summary": summary_result.get("summary", result.get("snippet", "")),
            "key_points": summary_result.get("key_points", [])
        }
        articles.append(article)
    
    logs = log_step(state, "summarize", "complete",
                    f"Summarized {len(articles)} articles",
                    {"summaries": [a["summary"][:100] for a in articles]})
    
    print(f"[summarize_node] ✅ Summarized {len(articles)} articles")
    
    return {
        "articles": articles,
        "current_step": "summarize",
        "steps_log": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 4: Write
# ─────────────────────────────────────────────────────────────────────────────

def write_node(state: AgentState) -> dict:
    """
    STEP 4 — WRITE
    Generate the full newsletter draft from summarized articles.
    """
    print(f"\n[write_node] ✍️  Writing newsletter draft...")
    
    llm = get_llm()
    articles = state.get("articles", [])
    
    # Format articles for the prompt
    articles_text = ""
    for i, article in enumerate(articles, 1):
        articles_text += f"""
**Article {i}:** {article['title']}
URL: {article['url']}
Summary: {article['summary']}
Key Points: {', '.join(article.get('key_points', [])[:3])}
---"""
    
    result = call_llm_json(
        llm,
        SYSTEM_PROMPT,
        WRITE_PROMPT.format(
            topic=state.get("topic", "AI News"),
            audience=state.get("audience", "professionals"),
            plan=state.get("plan", ""),
            articles_text=articles_text,
            num_articles=len(articles),
            date=datetime.now().strftime("%B %d, %Y")
        )
    )
    
    newsletter_md = result.get("newsletter", "")
    subject_line = result.get("subject_line", f"This Week in {state.get('topic', 'AI')}")
    preview_text = result.get("preview_text", "Your weekly digest of the latest news")
    
    print(f"[write_node] ✅ Draft written ({len(newsletter_md)} chars)")
    print(f"[write_node] 📧 Subject: {subject_line}")
    
    logs = log_step(state, "write", "complete",
                    f"Draft written: {len(newsletter_md)} chars",
                    {"subject_line": subject_line, "preview_text": preview_text})
    
    return {
        "newsletter_draft": newsletter_md,
        "subject_line": subject_line,
        "preview_text": preview_text,
        "current_step": "write",
        "steps_log": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 5: Review (Self-Reflection / Critique)
# ─────────────────────────────────────────────────────────────────────────────

def review_node(state: AgentState) -> dict:
    """
    STEP 5 — REVIEW (Self-Reflection)
    Agent critiques its own newsletter, scores quality, decides if improvement needed.
    This is the key agentic behavior: self-evaluation.
    """
    print(f"\n[review_node] 🔎 Self-reviewing newsletter...")
    
    llm = get_llm()
    
    # Use latest draft (could be improved version)
    newsletter = state.get("newsletter_draft", "")
    
    result = call_llm_json(
        llm,
        SYSTEM_PROMPT,
        CRITIQUE_PROMPT.format(newsletter=newsletter[:4000])
    )
    
    quality_score = result.get("overall_score", 7)
    critique = result.get("critique", "No critique available")
    improvement_needed = result.get("improvement_needed", False)
    top_improvements = result.get("top_improvements", [])
    
    # Override: force improvement if we haven't hit max iterations
    current_iteration = state.get("iteration_count", 0)
    if current_iteration >= MAX_IMPROVE_ITERATIONS:
        improvement_needed = False  # Stop loop
    
    print(f"[review_node] 📊 Quality score: {quality_score}/10")
    print(f"[review_node] 💬 Critique: {critique[:100]}...")
    print(f"[review_node] 🔄 Improvement needed: {improvement_needed}")
    
    logs = log_step(state, "review", "complete",
                    f"Quality score: {quality_score}/10. {'Improvements needed.' if improvement_needed else 'Approved.'}",
                    {
                        "quality_score": quality_score,
                        "critique": critique,
                        "improvement_needed": improvement_needed,
                        "top_improvements": top_improvements,
                        "scores": result.get("scores", {})
                    })
    
    return {
        "critique": critique,
        "quality_score": quality_score,
        "improvement_needed": improvement_needed,
        "current_step": "review",
        "steps_log": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 6: Improve
# ─────────────────────────────────────────────────────────────────────────────

def improve_node(state: AgentState) -> dict:
    """
    STEP 6 — IMPROVE (Conditional)
    Rewrites the newsletter based on the critique.
    Only runs if review_node set improvement_needed=True.
    """
    iteration = state.get("iteration_count", 0) + 1
    print(f"\n[improve_node] 🔄 Improving newsletter (iteration {iteration})...")
    
    llm = get_llm()
    
    result = call_llm_json(
        llm,
        SYSTEM_PROMPT,
        IMPROVE_PROMPT.format(
            newsletter=state.get("newsletter_draft", ""),
            critique=state.get("critique", ""),
            improvements="\n".join(state.get("improvement_areas", [])),
            iteration=iteration
        )
    )
    
    improved_draft = result.get("newsletter", state.get("newsletter_draft", ""))
    new_subject = result.get("subject_line", state.get("subject_line", ""))
    new_preview = result.get("preview_text", state.get("preview_text", ""))
    
    print(f"[improve_node] ✅ Improved draft ({len(improved_draft)} chars)")
    
    logs = log_step(state, "improve", "complete",
                    f"Newsletter improved (iteration {iteration})",
                    {"iteration": iteration})
    
    return {
        "newsletter_draft": improved_draft,
        "subject_line": new_subject or state.get("subject_line", ""),
        "preview_text": new_preview or state.get("preview_text", ""),
        "iteration_count": iteration,
        "current_step": "improve",
        "steps_log": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 7: Output
# ─────────────────────────────────────────────────────────────────────────────

def output_node(state: AgentState) -> dict:
    """
    STEP 7 — OUTPUT
    Generate final HTML, save to disk, prepare delivery simulation.
    """
    print(f"\n[output_node] 💾 Generating final output...")
    
    articles = state.get("articles", [])
    newsletter_md = state.get("newsletter_draft", "")
    topic = state.get("topic", "AI Newsletter")
    subject_line = state.get("subject_line", "Weekly Newsletter")
    run_id = state.get("run_id", str(uuid.uuid4())[:8])
    
    # Generate HTML
    newsletter_html = html_generator_tool(
        markdown_content=newsletter_md,
        subject_line=subject_line,
        topic=topic,
        article_count=len(articles)
    )
    
    # Save to disk
    output_path = file_output_tool(newsletter_html, run_id, subject_line)
    
    # Generate plain text version
    plain_text = f"""
Subject: {subject_line}
Preview: {state.get('preview_text', '')}
{'='*60}

{newsletter_md}

{'='*60}
Generated by Newsletter Agent on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """.strip()
    
    print(f"[output_node] ✅ Newsletter saved to: {output_path}")
    print(f"\n{'='*60}")
    print(f"📧 SUBJECT: {subject_line}")
    print(f"📋 PREVIEW: {state.get('preview_text', '')}")
    print(f"📰 ARTICLES: {len(articles)}")
    print(f"⭐ QUALITY: {state.get('quality_score', 0)}/10")
    print(f"📄 SAVED TO: {output_path}")
    print(f"{'='*60}\n")
    
    logs = log_step(state, "output", "complete",
                    f"Newsletter ready! Saved to {output_path}",
                    {
                        "output_path": output_path,
                        "subject_line": subject_line,
                        "article_count": len(articles),
                        "quality_score": state.get("quality_score", 0)
                    })
    
    return {
        "newsletter_html": newsletter_html,
        "plain_text_output": plain_text,
        "output_path": output_path,
        "current_step": "output",
        "steps_log": logs,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Conditional Router
# ─────────────────────────────────────────────────────────────────────────────

def should_improve(state: AgentState) -> str:
    """
    Router: Decide whether to improve or output.
    Returns 'improve' or 'output'.
    """
    if state.get("improvement_needed", False):
        return "improve"
    return "output"
