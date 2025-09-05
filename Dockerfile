# xanadOS Search & Destroy - Modern Development Container
# Multi-stage build with 2025 best practices

# Build stage with modern package managers
FROM node:20-slim AS node-builder

# Install pnpm for faster package management
RUN npm install -g pnpm@latest

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json pnpm-lock.yaml* ./

# Install Node.js dependencies with pnpm
RUN if [ -f pnpm-lock.yaml ]; then pnpm install --frozen-lockfile; else npm ci; fi

# Python build stage
FROM python:3.11-slim AS python-builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster Python package management
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy Python dependency files
COPY requirements*.txt pyproject.toml uv.toml uv.lock* ./

# Install Python dependencies with uv
RUN uv sync --all-extras --no-dev

# Main application stage
FROM python:3.11-slim AS runtime

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    clamav \
    clamav-daemon \
    rkhunter \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 developer

# Set working directory
WORKDIR /app

# Copy Python environment from builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy Node.js dependencies from builder
COPY --from=node-builder /app/node_modules /app/node_modules

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app:$PYTHONPATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Update virus databases
RUN freshclam || true

# Change ownership to non-root user
RUN chown -R developer:developer /app

# Switch to non-root user
USER developer

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import app.main" || exit 1

# Default command
CMD ["python", "-m", "app.main"]

# Development stage with additional tools
FROM runtime AS development

# Switch back to root for installing dev tools
USER root

# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    less \
    htop \
    strace \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
RUN /app/.venv/bin/pip install \
    pytest \
    black \
    ruff \
    mypy \
    bandit \
    safety

# Install fnm for Node.js version management
RUN curl -fsSL https://fnm.vercel.app/install | bash

# Copy development configuration
COPY .envrc /app/.envrc
COPY Makefile.modern /app/Makefile

# Switch back to developer user
USER developer

# Set development environment variables
ENV NODE_ENV=development
ENV FLASK_ENV=development
ENV DEBUG=1

# Development command
CMD ["bash"]
