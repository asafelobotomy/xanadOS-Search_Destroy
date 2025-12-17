#!/usr/bin/env python3
"""
FastAPI ML Inference API

Provides REST API endpoints for ML-based malware detection.
"""

import hashlib
import logging
import time
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import (
    FastAPI,
    File,
    HTTPException,
    Header,
    UploadFile,
    Depends,
    status,
    Request,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.ml_scanner_integration import MLThreatDetector, MLScanResult
from app.ml.model_registry import ModelRegistry
from app.utils.config import load_config

# Configure logging
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="xanadOS ML Malware Detection API",
    description="Machine learning-based malware detection service",
    version="1.0.0",
    docs_url="/api/ml/docs",
    redoc_url="/api/ml/redoc",
    openapi_url="/api/ml/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Configure rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Global ML detector instance
ml_detector: Optional[MLThreatDetector] = None
model_registry = ModelRegistry()


# ==================== Pydantic Models ====================


class HealthResponse(BaseModel):
    """Health check response."""

    model_config = {"protected_namespaces": ()}  # Allow model_ fields

    status: str = Field(..., description="Service status")
    ml_enabled: bool = Field(..., description="ML detection enabled")
    model_version: Optional[str] = Field(None, description="Loaded model version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")


class PredictionRequest(BaseModel):
    """Prediction request (for JSON API)."""

    file_hash: str = Field(..., description="SHA256 hash of file")
    file_size: int = Field(..., description="File size in bytes")


class PredictionResponse(BaseModel):
    """Prediction response."""

    model_config = {"protected_namespaces": ()}  # Allow model_ fields

    file_hash: str = Field(..., description="SHA256 hash of scanned file")
    is_malware: bool = Field(..., description="Malware detection result")
    confidence: float = Field(..., description="Prediction confidence (0.0-1.0)")
    threat_level: str = Field(..., description="Threat level (HIGH/MEDIUM/LOW/CLEAN)")
    model_version: str = Field(..., description="Model version used")
    scan_time_ms: float = Field(..., description="Scan time in milliseconds")
    engine: str = Field(default="ML-RandomForest", description="Detection engine")


class ModelInfo(BaseModel):
    """Model information."""

    name: str = Field(..., description="Model name")
    version: str = Field(..., description="Model version")
    stage: str = Field(..., description="Model stage (production/checkpoint)")
    architecture: str = Field(..., description="Model architecture")
    created_at: str = Field(..., description="Creation timestamp")
    test_accuracy: float = Field(..., description="Test set accuracy")
    test_precision: float = Field(..., description="Test set precision")
    test_recall: float = Field(..., description="Test set recall")


class ModelsListResponse(BaseModel):
    """List of available models."""

    models: list[ModelInfo] = Field(..., description="Available models")
    production_model: Optional[str] = Field(
        None, description="Current production model version"
    )


class ErrorResponse(BaseModel):
    """Error response."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Error details")


# ==================== Authentication ====================


async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """
    Verify API key from request header.

    In production, implement proper API key management.
    For now, check against config or accept any key for testing.
    """
    config = load_config()
    api_config = config.get("api", {})

    # If authentication disabled in config, allow all requests
    if not api_config.get("require_auth", False):
        return True

    # Check API key
    valid_keys = api_config.get("api_keys", [])
    if not valid_keys:
        # No keys configured, allow for development
        logger.warning("No API keys configured - allowing all requests")
        return True

    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
        )

    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid API key"
        )

    return True


# ==================== Startup/Shutdown ====================


@app.on_event("startup")
async def startup_event():
    """Initialize ML detector on startup."""
    global ml_detector

    logger.info("Starting ML inference API...")

    try:
        # Load production model
        ml_detector = MLThreatDetector()
        logger.info(
            f"ML detector initialized with model v{ml_detector.metadata.version}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize ML detector: {e}")
        ml_detector = None
        logger.warning("ML inference API running without ML detector")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down ML inference API...")


# ==================== API Endpoints ====================


@app.get("/api/ml/health", response_model=HealthResponse, tags=["Health"])
@limiter.limit("30/minute")
async def health_check(request: Request):
    """
    Health check endpoint.

    Returns service status and ML detector availability.
    """
    return HealthResponse(
        status="healthy" if ml_detector else "degraded",
        ml_enabled=ml_detector is not None,
        model_version=ml_detector.metadata.version if ml_detector else None,
        uptime_seconds=time.process_time(),
    )


@app.post(
    "/api/ml/predict",
    response_model=PredictionResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
    },
    tags=["Prediction"],
)
@limiter.limit("10/minute")
async def predict_file(
    request: Request,
    file: UploadFile = File(..., description="File to scan for malware"),
    authenticated: bool = Depends(verify_api_key),
):
    """
    Scan uploaded file for malware using ML model.

    **Rate Limit:** 10 requests per minute per IP

    **Authentication:** Requires X-API-Key header (if enabled in config)

    **Request:**
    - file: Binary file to scan (max 100MB)

    **Response:**
    - is_malware: True if malware detected
    - confidence: Prediction confidence (0.0-1.0)
    - threat_level: HIGH/MEDIUM/LOW/CLEAN
    - model_version: Model version used
    - scan_time_ms: Scan duration in milliseconds
    """
    if not ml_detector:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML detector not available",
        )

    try:
        # Read file content
        content = await file.read()

        # Validate file size (100MB max)
        max_size = 100 * 1024 * 1024
        if len(content) > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File too large (max {max_size} bytes)",
            )

        # Calculate file hash
        file_hash = hashlib.sha256(content).hexdigest()

        # Save to temporary file for scanning
        import tempfile

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f"_{file.filename}"
        ) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            # Scan file
            result: MLScanResult = ml_detector.scan_file(tmp_path)

            # Return prediction
            return PredictionResponse(
                file_hash=file_hash,
                is_malware=result.is_malware,
                confidence=result.confidence,
                threat_level=result.threat_level,
                model_version=result.model_version,
                scan_time_ms=result.detection_time * 1000,
                engine=result.engine,
            )
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}",
        )


@app.get("/api/ml/models", response_model=ModelsListResponse, tags=["Models"])
@limiter.limit("30/minute")
async def list_models(request: Request, authenticated: bool = Depends(verify_api_key)):
    """
    List all available ML models.

    Returns information about all registered models including
    production and checkpoint versions.
    """
    try:
        # Get all models
        all_models = model_registry.list_models(name="malware_detector_rf")

        # Find production model
        production_models = [m for m in all_models if m.stage == "production"]
        production_version = production_models[0].version if production_models else None

        # Convert to response format
        models_info = []
        for model_meta in all_models:
            models_info.append(
                ModelInfo(
                    name=model_meta.name,
                    version=model_meta.version,
                    stage=model_meta.stage,
                    architecture=model_meta.architecture,
                    created_at=model_meta.created_at,
                    test_accuracy=model_meta.metrics.get("test_accuracy", 0.0),
                    test_precision=model_meta.metrics.get("test_precision", 0.0),
                    test_recall=model_meta.metrics.get("test_recall", 0.0),
                )
            )

        return ModelsListResponse(
            models=models_info, production_model=production_version
        )

    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve models: {str(e)}",
        )


@app.post("/api/ml/models/{version}/reload", response_model=dict, tags=["Models"])
@limiter.limit("5/minute")
async def reload_model(
    version: str, request: Request, authenticated: bool = Depends(verify_api_key)
):
    """
    Reload ML detector with specified model version.

    Useful for switching between models or reloading after updates.
    """
    global ml_detector

    try:
        # Create new detector with specified version
        new_detector = MLThreatDetector(
            model_name="malware_detector_rf", model_version=version
        )

        # Replace global detector
        ml_detector = new_detector

        logger.info(f"Reloaded ML detector with model v{version}")

        return {
            "status": "success",
            "message": f"Model v{version} loaded successfully",
            "model_info": ml_detector.get_model_info(),
        }

    except Exception as e:
        logger.error(f"Failed to reload model v{version}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload model: {str(e)}",
        )


# ==================== Error Handlers ====================


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "detail": str(exc)},
    )


# ==================== Main Entry Point ====================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
