import asyncio

import httpx
import loguru

from utils import load_cookies

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

limit = asyncio.Semaphore(5)

cookies = load_cookies()

timeout = httpx.Timeout(10, connect=10, read=20)


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    global limit
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            response = await client.post(url, data=data, cookies=cookies, headers=headers, *args, **kwargs)
            loguru.logger.info(f'[POST] {url} {str(data)[:15]} {
            response.status_code}')
            response.json()
            return response


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            response = await client.get(url, params=params, cookies=cookies, headers=headers, *args, **kwargs)
            loguru.logger.info(f'[GET] {url} {response.status_code}')
            return response


def reload_cookies():
    global cookies
    cookies = load_cookies()