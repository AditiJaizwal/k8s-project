## **Kubernetes Probes**

Probes allow the **kubelet** to periodically check the state of the application running inside a container.

The three main probes are:

```text
Startup Probe
Readiness Probe
Liveness Probe
```

### **Probe Types**

Kubernetes probes can check applications using:

```text
HTTP      → HTTP endpoint
TCP       → Check whether a TCP connection succeeds
Exec      → Run a command inside the container
gRPC      → gRPC health check
```

### **Readiness Probe**

Readiness answers: **Should this Pod receive traffic right now?**

If the readiness probe fails:

```text
Readiness fails
      ↓
Pod becomes NotReady
      ↓
EndpointSlice marks endpoint ready=false
      ↓
Service stops sending normal traffic to the Pod
      ↓
Container continues running
```

### **Liveness Probe**

Liveness answers: **Is the application unhealthy/stuck in a way where restarting the container may help?**

If the liveness probe repeatedly fails:

```text
Liveness fails
      ↓
failureThreshold reached
      ↓
kubelet kills the container
      ↓
container is restarted
      ↓
Pod usually remains the same
      ↓
RESTARTS increases
```
Liveness is **not needed just to detect that a container process exited**. Kubernetes already knows when a container stops.

It is useful when the container/process is still running but the application is stuck or unresponsive.

ServiceAccount = an identity used by Pods/workloads when interacting with the Kubernetes API. RBAC determines what that identity can do. In EKS, the ServiceAccount can also be associated with AWS IAM permissions for workloads that need to call AWS APIs.




## Requests and Limits

### Requests

Resources Kubernetes uses when **scheduling a Pod**.

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
```

- `100m` CPU = `0.1` CPU core.
- Scheduler checks requests to decide whether a Pod fits on a Node.
- Pod can use less or more than its request if resources are available.
- Request is **not a maximum**.

**Remember:**

> Request = How much capacity should Kubernetes plan for me?

### Limits

Maximum resources a container is allowed to consume.

```yaml
resources:
  limits:
    cpu: "500m"
    memory: "256Mi"
```

- CPU exceeds limit → **CPU throttling**
- Memory exceeds limit → container can be **OOMKilled**

**Remember:**

> Limit = How much resource am I allowed to consume?

### Memory Failure Difference

```text
Container exceeds memory limit
        ↓
OOMKilled
```

```text
Node runs out of memory
        ↓
MemoryPressure
        ↓
Pods may be evicted
```

---

## HPA - Horizontal Pod Autoscaler

HPA automatically increases or decreases the number of **Pod replicas** based on metrics such as CPU or memory.

```text
Traffic increases
      ↓
CPU increases
      ↓
Metrics Server
      ↓
HPA
      ↓
Deployment replicas
3 → 6
```

For CPU-based HPA:

```text
CPU utilization = actual CPU usage / CPU request
```

Example:

```text
CPU request = 100m
HPA target  = 50%

Target usage ≈ 50m CPU per Pod
```

Approximate HPA calculation:

```text
desired replicas =
current replicas × current utilization / target utilization
```

Example:

```text
Current replicas     = 3
Current utilization  = 94%
Target utilization   = 50%

3 × 94 / 50 ≈ 6 replicas
```

HPA changes the replica count on the Deployment.

> **HPA scales Pods, not Nodes.**

Scale-down is intentionally slower to prevent frequent scaling up/down (**flapping**).

---

## ServiceAccount

A **ServiceAccount is a Kubernetes identity for Pods/workloads**.

```text
Pod
 ↓
ServiceAccount
 ↓
Identity used when talking to Kubernetes API
```

If no ServiceAccount is specified, a Pod normally uses the namespace's `default` ServiceAccount.

A ServiceAccount itself does **not** grant permissions.

```text
ServiceAccount = WHO are you?
RBAC           = WHAT can you do?
```

Example:

```yaml
spec:
  serviceAccountName: cluster-autoscaler
```

The identity becomes:

```text
system:serviceaccount:kube-system:cluster-autoscaler
```

---

## RBAC - Role Based Access Control

RBAC controls what an identity is allowed to do **inside Kubernetes**.

```text
ServiceAccount
      ↓
RoleBinding / ClusterRoleBinding
      ↓
Role / ClusterRole
      ↓
Permissions
```

Example:

```text
list Pods       ✅
list Nodes      ✅
delete Secrets  ❌
```

### Role vs ClusterRole

```text
Role
→ namespace-scoped permissions

ClusterRole
→ cluster-wide permissions
```

### Binding

```text
RoleBinding
→ connects an identity to a Role

ClusterRoleBinding
→ connects an identity to a ClusterRole
```

Check permissions:

```bash
kubectl auth can-i list pods \
  --as=system:serviceaccount:kube-system:cluster-autoscaler \
  --all-namespaces
```

**Remember:**

```text
ServiceAccount       = identity
Role/ClusterRole     = permissions
RoleBinding          = assigns permissions to identity
```

---

## IRSA - IAM Roles for Service Accounts

IRSA allows an EKS Pod to obtain **AWS IAM permissions through its Kubernetes ServiceAccount**.

```text
Pod
 ↓
ServiceAccount
 ↓
OIDC / IRSA
 ↓
IAM Role
 ↓
AWS APIs
```

This avoids storing static AWS credentials inside Pods.

Example:

```text
Cluster Autoscaler Pod
      ↓
ServiceAccount
      ↓
IRSA
      ↓
IAM Role
      ↓
AWS Auto Scaling API
```

The ServiceAccount is annotated with the IAM Role:

```yaml
annotations:
  eks.amazonaws.com/role-arn: <IAM-ROLE-ARN>
```

**Remember:**

```text
RBAC
→ permissions inside Kubernetes

IRSA + IAM
→ permissions in AWS
```

---

## Cluster Autoscaler

Cluster Autoscaler automatically increases or decreases **worker Nodes** based on Kubernetes scheduling requirements.

Example:

```text
Pod created
      ↓
Scheduler tries to schedule it
      ↓
Insufficient CPU / Memory
      ↓
Pod stays Pending
      ↓
Cluster Autoscaler detects unschedulable Pod
      ↓
MNG / ASG desired capacity increases
      ↓
AWS creates EC2 worker
      ↓
Node joins EKS
      ↓
Scheduler places Pending Pod
```

### MNG / ASG vs Cluster Autoscaler

Managed Node Group / Auto Scaling Group provides the **ability to add/remove Nodes**.

Example:

```text
min     = 1
desired = 1
max     = 3
```

This only means:

```text
Node group CAN scale between 1 and 3 Nodes.
```

It does not know that Kubernetes has Pending Pods.

Cluster Autoscaler is the Kubernetes-aware component that decides:

```text
"We need another Node."
```

and changes:

```text
desired: 1 → 2
```

### Remember

```text
MNG / ASG
→ mechanism that CAN add/remove Nodes

Cluster Autoscaler
→ decides WHEN Kubernetes needs more/fewer Nodes
```

---

## Cluster Autoscaler Permissions

Cluster Autoscaler needs access to **two different systems**.

```text
              Cluster Autoscaler Pod
                       |
                       ↓
                 ServiceAccount
                  /         \
                 /           \
                ↓             ↓
              RBAC           IRSA
                ↓             ↓
        Kubernetes API     IAM Role
                ↓             ↓
          Pods / Nodes     AWS APIs
```

### Kubernetes side

RBAC allows Cluster Autoscaler to inspect things such as:

```text
Pods
Nodes
ReplicaSets
StatefulSets
PVCs
StorageClasses
etc.
```

This lets it understand:

```text
Which Pods are Pending?
Why can't they schedule?
Which Nodes exist?
```

### AWS side

IRSA/IAM allows it to perform AWS actions such as:

```text
DescribeAutoScalingGroups
SetDesiredCapacity
TerminateInstanceInAutoScalingGroup
DescribeNodegroup
```

---

## Complete Autoscaling Flow

```text
Traffic increases
      ↓
Backend CPU increases
      ↓
Metrics Server reports CPU
      ↓
HPA
      ↓
Deployment replicas increase
3 → 6
      ↓
Scheduler tries to place new Pods
      ↓
Node has insufficient resources
      ↓
Some Pods remain Pending
      ↓
Cluster Autoscaler detects Pending Pods
      ↓
MNG / ASG desired capacity increases
1 → 2
      ↓
AWS creates EC2 worker
      ↓
New Node joins EKS
      ↓
Scheduler places Pending Pods
      ↓
Pods become Running
```

When load decreases:

```text
Traffic decreases
      ↓
CPU decreases
      ↓
HPA
      ↓
Pods decrease
6 → 3
      ↓
Extra Node becomes unnecessary
      ↓
Cluster Autoscaler
      ↓
Node group scales down
2 → 1
```

---

## Autoscaling - Quick Revision

```text
HPA
→ scales Pods

Cluster Autoscaler
→ scales Nodes

MNG / ASG
→ provides the Node scaling mechanism

Metrics Server
→ provides CPU/memory metrics

Scheduler
→ decides which Node a Pod runs on
```

Full flow:

```text
Traffic
  ↓
HPA
  ↓
More Pods
  ↓
Scheduler
  ↓
Insufficient capacity
  ↓
Pending Pods
  ↓
Cluster Autoscaler
  ↓
MNG / ASG
  ↓
More EC2 Nodes
  ↓
Pending Pods scheduled
```
