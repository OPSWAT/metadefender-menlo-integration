import codecs  
from kafka import KafkaConsumer

server ='localhost:9092'
consumer = KafkaConsumer('test', bootstrap_servers=server)

print("Start consumer:{0}".format(server))

for msg in consumer:
    try:
        print (msg.value.decode('utf-8', 'ignore'))
        print('\n')
    except Exception as e:
        print(e)
