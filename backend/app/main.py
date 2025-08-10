"""
Main FastAPI application entry point.
Configures the application with all necessary middleware, routers, and lifecycle events.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import uvicorn

from .core.config import settings
from .core.logging import configure_logging, get_logger
from .core.dependencies import get_service_container
from .core.exceptions import VoiceAgentException
from .api.endpoints import router as api_router
from .api.websocket import router as websocket_router

# Configure logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan management."""
    # Startup
    logger.info("Starting Voice-enabled GPT Agent application")
    
    try:
        # Initialize services
        container = get_service_container()
        await container.initialize()
        logger.info("Service container initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error("Failed to initialize application", error=str(e))
        raise
    
    finally:
        # Shutdown
        logger.info("Shutting down Voice-enabled GPT Agent application")
        try:
            container = get_service_container()
            await container.cleanup()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Voice-enabled GPT Agent with FastAPI - Complete voice interaction system with speech-to-text, chat, and text-to-speech capabilities",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Global exception handler for custom exceptions
@app.exception_handler(VoiceAgentException)
async def voice_agent_exception_handler(request, exc: VoiceAgentException):
    """Handle custom voice agent exceptions."""
    logger.error(
        "Voice agent exception",
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "error_code": exc.error_code,
            "details": exc.details
        }
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error("Unexpected exception", error=str(exc), path=request.url.path)
    
    if settings.debug:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "details": str(exc)
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"}
        )


# Include routers
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["voice-agent"]
)

app.include_router(
    websocket_router,
    prefix="/api/v1",
    tags=["websocket"]
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/health",
            "websocket": "/api/v1/ws/{connection_id}"
        }
    }


# Simple health check endpoint (separate from detailed service health check)
@app.get("/health")
async def simple_health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}


# Serve static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")


def create_app() -> FastAPI:
    """Factory function to create the FastAPI application."""
    return app


def main():
    """Entry point for running the application directly."""
    uvicorn.run(
        "app.main:app",
        host=settings.api_settings.host,
        port=settings.api_settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
