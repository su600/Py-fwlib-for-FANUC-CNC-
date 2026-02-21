# Multi-stage build for FANUC CNC Data Collection
# Stage 1: Base image with dependencies
FROM python:3.9-slim-bullseye as builder

# Set working directory
WORKDIR /build

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir paho-mqtt

# Stage 2: Final runtime image
FROM python:3.9-slim-bullseye

# Set labels for metadata
LABEL maintainer="Su600"
LABEL description="FANUC CNC Data Collection via FOCAS Library"
LABEL version="1.2"

# Create non-root user for security
RUN groupadd -r fanuc && useradd -r -g fanuc fanuc

# Set working directory
WORKDIR /su600

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages

# Copy application files
COPY fanuc-su.py .
COPY fanuc-config.json .
COPY libfwlib32.so .
COPY RunPython.sh .

# Make script executable
RUN chmod +x RunPython.sh

# Change ownership to non-root user
RUN chown -R fanuc:fanuc /su600

# Switch to non-root user
USER fanuc

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD test -f /su600/fanuc-su.log || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["./RunPython.sh"]