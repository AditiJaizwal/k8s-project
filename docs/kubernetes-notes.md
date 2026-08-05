Control Plane Flow
 

Kubectl (yaml -> json -> https request)
        |
        |
API Server (Authentication, Authorization, Syntax/Format checks)
        |
        |
Etcd (Stores the desired state)
        |
        |
Controller Manager (Compares the Current state with the Desired State - Then runs the reconciliation Loop)
        |
        |
Replica Set (Creates the required Pods)
        |
        |
Scheduler (Schedules the Pod on a Node)
        |
        |
API Server (It get to know that the Pod is not schedules on a node)
        |
        |
Kubelet (Kubelet check with the API server, get to know that a new pod is schedules on node, Tells the CRI to pull image and run container)
        |
        |
CRI (It pulls the image, creates container and runs it)
        |
        |
Kubelet (Check the status of the pod, node, and inform the api server)


Kubelet

1. It is a process on a worker node
2. It notices if a pod is schedules (through API Server)
3. It tells CRI to pull image and create containers.
4. Mount Volumes
5. Monitor Pod and Node health
6. If a probe fails it kills the container and starts again
7. It regularly sends information to the API Server:
    - Node Health 
    - cpu/memory usage
    - Pod Status
    - Container Status
