## Reputation Contracts

### Build

```shell
$ forge build
```

### Test

```shell
$ forge test
```

### Format

```shell
$ forge fmt
```

### Gas Snapshots

```shell
$ forge snapshot
```

### Anvil

```shell
$ anvil
```

### Deploy

```shell
$ (source ../.env; PRIVATE_KEY="$PRIVATE_KEY" forge script script/Deploy.s.sol --rpc-url "$RPC" --broadcast --verify --etherscan-api-key "$ETHERSCAN_KEY" --chain sepolia )
```

### Cast

```shell
$ cast <subcommand>
```
