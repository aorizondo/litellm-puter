from litellm_puter.provider import AsyncPuterWebLogin
import asyncio
from xvfbwrapper import Xvfb

async def login(url: str = 'https://puter.com',):
    with Xvfb(width=1920, height=1080) as xvfb:
        try:
            # launch stuff inside virtual display here
            solver = AsyncPuterWebLogin(headless=False, debug=True)
            token = await solver.get_temp_token(proxy="http://10.14.0.13:3128")
        finally:
            # xvfb.stop()
            pass
    print(token)
    with open('token.txt', 'a') as f:
        if token:
            f.writelines([token, "\n"])
async def main():
    for x in range(10):
        await login()
        await asyncio.sleep(10)
if __name__ == '__main__':
    asyncio.run(main(), debug=True)