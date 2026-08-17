## **Control Plane Flow**
```
Kubectl (YAML → JSON → HTTPS Request)
        |
        v
API Server (Authentication, Authorization, Validation)
        |
        v
etcd (Stores the Desired State)
        |
        v
Controller Manager (Compares Desired State with Current State and runs the Reconciliation Loop)
        |
        v
ReplicaSet (Creates the required Pods)
        |
        v
Scheduler (Assigns the Pod to a Worker Node)
        |
        v
API Server (Stores the scheduling decision)
        |
        v
Kubelet (Watches the API Server, notices a Pod is assigned to its node, and tells the CRI to pull the image and start the container)
        |
        v
CRI (Pulls the image, creates, and starts the container)
        |
        v
Kubelet (Monitors Pod and Node health and reports status to the API Server)
```
## **Kubelet**

1. Runs on every Worker Node.
2. Watches the API Server for Pods assigned to its node.
3. Instructs the CRI to pull images and start containers.
4. Mounts volumes.
5. Monitors Pod and Node health.
6. Restarts containers if health probes fail.
7. Regularly reports to the API Server:
   - Node Health
   - CPU/Memory Usage
   - Pod Status
   - Container Status


## **CoreDNS**

Applications should not need to remember service's IP
Instead, the backend connects to service endpoint ```eg: postgres-svc```

The Pod asks CoreDNS:
"What IP is postgres-svc?"

CoreDNS returns the Service ClusterIP:
```
postgres-svc
      ↓
CoreDNS
      ↓
172.20.142.119
```
The full Service DNS name is:

```<service>.<namespace>.svc.cluster.local```


## **Kube Proxy**

1. kube-proxy programs the Linux kernel's networking stack.
2. It writes IPs in Iptables

Responsibility of Kube-Proxy 

```
API Server
↓
Endpoint changes
↓
kube-proxy
↓
Programs iptables
↓
Done

```

Traffic flow:

```
Packet
↓
Linux Kernel route the Packet to Pod
↓
Pod

```

## **CNI - Cluster Network Interface**

1. It creates the network so that every Pod IP is routable.
2. After kube-proxy rewrites the Service IP to a Pod IP, Kubernetes still needs a way to physically deliver the packet to that Pod, even if it is running on another node.

Simple mental model:
```
CoreDNS
"What is the Service IP?"

        ↓

kube-proxy / Service networking
"Which Pod endpoint should receive this?"

        ↓

CNI
"How can the packet reach that Pod IP?"
```
On EKS we observed ```aws-node``` running in kube-system.

This is part of the AWS VPC CNI setup.

### Responsibilities of CNI

- Assigns an IP address to every Pod.
- Makes every Pod IP routable across the cluster.
- Connects Pods running on different nodes.
- Configures Linux networking (routes, veth pairs, bridges, etc.) depending on the CNI implementation.

## Difference between Kube-proxy and CNI

### Kube-proxy

Responsible for:
- Services
- ClusterIP
- Load balancing
- Endpoint updates
- iptables/IPVS programming

Question it answers: "Which Pod should receive this packet?"

### CNI

Responsible for:
- Pod IP allocation
- Pod networking
- Cross-node communication
- Linux routes
- veth pairs
- Bridges/Tunnels/VPC routing

Question it answers: "How do I physically reach this Pod?"


## Deployment

A Deployment is a recipe describing how Kubernetes should create and manage Pods.

Basic structure:
```
Deployment
│
├── metadata
│
└── spec
    ├── replicas
    ├── selector
    └── template
        ├── metadata
        │   └── labels
        └── spec
            └── containers

```
##  **Service**

1. A service is not a process or a pod, it is an object stored in etcd.
2. It's just a data.
3. The Service itself does nothing.
4. It's just metadata. The actual work is done by:
    - CoreDNS (name → ClusterIP)
    - kube-proxy (ClusterIP → Pod IP)
    - Linux kernel (packet forwarding)

A Service provides a stable network endpoint (IP + DNS name) for accessing a group of Pods.

Why is it needed? Pods are temporary—their IP addresses can change when they are recreated. A Service lets applications communicate without knowing individual Pod IPs.

Basic structure
```
Service
│
├── apiVersion: v1
│
├── kind: Service
│
├── metadata
│   └── name: postgres-svc
│
└── spec
    │
    ├── selector
    │   └── app: postgres
    │
    ├── ports
    │   ├── port: 5432
    │   └── targetPort: 5432
    │
    └── type: ClusterIP
```

## Labels and Selectors

Simple rule:

Labels identify objects. Selectors find objects.

The Pod template adds:
```
labels:
  app: backend
```

The Deployment/ReplicaSet uses:
```
selector:
  matchLabels:
    app: backend
```

## Pod Failure States
#### ErrImagePull

Means Kubernetes attempted to pull the container image and failed.
We debugged it using:

```kubectl describe pod <pod>```

The important section was:

Events

Our failure was caused by the image not existing in ECR.

#### ImagePullBackOff

After an image pull fails, Kubernetes retries.
Instead of retrying continuously, it progressively waits longer between attempts.
```
ErrImagePull
     ↓
ImagePullBackOff
     ↓
retry
```
#### CrashLoopBackOff

Our image eventually pulled successfully, but the application crashed because it tried to connect to: ```localhost:5432```

There was no PostgreSQL server inside the backend Pod. The application exited, Kubernetes restarted it, it failed again, and eventually entered: CrashLoopBackOff




## Commands Worth Remembering
### Workloads
- ```kubectl get pods```
- ```kubectl get pods -o wide```
- ```kubectl get deployments```
- ```kubectl get rs```

### Debugging
- ```kubectl describe pod <pod>```
- ```kubectl logs <pod>```

### Services
- ```kubectl get svc```
- ```kubectl get endpointslices```

### Rollouts
- ```kubectl rollout status deployment/<deployment>```
- ```kubectl rollout history deployment/<deployment>```
- ```kubectl rollout undo deployment/<deployment>```

### Cluster
- ```kubectl get nodes```
- ```kubectl get pods -n kube-system```

### Context
- ```kubectl config current-context```
- ```kubectl config get-contexts```


## **Kubernetes Secrets**

Instead of putting sensitive values directly inside Pod YAML, we store them in a **Secret** and reference the Secret from the Pod.


```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret
type: Opaque
stringData:
  username: admin
  password: mypassword
```

### Use Secret as Environment Variables

```yaml
env:
  - name: DB_USERNAME
    valueFrom:
      secretKeyRef:
        name: db-secret
        key: username
```

> **Note:** Kubernetes Secrets are not encrypted just because they are Secrets. By default, Secret data stored in etcd may only be base64 encoded unless encryption at rest is configured.


## **PVC - PersistentVolumeClaim**

Containers have ephemeral storage.

If a Pod/container is deleted, data stored inside the container can be lost.

For persistent data, Kubernetes uses:

```text
Pod
 |
 v
PVC (Request for Storage)
 |
 v
PV (Actual Storage)
 |
 v
Disk / EBS / Azure Disk / etc.
```

### PVC

PVC = **PersistentVolumeClaim**

A PVC is a request for storage.

Example:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-pvc
spec:
  accessModes:
    - ReadWriteOnce

  resources:
    requests:
      storage: 10Gi
```

Pod can then mount the PVC:

```yaml
volumes:
  - name: app-storage
    persistentVolumeClaim:
      claimName: app-pvc
```

### Important

```text
Pod requests PVC
      |
      v
PVC gets bound to PV
      |
      v
Pod uses the storage
```

---

## **Storage Class**

A StorageClass defines **how Kubernetes should provision storage**.

Without dynamic provisioning, an administrator may need to create PVs manually.

With a StorageClass:

```text
Pod
 |
 v
PVC
 |
 | requests StorageClass
 v
StorageClass
 |
 | dynamically provisions
 v
PV
 |
 v
Actual Disk
```

Example:

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3
provisioner: ebs.csi.aws.com
parameters:
  type: gp3
```

PVC:

```yaml
spec:
  storageClassName: gp3

  accessModes:
    - ReadWriteOnce

  resources:
    requests:
      storage: 10Gi
```

### Remember

```text
PVC          = I need 10Gi storage

StorageClass = What type/how should storage be created?

PV           = The storage Kubernetes gives me
```

---

## **CSI Drivers**

CSI = **Container Storage Interface**

CSI allows Kubernetes to communicate with external storage systems.

Examples:

```text
AWS   → EBS CSI Driver
Azure → Azure Disk CSI Driver
GCP   → Persistent Disk CSI Driver
```

### Flow

```text
Pod
 |
 v
PVC
 |
 v
StorageClass
 |
 v
CSI Driver
 |
 | Calls Cloud Provider API
 v
EBS / Azure Disk / GCP Disk
 |
 v
PV
 |
 v
Mounted into Pod
```

For example, on AWS:

```text
PVC requests 10Gi gp3
        |
        v
StorageClass
provisioner: ebs.csi.aws.com
        |
        v
EBS CSI Driver
        |
        v
AWS API
        |
        v
Creates EBS Volume
        |
        v
PV created/bound
        |
        v
Volume attached to Node
        |
        v
Mounted into Pod
```

### Important

The CSI Driver generally has two main parts:

```text
CSI Controller
    |
    | Creates / Deletes volumes
    | Attach / Detach operations
    v
Cloud Provider


CSI Node
    |
    | Runs on Worker Nodes
    | Mounts / Unmounts volumes
    v
Pod
```

---

## **Storage - Quick Revision**

```text
PVC
 |
 | "I need storage"
 v
StorageClass
 |
 | "This is how to create it"
 v
CSI Driver
 |
 | "I'll talk to the storage provider"
 v
Cloud Storage (EBS etc.)
 |
 v
PV
 |
 | Bound to PVC
 v
Pod
```

**PVC** → Storage request  
**PV** → Actual Kubernetes storage resource  
**StorageClass** → Defines how storage is provisioned  
**CSI Driver** → Connects Kubernetes with the storage provider