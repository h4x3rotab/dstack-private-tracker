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

@app.get("/tdx_quote")
async def tdx_quote():
    tdx_quote, _, _ = quote_and_ethereum_account()
    return tdx_quote

@app.get("/")
async def get_info():
    client = AsyncTappdClient()
    info = await client.info()
    return JSONResponse(content=info.model_dump())

@app.get("/update_db")
async def update_db():
    pass

@app.get("/sync_db")
async def sync_db():
    pass
