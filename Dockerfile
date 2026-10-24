FROM python@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d AS launcher
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/*
COPY noaslr.c /tmp/noaslr.c
RUN cc -O2 -Wall -Wextra /tmp/noaslr.c -o /noaslr

FROM python@sha256:65a93d69fa75478d554f4ad27c85c1e69fa184956261b4301ebaf6dbb0a3543d

LABEL org.opencontainers.image.title="Python2Shell CVE-2026-111497 local lab"
LABEL org.opencontainers.image.description="Intentionally vulnerable static-offset Brotli 1.2.0 target"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=0 \
    MALLOC_ARENA_MAX=1 \
    MALLOC_MMAP_THRESHOLD_=268435456 \
    MALLOC_MMAP_MAX_=0 \
    MALLOC_TRIM_THRESHOLD_=-1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app
COPY requirements-vulnerable.txt ./
RUN python -m pip install --no-cache-dir --only-binary=:all: --require-hashes \
    -r requirements-vulnerable.txt
COPY --from=launcher /noaslr /usr/local/bin/noaslr
COPY server.py realistic_server.py ./

USER 65534:65534
EXPOSE 8080
CMD ["/usr/local/bin/noaslr", "python", "/app/server.py"]
