# create docker container for kafka

git clone https://github.com/wurstmeister/kafka-docker.git 

cp docker-compose.yml  ./kafka-docker/docker-compose.yml 

cd kafka-docker

docker-compose up -d

cd ..

sleep 2

python kafka_consumer.py