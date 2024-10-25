import asyncio
import time
from json import JSONDecodeError

import httpx
import loguru

from utils import load_cookies

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

limit = asyncio.Semaphore(5)

cookies = {
}

cookies = load_cookies()

base_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'DNT': '1',
    'Origin': 'http://hlt-admin.honglitong.cn',
    'Pragma': 'no-cache',
    'Referer': 'http://hlt-admin.honglitong.cn/goods/add/page',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

timeout = httpx.Timeout(10, connect=10, read=20)


async def post(url, data, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_header = headers
    if headers is not None:
        new_header.update(headers)
    global limit
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            try:
                response = await client.post(url, data=data, cookies=cookies, headers=new_header, *args, **kwargs)
                loguru.logger.info(f'[POST] {url} {str(data)[:15]} {
                    response.status_code}')
                response.json()
                return response
            except JSONDecodeError as e:
                if '登录' in response.text:
                    loguru.logger.error(f'需要登录！')
                    raise Exception(f'需要登录！')
                raise Exception(f'JSONDecodeError: {e} {response.text}')
            except Exception as e:
                loguru.logger.error(str(type(e)), e)
                time.sleep(1)
                return await post(url, data, headers, *args, **kwargs)


async def get(url, params: dict = None, headers: dict = None, *args, **kwargs) -> httpx.Response:
    new_headers = base_headers
    if headers is not None:
        new_headers.update(headers)
    global limit
    async with limit:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=timeout) as client:
            try:
                response = await client.get(url, params=params, cookies=cookies, headers=new_headers, *args, **kwargs)
                loguru.logger.info(f'[GET] {url} {response.status_code}')

                assert '登录' not in response.text, '需要登录！'
                return response
            except AssertionError as e:
                loguru.logger.error(e)
                raise Exception(e)
            except Exception as e:
                loguru.logger.error(e)
                time.sleep(1)
                return await get(url, params, *args, **kwargs)


def reload_cookies():
    global cookies
    cookies = load_cookies()
