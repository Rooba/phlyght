from asyncio import run
from rich import print

from phlyght.api import Router


async def main():
    router = Router("TzPrxDf9hyWZoR5jvUaGDZn4Hlxp2XF67ue4ynSI")
    lights = await router.get_lights()
    for light in lights:
        detailed_light = await router.get_light(light_id=str(light.id))
        print(detailed_light)


run(main())
