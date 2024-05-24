FROM python:3.8-alpine

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY ./requirements.txt /usr/src/app/

RUN pip3 install --no-cache-dir -r requirements.txt

RUN apk add --upgrade libexpat

COPY . /usr/src/app
RUN mkdir /var/log/metadefender-menlo

EXPOSE 3000

ENTRYPOINT ["python3"]

CMD ["-m", "metadefender_menlo"]
