
# EHI Bootstrap Installation Instructions

How to install this clustered AWX setup.


## Provision the Servers

Provision at least 3 Debian 11 or Ubuntu 22.04 server with >=8GB RAM, disabled swap and a public IP, then setup SSH access to root@{{ awx_url }} account, these will be our Rancher/AWX servers.

Alternatively you can provision these servers and configure the DNS automatically using DigitalOcean or Proxmox and Cloudflare by running this playbook with the 'provision' tag:

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
frontend http
    bind *:80

    # HTTPS redirect
    redirect scheme https code 301 if !{ ssl_fc }

    mode http
    option tcplog
    acl letsencrypt path_beg /.well-known/acme-challenge/
    use_backend letsencrypt if letsencrypt

    # Add this line to forward traffic to the RKE2 cluster
    use_backend rke2_cluster if { hdr(host) -i leader.example.org }

    default_backend blackhole

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

`$ ansible-playbook -v -i ./inventory/hosts -t "rke2-setup" setup.yml`
