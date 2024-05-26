from flask import Flask, jsonify
from time import sleep
import argparse
import subprocess
import threading
import pika
import consul_func
import json

messages = []

parser = argparse.ArgumentParser(description='RabbitMQ message service')

parser.add_argument('--port', type=int, choices=[8006, 8007], help='Message service port', required=True)
argv = parser.parse_args()
messages_port = argv.port

try:
    subprocess.run(['docker-compose', '-f', './docker-compose-files/rabbitmq.yml', 'up', '-d'], check=True)
    print(f"Service will be started in a minute")
    sleep(60)
except subprocess.CalledProcessError as e:
    print(f"Start RabbitMQ failed with exit code {e.returncode}")
    exit(1)

message_service_config_json = consul_func.get_key_value('rabbitmq_configurations')
if message_service_config_json:
    message_service_config = json.loads(message_service_config_json)
    print("Message Service Config:", message_service_config)
else:
    print("Message service configuration not found in Consul.")
    exit(1)

message_id = consul_func.register_service('messages-service', messages_port)

def consume_messages():
    connection = pika.BlockingConnection(pika.ConnectionParameters(message_service_config['queue_address'], int(message_service_config['queue_port'])))
    channel = connection.channel()
    channel.queue_declare(queue=message_service_config['queue_name'])

    def callback(ch, method, properties, body):
        messages.append(body)        
        print("Received message:", body)

    channel.basic_consume(queue=message_service_config['queue_name'], on_message_callback=callback, auto_ack=True)
    print('Waiting for messages...')
    try:
        channel.start_consuming()
    except pika.exceptions.ConnectionClosedByBroker:
        print("RabbitMQ broker forced connection closure. Exiting consume_messages()...")

app = Flask(__name__)

@app.route('/messages', methods=['GET'])
def get_messages():
        if messages:
            decoded_messages = [msg.decode('utf-8') for msg in messages]
            return jsonify({f"Data from message service with port {messages_port}": decoded_messages})
        else:
            return "There is no messages"

if __name__ == '__main__':
    flask_thread = threading.Thread(target=app.run, kwargs={"port": messages_port})
    flask_thread.daemon = True
    flask_thread.start()

    consume_thread = threading.Thread(target=consume_messages)
    consume_thread.daemon = True
    consume_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        subprocess.run(['docker-compose', '-f', './docker-compose-files/rabbitmq.yml', 'stop'])
        consul_func.deregister_service(message_id)