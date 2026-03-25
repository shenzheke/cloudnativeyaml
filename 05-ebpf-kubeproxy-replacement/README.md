# 场景5：eBPF 取代 kube-proxy 验证（基于 Calico eBPF dataplane）

> 前提：你当前是 Calico 集群。该方案通过 Calico eBPF 模式实现 Service 负载均衡，替代 kube-proxy 的 iptables/IPVS 转发路径。

## 文件说明
- `namespace.yaml`
- `service-test.yaml`
- `nodeport-test.yaml`

---

## 0. 风险提示
- 建议先在测试窗口执行，变更前备份当前 `FelixConfiguration`。
- 若 kube-proxy 以 DaemonSet 运行，建议先灰度节点，再全量迁移。

---

## 1. 开启 Calico eBPF dataplane（示例）

```bash
kubectl get felixconfiguration default -o yaml > felix-default-backup.yaml

# 打开 bpfEnabled
kubectl patch felixconfiguration default --type=merge -p '{"spec":{"bpfEnabled":true}}'

# Calico 推荐关闭 kube-proxy 依赖的 conntrack cleanup 行为（按版本文档确认）
kubectl -n calico-system rollout restart ds/calico-node
kubectl -n calico-system rollout status ds/calico-node
```

> kube-proxy 替代通常还需按 Calico 版本执行额外参数（如 BPF service mode）。请严格对照你当前安装版本文档。

---

## 2. 部署 Service 验证工作负载

```bash
kubectl apply -f namespace.yaml
kubectl apply -f service-test.yaml
kubectl apply -f nodeport-test.yaml
kubectl -n ebpf-lab get pod,svc -o wide
```

---

## 3. 功能验证项

### A. ClusterIP

```bash
kubectl -n ebpf-lab run curler --image=curlimages/curl:8.7.1 --rm -it --restart=Never -- \
  sh -c 'for i in $(seq 1 20); do curl -s http://echo; done'
```

预期：请求可达，且响应 Pod 主机名有轮询分布。

### B. NodePort（跨节点）

```bash
kubectl -n ebpf-lab get svc echo-nodeport
# 从任一节点/外部测试机访问任一NodeIP:NodePort
```

预期：任意节点 NodePort 都可访问后端服务（取决于 externalTrafficPolicy 配置）。

### C. 外部流量源地址保留（可选）

```bash
kubectl -n ebpf-lab patch svc echo-nodeport -p '{"spec":{"externalTrafficPolicy":"Local"}}'
```

预期：后端日志可观察客户端源地址是否被保留。

---

## 4. 数据面确认（关键）

```bash
# 节点上检查 BPF map/program（需要主机权限）
bpftool prog show | head -n 50
bpftool map show | head -n 50

# 对比 kube-proxy 规则显著减少
iptables-save | rg -n "KUBE-SVC|KUBE-SEP|KUBE-NODEPORT" | head
```

判定依据：
- Service 连通性正常；
- kube-proxy 规则不再作为主要转发表；
- Calico 节点日志中无大规模 dataplane 错误。

---

## 5. 回滚

```bash
kubectl patch felixconfiguration default --type=merge -p '{"spec":{"bpfEnabled":false}}'
kubectl -n calico-system rollout restart ds/calico-node
```

如已移除 kube-proxy，请重新部署 kube-proxy DaemonSet。

---

## 清理

```bash
kubectl delete ns ebpf-lab
```
