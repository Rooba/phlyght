from asyncio import get_running_loop, sleep
from pathlib import Path
from phlyght import HueEntsV2, Router, Attributes, _XY
from random import random


class HueRouter(Router):
    async def on_light_update(self, light: HueEntsV2.Light):
        return True

    async def on_button_update(self, button: HueEntsV2.Button):
        if (
            button.id == self.ra_button.id
            and button.button.last_event == "initial_press"
        ):
            for l in [
                self.curtain,
                self.lamp,
                self.desk,
                self.lightbar_under,
                self.lightbar_monitor,
            ]:
                l.color = Attributes.LightColor(xy=_XY(x=random(), y=random()))
                if l.dimming.brightness < 30:
                    l.dimming = Attributes.Dimming(brightness=75.0)
                else:
                    l.dimming = Attributes.Dimming(brightness=5.0)

                await l.update()
        return True

    async def on_grouped_light_update(self, grouped_light: HueEntsV2.GroupedLight):
        return True

    async def on_motion_update(self, motion: HueEntsV2.Motion):
        return True

    async def _shift(
        self, light: HueEntsV2.Light
    ):  # this wont be ran unless the lines in on_ready are uncommented
        while get_running_loop().is_running():
            # We can set the values by explicitly setting the attributes
            light.color = Attributes.LightColor(xy=_XY(x=random(), y=random()))
            await light.update()
            await sleep(0.3)

    async def on_ready(self):  # This will be called once, right after startup
        await self.dump(Path("config.yaml"))
        # don't use this if prone to seizures
        # # for l in [
        #     self.curtain,
        #     self.lamp,
        #     self.desk,
        #     self.lightbar_under,
        #     self.lightbar_monitor,
        # ]:
        #     # These are all aliases defined in the config, accessible as an attribute using the name on the router
        #     self.new_task(self._shift(l))
        #     await sleep(0.5)
        ...


router = HueRouter(
    "TzPrxDf9hyW5oR5lvUaG2Zn4Hlbp2yFg7ue2ynzI",  # Fill this in with [[YOUR API KEY]] otherwise it wont run
    bridge_ip="https://192.168.1.1",  # Your bridge IP here
    max_cache_size=64,
)
router.run()
