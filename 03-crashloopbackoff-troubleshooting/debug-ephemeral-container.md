# 使用 Ephemeral Container 辅助排障

```bash
kubectl -n crash-lab debug -it pod/<pod-name> --image=busybox:1.36 --target=<container-name>
```

进入后可执行：

```bash
ps aux
cat /etc/resolv.conf
nslookup kubernetes.default.svc.cluster.local
```

> 适用：镜像太精简（无 shell/curl），但需要进入 Pod 网络命名空间观察现场。
