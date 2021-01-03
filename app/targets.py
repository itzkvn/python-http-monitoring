import time
import asyncio

import yaml
from typing import NamedTuple, Optional

from pydantic import BaseModel

from aiohttp import ClientSession
from aiohttp.client_exceptions import ClientConnectorError

from settings import (
    TARGETS_FILE,
    SESSION,
    REQUEST_RETRIES,
    REQUEST_RETRIES_WAIT,
    REQUEST_TIMEOUT,
)


class TargetStatus(BaseModel):
    display: str
    url: str
    response_http_code: int
    expected_http_code: int
    elapsed: float
    error: Optional[str]
    status: bool


def get_targets():
    # TODO: Target "schema" validation
    with open(TARGETS_FILE) as file:
        targets = yaml.safe_load(file.read())
    return targets


async def get_target_status(target: dict):
    display = target["display"]
    url = target["url"]
    expected_http_code = target["expected_http_code"]

    error = None
    for _ in range(REQUEST_RETRIES):
        start = time.monotonic()
        try:
            async with SESSION.get(
                url=url, allow_redirects=False, timeout=REQUEST_TIMEOUT
            ) as response:
                response_http_code = response.status
        except ClientConnectorError as ex:
            response_http_code = -1
            error = ex
        elapsed = round(time.monotonic() - start, 2)

        status = response_http_code == expected_http_code

        if not status and response_http_code != -1 and not error:
            error = "Status code does not match expected code"

        if status:
            break

        await asyncio.sleep(REQUEST_RETRIES_WAIT)

    return TargetStatus(
        display=display,
        url=url,
        response_http_code=response_http_code,
        expected_http_code=expected_http_code,
        elapsed=elapsed,
        status=status,
        error=error,
    )


async def get_targets_status():
    targets = get_targets()
    targets = targets["targets"]
    targets_status = await asyncio.gather(
        *(get_target_status(target=target) for target in targets)
    )

    return {
        "up": [target for target in targets_status if not target.error],
        "down": [target for target in targets_status if target.error],
    }