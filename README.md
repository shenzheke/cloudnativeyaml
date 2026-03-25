# Kubernetes 1.29.8 验证场景（3 Master + 3 Worker）

本仓库提供 5 个独立目录，对应你提出的验证目标。每个目录包含可直接执行的 YAML 与完整 Markdown 验证步骤。

## 目录
1. `01-scheduling/`：调度全过程（NodeResourcesFit / TaintsAndTolerations / NodeAffinity）
2. `02-autoscaling/`：自动扩缩容（HPA、VPA 建议、CA 联动）
3. `03-crashloopbackoff-troubleshooting/`：CrashLoopBackOff 系统排查
4. `04-pod-network-troubleshooting/`：Pod 通信故障（同节点/跨节点）
5. `05-ebpf-kubeproxy-replacement/`：eBPF 替代 kube-proxy 验证（Calico）

## 使用建议
- 按目录逐个执行，避免多个场景相互干扰。
- 每个场景都提供 `namespace.yaml`，可独立清理。
- 建议配合 `kubectl get events --sort-by=.lastTimestamp` 全程观察。

6. `06-kafka-seckill-decoupling/`：Kafka 微服务解耦 + 秒杀削峰填谷
