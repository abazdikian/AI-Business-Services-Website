"""
Render all social content batch carousels and upload to Google Drive.
Usage: python render_batch.py
"""
import os
import sys
import json

sys.path.insert(0, os.path.dirname(__file__))
from render_graphics import render_carousel
from config import OUTPUT_DIR

BATCH_DATE = "2026-04-11"

POSTS = [
    {
        "slug": "post-1-claude-for-content",
        "headline": "You're Using Claude Wrong. Here's What It Can Actually Do for Your Content.",
        "summary": "Most people treat Claude like a chatbot. Here's how to turn it into a content machine.",
        "category": "how-to",
        "carousel_points": [
            {"number": "01", "title": "The Problem", "body": "Most people treat Claude like a chatbot. Ask a question. Get an answer. Copy-paste it somewhere.\n\nThat's like buying a Ferrari and only driving it in your driveway. You're using maybe 10% of what Claude can actually do."},
            {"number": "02", "title": "What Claude Actually Does", "body": "When you set it up properly, Claude can:\n\n\u2192 Turn one idea into a full carousel with hooks, flow, and CTA\n\u2192 Draft 5 versions of the same post for different platforms\n\u2192 Write in YOUR voice \u2014 not that generic AI tone\n\u2192 Plan a full week of content in 20 minutes"},
            {"number": "03", "title": "The Setup That Changes Everything", "body": "Teach Claude three things:\n\n1. Your brand voice and tone\n2. Your audience and what they care about\n3. Your quality standards\n\nDo it once. Claude remembers it across every conversation. You never repeat yourself again."},
            {"number": "04", "title": "The Result", "body": "A content machine that sounds like you on your best day. Not a robot. Not generic. Not that unmistakable 'ChatGPT tone.'\n\nYOU \u2014 but faster, more consistent, and without the Sunday night content scramble."},
        ],
    },
    {
        "slug": "post-2-claude-cowork",
        "headline": "The Claude Tool Nobody's Talking About",
        "summary": "Chat is too basic. Code is too technical. Cowork is built for entrepreneurs.",
        "category": "ai-news",
        "carousel_points": [
            {"number": "01", "title": "The Gap", "body": "Chat is great for quick questions. Code is powerful but requires a terminal and tech skills.\n\nMost entrepreneurs are stuck in between \u2014 wanting more than a chatbot but not ready to learn to code. There's a tool for that."},
            {"number": "02", "title": "Meet Claude Cowork", "body": "Same powerful brain as Claude Code. No terminal required. No coding background needed.\n\nIf you can describe what you want in plain English, you can build it. Skills, plugins, and automations \u2014 all created through conversation."},
            {"number": "03", "title": "Your $100/Month Business Analyst", "body": "Claude Cowork runs multiple tasks in parallel while you focus on strategy. It handles:\n\n\u2192 Client communications in your voice\n\u2192 Weekly reports and data analysis\n\u2192 Content drafts and social posts\n\u2192 Proposal writing and follow-ups"},
            {"number": "04", "title": "Why This Matters for You", "body": "A virtual assistant costs $2,000\u2013$4,000/month. Claude Cowork costs $100.\n\nIt doesn't call in sick. It doesn't need training every Monday. And it remembers your preferences, your voice, and your standards \u2014 permanently."},
        ],
    },
    {
        "slug": "post-3-claude-strategist",
        "headline": "Claude Isn't a Chatbot. It's a Business Strategist.",
        "summary": "Stop asking Claude to write. Start asking it to think.",
        "category": "thought-leadership",
        "carousel_points": [
            {"number": "01", "title": "What Most People Do", "body": "\"Write me a marketing plan.\"\n\"Give me 10 social media ideas.\"\n\"Draft an email.\"\n\nThe output? Generic. Forgettable. Sounds like everyone else's AI. Because you're using it like a search engine, not a strategist."},
            {"number": "02", "title": "Ask It to Think, Not Write", "body": "Give Claude your real numbers. Your actual constraints. Your specific goals.\n\nThen ask it to pressure-test your strategy before you spend a dollar. Challenge your assumptions. Find the gaps in your plan. That's where the real value is."},
            {"number": "03", "title": "Configure It Once", "body": "Your business model. Your audience. Your voice. Your standards.\n\nClaude remembers everything across conversations. Every session builds on the last. It gets smarter about YOUR business the more you use it."},
            {"number": "04", "title": "Use It for Decisions", "body": "\"Should I launch this offer at $297 or $497?\" with your actual revenue data is worth more than 100 generic prompts.\n\nThe gap between 'I use AI' and 'AI drives my business decisions' isn't technical skill. It's how you set up the relationship."},
        ],
    },
    {
        "slug": "post-4-run-business-on-ai",
        "headline": "Stop Using AI. Start Running Your Business On It.",
        "summary": "The gap between casual AI use and real infrastructure.",
        "category": "how-to",
        "carousel_points": [
            {"number": "01", "title": "What Most People Do", "body": "Ask AI a question. Copy the answer. Paste it into a doc. Repeat tomorrow.\n\nThat's not a system. That's a conversation with a robot. And it's why most entrepreneurs say 'AI didn't really save me time.'"},
            {"number": "02", "title": "What Infrastructure Looks Like", "body": "Monday morning. You open your laptop.\n\nYour emails are already sorted by priority. Your meetings are summarized with context. Five pieces of content are drafted from today's headlines.\n\nYou haven't done anything yet."},
            {"number": "03", "title": "How Claude Skills Work", "body": "A skill is an automated workflow that Claude runs on repeat \u2014 without you lifting a finger.\n\nYou configure it once: what to do, how to do it, what your standards are. Then it runs every day, every week, or on demand."},
            {"number": "04", "title": "Real Examples Running Right Now", "body": "\u2192 One skill drafts client replies in my voice\n\u2192 Another turns one newsletter into 12+ social posts\n\u2192 Another plans content calendars from a single topic\n\nYou set up the workflows once. Claude runs them on repeat."},
        ],
    },
    {
        "slug": "post-5-ai-sounds-generic",
        "headline": "Your AI Sounds Like Everyone Else's. Here's How to Fix It.",
        "summary": "Out of the box, AI is generic. Here's how to make it yours.",
        "category": "how-to",
        "carousel_points": [
            {"number": "01", "title": "The Problem", "body": "Out of the box, ChatGPT and Claude are trained to be pleasant, neutral, and slightly generic.\n\nFine for a Google search. Not fine when you're writing proposals, client emails, or content that needs to sound like YOU."},
            {"number": "02", "title": "Teach AI Your Voice", "body": "Your tone. Your preferences. The way you phrase things. The standards you hold yourself to.\n\nSet it once in Claude \u2014 it remembers forever. Every output stops sounding like a stranger wrote it and starts sounding like you on a good day."},
            {"number": "03", "title": "Kill the Copy-Paste Tax", "body": "Most people's AI workflow:\n\nCopy from Google Docs \u2192 Paste into Claude \u2192 Copy the answer \u2192 Paste back into Docs\n\nYOU are the bottleneck. And it's where most of the time savings leak away."},
            {"number": "04", "title": "Connect AI to Your Tools", "body": "When Claude has direct access to Google Drive, your CRM, and your inbox \u2014 the copy-paste tax disappears.\n\nThat's the difference between 'I use AI sometimes' and 'AI fits how I work.' It takes 30 minutes to set up."},
        ],
    },
    {
        "slug": "post-6-newsletter-blog",
        "headline": "Your AI Sounds Like Everyone Else's. Here's the Fix.",
        "summary": "Teach Claude your voice and connect it to your tools.",
        "category": "thought-leadership",
        "carousel_points": [
            {"number": "01", "title": "The Generic Problem", "body": "Every AI is trained to sound pleasant, neutral, and slightly American.\n\nThat's perfectly fine for a random query. But it's not fine when you're trying to get real work done \u2014 in your voice, with your standards, on your material."},
            {"number": "02", "title": "Personal AI", "body": "Teaching Claude what 'good' looks like \u2014 for you specifically.\n\nYour tone. Your preferences. Your standards. This is subjective, and that's the point. No technical skill needed. Set it once and Claude remembers across every conversation."},
            {"number": "03", "title": "Kill the Copy-Paste Tax", "body": "Most entrepreneurs have a copy-paste bottleneck somewhere in their AI workflow.\n\nYou grab text from one tool, paste it into Claude, copy the answer back out, paste it somewhere else. You are the middleman. And it's where the time savings leak away."},
            {"number": "04", "title": "AI Fits How I Work", "body": "These two shifts \u2014 personalizing your AI and connecting it to your tools \u2014 are the jump from casual use to real productivity.\n\nIt's not technical. It's personal. And it takes 30 minutes to set up with someone who knows how."},
        ],
    },
]


def main():
    batch_dir = os.path.join(OUTPUT_DIR, f"batch-{BATCH_DATE}")
    os.makedirs(batch_dir, exist_ok=True)

    for post in POSTS:
        slug = post["slug"]
        post_dir = os.path.join(batch_dir, slug)
        os.makedirs(post_dir, exist_ok=True)

        print(f"\n{'='*60}")
        print(f"Rendering: {post['headline']}")
        print(f"Output: {post_dir}")
        print(f"{'='*60}")

        pdf_path = render_carousel(post, post_dir)
        if pdf_path:
            print(f"  ✓ Carousel PDF: {pdf_path}")
        else:
            print(f"  ✗ No carousel generated")

    print(f"\n\nAll done! Files in: {batch_dir}")
    print(f"Total posts rendered: {len(POSTS)}")


if __name__ == "__main__":
    main()
