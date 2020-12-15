FROM orchestrator:latest

COPY Config .

ENV CONFIG_FILE="config.yaml"