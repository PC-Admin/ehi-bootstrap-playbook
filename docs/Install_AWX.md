
# EHI Bootstrap Installation Instructions

How to install this clustered AWX setup.


## Provision the Servers

Use MAAS and [ehi-cloudy-dreams](https://github.com/application-research/ehi-cloudy-dreams) to provision at least 3 control-plane servers and 0 to N worker nodes if you prefer to have seperate worker nodes.


## Setup DNS Entries for it

1) A/AAAA records for awx.example.org and rancher.example.org pointing to the external IP of the load balancer (or use CNAME records for it pointing both of them to your load balancers A/AAAA record).

2) setup internal A/AAAA DNS records (or external if you need) for each RKE2 server, this is to ensure they can reach each other with the FQDN.


## Configure HAProxy

First add new backend and frontend definitions to the /etc/haproxy/haproxy.cfg file on each haproxy host, you can see [a few examples of a haproxyconfig file in the docs](/docs/haproxy_example_1.cfg).

Then reload the haproxy service:
`$ sudo systemctl reload haproxy.service`

Note: The other server nodes besides the bootstrap node are commented out, this is needed to deploy initially but once 3 of the server nodes are up you can include them here too.


## Install

1) Install the following ansible-galaxy packages on the controller:
```
$ ansible-galaxy collection install --force awx.awx:21.14.0
$ ansible-galaxy install lablabs.rke2
$ ansible-galaxy collection install community.grafana
$ ansible-galaxy collection install community.digitalocean
```


2) Edit hosts into [./inventories/dev/hosts](./inventories/dev/hosts) or whatever specific inventory you want to use.

Create folder for each host at: ./inventories/dev/host_vars/

Record each hosts variables into each hosts ./inventories/dev/host_vars/awx1.example.org/vars.yml file.


3) Create a global variables file in ./group_vars/all.yml, you can see an example for this in  [./group_vars/all_example.yml](./group_vars/all_example.yml)


4) Run the playbook with the following tags:

`$ ansible-playbook -v -i ./inventories/pchq/ setup.yml`

This playbook has the following tags available (-t):
- setup-rke2        Runs only the RKE2 setup section.
- rancher-setup     Runs only the Rancher setup section.
- awx-setup         Runs only the AWX setup section.
- configure-awx     Runs only the AWX configuration section.