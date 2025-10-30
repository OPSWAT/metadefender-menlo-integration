FROM python:3.13-alpine

# Create app directory
RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

# Copy requirements first for layer caching
COPY ./requirements.txt /usr/src/app/

# Update Alpine packages, ensure pip is cleanly installed, and upgrade it
RUN apk add --no-cache libexpat && \
    python3 -m ensurepip && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    rm -rf /root/.cache/pip /var/cache/apk/*

# Copy application code
COPY . /usr/src/app

# Create log directory
RUN mkdir -p /var/log/metadefender-menlo

EXPOSE 3000

ENTRYPOINT ["python3"]
CMD ["-m", "metadefender_menlo"]
