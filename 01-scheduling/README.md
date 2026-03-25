# 场景1：Kubernetes 调度全过程验证（v1.29.8）

> 目标：系统验证 Scheduler 在常见约束下的行为，覆盖 `NodeResourcesFit`、`TaintsAndTolerations`、`NodeAffinity`，并通过事件和 Pod 分布结果反推调度链路。

## 目录文件
- `namespace.yaml`：测试命名空间。
- `node-labels-and-taints.sh`：节点标签/污点准备脚本。
- `01-node-resourcesfit.yaml`：资源匹配验证。
- `02-taints-tolerations.yaml`：污点容忍验证。
- `03-node-affinity.yaml`：节点亲和验证。
- `04-combined-scheduling.yaml`：组合约束验证。

---

## 0. 环境准备

```bash
kubectl apply -f namespace.yaml
bash node-labels-and-taints.sh
kubectl get nodes --show-labels | sed 's/,/\n  /g'
kubectl describe node <任意节点> | rg -n "Taints|Labels"
```

> 建议约定：
> - `master` 节点默认有 `NoSchedule` 控制面污点，不作为工作负载目标。
> - 3 个 worker 分别打标：`dedicated=high-mem`、`dedicated=general`、`zone=test-a|test-b`。

---

## 1. NodeResourcesFit 验证

```bash
kubectl apply -f 01-node-resourcesfit.yaml
kubectl -n sched-lab get pod -o wide
kubectl -n sched-lab describe pod resourcefit-ok
kubectl -n sched-lab describe pod resourcefit-too-large | sed -n '/Events/,$p'
```

### 预期
- `resourcefit-ok` 进入 `Running`。
- `resourcefit-too-large` 长时间 `Pending`，事件包含：
  - `0/6 nodes are available`
  - `Insufficient cpu` 或 `Insufficient memory`
- 这表明 `Filter` 阶段触发了 `NodeResourcesFit`。

---

## 2. TaintsAndTolerations 验证

```bash
kubectl apply -f 02-taints-tolerations.yaml
kubectl -n sched-lab get pod -o wide
kubectl -n sched-lab describe pod no-toleration | sed -n '/Events/,$p'
kubectl -n sched-lab describe pod with-toleration | sed -n '/Node:/p;/Events/,$p'
```

### 预期
- `no-toleration`：`Pending`，事件出现 `had taint {workload=isolated: NoSchedule}`。
- `with-toleration`：`Running`，且调度到被污点隔离的目标 worker。

---

## 3. NodeAffinity 验证

```bash
kubectl apply -f 03-node-affinity.yaml
kubectl -n sched-lab get pod -o wide
kubectl -n sched-lab describe pod affinity-required | sed -n '/Node-Selectors/,+8p;/Events/,$p'
kubectl -n sched-lab describe pod affinity-preferred | sed -n '/Node-Selectors/,+8p;/Events/,$p'
```

### 预期
- `affinity-required`：仅能落在 `zone=test-a` 节点。
- `affinity-preferred`：优先落在 `dedicated=general`，资源紧张时可退让到其他可行节点。

---

## 4. 组合约束（真实生产场景）

```bash
kubectl apply -f 04-combined-scheduling.yaml
kubectl -n sched-lab get pod -o wide
kubectl -n sched-lab describe pod prod-like-scheduling | sed -n '/Node:/p;/Events/,$p'
```

### 预期
- Pod 同时满足：
  - 资源请求可被节点满足（NodeResourcesFit）
  - 节点具备 `zone=test-b`（NodeAffinity required）
  - 能容忍 `workload=isolated:NoSchedule`（Tolerations）

---

## 5. 调度全过程观察（建议）

```bash
kubectl get events -A --sort-by=.lastTimestamp | tail -n 80
kubectl -n kube-system logs deploy/coredns --tail=20
kubectl -n sched-lab get pod -o custom-columns=NAME:.metadata.name,NODE:.spec.nodeName,PHASE:.status.phase
```

> 可选进阶（如启用 scheduler profile / tracing）：
> - 开启 scheduler `--v=4` 或审计日志，观察 QueueSort / Filter / Score / Bind 决策路径。

---

## 清理

```bash
kubectl delete ns sched-lab
```
