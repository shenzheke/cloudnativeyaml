# 场景4：Pod 间无法通信系统性排查（同节点/跨节点）

> 目标：在 Calico 网络下快速定位“DNS、Service、NetworkPolicy、路由/BGP、主机防火墙、CNI”层面的故障。

## 文件说明
- `namespace.yaml`
- `network-test-workloads.yaml`
- `network-policy-deny.yaml`
- `network-policy-allow.yaml`
- `diag-commands.md`

---

## 1. 部署测试基线

```bash
kubectl apply -f namespace.yaml
kubectl apply -f network-test-workloads.yaml
kubectl -n net-lab get pod -o wide
kubectl -n net-lab get svc
```

工作负载：
- `server`：nginx + ClusterIP Service
- `client-same-node`：通过 podAffinity 尽量与 server 同节点
- `client-cross-node`：通过 podAntiAffinity 尽量与 server 跨节点

---

## 2. 同节点通信验证

```bash
kubectl -n net-lab exec deploy/client-same-node -- wget -qO- http://server.net-lab.svc.cluster.local
kubectl -n net-lab exec deploy/client-same-node -- ping -c 3 server.net-lab.svc.cluster.local
```

### 失败时排查
1. DNS 解析是否正常
2. Service Endpoints 是否就绪
3. 节点本机 iptables/nftables 是否拦截

---

## 3. 跨节点通信验证

```bash
kubectl -n net-lab exec deploy/client-cross-node -- wget -qO- http://server.net-lab.svc.cluster.local
kubectl -n net-lab exec deploy/client-cross-node -- ping -c 3 $(kubectl -n net-lab get pod -l app=server -o jsonpath='{.items[0].status.podIP}')
```

### 失败时排查重点
- Calico Node 状态/BGP 邻居
- VXLAN/IPIP 隧道是否建立
- 主机间路由和 MTU
- 跨节点防火墙（安全组）

---

## 4. 注入 NetworkPolicy 故障并恢复

```bash
kubectl apply -f network-policy-deny.yaml
kubectl -n net-lab exec deploy/client-cross-node -- wget -qO- --timeout=3 http://server.net-lab.svc.cluster.local || echo "blocked"

kubectl apply -f network-policy-allow.yaml
kubectl -n net-lab exec deploy/client-cross-node -- wget -qO- --timeout=3 http://server.net-lab.svc.cluster.local
```

### 预期
- deny 生效后访问失败。
- allow 策略下仅允许 `role=client` 访问 server:80。

---

## 清理

```bash
kubectl delete ns net-lab
```
