# create docker container for kafka

git clone https://github.com/wurstmeister/kafka-docker.git 

cp docker-compose.yml  ./kafka-docker/docker-compose.yml 

cd kafka-docker

docker-compose up -d

docker exec -i -t -u root $(docker ps | grep docker_kafka | cut -d' ' -f1) /bin/bash 

"$KAFKA_HOME/bin/kafka-console-consumer.sh --from-beginning --bootstrap-server kafka:9092 --topic=test 