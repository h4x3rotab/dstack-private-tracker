# dstack-private-tracker

## Deployments

Check [docker-compose.yml](./docker-compose.yml)

## SSH into the CVM

SSH config:

```
Host my-dstack-app
    HostName 974bd8cf5824ef6cd318a2994270720ac7aa14bc-22.dstack-prod5.phala.network
    Port 443
    User root
    ProxyCommand openssl s_client -quiet -connect %h:%p
```

Then: `ssh my-dstack-app`