import hazelcast
import time

client = hazelcast.HazelcastClient(
cluster_name="dev",
cluster_members=[
    "172.17.0.2:5701",
    "172.17.0.3:5701",
    "172.17.0.4:5701",
    ]
)

queue = client.get_queue("queue").blocking()

for i in range(1, 101):
    queue.put(i)
    print(f"Write {i}")
    time.sleep(0.1)

client.shutdown()