#!/usr/bin/env bash
set -euo pipefail

# 按需替换为你的 worker 节点名
WORKER1=${WORKER1:-worker1}
WORKER2=${WORKER2:-worker2}
WORKER3=${WORKER3:-worker3}

kubectl label node "$WORKER1" dedicated=high-mem zone=test-a --overwrite
kubectl label node "$WORKER2" dedicated=general zone=test-b --overwrite
kubectl label node "$WORKER3" dedicated=general zone=test-a --overwrite

# 为 WORKER2 添加隔离污点
kubectl taint node "$WORKER2" workload=isolated:NoSchedule --overwrite

echo "labels/taints configured"
kubectl get nodes -L dedicated,zone
