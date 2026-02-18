FROM python:3.12-slim

WORKDIR /app

# Install git (needed for agent-framework from GitHub)
RUN apt-get update && apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/

# Default port for M365 Agents SDK
EXPOSE 3978

# Run the bot
CMD ["python", "-m", "src.backend.main"]
