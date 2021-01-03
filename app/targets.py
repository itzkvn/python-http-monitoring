import time
import asyncio
from asyncio import TimeoutError

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
    REQUEST_DEFAULT_HTTP_CODE,
)


class TargetStatus(BaseModel):
    display: str
    url: str
    response_http_code: int
    expected_http_code: int
    elapsed: float
    error: Optional[str]


def get_targets():
    # TODO: Proper "schema" validation
    with open(TARGETS_FILE) as file:
        targets = yaml.safe_load(file.read())
    if not all(
        [target.get("display") and target.get("url") for target in targets["targets"]]
    ):
        raise AssertionError(
            f"Couldn't find 'display' or 'url' for all targets in {TARGETS_FILE}"
        )
    return targets


async def get_target_status(target: dict):
    display = target["display"]
    url = target["url"]
    expected_http_code = target.get("expected_http_code") or REQUEST_DEFAULT_HTTP_CODE

    for RETRY_NUMBER in range(REQUEST_RETRIES):
        error = None
        start = time.monotonic()
        try:
            async with SESSION.get(
                url=url, allow_redirects=False, timeout=REQUEST_TIMEOUT
            ) as response:
                response_http_code = response.status
        except ClientConnectorError as ex:
            response_http_code = -1
            error = str(ex) or str(type(ex))
        except TimeoutError as ex:
            response_http_code = -1
            error = f"Request timeout after {REQUEST_TIMEOUT}s"

        elapsed = round(time.monotonic() - start, 2)

        if not error:
            break

        # Wait potential flapping time.
        await asyncio.sleep(REQUEST_RETRIES_WAIT)


        # If we already know the error no need for http comparison.
        if error:
            continue

        if response_http_code != expected_http_code:
            error = "Status code does not match expected code"
            continue

    return TargetStatus(
        display=display,
        url=url,
        response_http_code=response_http_code,
        expected_http_code=expected_http_code,
        elapsed=elapsed,
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