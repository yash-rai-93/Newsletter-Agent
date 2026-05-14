"""
Prompts
-------
All LLM prompts used by the Newsletter Agent.
Centralized here for easy tuning and versioning.
"""

SYSTEM_PROMPT = """You are an expert newsletter writer and research analyst. 
You are part of an autonomous AI agent pipeline. Be precise, professional, 
and focused. Always respond in valid JSON when asked to."""


PLAN_PROMPT = """You are the planning stage of an autonomous newsletter agent.

USER GOAL: {goal}

Your job is to create a detailed research and writing plan. Analyze the goal and produce:

1. A clear topic statement (1-2 sentences)
2. The target audience for this newsletter
3. A structured plan (3-5 bullet points)
4. Exactly 5 targeted search queries to find the most relevant, recent news

Respond ONLY with valid JSON in this exact format:
{{
  "topic": "Clear topic statement",
  "audience": "Target audience description",
  "plan": "Multi-line plan with bullet points",
  "search_queries": [
    "query 1",
    "query 2",
    "query 3",
    "query 4",
    "query 5"
  ]
}}

Make the search queries specific and include the current year (2025) where appropriate.
Focus on finding recent news, not general explainers."""


SUMMARIZE_PROMPT = """You are a research analyst summarizing an article for a newsletter.

ARTICLE TITLE: {title}
ARTICLE URL: {url}
ARTICLE CONTENT:
{content}

Summarize this article for a newsletter audience. Be concise and professional.

Respond ONLY with valid JSON:
{{
  "summary": "2-3 sentence summary of the article",
  "key_points": ["point 1", "point 2", "point 3"]
}}

Focus on the most important insights. Keep the summary to 60-80 words."""


WRITE_PROMPT = """You are an expert newsletter writer.

NEWSLETTER TOPIC: {topic}
TARGET AUDIENCE: {audience}
RESEARCH PLAN: {plan}

RESEARCHED ARTICLES (use all of them):
{articles_text}

Write a complete, engaging weekly newsletter. Structure it as follows:

1. **Subject Line**: Attention-grabbing email subject (max 60 chars)
2. **Preview Text**: One sentence preview (max 100 chars)
3. **Header**: Newsletter name and date (Week of {date})
4. **Introduction**: 2-3 sentences hooking the reader (mention it's a curated digest)
5. **Top Stories**: Cover ALL {num_articles} articles with:
   - Bold title as heading
   - Source and link  
   - 2-3 sentence summary + why it matters
   - Key takeaway bullet
6. **Quick Takes**: 2-3 brief observations on the week's trends
7. **Closing**: Brief sign-off and what to expect next week

Format in clean Markdown. Be professional but conversational. Aim for 600-800 words.

Respond ONLY with valid JSON:
{{
  "subject_line": "Your subject line",
  "preview_text": "Your preview text",
  "newsletter": "Full newsletter in Markdown"
}}"""


CRITIQUE_PROMPT = """You are a senior newsletter editor performing a quality review.

NEWSLETTER DRAFT:
{newsletter}

Evaluate this newsletter on these criteria (score each 1-10):
1. **Relevance**: Are the articles genuinely relevant and recent?
2. **Readability**: Is it easy to read and well-structured?
3. **Value**: Does it provide clear value to the reader?
4. **Completeness**: Does it cover the topic thoroughly?
5. **Professionalism**: Is the tone and quality professional?

Calculate an overall score (average, round to nearest integer).

Then write a specific, actionable critique identifying the top 2-3 improvements needed.

Respond ONLY with valid JSON:
{{
  "scores": {{
    "relevance": 8,
    "readability": 7,
    "value": 8,
    "completeness": 6,
    "professionalism": 9
  }},
  "overall_score": 8,
  "critique": "Specific critique here",
  "improvement_needed": true,
  "top_improvements": ["improvement 1", "improvement 2"]
}}

Set improvement_needed to true only if overall_score < 7."""


IMPROVE_PROMPT = """You are rewriting a newsletter based on editorial feedback.

ORIGINAL NEWSLETTER:
{newsletter}

EDITORIAL CRITIQUE:
{critique}

TOP IMPROVEMENTS NEEDED:
{improvements}

Rewrite the newsletter addressing ALL the critique points. Keep the same structure 
but improve the quality significantly. This is iteration {iteration} of improvement.

Respond ONLY with valid JSON:
{{
  "subject_line": "Potentially improved subject line",
  "preview_text": "Potentially improved preview text",
  "newsletter": "Improved newsletter in Markdown"
}}"""
