"""RealtyAI — System prompts for the AI assistant.

Token-saver: SYSTEM_PROMPT is the compact (caveman-lite) version used by
default to cut per-call input tokens. SYSTEM_PROMPT_FULL is the verbose
original (restored when TOKEN_SAVER=0). See token_saver.py.
"""
from token_saver import system_prompt, VERBOSE_SYSTEM_PROMPT

SYSTEM_PROMPT = system_prompt()
SYSTEM_PROMPT_FULL = VERBOSE_SYSTEM_PROMPT


FOLLOW_UP_EMAIL_PROMPT = """You are drafting a follow-up email for a real estate agent to send to a lead.

Generate a professional, warm email that:
- References the property the lead viewed
- Asks if they have any questions
- Offers to schedule another showing or provide more information
- Includes a clear call to action

Keep it to 3-4 short paragraphs."""
