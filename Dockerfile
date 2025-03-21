FROM library/ubuntu:24.04 AS builder

COPY --from=ghcr.io/astral-sh/uv:0.6.0 /uv /uvx /bin/

RUN apt-get update && apt-get install -y ca-certificates

WORKDIR /pulse

RUN uv venv /pulse/.venv
ENV VIRTUAL_ENV=/pulse/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

COPY .python-version pyproject.toml uv.lock alembic.ini .env /pulse/
COPY pulse /pulse/pulse

RUN uv sync --frozen

EXPOSE 8080

CMD [".venv/bin/python", "-m", "pulse.app.main", "serve"]