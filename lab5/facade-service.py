from flask import Flask, jsonify, request, abort
import requests, threading
import uuid
import pika
import argparse
import consul_func
import json

parser = argparse.ArgumentParser(description='Facade service')

parser.add_argument('--port', type=int, help='Facade service port', required=True)
argv = parser.parse_args()
facade_port = argv.port

facade_id = consul_func.register_service('facade-service', facade_port)

message_service_config_json = consul_func.get_key_value('rabbitmq_configurations')
if message_service_config_json:
    message_service_config = json.loads(message_service_config_json)
    print("Message Service Config:", message_service_config)
else:
    print("Message service configuration not found in Consul.")
    exit(1)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def facade_requests():
    logging_service = consul_func.get_service_address_port('logging-service')
    message_service = consul_func.get_service_address_port('messages-service')
    if not logging_service:
        return jsonify({"error": "Sorry, logging services are disabled"}), 500
    elif not message_service:
        return jsonify({"error": "Sorry, messages services are disabled"}), 500

    if request.method == 'GET':
        try:
            logging_response = requests.get(f"{logging_service}/logging")
            logging_response.raise_for_status()
            messages_response = requests.get(f"{message_service}/messages")
            messages_response.raise_for_status()
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        return jsonify({"logs": logging_response.text, "messages": messages_response.text}), 200
    
    elif request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                message = data.get('msg')
            else:
                message = request.form.get("msg")
            if not message:
                return jsonify({"error": "There is no message"}), 400
            id = str(uuid.uuid4())
            data = {"id": id, "msg": message}
            response = requests.post(f"{logging_service}/logging", data=data)
            response.raise_for_status()

            #Insert message to the RabbitMQ queue
            connection = pika.BlockingConnection(pika.ConnectionParameters(message_service_config['queue_address'], int(message_service_config['queue_port'])))
            channel = connection.channel()
            channel.queue_declare(queue=message_service_config['queue_name'])
            channel.basic_publish(exchange='', routing_key=message_service_config['queue_name'], body=message)
            connection.close()
            
            return jsonify(data), 200
        except requests.RequestException as e:
            return jsonify({"error": str(e)}), 500
        
    else:
        abort(400)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=app.run, kwargs={"port": facade_port})
    flask_thread.daemon = True
    flask_thread.start()

    try:
        while 1:
            pass
    except KeyboardInterrupt:
        consul_func.deregister_service(facade_id)
        
