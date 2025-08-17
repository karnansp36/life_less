# # main.py
# import os
# import json
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse
# from fastapi.middleware.cors import CORSMiddleware

# # Import providers
# from app.providers.gemini import generate_with_gemini
# from app.providers.mistral import generate_with_mistral
# from dotenv import load_dotenv
# load_dotenv()

# # Load config from env
# AI_PROVIDER = os.getenv("AI_PROVIDER", "mistral").lower()  # Normalize to lowercase

# app = FastAPI(title="AI Service", version="1.0")

# # Configure CORS
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @app.post("/chat/")
# async def chat(request: Request):
#     try:
#         # Parse and validate request
#         try:
#             body = await request.json()
#             prompt = body.get("prompt", "").strip()
#         except json.JSONDecodeError:
#             raise HTTPException(status_code=400, detail="Invalid JSON format")
        
#         if not prompt:
#             raise HTTPException(status_code=400, detail="Prompt cannot be empty")

#         # Process with selected provider
#         try:
#             if AI_PROVIDER == "gemini":
#                 reply = await generate_with_gemini(prompt)
#             elif AI_PROVIDER in ["mistral", "mistral:latest"]:
#                 reply = generate_with_mistral(prompt)
#             else:
#                 raise HTTPException(
#                     status_code=400, 
#                     detail=f"Unsupported AI provider: {AI_PROVIDER}. Supported: gemini, mistral"
#                 )

#             return {
#                 "reply": reply,
#                 "provider": AI_PROVIDER,
#                 "status": "success"
#             }
            
#         except Exception as provider_error:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"AI processing error: {str(provider_error)}"
#             )

#     except HTTPException:
#         raise  # Re-raise existing HTTP exceptions
#     except Exception as e:
#         raise HTTPException(
#             status_code=500,
#             detail=f"Unexpected server error: {str(e)}"
#         )

# @app.get("/")
# async def root():
#     return {
#         "message": f"AI service 🚀 running with {AI_PROVIDER} provider",
#         "status": "operational"
#     }

# @app.exception_handler(HTTPException)
# async def http_exception_handler(request: Request, exc: HTTPException):
#     return JSONResponse(
#         status_code=exc.status_code,
#         content={
#             "error": exc.detail or "Unknown error occurred",
#             "status": "error"
#         },
#     )


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.settings import settings
from app.routers.chat import router as chat_router
from app.startup import init_db

app = FastAPI(title="AI Service w/ CrewAI", version="0.2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)

@app.on_event("startup")
async def on_startup():
    await init_db(app)

@app.get("/")
async def root():
    return {"message": "CrewAI service running ✅", "provider": settings.AI_PROVIDER}
