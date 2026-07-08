## MongoDB as service on Multi Node vCluster deployed inside Docker with local PV/PVC.

See `vcluster.yaml`

1. Create Cluster

```bash
# Create a vCluster in Docker (automatically connects)
sudo vcluster create my-pipeline --values vcluster.yaml

# if Error
# Verify it's working
kubectl get nodes
kubectl get namespaces
```

2. Create Namespaces

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: app
EOF
```

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Namespace
metadata:
  name: argocd
EOF
```

3. Create PV and PVC

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-vc-pv-app
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/app
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: app-pvc-claim
  namespace: app
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  volumeName: my-vc-pv-app
  storageClassName: ""
EOF
```

```bash
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: my-vc-pv-argocd
spec:
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /data/argocd
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: argocd-pvc-claim
  namespace: argocd
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
  volumeName: my-vc-pv-argocd
  storageClassName: ""
EOF
```
or

```bash
kubectl apply -f 1.app-pvclaim.yaml
```

**Confirm created:**

```bash
kubectl get pv -o wide
```

NAME               CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                       STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE   VOLUMEMODE
my-vc-pv-app       1Gi        RWO            Retain           Bound    app/app-pvc-claim                          <unset>                          16s   Filesystem
my-vc-pv-argocd   1Gi        RWO            Retain           Bound    argocd/argocd-pvc-claim                  <unset>                          8s    Filesyste


```bash
kubectl get pvc -n argocd -o wide
```

NAME                STATUS   VOLUME             CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
argocd-pvc-claim   Bound    my-vc-pv-argocd   1Gi        RWO                           <unset>                 60s   Filesystem

```bash
kubectl get pvc -n app -o wide
```

NAME            STATUS   VOLUME         CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE   VOLUMEMODE
app-pvc-claim   Bound    my-vc-pv-app   1Gi        RWO                           <unset>                 96s   Filesystem

For more detail:

```bash
kubectl describe pvc argocd-pvc-claim -n argocd

# or
kubectl describe pvc app-pvc-claim -n app
```

Name:          app-pvc-claim
Namespace:     db
StorageClass:  
Status:        Bound
Volume:        my-vc3-pv-app
Labels:        <none>
Annotations:   pv.kubernetes.io/bind-completed: yes
Finalizers:    [kubernetes.io/pvc-protection]
Capacity:      1Gi
Access Modes:  RWO
VolumeMode:    Filesystem
Used By:       <none>
Events:        <none>



4. Create Secrets

```bash
kubectl apply -f mongo/2.mongodb-secrets.yaml
```

**Confirm created:**

```bash
kubectl get secrets -n db
```

NAME          TYPE     DATA   AGE
mongo-creds   Opaque   2      4m8s

5. Deploy MongoDB

```bash
kubectl apply -f mongo/3.mongodb-deployment.yaml
```

**Confirm created:**

```bash
kubectl get all -n db -o wide
```

6. Deploy Nodeport Service

```bash
kubectl apply -f mongo/4.mongodb-nodeport-svc.yaml
```

7. Verify deployment, service and storage

```bash
kubectl get all -n db -o wide
# or for more information
kubectl describe pod/mongo-675f47df54-99np2 -n db
```

**Check Connectivity from HOST**

```bash
kubectl port-forward service/mongo-nodeport-svc 27017:27017 -n db
```

Then download and install and use: [MongoDB Compass](https://www.mongodb.com/try/download/compass)

OR

```bash
kubectl exec pod/mongo-675f47df54-99np2 -n db -- /bin/bash
mongosh --host mongo-nodeport-svc --port 27017 -u adminuser -p password123

show dbs
# Returns
#admin   100.00 KiB
#config   60.00 KiB
#local    64.00 KiB

show collections

use admin
# Returns
#switched to db admin

show collections
# Returns
#system.users
#system.version

```

### References

[mongodb-shell-commands](https://www.tutorialsteacher.com/mongodb/mongodb-shell-commands)
[mongo-shell-basic-commands](https://www.bmc.com/blogs/mongo-shell-basic-commands/)
[how-to-use-the-mongodb-shell](https://www.digitalocean.com/community/tutorials/how-to-use-the-mongodb-shell)

[MongoDB Compass](https://www.mongodb.com/try/download/compass)
