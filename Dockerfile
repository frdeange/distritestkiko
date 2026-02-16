FROM python:3.12-slim

WORKDIR /app

# Install git (needed for agent-framework from GitHub) and .NET runtime (needed for PowerFx expressions)
RUN apt-get update && apt-get install -y git wget libicu-dev && \
    wget https://dot.net/v1/dotnet-install.sh -O dotnet-install.sh && \
    chmod +x dotnet-install.sh && \
    ./dotnet-install.sh --channel 9.0 --runtime dotnet && \
    rm dotnet-install.sh && \
    apt-get purge -y wget && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

ENV DOTNET_ROOT=/root/.dotnet
ENV PATH="${DOTNET_ROOT}:${PATH}"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ src/

# Default port for M365 Agents SDK
EXPOSE 3978

# Run the bot
CMD ["python", "-m", "src.backend.main"]
