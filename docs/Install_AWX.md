
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
frontend tcp_frontend
    bind *:9345

    mode tcp
    option tcplog
    default_backend rke2_cluster

backend rke2_cluster
    balance roundrobin
    option tcp-check
    tcp-check connect port 9345
    server awx1 awx1.example.org:9345 check
    server awx2 awx2.example.org:9345 check
    server awx3 awx3.example.org:9345 check
```

Then reset the haproxy service:
`$ sudo systemctl restart haproxy.service`


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
