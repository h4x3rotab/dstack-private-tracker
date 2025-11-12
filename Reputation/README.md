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

### Interactive local test (Factory + Reputation)

This quick script shows how to deploy the **Factory**, create a **genesis Reputation** (no referrer), add/update a user, create a **child Reputation** that references the first one, migrate the user, and update again — all with `cast` on a local Anvil chain.

> **Prereqs**: Foundry (`anvil`, `forge`, `cast`), plus `jq` and `awk`.

#### 0) Start a local chain

```bash
anvil
```

Keep it running in a separate terminal.

#### 1) Set env and deploy the Factory

Run from `Reputation/`.

```bash
export RPC=http://127.0.0.1:8545
export PK0=0x<copy first private key from anvil output>

FACTORY=$(forge create src/factory.sol:ReputationFactory \
  --rpc-url "$RPC" \
  --private-key "$PK0" \
  --broadcast \
  --json | jq -r .deployedTo)

echo "FACTORY=$FACTORY"
```

#### 2) Create the initial Reputation (no referrer) and capture its address as `REP1`

We emit a `ReputationCreated(address,address,address,bytes)` event; the newly created Reputation address is the **first argument** and is ABI-encoded in the log **data**. The pipeline below extracts that address.

```bash
REP1=$(
cast send "$FACTORY" "createReputation(address,bytes)" \
  0x0000000000000000000000000000000000000000 0x \
  --rpc-url "$RPC" --private-key "$PK0" | \
  grep '^logs ' | cut -c 6- | jq -r '.[0].data' | awk '{print "0x" substr($0, 27, 40)}'
)

echo "REP1=$REP1"
cast code "$REP1" --rpc-url "$RPC"     # should NOT be 0x
```

_(If your shell shows a different `cast send` output shape, you can also decode via the transaction receipt and topic0; see comments in the codebase.)_

#### 3) Add a user to `REP1` and update their numbers

We treat the "ratio" as the pair `(downloadSize, uploadSize)` stored on-chain.

```bash
USER="alice"
SALT="salt1"
PASSHASH=$(cast keccak "p@ss|$SALT")  # 32-byte hex

# initial values
DOWN=1000
UP=500

# Add user on REP1
cast send "$REP1" "addUser(string,string,bytes32,uint256,uint256)" \
  "$USER" "$SALT" "$PASSHASH" "$DOWN" "$UP" \
  --rpc-url "$RPC" --private-key "$PK0"

# Read back
cast call "$REP1" "getUserData(string)((string,string,bytes32,uint256,uint256))" "$USER" --rpc-url "$RPC"

# Update numbers (ratio = 2400/800 = 3)
DOWN=2400
UP=800
cast send "$REP1" "updateUser(string,uint256,uint256)" "$USER" "$DOWN" "$UP" \
  --rpc-url "$RPC" --private-key "$PK0"

# Confirm
cast call "$REP1" "getUserData(string)((string,string,bytes32,uint256,uint256))" "$USER" --rpc-url "$RPC"
```

#### 4) Create a child Reputation that references `REP1` and capture as `REP2`

```bash
REP2=$(
cast send "$FACTORY" "createReputation(address,bytes)" \
  "$REP1" 0x \
  --rpc-url "$RPC" --private-key "$PK0" | \
  grep '^logs ' | cut -c 6- | jq -r '.[0].data' | awk '{print "0x" substr($0, 27, 40)}'
)

echo "REP2=$REP2"
cast code "$REP2" --rpc-url "$RPC"     # should NOT be 0x
```

#### 5) Migrate the user from `REP1` → `REP2` and verify

```bash
# Before migration (likely empty on REP2)
cast call "$REP2" "getUserData(string)((string,string,bytes32,uint256,uint256))" "$USER" --rpc-url "$RPC"

# Migrate (single-hop copy from referrer)
cast send "$REP2" "migrateUserData(string)" "$USER" --rpc-url "$RPC" --private-key "$PK0"

# After migration — should match REP1's latest (DOWN=2400, UP=800)
cast call "$REP2" "getUserData(string)((string,string,bytes32,uint256,uint256))" "$USER" --rpc-url "$RPC"
```

#### 6) Update the user again on `REP2`

```bash
DOWN=3600
UP=900
cast send "$REP2" "updateUser(string,uint256,uint256)" "$USER" "$DOWN" "$UP" \
  --rpc-url "$RPC" --private-key "$PK0"

# Confirm on REP2
cast call "$REP2" "getUserData(string)((string,string,bytes32,uint256,uint256))" "$USER" --rpc-url "$RPC"
```
