# Kafka 云原生典型场景：微服务解耦 + 削峰填谷（秒杀）

本场景模拟“秒杀系统”：
- API 网关层只负责快速接单，写入 Kafka（立即返回 202）。
- Worker 消费 Kafka，按固定 QPS 处理订单，避免数据库/库存服务被瞬时洪峰打爆。
- Redis 用作库存扣减与订单结果落地，演示“先排队再处理”的削峰架构。

## 架构

1. `seckill-api`（2 副本）：接收下单请求，写入 `flash-sale-orders` Topic。
2. `Kafka`：作为缓冲队列，解耦入口流量与后端处理能力。
3. `seckill-worker`（2~8 副本，HPA）：按 `WORKER_QPS` 消费并扣减 Redis 库存。
4. `Redis`：保存库存（`stock:sku-iphone-15`）与订单处理状态（`order:<order_id>`）。

## 部署步骤

```bash
kubectl apply -f namespace.yaml
kubectl apply -f kafka.yaml
kubectl apply -f redis.yaml
kubectl apply -f apps.yaml
kubectl apply -f topic-job.yaml
```

检查：

```bash
kubectl -n kafka-scenario get pods
kubectl -n kafka-scenario logs deploy/seckill-worker -f
```

## 触发秒杀洪峰

```bash
kubectl apply -f loadtest-job.yaml
kubectl -n kafka-scenario logs job/seckill-burst-load
```

## 验证削峰填谷

1. API 接口会快速返回 202（已排队）。
2. Worker 日志会持续输出 SUCCESS/SOLD_OUT，处理速度受 `WORKER_QPS` 控制。
3. 可查看剩余库存：

```bash
kubectl -n kafka-scenario exec deploy/redis -- redis-cli GET stock:sku-iphone-15
```

## 微服务解耦价值

- **高并发入口稳定**：写 Kafka 的延迟远小于直接落库事务。
- **后端可弹性扩展**：通过 HPA 横向扩容 Worker，逐步吃掉积压。
- **故障隔离**：Worker 故障不会直接阻塞入口，下游恢复后可继续消费。

## 清理

```bash
kubectl delete ns kafka-scenario
```
