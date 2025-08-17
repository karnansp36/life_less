# # gemini.py
# import os
# import httpx
# import json
# from dotenv import load_dotenv
# load_dotenv()

# API_KEY = os.getenv("GEMINI_API_KEY")
# MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")  # Default model
# TIMEOUT = 30.0  # seconds

# async def generate_with_gemini(prompt: str) -> str:
#     """Generate content using Gemini API with robust error handling"""
#     # Validate inputs
#     if not API_KEY:
#         raise ValueError("GEMINI_API_KEY environment variable not set")
#     if not prompt or not isinstance(prompt, str):
#         raise ValueError("Prompt must be a non-empty string")

#     url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
#     headers = {"Content-Type": "application/json"}
#     body = {
#         "contents": [{
#             "parts": [{"text": prompt}]
#         }]
#     }

#     async with httpx.AsyncClient(timeout=TIMEOUT) as client:
#         try:
#             # Make the API request
#             resp = await client.post(url, headers=headers, json=body)
            
#             # Check for HTTP errors
#             resp.raise_for_status()
            
#             # Parse and validate response
#             try:
#                 data = resp.json()
#                 if not data.get("candidates"):
#                     raise ValueError("No candidates in response")
                
#                 candidate = data["candidates"][0]
#                 if not candidate.get("content", {}).get("parts"):
#                     raise ValueError("Missing content parts in response")
                
#                 return candidate["content"]["parts"][0]["text"]
                
#             except (KeyError, IndexError) as e:
#                 error_detail = {
#                     "error": "Unexpected response structure",
#                     "response": data,
#                     "expected_structure": {
#                         "candidates": [{
#                             "content": {
#                                 "parts": [{
#                                     "text": "response text"
#                                 }]
#                             }
#                         }]
#                     }
#                 }
#                 raise ValueError(json.dumps(error_detail)) from e
                
#         except httpx.HTTPStatusError as e:
#             # Extract detailed error message from response
#             try:
#                 error_data = e.response.json()
#                 error_msg = error_data.get("error", {}).get("message", str(e))
#             except json.JSONDecodeError:
#                 error_msg = str(e)
            
#             raise ValueError(f"Gemini API error: {error_msg}") from e
            
#         except httpx.RequestError as e:
#             raise ValueError(f"Network error: {str(e)}") from e
#         except Exception as e:
#             raise ValueError(f"Unexpected error: {str(e)}") from e


import os, json, httpx
from app.settings import settings

TIMEOUT = 30.0

async def generate_with_gemini_raw(prompt: str) -> str:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent?key={settings.GEMINI_API_KEY}"
    body = { "contents": [{ "parts": [{ "text": prompt }]}] }
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        resp = await client.post(url, headers={"Content-Type": "application/json"}, json=body)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            raise ValueError(f"Unexpected Gemini response: {json.dumps(data)[:800]}")
