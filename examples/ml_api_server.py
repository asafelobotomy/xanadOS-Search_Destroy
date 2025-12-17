#!/usr/bin/env python3
"""
Example: ML Inference API Server

Demonstrates running the FastAPI ML inference server.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from app.api.ml_inference import app


if __name__ == "__main__":
    print(
        """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║        🚀 ML Inference API Server                                        ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝

Starting FastAPI server...

📍 Endpoints:
   • POST http://localhost:8000/api/ml/predict     - Scan file
   • GET  http://localhost:8000/api/ml/models      - List models
   • POST http://localhost:8000/api/ml/models/{v}/reload - Reload model
   • GET  http://localhost:8000/api/ml/health      - Health check

📖 Documentation:
   • Swagger UI: http://localhost:8000/api/ml/docs
   • ReDoc:      http://localhost:8000/api/ml/redoc
   • OpenAPI:    http://localhost:8000/api/ml/openapi.json

🔐 Authentication:
   • Set X-API-Key header (if enabled in config)
   • Default: Authentication disabled for development

⚡ Rate Limits:
   • /predict: 10 requests/minute
   • /models: 30 requests/minute
   • /health: 30 requests/minute

Starting server on http://0.0.0.0:8000...
    """
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False,  # Set True for development
    )
