# 网络故障诊断命令清单

## 通用
```bash
kubectl -n net-lab get pod -o wide
kubectl -n net-lab get svc,endpoints
kubectl -n net-lab get networkpolicy
kubectl -n net-lab get events --sort-by=.lastTimestamp | tail -n 100
```

## DNS
```bash
kubectl -n net-lab exec deploy/client-cross-node -- nslookup server.net-lab.svc.cluster.local
kubectl -n kube-system logs deploy/coredns --tail=100
```

## Calico
```bash
kubectl -n calico-system get pod -o wide
kubectl -n calico-system logs ds/calico-node --tail=200
kubectl -n calico-system exec ds/calico-node -- calicoctl node status
```

## 节点网络
```bash
ip route
ip link
iptables -S | head -n 80
nft list ruleset | head -n 120
```
