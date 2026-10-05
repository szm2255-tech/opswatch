FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml ./
COPY opswatch ./opswatch
RUN pip install --no-cache-dir .
ENTRYPOINT ["opswatch"]
CMD ["--help"]
