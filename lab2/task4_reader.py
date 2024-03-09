import hazelcast

client = hazelcast.HazelcastClient(
cluster_name="dev",
cluster_members=[
    "172.17.0.2:5701",
    "172.17.0.3:5701",
    "172.17.0.4:5701",
    ]
)

topic = client.get_topic("lab_topic")

def message_listener(message):
    print("Received message:", message.message)

listener = topic.add_listener(message_listener)
input("Press Enter to exit...\n")
topic.remove_listener(listener)

client.shutdown()