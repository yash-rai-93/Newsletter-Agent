"""
Tools
-----
Tool definitions for the Newsletter Agent.
Each tool is a standalone async function used by the agent nodes.

Tools:
- web_search_tool: Search for articles via Tavily API
- fetch_article_tool: Fetch and parse article content
- html_generator_tool: Convert markdown newsletter to HTML
- file_output_tool: Save newsletter to disk
"""

import os
import re
import json
import httpx
import asyncio
from datetime import datetime
from typing import List, Optional
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./outputs")


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1: Web Search
# ─────────────────────────────────────────────────────────────────────────────

async def web_search_tool(query: str, max_results: int = 5) -> List[dict]:
    """
    Search for recent articles using Tavily API.
    Falls back to DuckDuckGo if Tavily key is not set.
    
    Args:
        query: Search query string
        max_results: Max number of results to return
        
    Returns:
        List of dicts with title, url, content, score
    """
    if TAVILY_API_KEY:
        return await _tavily_search(query, max_results)
    else:
        return await _ddg_fallback_search(query, max_results)


async def _tavily_search(query: str, max_results: int) -> List[dict]:
    """Search using Tavily API (preferred — built for AI agents)."""
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": TAVILY_API_KEY,
                    "query": query,
                    "search_depth": "advanced",
                    "include_answer": False,
                    "include_raw_content": False,
                    "max_results": max_results,
                    "include_domains": [],
                    "exclude_domains": []
                }
            )
            response.raise_for_status()
            data = response.json()
            
            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("content", "")[:500],
                    "score": r.get("score", 0),
                    "published_date": r.get("published_date", "")
                })
            return results
            
        except Exception as e:
            print(f"[Tools] Tavily search error: {e}")
            return []


async def _ddg_fallback_search(query: str, max_results: int) -> List[dict]:
    """Fallback: scrape DuckDuckGo HTML results."""
    async with httpx.AsyncClient(
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0 (compatible; NewsletterAgent/1.0)"},
        follow_redirects=True
    ) as client:
        try:
            url = f"https://html.duckduckgo.com/html/?q={query.replace(' ', '+')}"
            response = await client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            results = []
            for result in soup.select(".result")[:max_results]:
                title_el = result.select_one(".result__title")
                snippet_el = result.select_one(".result__snippet")
                url_el = result.select_one(".result__url")
                
                if title_el and snippet_el:
                    results.append({
                        "title": title_el.get_text(strip=True),
                        "url": f"https://{url_el.get_text(strip=True)}" if url_el else "",
                        "snippet": snippet_el.get_text(strip=True),
                        "score": 0.5,
                        "published_date": ""
                    })
            return results
            
        except Exception as e:
            print(f"[Tools] DDG fallback error: {e}")
            return []


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2: Article Fetcher
# ─────────────────────────────────────────────────────────────────────────────

async def fetch_article_tool(url: str, max_chars: int = 3000) -> str:
    """
    Fetch and parse article content from a URL.
    Extracts main text content, removing nav/footer/ads.
    
    Args:
        url: Article URL to fetch
        max_chars: Max characters to return
        
    Returns:
        Extracted article text content
    """
    if not url or not url.startswith("http"):
        return ""
    
    async with httpx.AsyncClient(
        timeout=15,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NewsletterAgent/1.0)",
            "Accept": "text/html,application/xhtml+xml"
        },
        follow_redirects=True
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove boilerplate elements
            for tag in soup(["script", "style", "nav", "header", "footer",
                             "aside", "advertisement", "iframe", "noscript"]):
                tag.decompose()
            
            # Try to find main article content
            main_content = (
                soup.find("article") or
                soup.find("main") or
                soup.find(class_=re.compile(r"article|content|post|story", re.I)) or
                soup.body
            )
            
            if main_content:
                text = main_content.get_text(separator=" ", strip=True)
            else:
                text = soup.get_text(separator=" ", strip=True)
            
            # Clean up whitespace
            text = re.sub(r"\s+", " ", text).strip()
            
            return text[:max_chars]
            
        except Exception as e:
            print(f"[Tools] Fetch error for {url}: {e}")
            return ""


async def fetch_articles_parallel(urls: List[str]) -> List[str]:
    """Fetch multiple articles in parallel for speed."""
    tasks = [fetch_article_tool(url) for url in urls]
    return await asyncio.gather(*tasks)


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3: HTML Generator
# ─────────────────────────────────────────────────────────────────────────────

def html_generator_tool(
    markdown_content: str,
    subject_line: str,
    topic: str,
    article_count: int
) -> str:
    """
    Convert markdown newsletter to a beautiful, responsive HTML email.
    
    Args:
        markdown_content: Newsletter in Markdown format
        subject_line: Email subject line
        topic: Newsletter topic for header
        article_count: Number of articles included
        
    Returns:
        Complete HTML string
    """
    import markdown2
    
    # Convert markdown to HTML
    html_body = markdown2.markdown(
        markdown_content,
        extras=["fenced-code-blocks", "tables", "strike", "cuddled-lists"]
    )
    
    date_str = datetime.now().strftime("%B %d, %Y")
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="x-apple-disable-message-reformatting">
  <title>{subject_line}</title>
  <style>
    /* Reset */
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background-color: #f0f4f8; font-family: 'Georgia', serif; color: #1a202c; }}
    
    /* Wrapper */
    .wrapper {{ max-width: 640px; margin: 0 auto; padding: 24px 16px; }}
    
    /* Header */
    .header {{ 
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      border-radius: 16px 16px 0 0;
      padding: 40px 40px 32px;
      text-align: center;
    }}
    .header-badge {{
      display: inline-block;
      background: rgba(255,255,255,0.1);
      color: #a0c4ff;
      font-family: 'Courier New', monospace;
      font-size: 11px;
      letter-spacing: 3px;
      text-transform: uppercase;
      padding: 6px 16px;
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,0.15);
      margin-bottom: 16px;
    }}
    .header h1 {{ 
      color: #ffffff;
      font-size: 28px;
      font-weight: 700;
      letter-spacing: -0.5px;
      margin-bottom: 8px;
      line-height: 1.2;
    }}
    .header-meta {{ 
      color: rgba(255,255,255,0.5);
      font-size: 13px;
      font-family: sans-serif;
      margin-top: 12px;
    }}
    .header-divider {{
      height: 1px;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
      margin-top: 24px;
    }}
    
    /* Body */
    .body {{
      background: #ffffff;
      padding: 40px;
      border-left: 1px solid #e2e8f0;
      border-right: 1px solid #e2e8f0;
    }}
    
    /* Typography */
    .body h1 {{ font-size: 26px; color: #0f3460; margin: 32px 0 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 8px; }}
    .body h2 {{ font-size: 20px; color: #1a1a2e; margin: 28px 0 10px; }}
    .body h3 {{ font-size: 17px; color: #2d3748; margin: 20px 0 8px; }}
    .body p {{ font-size: 16px; line-height: 1.75; color: #4a5568; margin-bottom: 16px; }}
    .body ul {{ margin: 12px 0 16px 20px; }}
    .body ul li {{ font-size: 15px; line-height: 1.7; color: #4a5568; margin-bottom: 8px; }}
    .body a {{ color: #0f3460; text-decoration: underline; text-underline-offset: 3px; }}
    .body strong {{ color: #2d3748; font-weight: 600; }}
    .body blockquote {{
      border-left: 3px solid #0f3460;
      padding: 12px 20px;
      margin: 20px 0;
      background: #f7fafc;
      border-radius: 0 8px 8px 0;
      font-style: italic;
      color: #4a5568;
    }}
    
    /* Article cards */
    .body h2 + p, .body h3 + p {{
      padding: 16px;
      background: #f8fafc;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
    }}
    
    /* Stats bar */
    .stats-bar {{
      background: linear-gradient(90deg, #0f3460, #533483);
      border-radius: 8px;
      padding: 16px 24px;
      display: flex;
      justify-content: space-around;
      margin: 24px 0;
    }}
    .stat {{ text-align: center; }}
    .stat-num {{ color: #ffffff; font-size: 22px; font-weight: 700; font-family: sans-serif; }}
    .stat-label {{ color: rgba(255,255,255,0.6); font-size: 11px; letter-spacing: 1px; text-transform: uppercase; font-family: sans-serif; }}
    
    /* Footer */
    .footer {{
      background: #1a1a2e;
      padding: 28px 40px;
      text-align: center;
      border-radius: 0 0 16px 16px;
    }}
    .footer p {{ color: rgba(255,255,255,0.4); font-size: 12px; font-family: sans-serif; line-height: 1.6; margin-bottom: 4px; }}
    .footer a {{ color: rgba(255,255,255,0.6); }}
    .footer-badge {{
      display: inline-block;
      background: rgba(255,255,255,0.05);
      color: rgba(255,255,255,0.3);
      font-family: monospace;
      font-size: 10px;
      padding: 4px 12px;
      border-radius: 12px;
      margin-top: 12px;
      border: 1px solid rgba(255,255,255,0.08);
    }}
    
    /* Responsive */
    @media (max-width: 480px) {{
      .body {{ padding: 24px 20px; }}
      .header {{ padding: 28px 20px 24px; }}
      .header h1 {{ font-size: 22px; }}
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <!-- Header -->
    <div class="header">
      <div class="header-badge">📰 Weekly Digest</div>
      <h1>{topic}</h1>
      <div class="header-meta">{date_str} &nbsp;·&nbsp; {article_count} stories curated by AI</div>
      <div class="header-divider"></div>
    </div>
    
    <!-- Stats Bar -->
    <div class="body">
      <div class="stats-bar">
        <div class="stat">
          <div class="stat-num">{article_count}</div>
          <div class="stat-label">Stories</div>
        </div>
        <div class="stat">
          <div class="stat-num">AI</div>
          <div class="stat-label">Curated</div>
        </div>
        <div class="stat">
          <div class="stat-num">Weekly</div>
          <div class="stat-label">Edition</div>
        </div>
      </div>
      
      <!-- Newsletter Content -->
      {html_body}
    </div>
    
    <!-- Footer -->
    <div class="footer">
      <p>You're receiving this because you subscribed to our newsletter.</p>
      <p><a href="#">Unsubscribe</a> &nbsp;·&nbsp; <a href="#">View in browser</a></p>
      <div class="footer-badge">Generated by Newsletter Agent · Powered by Gemini</div>
    </div>
  </div>
</body>
</html>"""


# ─────────────────────────────────────────────────────────────────────────────
# Tool 4: File Output
# ─────────────────────────────────────────────────────────────────────────────

def file_output_tool(html_content: str, run_id: str, subject_line: str) -> str:
    """
    Save newsletter HTML to disk and return the file path.
    
    Args:
        html_content: Full HTML string
        run_id: Unique run identifier
        subject_line: For the filename
        
    Returns:
        Path to saved file
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Clean subject for filename
    safe_name = re.sub(r"[^a-z0-9_-]", "_", subject_line.lower())[:50]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"newsletter_{timestamp}_{safe_name}.html"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"[Tools] Newsletter saved to: {filepath}")
    return filepath


def deduplicate_articles(articles: List[dict]) -> List[dict]:
    """Remove duplicate articles by URL."""
    seen_urls = set()
    unique = []
    for article in articles:
        url = article.get("url", "")
        # Also dedup by domain to avoid same source twice
        domain = re.sub(r"https?://(www\.)?", "", url).split("/")[0]
        if url and url not in seen_urls and domain not in seen_urls:
            seen_urls.add(url)
            seen_urls.add(domain)
            unique.append(article)
    return unique
