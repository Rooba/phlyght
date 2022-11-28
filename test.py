from asyncio import run

from phlyght.api import Router

try:
    from rich import print  # noqa
except ImportError:
    ...


async def main():
    router = Router("user api key")

    lights = await router.get_lights()
    for light in lights:
        detailed_light = await router.get_light(light_id=str(light.id))  # noqa
        print(light, detailed_light)

    scenes = await router.get_scenes()
    for scene in scenes:
        print(scene)

    devices = await router.get_devices()
    for device in devices:
        print(device)


run(main())
