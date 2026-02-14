from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from auth import router as auth_router
from recordings import router as recordings_router
from library import router as library_router


# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title="Rec4U API",
    description="Backend API for Rec4U Screen Recorder App",
    version="1.0.0"
)

# -----------------------------
# CORS Configuration
# -----------------------------
origins = [
    "http://localhost:3000", # frontend dev server
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # use ["*"] only in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Include Routers
# -----------------------------
app.include_router(auth_router, prefix="/auth", tags=["Auth"])
app.include_router(recordings_router, prefix="/recordings", tags=["Recordings"])
app.include_router(library_router, prefix="/library", tags=["Library"])


# -----------------------------
# Root Endpoint
# -----------------------------
@app.get("/")
def root():
    return {"message": "Welcome to Rec4U API 🚀"}