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

<service>.<namespace>.svc.cluster.local


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
kubectl get pods
kubectl get pods -o wide
kubectl get deployments
kubectl get rs

### Debugging
kubectl describe pod <pod>
kubectl logs <pod>

### Services
kubectl get svc
kubectl get endpointslices

### Rollouts
kubectl rollout status deployment/<deployment>
kubectl rollout history deployment/<deployment>
kubectl rollout undo deployment/<deployment>

### Cluster
kubectl get nodes
kubectl get pods -n kube-system

### Context
kubectl config current-context
kubectl config get-contexts