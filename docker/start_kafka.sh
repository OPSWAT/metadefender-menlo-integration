# create docker container for kafka
echo "Clone kafka-docker"
git clone https://github.com/wurstmeister/kafka-docker.git 

echo "copy preconfigure docker-compose.yml\n"
cp docker-compose.yml  ./kafka-docker/docker-compose.yml 

cd kafka-docker

echo "Create and start containers\n"
docker-compose up -d

cd ..

echo "wait for containers to be ready\n"
sleep 5

echo "start kafka consumer\n"
python kafka_consumer.py