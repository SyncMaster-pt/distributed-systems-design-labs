import consul
import uuid
import json

from random import choice

client = consul.Consul(host="172.17.0.2", port=8500)

service_address = 'localhost'

def register_service(service_name, service_port):
    service_id=str(uuid.uuid4())
    client.agent.service.register(
        service_name,
        service_id,
        address=service_address,
        port=service_port,
    )
    return service_id

def deregister_service(service_id):
    client.agent.service.deregister(service_id)

def get_service_address_port(service_name):
    services = client.agent.services()
    services_tmp = []
    for service_id, service_info in services.items():
        if service_info['Service'] == service_name:
            services_tmp.append(f"http://{service_info['Address']}:{service_info['Port']}")
    if services_tmp:
        return choice(services_tmp)
    
    return None 

def store_key_value(key, value):
    client.kv.put(key, value)

def get_key_value(key):
    _, data = client.kv.get(key)
    if data is not None:
        return data['Value'].decode('utf-8')
    else:
        return None

'''hz_configurations = {
        "map": "messages_map",
        "cluster_name": "dev",
        "cluster_members": [
            "172.17.0.3:5701",
            "172.17.0.4:5701",
            "172.17.0.5:5701"
        ]
    }

rabbitmq_configurations = {
        "queue_address": "localhost",
        "queue_name": "lab4_messages",
        "queue_port": "5672"
    }

rabbitmq_configurations_json = json.dumps(rabbitmq_configurations)
hz_configurations_json = json.dumps(hz_configurations)

store_key_value('rabbitmq_configurations', rabbitmq_configurations_json)

store_key_value('hz_configurations', hz_configurations_json)'''

