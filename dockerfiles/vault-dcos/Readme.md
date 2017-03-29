# Vault on DC/OS

This is an example of how to run [HashiCorp's Vault](https://github.com/hashicorp/vault) on DC/OS. By default, it's configured in HA mode with ZooKeeper as the backend.

## Running on DC/OS

### Step 1: Launch Vault server
Save the following JSON as `vault.json`:
```json
{
  "id": "vault",
  "cpus": 1,
  "mem": 1000,
  "requirePorts":true,
  "instances": 1,
  "container": {
    "type": "DOCKER",
    "docker": {
      "image": "geoint/scale-vault",
      "network": "HOST",
      "forcePullImage": true
    }
  },
  "healthChecks": [{
      "protocol": "TCP",
      "portIndex": 0,
      "timeoutSeconds": 10,
      "gracePeriodSeconds": 10,
      "intervalSeconds": 2,
      "maxConsecutiveFailures": 10
  }]
}
```
Now launch on Marathon:
```
$ dcos marathon app add vault.json
```

**Note**: you may configure some parameters via environment variables, from the wrapper script [`run-vault`](run-vault). You may set the following environment variables:
 * VAULT_TLS_KEY: TLS key file contents
 * VAULT_TLS_CERT: TLS cert file contents
 * VAULT_CONFIG_HCL: HCL config file contents
 * VAULT_CONFIG_JSON: JSON config file contents

### Step 2: Initialize the vault
SSH into one of the DC/OS cluster nodes, and initialize the vault with the following:
```
$ docker run -e "VAULT_SKIP_VERIFY=true" -e "VAULT_ADDR=vault.marathon.l4lb.thisdcos.directory:8200" --entrypoint=vault -t geoint/scale-vault init
Key 1: 62b6e5c157446c05c067bb41fadf931fd8f422f4af2a4c0ee056acbd5a89d3ed01
Key 2: a065dbfd663c5a619bfdc74ebce68051f9e7004d19c67bc6726daf49e209d4ea02
Key 3: 91e97d22436508a67905e535f636bb3e4550a8ad77b9f69da43717baa4012b5b03
Key 4: dcef79c03925db47c8494decfe959be39079ac987ac774fc5fb7148528dcb33a04
Key 5: ed63df1f1c7c89802ab16f97b445a08c2cce047814b8f9a789edac766ed44c8b05
Initial Root Token: 11aaf733-f280-fbaf-251d-69b9606bf4fa

Vault initialized with 5 keys and a key threshold of 3. Please
securely distribute the above keys. When the Vault is re-sealed,
restarted, or stopped, you must provide at least 3 of these keys
to unseal it again.

Vault does not store the master key. Without at least 3 keys,
your Vault will remain permanently sealed.
```
After, check to make sure it was properly initialized:
```
$ docker run -e "VAULT_SKIP_VERIFY=true" -e "VAULT_ADDR=vault.marathon.l4lb.thisdcos.directory:8200" --entrypoint=vault -t geoint/scale-vault status
Sealed: true
Key Shares: 5
Key Threshold: 3
Unseal Progress: 0

High-Availability Enabled: true
	Mode: sealed
```
### Step 3: Unseal your vault
Repeat the following command 3 times, pasting a separate key each time:
```
$ docker run -i -e "VAULT_SKIP_VERIFY=true" -e "VAULT_ADDR=vault.marathon.l4lb.thisdcos.directory:8200" --entrypoint=vault -t geoint/scale-vault unseal
Key (will be hidden):
Sealed: true
Key Shares: 5
Key Threshold: 3
Unseal Progress: 1
```
Once it says `Sealed: false`, your vault is unsealed.

**Note**: You'll have to run the command above with each key for each instance of Vault you're running. For example, if you run 3 instances (in HA mode), you'll have to repeatedly run the command and enter each key 3 times to unseal all 3 Vault instances. That's a total of 9 commands, if you're counting.
### Step 4: Start using your vault!
Run an interactive shell to test your vault:
```
$ docker run -i -e "VAULT_SKIP_VERIFY=true" -e "VAULT_ADDR=vault.marathon.l4lb.thisdcos.directory:8200" --entrypoint=/bin/sh -t geoint/scale-vault
$ vault auth 11aaf733-f280-fbaf-251d-69b9606bf4fa # use root token from init
Successfully authenticated!
token: 11aaf733-f280-fbaf-251d-69b9606bf4fa
token_duration: 0
token_policies: [root]
$ vault token-create
Key            	Value
token          	d72b4cc0-a0a2-9be8-7c69-8fde5fe8bbe5
token_duration 	0
token_renewable	false
token_policies 	[root]
$ vault write secret/hello value=world
Success! Data written to: secret/hello
$ vault read secret/hello
Key           	Value
lease_duration	2592000
value         	world
```
For more examples, take a look at the [Vault getting started guide](https://vaultproject.io/intro/getting-started/install.html).

## Next steps
After you get Vault up and running, you may want to consider running multiple instances, and enabling discovery via [marathon-lb](https://github.com/mesosphere/marathon-lb).
