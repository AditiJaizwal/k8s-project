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


##  **Service**

1. A service is not a process or a pod, it is an object stored in etcd.
2. It's just a data.
3. The Service itself does nothing.
4. It's just metadata. The actual work is done by:
    - CoreDNS (name → ClusterIP)
    - kube-proxy (ClusterIP → Pod IP)
    - Linux kernel (packet forwarding)

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

### Responsibilities of CNI

- Assigns an IP address to every Pod.
- Makes every Pod IP routable across the cluster.
- Connects Pods running on different nodes.
- Configures Linux networking (routes, veth pairs, bridges, etc.) depending on the CNI implementation.

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