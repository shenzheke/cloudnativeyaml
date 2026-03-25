import json
import os
import time
from kafka import KafkaConsumer
import redis

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka.kafka-scenario.svc.cluster.local:9092")
TOPIC = os.getenv("KAFKA_TOPIC", "flash-sale-orders")
GROUP = os.getenv("CONSUMER_GROUP", "seckill-worker")
WORKER_QPS = float(os.getenv("WORKER_QPS", "20"))
REDIS_HOST = os.getenv("REDIS_HOST", "redis.kafka-scenario.svc.cluster.local")
STOCK_KEY = os.getenv("STOCK_KEY", "stock:sku-iphone-15")
INIT_STOCK = int(os.getenv("INIT_STOCK", "200"))

r = redis.Redis(host=REDIS_HOST, port=6379, decode_responses=True)
if not r.exists(STOCK_KEY):
    r.set(STOCK_KEY, INIT_STOCK)

LUA_DEDUCT = """
local stock = tonumber(redis.call('GET', KEYS[1]) or '0')
local qty = tonumber(ARGV[1])
if stock >= qty then
  return redis.call('DECRBY', KEYS[1], qty)
else
  return -1
end
"""

consumer = KafkaConsumer(
    TOPIC,
    bootstrap_servers=BOOTSTRAP,
    value_deserializer=lambda x: json.loads(x.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id=GROUP,
)

print(f"[worker] started, topic={TOPIC}, qps={WORKER_QPS}")
last = time.time()

for message in consumer:
    now = time.time()
    interval = 1.0 / WORKER_QPS
    if now - last < interval:
        time.sleep(interval - (now - last))
    last = time.time()

    order = message.value
    qty = int(order.get("quantity", 1))
    left = r.eval(LUA_DEDUCT, 1, STOCK_KEY, qty)

    if int(left) >= 0:
        status = "SUCCESS"
        result = f"order={order['order_id']} user={order['user_id']} left_stock={left}"
    else:
        status = "SOLD_OUT"
        result = f"order={order['order_id']} user={order['user_id']} sold out"

    r.hset(f"order:{order['order_id']}", mapping={"status": status, "payload": json.dumps(order)})
    print(f"[worker] {result}")
