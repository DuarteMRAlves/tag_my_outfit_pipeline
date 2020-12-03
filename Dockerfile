FROM orchestrator:latest

COPY Config .

ENV STAGES_INFO_FILE="stages.csv"
ENV LINKS_INFO_FILE="connections.csv"