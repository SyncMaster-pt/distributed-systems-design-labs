from flask import Flask, jsonify, request, abort
import argparse
import subprocess
import hazelcast
import threading
import consul_func
import json

parser = argparse.ArgumentParser(description='Hazelcast map logging service')

parser.add_argument('--port', type=int, choices=[8003, 8004, 8005], help='Logging service port', required=True)
argv = parser.parse_args()

logging_port = argv.port

try:
    subprocess.run(['docker-compose', '-f', f"./docker-compose-files/hz_4_logging_{logging_port}.yml", 'up', '-d'], check=True)
except subprocess.CalledProcessError as e:
    print(f"Start hazelcast failed with exit code {e.returncode}")
    exit(1)

logging_id = consul_func.register_service('logging-service', logging_port)

hazelcast_config_json = consul_func.get_key_value('hz_configurations')
if hazelcast_config_json:
    hazelcast_config = json.loads(hazelcast_config_json)
    print("Logging service config (Hazelcast):", hazelcast_config)
else:
    print("Hazelcast configuration not found in Consul.")
    exit(1)

client = hazelcast.HazelcastClient(
cluster_name=hazelcast_config['cluster_name'],
cluster_members=hazelcast_config['cluster_members']
)

map = client.get_map(hazelcast_config['map']).blocking()

app = Flask(__name__)

@app.route('/logging', methods=['GET', 'POST'])
def logging_requests():
    if request.method == 'GET':
        logging_data = []
        keys = map.key_set()
        for key in keys:
            logging_data.append(map.get(key))
        if logging_data:
            return jsonify(list(logging_data))
        else:
            return "There is no messages"

    elif request.method == 'POST':
        id = request.form['id']
        message = request.form['msg']
        map.put(id, message)
        print(f"Received message: {message}")
        return "Message was recevived by logging service", 201
    
    else:
        abort(400)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=app.run, kwargs={"port": logging_port})
    flask_thread.daemon = True
    flask_thread.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        client.shutdown()
        subprocess.run(['docker-compose', '-f', f'./docker-compose-files/hz_4_logging_{logging_port}.yml', 'stop'])
        consul_func.deregister_service(logging_id)