from asyncio import get_running_loop, sleep

from phlyght import HueEntsV2, Router, Attributes, _XY
from rich import print
from random import random

try:
    from uvloop import install

    install()
except ImportError:
    ...


class HueRouter(Router):
    async def on_light_update(self, light: HueEntsV2.Light):
        print(f"A light was updated: {light}")
        return True

    async def on_button_update(self, button: HueEntsV2.Button):
        print(f"A button was pressed: {button}")
        return True

    async def _shift(self, light: HueEntsV2.Light):
        while get_running_loop().is_running():
            light.color = Attributes.LightColor(xy=_XY(x=random(), y=random()))
            light.dimming = Attributes.Dimming(brightness=100.0, min_dim_level=0.2)
            # We can modify the attributes of the lights and send the light object as the parameter to set_light()
            await self.set_light(
                light.id,
                light,
            )
            await sleep(0.3)
            # Could potentially get more in / at a faster update rate but its getting pretty close to making the bridge unresponsive at this rate

    async def on_ready(self):  # This will be called once, right after startup
        for light in [
            self.entry,
            self.bed,
            self.kitchen,
            self.bathroom,
            self.footrest,
        ]:
            # These are all aliases defined in the config, accessible as an attribute using the name on the router
            self.new_task(self._shift(light))
            await sleep(0.5)


router = HueRouter(
    "Your API Key",
    bridge_ip="https://192.168.1.1",
    max_cache_size=64,
)
router.run()
