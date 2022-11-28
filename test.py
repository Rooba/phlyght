from asyncio import run
from rich import print

from phlyght.api import Router


async def main():
    router = Router("ur api key")
    lights = await router.get_lights()
    print(lights.json())


run(main())
