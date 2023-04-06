
## Managing Ansible Vault Keys

This playbook will automatically generate a ./vault/password-file if you don't have one already. It is used to unlock your ./group_vars/secrets.yml file. Make sure you hang onto the password-file, if you don't you'll loose access to the content of secrets.yml.

Your AWX token is preserved in this secrets.yml file for now but other variables could be added to it if you consider them sensitive.

To preserve the decrypted variable file, run the playbook with the 'ansible-vault,preserve-vault-file' tags. This will cause a plain-text version to remain available at ./group_vars/plain-text.yml, you can make changes to this plain-text file and re-encrypt it by simply running this playbook again with the 'ansible-vault' tag.


To cycle your Ansible Vault password-file, do the following:

1) Decrypt the old secrets.yml file to plain-text.yml:

`/ehi-bootsrap-playbook$ ansible-playbook -v -i ./inventory/hosts -t "ansible-vault,preserve-vault-file" setup.yml`


2) Then preserve a copy of the old password file:

`/ehi-bootsrap-playbook$ mv ./vault/password-file ./vault/password-file-old`


3) Then check if the ./group_vars/plain-text.yml file is present. If it is delete your current secrets.yml file, we'll be re-encrypting this with the new password-file:

`/ehi-bootsrap-playbook$ rm ./group_vars/secrets.yml`


4) Re-run the playbook with the 'create-vault-password-file' and 'ansible-vault' tags:

`/ehi-bootsrap-playbook$ ansible-playbook -v -i ./inventory/hosts -t "create-vault-password-file,ansible-vault" setup.yml`


Congradulations! your vault-password file has been cycled and your secrets.yml is now encrypted with it!

# ? what if all this could happen with a 'cycle-password-file'