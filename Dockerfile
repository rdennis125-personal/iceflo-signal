FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md requirements.txt ./
COPY src ./src
COPY config ./config
COPY templates ./templates

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir .

ENTRYPOINT ["python", "-m", "iceflo_signal"]
CMD ["--help"]
