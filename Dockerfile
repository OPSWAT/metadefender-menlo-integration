FROM python:3.13-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --upgrade pip==26.1.2 && \
    pip3 install --no-cache-dir -r requirements.txt && \
    apk add --upgrade \
        --repository=https://dl-cdn.alpinelinux.org/alpine/edge/main \
        musl musl-utils libexpat && \
    rm -rf /var/cache/apk/*

COPY . /usr/src/app
RUN mkdir /var/log/metadefender-menlo

EXPOSE 3000

ENTRYPOINT ["python3"]

CMD ["-m", "metadefender_menlo"]
