# --------------------------------------------------
# Stage 1: Build Stage
# --------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Installing system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

COPY pyproject.toml .
COPY README.md .

COPY . /app

RUN python -m build

# --------------------------------------------------
# Stage 2: Final Runtime Stage
# --------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/dist/*.whl /tmp/

COPY requirements.txt /tmp/requirements.txt

# Installing package wheel + the runtime dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /tmp/*.whl \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /tmp/*.whl /tmp/requirements.txt

COPY ./doc/demo.py /app/demo.py

CMD ["tail", "-f", "/dev/null"]
