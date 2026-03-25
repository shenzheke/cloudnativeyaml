# 场景2：自动扩缩容验证（HPA + VPA + Cluster Autoscaler联动视角）

> 目标：在现有 Prometheus/ArgoCD/Traefik 基础上，验证业务副本自动扩缩、资源建议与节点扩缩之间的关系。

## 文件说明
- `namespace.yaml`
- `deployment-cpu-demo.yaml`
- `hpa-cpu-demo.yaml`
- `load-generator.yaml`
- `vpa-recommendation.yaml`

---

## 1. 部署基础负载与 HPA

```bash
kubectl apply -f namespace.yaml
kubectl apply -f deployment-cpu-demo.yaml
kubectl apply -f hpa-cpu-demo.yaml
kubectl -n autoscale-lab get deploy,pod,hpa
```

### 验证点
- HPA 读取 metrics-server 指标（或外部指标）
- 副本数在 `minReplicas=2` 到 `maxReplicas=10` 区间内变化

---

## 2. 施加压力触发扩容

```bash
kubectl apply -f load-generator.yaml
kubectl -n autoscale-lab logs -f deploy/load-generator
```

另开窗口观察：

```bash
kubectl -n autoscale-lab get hpa cpu-demo-hpa -w
kubectl -n autoscale-lab get pod -l app=cpu-demo -w
```

### 预期
- `TARGETS` 持续超过 `60%` 时，HPA 扩容。
- 压力结束后，副本缓慢回落（受 stabilization window 影响）。

---

## 3. VPA（建议模式）验证

```bash
kubectl apply -f vpa-recommendation.yaml
kubectl -n autoscale-lab get vpa
kubectl -n autoscale-lab describe vpa cpu-demo-vpa
```

### 预期
- `updateMode: Off` 不会自动重建 Pod，仅给出 CPU/内存建议区间。
- 可将建议回写 Deployment requests/limits，形成调优闭环。

---

## 4. Cluster Autoscaler（如已安装）联动验证

> 本目录不强绑定具体云厂商参数；若已部署 CA，可使用下列方式验证：

```bash
kubectl -n kube-system logs deploy/cluster-autoscaler --tail=200 | rg -n "scale up|scale down|unneeded"
kubectl get nodes -w
```

### 预期
- HPA 扩容导致 Pending Pod 时，CA 触发加节点。
- 负载回落且节点空闲后，CA 缩容（受 PDB、drain、cooldown 约束）。

---

## 清理

```bash
kubectl delete ns autoscale-lab
```
