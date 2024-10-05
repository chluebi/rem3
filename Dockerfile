FROM python:3.11-slim as builder

ENV POETRY_HOME="/opt/poetry"
ENV POETRY_VERSION="1.8.2"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt-get update && \
    apt-get install -y curl build-essential libpq-dev gcc && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY pyproject.toml poetry.lock /app/

RUN poetry config virtualenvs.create false

RUN poetry install --no-root

COPY src src

RUN pip wheel --no-cache-dir --wheel-dir wheels .



FROM python:3.11-slim AS runner

RUN apt-get update && \
    apt-get install -y libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

CMD ["bash"]
