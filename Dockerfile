# Stage 1: Build project
FROM python:3.12-slim-bookworm AS build

# Installing build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Installing Poetry
RUN python3 -m pip install --no-cache-dir poetry

WORKDIR /app

# Copying project dependency files
COPY pyproject.toml poetry.lock README.md /app/

# Installing project dependencies
ENV PATH="/root/.local/bin:$PATH"
RUN poetry config virtualenvs.create true
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi

# Stage 2: Run project
FROM python:3.12-slim-bookworm AS project

# Installing runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb \
    xauth \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
    
COPY --from=build /app /app

# Installing Playwright
ENV PATH="/app/.venv/bin:$PATH"
RUN python3 -m pip install --no-cache-dir poetry playwright && \
    playwright install chrome --with-deps

WORKDIR /app

# Copying project files
COPY src /app/src

# Copying entypoint file
COPY start.sh /app/
RUN chmod +x /app/start.sh

ENTRYPOINT ["/app/start.sh"]