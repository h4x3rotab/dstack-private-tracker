# Based on https://github.com/Phala-Network/phala-cloud-python-starter/blob/main/main.py
from dstack_sdk import TappdClient
from dstack_sdk.ethereum import to_account_secure

def quote_and_ethereum_account():
    tdx_quote = TappdClient().tdx_quote('test')
    key = TappdClient().derive_key('test')
    account = to_account_secure(key)
    return tdx_quote, account, key

# Async stuff
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from dstack_sdk import AsyncTappdClient
app = FastAPI()

@app.get("/address")
async def address():
    _, account, _ = quote_and_ethereum_account()
    return { 'address': account.address }

@app.get("/key")
async def key():
    _, account, key = quote_and_ethereum_account()
    return key

from web3 import Web3

@app.get("/factory")
async def factory():
    _, account, key = quote_and_ethereum_account()
    address = '0xEAb2770C98103ff12ca975a4Ab94f054238358B6'
    abi = '[{"type":"function","name":"createReputation","inputs":[{"name":"_referrerReputation","type":"address","internalType":"address"}],"outputs":[{"name":"","type":"address","internalType":"address"}],"stateMutability":"nonpayable"},{"type":"event","name":"ReputationCreated","inputs":[{"name":"newReputationAddress","type":"address","indexed":false,"internalType":"address"},{"name":"owner","type":"address","indexed":false,"internalType":"address"},{"name":"referrer","type":"address","indexed":false,"internalType":"address"}],"anonymous":false}]'
    w3 = Web3(Web3.HTTPProvider("https://ethereum-sepolia-rpc.publicnode.com"))
    factory = w3.eth.contract(address=address, abi=abi)
    unsent_tx = factory.functions.createReputation('0x0000000000000000000000000000000000000000').build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address),
    })
    signed_tx = account.sign_transaction(unsent_tx)
    w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    return True


@app.get("/tdx_quote")
async def tdx_quote():
    tdx_quote, _, _ = quote_and_ethereum_account()
    return tdx_quote

@app.get("/")
async def get_info():
    client = AsyncTappdClient()
    info = await client.info()
    return JSONResponse(content=info.model_dump())
