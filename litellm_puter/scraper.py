import asyncio
import random
import re
from pprint import pprint
from typing import Optional

import httpx
from patchright._impl._errors import TargetClosedError
from patchright.async_api import async_playwright, expect, Request, Response


class AsyncPuterWebLogin:
    def __init__(self, debug: bool = False, headless: Optional[bool] = False, useragent: Optional[str] = None):
        self.debug = debug
        self.browser_type = "chrome"
        self.headless = headless
        self.useragent = useragent
        self.browser_args = []
        if useragent:
            self.browser_args.append(f"--user-agent={useragent}")
        self.stop = False
        self.token = None

    async def get_temp_token(self, url: str = 'https://puter.com', max_attempts: int = 10,
                             proxy: str | None = None) -> str | None:
        locator_str = "//*[@id='captcha-widget-turnstile-challenge-modal']"
        timeout = 1000 * 60 * 10
        url_with_slash = url + "/" if not url.endswith("/") else url
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel=self.browser_type,
                headless=self.headless,
                args=self.browser_args,
            )
            if proxy:
                context = await browser.new_context(proxy={"server": proxy})
            else:
                context = browser.contexts[0] if len(browser.contexts) else await browser.new_context()

            # await context.clear_cookies()
            page = context.pages[0] if len(context.pages) else await context.new_page()

            try:
                await page.goto(url_with_slash, timeout=0, wait_until='domcontentloaded')
            except Exception as e:
                print(e)
                return
            page.on("requestfinished", self.on_requestfinished)
            locator = page.locator(locator_str)
            modal = False
            click = False
            turnstile_response = False
            for _ in range(max_attempts):
                if self.stop:
                    return self.token
                try:
                    if not modal:
                        await locator.wait_for(state="attached", timeout=0)
                        modal = True
                        await page.locator("//*[@data-sitekey='0x4AAAAAABvMyOLo9EwjFVzC']").wait_for(state="attached",
                                                                                                     timeout=100)
                    await page.wait_for_timeout(random.randint(700, 3000))
                    if not click:
                        try:
                            await locator.click(timeout=500)
                        except:
                            pass
                        try:
                            await locator.wait_for(state="detached", timeout=500)
                            click = True
                        except:
                            pass
                    try:
                        if not turnstile_response:
                            await expect(page.locator("[name=cf-turnstile-response]")).to_have_value(re.compile(r"."),
                                                                                                     timeout=500)
                            turnstile_response = True
                    except:
                        pass
                    for cookie in await context.cookies():
                        if cookie['name'] == 'puter_auth_token':
                            return cookie['value']
                    if self.token:
                        return self.token
                except TargetClosedError as e:
                    return
                except Exception as e:
                    print(e)
                    continue
            while not self.stop:
                asyncio.wait(1000)
            await browser.close()
            return self.token

    async def on_requestfinished(self, request: Request):
        if 'puter.com/signup' in request.url:
            try:
                response: Response = await request.response()
                # await response.finished()
                print(str(await response.body()))
                r_json = await response.json()
                print(r_json)
                self.token = r_json['token']
            except:
                pass
            self.stop = True

proxy_list = []


async def login(url: str = 'https://puter.com', proxy=None):
    # with Xvfb(width=1920, height=1080) as xvfb:
    token = None
    if True:
        try:
            # launch stuff inside virtual display here
            solver = AsyncPuterWebLogin(headless=False, debug=True)
            solver.browser_type = 'chrome'
            token = await solver.get_temp_token(proxy=proxy, max_attempts=150)
        finally:
            # xvfb.stop()
            pass
    print(token)
    with open('token.txt', 'a') as f:
        if token:
            f.writelines([token, "\n"])


async def main():
    res = await httpx.AsyncClient().get(
        url='https://cdn.jsdelivr.net/gh/proxifly/free-proxy-list@main/proxies/protocols/socks5/data.txt')
    for proxy in res.content.decode().splitlines():
        print(proxy)
        if 'socks4://' in proxy:
            proxy = proxy.replace('socks4', 'socks')
        try:
            await httpx.AsyncClient(proxy=proxy).get(url='https://puter.com')
            proxy_list.append(proxy)
            await login(proxy=proxy)
        except Exception as e:
            print(e)
    pprint(proxy_list)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)