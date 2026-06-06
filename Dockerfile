FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AGENT_TELEMETRY_HOST=0.0.0.0 \
    AGENT_TELEMETRY_PORT=8080 \
    AGENT_TELEMETRY_STORE_PATH=/var/lib/agent-telemetry/traces.sqlite

WORKDIR /app

RUN adduser --disabled-password --gecos "" agent-telemetry \
    && mkdir -p /var/lib/agent-telemetry \
    && chown -R agent-telemetry:agent-telemetry /var/lib/agent-telemetry

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

USER agent-telemetry
EXPOSE 8080

CMD ["python", "-m", "agent_telemetry_dashboard.collector_server"]
