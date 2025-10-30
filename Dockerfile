FROM alpine:3.20

RUN apk add --no-cache python3 py3-pip && \
    python3 -m ensurepip && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    rm -rf /root/.cache/pip

WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 3000
ENTRYPOINT ["python3"]
CMD ["-m", "metadefender_menlo"]
