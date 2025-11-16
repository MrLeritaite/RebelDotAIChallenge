CLASSIFY_QUESTION_PROMPT = """
You are given a question from the user.

Your task is to classify the question into one of the following categories:
- IT
- non-IT

Respond with exactly one word: either IT or non-IT. Do not add any other text.

Examples of IT questions are:
- Is it possible to change my registered email address?
- How do I reset my password?
- How do I deactivate my account?

Examples of non-IT questions are:
- How is the weather today?
- What is the meaning of life?
- What is the capital of France?
"""

ANSWER_QUESTION_PROMPT = """
You are a helpful FAQ IT assistant. Answer concisely in 2–3 sentences max.
"""
