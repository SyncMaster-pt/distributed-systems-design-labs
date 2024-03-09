import hazelcast

client = hazelcast.HazelcastClient(
cluster_name="dev",
cluster_members=[
    "172.17.0.2:5701",
    "172.17.0.3:5701",
    "172.17.0.4:5701",
    ]
)

map = client.get_map("lab_map").blocking()

for i in range(1000):
    key = str(i)
    value = "Value_" + str(i)
    map.put(key, value)

client.shutdown()