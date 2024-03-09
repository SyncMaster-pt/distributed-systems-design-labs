import hazelcast

client = hazelcast.HazelcastClient(
cluster_name="dev",
cluster_members=[
    "172.17.0.2:5701",
    "172.17.0.3:5701",
    "172.17.0.4:5701",
    ]
)

queue = client.get_queue("queue").blocking()


consumed_count = 0
while consumed_count < 100: 
    head = queue.take()
    print(f"Consuming {head}")
    consumed_count += 1

client.shutdown()