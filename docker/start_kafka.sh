# create docker container for kafka

git clone https://github.com/wurstmeister/kafka-docker.git 

cd kafka-docker

echo "run containers container"
docker-compose up -d

echo 'acces docker_kafka container'
docker exec -i -t -u root $(docker ps | grep docker_kafka | cut -d' ' -f1) /bin/bash $KAFKA_HOME/bin/kafka-console-consumer.sh --from-beginning --bootstrap-server kafka:9092 --topic=test 

