"""Squola - School Scheduling Application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from squola.database import init_db
from squola.routers import teachers_router, classes_router, matters_router, scheduling_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler - initialize database on startup."""
    init_db()
    yield


app = FastAPI(
    title="Squola",
    description="School scheduling application to help teachers create arrangements efficiently",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(teachers_router, prefix="/api")
app.include_router(classes_router, prefix="/api")
app.include_router(matters_router, prefix="/api")
app.include_router(scheduling_router, prefix="/api")


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "Welcome to Squola - School Scheduling API"}


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


def main():
    """Entry point for running the application."""
    import uvicorn
    uvicorn.run("squola.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
