# 场景3：Pod 频繁重启（CrashLoopBackOff）系统性排查

> 目标：通过“故障注入 + 分层排查”建立标准 Runbook。

## 文件说明
- `namespace.yaml`
- `crashloop-scenarios.yaml`：一次性创建多个典型崩溃场景。
- `debug-ephemeral-container.md`：使用临时容器辅助排障。

---

## 1. 部署故障样例

```bash
kubectl apply -f namespace.yaml
kubectl apply -f crashloop-scenarios.yaml
kubectl -n crash-lab get pod
```

### 样例说明
1. `crash-exit-immediately`：主进程直接退出（exit 1）
2. `crash-missing-config`：依赖 ConfigMap 但 key 不存在
3. `crash-failed-liveness`：Liveness Probe 配置错误导致反复重启
4. `crash-oom`：内存限制过低，触发 OOMKilled

---

## 2. 排查流程（建议固定顺序）

### A. 看状态与重启次数

```bash
kubectl -n crash-lab get pod -o wide
kubectl -n crash-lab get pod -o custom-columns=NAME:.metadata.name,PHASE:.status.phase,RESTART:.status.containerStatuses[0].restartCount,REASON:.status.containerStatuses[0].state.waiting.reason
```

### B. 看事件（最关键）

```bash
kubectl -n crash-lab describe pod crash-failed-liveness | sed -n '/Events/,$p'
kubectl -n crash-lab get events --sort-by=.lastTimestamp | tail -n 80
```

### C. 看日志（当前 + 上一轮）

```bash
kubectl -n crash-lab logs crash-exit-immediately
kubectl -n crash-lab logs crash-exit-immediately --previous
```

### D. 识别根因类型

```bash
kubectl -n crash-lab get pod crash-oom -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}{"\n"}'
kubectl -n crash-lab get pod crash-oom -o jsonpath='{.status.containerStatuses[0].lastState.terminated.exitCode}{"\n"}'
```

常见映射：
- `OOMKilled`：资源限制或内存泄漏。
- `Error/ExitCode!=0`：应用启动逻辑失败。
- `CreateContainerConfigError`：引用 Secret/ConfigMap 错误。
- `Probe failed`：健康检查参数不匹配。

---

## 3. 修复与回归

1. 修复 YAML（命令、探针、资源、配置项）
2. `kubectl apply -f ...`
3. 观察 10~15 分钟重启次数是否归零

```bash
kubectl -n crash-lab rollout restart deploy/crash-failed-liveness
kubectl -n crash-lab rollout status deploy/crash-failed-liveness
kubectl -n crash-lab get pod -w
```

---

## 清理

```bash
kubectl delete ns crash-lab
```
