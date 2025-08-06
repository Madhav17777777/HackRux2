from app.llm_query import gemini_query
import json
import re

def clean_json_string(text):
    """Clean response in case LLM wraps JSON in markdown or text."""
    text = re.sub(r"```json|```", "", text).strip()
    return text

def evaluate_decision(query, clauses):
    prompt = f"""
You are an intelligent decision evaluator.

Your task is to read the following query and clauses, and return a JSON result ONLY.

Query:
"{query}"

Relevant Clauses:
{clauses}

Your JSON response MUST follow this exact format:
{{
  "decision": "approved" or "rejected",
  "amount": <number>,
  "justification": "short reason"
}}

Do not include anything outside the JSON object.
Return ONLY a parsable JSON object — no Markdown, no backticks, no explanation.
"""

    res = gemini_query(prompt)
    print("🔍 Gemini raw response:", res)  # <-- debug print

    try:
        cleaned = clean_json_string(res)
        return json.loads(cleaned)
    except Exception as e:
        print("❌ JSON parse failed:", e)
        return {
            "decision": "rejected",
            "amount": 0,
            "justification": "Unable to parse decision."
        }
