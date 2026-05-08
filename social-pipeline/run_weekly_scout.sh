#!/bin/bash
# Weekly Instagram Content Scout — runs every Sunday 9am ET
# Loads env vars from .env and runs the scout pipeline

cd "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline"

# Load environment variables
export $(grep -v '^#' "/Users/alicebazidian/Desktop/AI Project/AI Services Website/.env" | xargs)

# Run the scout
/usr/bin/python3 scout_instagram.py >> "/Users/alicebazidian/Desktop/AI Project/AI Services Website/social-pipeline/output/scout.log" 2>&1
