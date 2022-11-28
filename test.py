from asyncio import run
from rich import print

from phlyght.api import Router


async def main():
    router = Router("Your user key with the hue bridge")

    lights = await router.get_lights()
    for light in lights:
        detailed_light = await router.get_light(light_id=str(light.id))
        print(detailed_light)

    scenes = await router.get_scenes()
    for scene in scenes:
        print(scene)

    devices = await router.get_devices()
    for device in devices:
        print(device)


run(main())
