FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy and install dependencies
COPY pyproject.toml ./
COPY src/ ./src/
RUN uv pip install --system -e .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data

ENV DISPLAY_WIDTH=1448
ENV DISPLAY_HEIGHT=944

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set browser provider configuration
# ENV BROWSER_PROVIDER=anchorbrowser
# ENV ANCHOR_API_KEY=sk-840bb918200bc4bb275842c31455cda6
ENV BROWSER_PROVIDER=browserbase
ENV BROWSERBASE_API_KEY=bb_live_vZnYDhwOUDCQ0LWA6-6NRxgPn0M
ENV BROWSERBASE_PROJECT_ID=1326e79b-8473-4ee4-9434-fc5ad15a25b8
ENV ANTHROPIC_API_KEY=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

# Disable telemetry to avoid API key requirement
ENV BUCKEYE_TELEMETRY_ENABLED=false

# Note: Other environment variables can be set at runtime if needed:
# - Provider-specific API keys: STEEL_API_KEY, BROWSERBASE_API_KEY, etc.
# - GCP_CREDENTIALS_JSON: For Google Sheets functionality (if needed)

# Expose port for MCP HTTP server
EXPOSE 8765

# Copy service account file (will be mounted at runtime if needed)

# Run remote browser with persistent context
CMD ["sh", "-c", "\
    # Start context server in background \
    python -m controller.context >&2 & \
    # Wait for context server to start \
    sleep 2 && \
    # Start MCP server \
    exec python -m controller.server \
"]
