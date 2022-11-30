from asyncio import run, get_running_loop, sleep

from phlyght.http import Router
from phlyght import models

try:
    from rich import print  # noqa
except ImportError:
    ...


async def main():
    router = Router("Your Bridge Auth key", bridge_ip="https://192.168.1.1")
    # this will start listening in the background for all events sent out by the bridge
    router.subscribe()

    while True:
        # this will query for all lights every 10 seconds
        print(await router.get_lights)
        await sleep(10.0)


run(main())
