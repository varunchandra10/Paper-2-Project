import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api_router import api_router
from app.core.limits_dashboard import generate_limits_html_dashboard

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:4173",   # Vite preview
        "http://127.0.0.1:5173",   # Loopback dev
        "http://localhost:8000",   # Local dashboard
        "http://127.0.0.1:8000",   # Loopback backend
        "app://.",                 # Electron production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", response_class=HTMLResponse)
@app.get("/limits-dashboard", response_class=HTMLResponse)
def root_dashboard(request: Request):
    """
    Renders the visual Rate Limits & Quotas Dashboard when accessed from a browser.
    Returns JSON status when accessed by API clients requesting application/json.
    """
    accept = request.headers.get("accept", "")
    if request.url.path == "/limits-dashboard" or "text/html" in accept:
        return HTMLResponse(content=generate_limits_html_dashboard(), status_code=200)
    
    # API / Automated Client fallback
    return JSONResponse({
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "limits_ui": "/limits-dashboard",
        "api_v1": settings.API_V1_STR
    })


@app.get("/api/status")
def api_status_json():
    """Returns machine-readable JSON status for automated health checks."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "has_gemini": settings.has_gemini(),
        # [LEGACY CEREBRAS - PRESERVED & COMMENTED OUT]
        # [LEGACY SAMBANOVA - PRESERVED & COMMENTED OUT]
        # "has_sambanova": settings.has_sambanova(),
        "has_huggingface": settings.has_huggingface(),
        "has_groq": settings.has_groq(),
        "has_openrouter": settings.has_openrouter()
    }


if __name__ == "__main__":
    import sys
    import uvicorn

    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[backend_dir],
        app_dir=backend_dir
    )
