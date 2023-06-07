
# Migrate AWX to External Database

Today we're gonna try to migrate AWX to an external DB. Setting up a new AWX which *uses* an external DB is easy enough, but converting an existing installation to use an external DB is tough.

Steps done so far:

* Create a backup (create this as a k8s object)

```
---
apiVersion: awx.ansible.com/v1beta1
kind: AWXBackup
metadata:
  name: awxbackup-2023-06-06
  namespace: awx
spec:
  deployment_name: awx-estuary
```

* Wait for the backup to complete
* Back up your AWX deployment object as a manifest
```
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-estuary
  namespace: awx
spec:
  admin_email: not-my-real-email@protocol.ai
  admin_password_secret: not-my-real-password
  admin_user: admin
  auto_upgrade: true
  create_preload_data: true
  garbage_collect_secrets: false
  hostname: awx.estuary.tech
  image_pull_policy: IfNotPresent
  ingress_tls_secret: tls-awx-ingress
  ingress_type: ingress
  ipv6_disabled: false
  loadbalancer_ip: ''
  loadbalancer_port: 80
  loadbalancer_protocol: http
  no_log: true
  projects_persistence: false
  projects_storage_access_mode: ReadWriteMany
  projects_storage_size: 8Gi
  replicas: 1
  route_tls_termination_mechanism: Edge
  set_self_labels: true
  task_privileged: false
```

* Make a new copy of your AWX deployment object, adding the following line to spec (replace "awx-estuary" with the name of your AWX deployment):
```
  postgres_configuration_secret: awx-estuary-postgres-configuration
```

* Mount that backup using a temporary pod once it completes:
```
apiVersion: v1
kind: Pod
metadata:
  name: awx-rescue
  namespace: awx
spec:
  containers:
    - name: rescue
      image: ubuntu
      command: ["sleep", "360000"]
      volumeMounts:
        - name: backup-volume
          mountPath: /awx-backup
  volumes:
    - name: backup-volume
      persistentVolumeClaim:
        claimName: awx-estuary-backup-claim
```

* Within that backup, install an SSH client and use it to `scp` the entire backup onto a normal machine.
* Copy that backup to your database server.
* Restore the backup

`ubuntu@prod-ebi-db01:/var/lib/postgresql$ cat tower.db | sudo -u postgres pg_restore --clean --if-exists -d awx`

* Back up the awx-estuary-postgres-configuration secret (replace awx-estuary with whatever your AWX deployment name is).
```
apiVersion: v1
kind: Secret
metadata:
  name: awx-estuary-postgres-configuration
  namespace: awx
data:
  database: YXd4
  host: YXd4LWVzdHVhcnktcG9zdGdyZXMtMTM=
  password: REDACTED
  port: NTQzMg==
  type: bWFuYWdlZA==
  username: YXd4
```

* Make a new awx-estuary-postgres-configuration secret (replace awx-estuary as above). Note that we change type from "managed" to "unmanaged" here, signaling to AWX Operator that it doesn't need to manage this PostgreSQL.
```
kind: Secret
metadata:
  name: awx-estuary-postgres-configuration
  namespace: awx
data:
  database: YXd4
  host: REDACTED
  password: REDACTED
  port: REDACTED
  type: dW5tYW5hZ2Vk
  username: YXd4
```