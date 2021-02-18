from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import Response
import hmac
import os
import json

GITHUB_SECRET = bytes(os.environ['GITHUB_WEBHOOKS_SECRET'], 'ascii')
SCRIPT_PATH = os.environ['GITHUB_WEBHOOKS_SCRIPT']

app = FastAPI()


@app.post('/gh_webhook')
async def handle_gh_webhook(req: Request):
    signature = req.headers.get('X-Hub-Signature-256')
    if signature is None:
        return Response(status_code=401)

    body_bytes = await req.body()
    hashed_body = hmac.digest(
        GITHUB_SECRET,
        body_bytes,
        'SHA256'
    )

    if not hmac.compare_digest(signature, hashed_body):
        return Response(status_code=401)

    print(f'Received verified webhook: {str(body_bytes, "UTF-8")}')
    os.system(SCRIPT_PATH)
    return Response(status_code=200)
