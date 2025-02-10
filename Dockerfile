# --------------------------------------------------
# Stage 1: Builder
# --------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /builder

# Installing system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip setuptools wheel build

# --------------------------------------------------
# BUILD your Python project
# --------------------------------------------------

WORKDIR /builder/fandango-learn

COPY . /builder/fandango-learn

RUN python -m build --wheel --outdir /builder/dist

# --------------------------------------------------
# Stage 2: Final Runtime
# --------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# (Optional) Install minimal system libs at runtime (e.g. libgomp1 for LightGBM, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /builder/dist /tmp/dist

COPY requirements.txt /tmp/requirements.txt

# Installing package wheel + the runtime dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /tmp/dist/*.whl \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -rf /tmp/*.whl /tmp/requirements.txt

COPY ./doc/demo.py /app/demo.py

CMD ["tail", "-f", "/dev/null"]
