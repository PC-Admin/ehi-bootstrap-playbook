
# EHI Bootstrap Installation Instructions

How to install this clustered AWX setup.


## Provision the Servers

Provision at least 3 Ubuntu 22.04 servers with >=32GB RAM, swap disabled and at least 64GB of disk space in the root partition, then setup SSH access to each servers root account, these will be our RKE2/AWX servers.

Alternatively you can provision these servers and configure the DNS automatically using Proxmox and Cloudflare (for the DNS) by:
1) Save a VM template on Proxmox for an Ubuntu 22.04 with enough CPU/RAM and disk space. 

  a)Ensure the SSH key in [/group_vars/all.yml](/group_vars/all.yml) can be used to connect to the root account of this machine. 

  b) Also ensure the 'dhcp-identifier' line is added to the following file:
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
  c) Also make sure that the Proxmox templates Processors 'Type' is set to 'host' in Proxmox. This ensures the extra amd64 CPU functions AWX needs are available.

2) Ensure the following variables are filled out in each hosts vars.yml file:
```
# Proxmox Settings
proxmox_host: "10.1.1.150"      # the IP address of the target Proxmox node
proxmox_node: "apollo"          # the hostname of the target Proxmox node
proxmox_method: "clone"         # 'clone' or 'lxc'
proxmox_template: "ubuntu22-8c-8g-32g"   # the name of your VM template
proxmox_storage: "vm-storage"   # the Proxmox storage ID for the new VMs disk (eg: 'local-lvm')
```

3) Collect your CloudFlare API tokens for the DNS/Deployment:

  a) Log in to your Cloudflare account and navigate to the API Tokens page: https://dash.cloudflare.com/profile/api-tokens.

  b) Collect {{ cloudflare_api_token }} value from the 'Global API Key' section.

  c) Create the {{ cloudflare_dns_token }} with the following permissions:

    i) Select the 'Edit zone DNS' template.

    ii) In the 'Permissions' section at the top, add 'Zone - DNS - Read' and 'Zone - DNS - Edit' as permissions.

    iii) In 'Zone Resources' add an entry for 'Include - Specific zone - example.org' to limit the token to one domain.

    iv) Set IP filtering or an expiry date if you wish.

    v) Check 'Continue to summary'

4) Run this playbook with the 'provision' tag like so:

`$ ansible-playbook -v -i ./inventory/hosts -t "provision" setup.yml`

After your finished you can delete these servers/records with the 'teardown' tag:

`$ ansible-playbook -v -i ./inventory/hosts -t "teardown" setup.yml`


## Setup DNS Entries for it

1) A/AAAA record for awx1.example.org to the servers IP.

2) optionally, an A/AAAA record for rancher.example.org to the servers IP, 
    or a CNAME record for it pointing to awx.example.org.


## Configure HAProxy

First add new backend and frontend definitions to the /etc/haproxy/haproxy.cfg file on each haproxy host, you can see [an example of a haproxyconfig file in the docs](/docs/haproxy_example.cfg).

Then reset the haproxy service:
`$ sudo systemctl restart haproxy.service`

Note: The other server nodes besides the bootstrap node are commented out, this is needed to deploy initially but once 3 of the server nodes are up you can include them here too.


## Install

1) Install the following ansible-galaxy packages on the controller:
```
$ ansible-galaxy collection install --force awx.awx:21.14.0
$ ansible-galaxy install lablabs.rke2
$ ansible-galaxy collection install community.grafana
$ ansible-galaxy collection install community.digitalocean
```


2) Edit hosts into: [./inventory/hosts](./inventory/hosts)

Create folder for each host at: ./inventory/host_vars/

Record each hosts variables into each hosts ./inventory/host_vars/awx1.example.org/vars.yml file.


3) If this is your first time running this playbook and you haven't got either of these files:
```
./group_vars/secrets.yml
./vault/password-file
```

That's cool! It will create them automatically for you! Just be aware that you'll need to preserve the ./vault/password-file, keep it somewhere private and safe.


4) Run the playbook with the following tags:

`$ ansible-playbook -v -i ./inventory/hosts -t "rke2-setup,rancher-setup,awx-setup,ansible-vault,awx-token,configure-awx" setup.yml`

Note: To the 'ansible-vault' tag will decrypt the ./group_vars/secrets.yml file if it exists, otherwise it will create it for the first time with only a few variables about the AWX oauth token that's generated. 

