FROM python:3.11-slim
WORKDIR /workspace
RUN pip install --no-cache-dir pandas pytest
COPY events.json /workspace/events.json
COPY lineups.json /workspace/lineups.json
