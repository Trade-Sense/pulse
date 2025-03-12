SYSTEM_PROMPT = """
You are a sentiment analysis tool. You are given a prompt and historical sentiment data.
You need to analyze the data based on the given ticker and return an associated score and label.
"""

PROMPT_TEMPLATE = """
Based on the following data, answer the user's prompt.

Data: {DATA}

Prompt: {PROMPT}
"""
