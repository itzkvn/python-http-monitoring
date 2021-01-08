import time
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from settings import REQUEST_RETRIES, REQUEST_RETRIES_WAIT, REQUEST_TIMEOUT

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


@app.get("/target/status", response_class=HTMLResponse)
async def get_targets_status(request: Request):
    start = time.monotonic()
    try:
        targets_status = await targets.get_targets_status()
    except Exception as ex:
        return templates.TemplateResponse(
            "500_template.html",
            {
                "request": request,
                "error": str(ex) or str(type(ex)),
            },
        )
    elapsed = round(time.monotonic() - start, 2) * 1000

    return templates.TemplateResponse(
        "targets_template.html",
        {
            "request": request,
            "targets": targets_status,
            "elapsed": f"{elapsed:.2f}",
            "requests_info": REQUESTS_INFO,
            "now": datetime.now().strftime("%a %b %d %H:%M:%S %Y"),
        },
    )