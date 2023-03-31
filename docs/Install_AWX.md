
# EHI Bootstrap Installation Instructions

How to install this clustered AWX setup.


## Provision the Servers

Provision at least 3 Ubuntu 22.04 servers with >=32GB RAM and with swap disabled, then setup SSH access to each servers root account, these will be our Rancher/AWX servers.

Alternatively you can provision these servers and configure the DNS automatically using Proxmox and Cloudflare (for the DNS) by:
1) Save a VM template on Proxmox for an Ubuntu 22.04 with enough CPU/RAM and disk space. Ensure the SSH key in (/group_vrs/all.yml)[/group_vrs/all.yml] can be used to connect to the root account of this machine. Also ensure the 'dhcp-identifier' line is added to the following file:
```
root@ubuntu:~# cat /etc/netplan/00-installer-config.yaml
# This is the network config written by 'subiquity'
network:
  ethernets:
    ens18:
      dhcp4: true
      dhcp-identifier: mac
  version: 2
```

2) Ensure the following variables are filled out in each hosts vars.yml file:
```
# Proxmox Settings
proxmox_host: "10.1.1.150"      # the IP address of the target Proxmox node
proxmox_node: "apollo"          # the hostname of the target Proxmox node
proxmox_method: "clone"         # 'clone' or 'lxc'
proxmox_template: "ubuntu22-8c-8g-32g"   # the name of your VM template
proxmox_storage: "vm-storage"   # the Proxmox storage ID for the new VMs disk (eg: 'local-lvm')
```

3) Run this playbook with the 'provision' tag like so:

`$ ansible-playbook -v -i ./inventory/hosts -t "provision" setup.yml`

After your finished you can delete these servers/records with the 'teardown' tag:

`$ ansible-playbook -v -i ./inventory/hosts -t "teardown" setup.yml`


## Setup DNS Entries for it

1) A/AAAA record for awx1.example.org to the servers IP.

2) optionally, an A/AAAA record for rancher.example.org to the servers IP, 
    or a CNAME record for it pointing to awx.example.org.


## Configure HAProxy

First add a backend and frontend definition to the /etc/haproxy/haproxy.cfg file:

```
global
    log /dev/log local0 debug
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log global
    mode tcp
    option tcplog
    option log-separate-errors
    option log-health-checks
    retries 3
    timeout connect 5000
    timeout client 50000
    timeout server 50000

frontend tcp_frontend
    bind *:9345
    mode tcp
    option tcplog
    log global
    default_backend rke2_cluster

frontend http_frontend
    bind *:80
    mode http
    log global
    use_backend http_backend

frontend https_frontend
    bind *:443
    mode tcp
    option tcplog
    option logasap
    log global
    tcp-request inspect-delay 5s
    tcp-request content accept if { req_ssl_hello_type 1 }
    use_backend https_backend

backend rke2_cluster
    balance roundrobin
    option tcp-check
    tcp-check connect port 9345
    timeout check 5000
    server awx1 awx1.perthchat2.org:9345 check

backend http_backend
    mode http
    balance roundrobin
    option httpchk GET /healthz HTTP/1.1\r\nHost:\ ingress.perthchat2.org
    http-check expect status 200
    timeout check 5000
    log global
    server awx4 awx4.perthchat2.org:80 check
    server awx5 awx5.perthchat2.org:80 check

backend https_backend
    mode tcp
    balance roundrobin
    option ssl-hello-chk
    log global
    server awx4 awx4.perthchat2.org:443 check
    server awx5 awx5.perthchat2.org:443 check
```

Then reset the haproxy service:
`$ sudo systemctl restart haproxy.service`

Note: The other server nodes besides the bootstrap node are commented out, this is needed to deploy initially but once 3 of the server nodes are up you can include them here too.


## Install

1) Install the following ansible-galaxy packages on the controller:
```
$ ansible-galaxy collection install --force awx.awx:21.9.0
$ ansible-galaxy install lablabs.rke2
$ ansible-galaxy collection install community.grafana
$ ansible-galaxy collection install community.digitalocean
```


2) Edit hosts into: [./inventory/hosts](./inventory/hosts)

Create folder for each host at: ./inventory/host_vars/

Record each hosts variables into each hosts ./inventory/host_vars/awx1.example.org/vars.yml file.


3) Run the playbook with the following tags:

`$ ansible-playbook -v -i ./inventory/hosts -t "rke2-setup,rancher-setup" setup.yml`
