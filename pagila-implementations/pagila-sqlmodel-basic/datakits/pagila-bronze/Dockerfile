FROM python:3.11-slim
RUN pip install --no-cache-dir uv
WORKDIR /opt/app
COPY . /opt/app
RUN uv pip install --system .
ENTRYPOINT ["datakit-bronze"]
