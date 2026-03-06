from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from . import models
from .routers import auth, mindmaps, nodes
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from urllib.parse import urlparse

# Initialize limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="MindMap API",
    description="API for creating and managing mind maps",
    version="1.0.0"
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware - Load allowed origins from environment variable
CORS_ORIGINS = os.getenv(
    "CORS_ORIGINS", 
    "http://localhost:3000,http://127.0.0.1:3000,http://116.118.44.79:3000"
).split(",")

# Parse CORS origins to list of allowed origins
allowed_origins_list = CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)

# CSRF Protection Middleware (for API with JWT tokens in headers)
# Note: JWT tokens in Authorization headers are naturally CSRF-resistant
# This middleware provides additional Origin validation for POST/PUT/DELETE requests
@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    # Only validate Origin if the header is present
    # This allows requests without Origin header (curl, API tools, etc.)
    # while protecting against CSRF for browser-based requests
    
    if request.method in ["POST", "PUT", "DELETE"]:
        origin = request.headers.get("Origin")
        referer = request.headers.get("Referer")
        
        # Only validate Origin/Referer if they are present
        if origin or referer:
            # Extract base URL from Referer if Origin is missing
            if referer and not origin:
                parsed = urlparse(referer)
                origin = f"{parsed.scheme}://{parsed.netloc}"
            
            # Validate against allowed origins
            if origin and origin not in allowed_origins_list:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF protection: Origin not allowed"}
                )
    
    # Pass request to next middleware or route handler
    response = await call_next(request)
    return response

# Include routers (BEFORE static files to avoid route conflicts)
app.include_router(auth.router)
app.include_router(mindmaps.router)
app.include_router(nodes.router)

# Create database tables
Base.metadata.create_all(bind=engine)

# Mount static files for frontend if directory exists
# API routes have priority over static file routes
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    # Fix: Ensure correct absolute paths for mounting
    css_path = os.path.abspath(os.path.join(frontend_path, "css"))
    js_path = os.path.abspath(os.path.join(frontend_path, "js"))
    
    if os.path.exists(css_path):
        app.mount("/css", StaticFiles(directory=css_path), name="css")
    if os.path.exists(js_path):
        app.mount("/js", StaticFiles(directory=js_path), name="js")
    
    app.mount("/static", StaticFiles(directory=os.path.abspath(frontend_path)), name="static")
    
    @app.get("/")
    def read_root():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_path, "index.html"))
    
    @app.get("/login")
    def read_login():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_path, "login.html"))
    
    @app.get("/register")
    def read_register():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_path, "register.html"))
    
    @app.get("/workspace")
    def read_workspace():
        from fastapi.responses import FileResponse
        return FileResponse(os.path.join(frontend_path, "workspace.html"))
else:
    @app.get("/")
    def root():
        return {
            "message": "MindMap API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
