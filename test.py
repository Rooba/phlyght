from asyncio import run

from phlyght.api import Router

try:
    from rich import print  # noqa
except ImportError:
    ...


async def main():
    router = Router("your api key")

    print(await router.get_lights())
    print(await router.get_scenes())
    print(await router.get_devices())
    print(await router.get_rooms())
    print(await router.get_zones())
    print(await router.get_bridge_homes())
    print(await router.get_grouped_lights())
    print(await router.get_bridges())
    print(await router.get_device_powers())
    print(await router.get_zigbee_connectivities())
    print(await router.get_zgb_connectivities())
    print(await router.get_motions())
    print(await router.get_temperatures())
    print(await router.get_light_levels())
    print(await router.get_buttons())
    print(await router.get_behavior_scripts())
    print(await router.get_behavior_instances())
    print(await router.get_geofence_clients())
    print(await router.get_geolocations())
    print(await router.get_entertainment_configurations())
    print(await router.get_entertainments())
    print(await router.get_homekits())
    print(await router.get_resources())


run(main())
