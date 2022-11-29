from asyncio import run, sleep

from phlyght.api import Router

try:
    from rich import print  # noqa
except ImportError:
    ...


async def main():
    router = Router("ur key")

    print(await router.get_lights())
    print(await router.get_scenes())
    print(await router.get_devices())
    await router.get_rooms()
    await router.get_zones()
    await router.get_bridge_homes()
    await router.get_grouped_lights()
    await router.get_bridges()
    await router.get_device_powers()
    await router.get_zigbee_connectivities()
    await router.get_zgb_connectivities()
    print(await router.get_motions())
    print(await router.get_temperatures())
    await router.get_light_levels()
    await router.get_buttons()
    await router.get_behavior_scripts()
    await router.get_behavior_instances()
    await router.get_geofence_clients()
    await router.get_geolocations()
    await router.get_entertainment_configurations()
    await router.get_entertainments()
    await router.get_homekits()
    await router.get_resources()
    await router._subscribe()
    while True:
        await sleep(5)


run(main())
