import time
from datetime import datetime

import aiohttp

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from settings import SESSION, REQUEST_RETRIES, REQUEST_RETRIES_WAIT, REQUEST_TIMEOUT

import targets

REQUESTS_INFO = {
    "retries": REQUEST_RETRIES,
    "retries_wait": REQUEST_RETRIES_WAIT,
    "timeout": REQUEST_TIMEOUT,
}

app = FastAPI(
    title="python-http-monitoring",
    description='HTTP(s) "monitoring" webpage via FastAPI+Jinja2. Inspired by https://github.com/RaymiiOrg/bash-http-monitoring',
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.on_event("shutdown")
async def startup_event():
    await SESSION.close()

@app.get("/target/status", response_class=HTMLResponse)
async def get_targets_status(request: Request):
    start = time.monotonic()
    targets_status = await targets.get_targets_status()
    elapsed = round(time.monotonic() - start, 2) * 1000

    return templates.TemplateResponse(
        "target_status.html",
        {
            "request": request,
            "targets": targets_status,
            "elapsed": f"{elapsed:.2f}",
            "requests_info": REQUESTS_INFO,
            "now": datetime.now().strftime("%a %b %d %H:%M:%S %Y"),
        },
    )