from logging import basicConfig
from asyncio import get_running_loop, sleep
from phlyght import HueEntsV2, Router, Attributes, _XY
from random import random, randint
from rich import print
from loguru import logger

basicConfig(filename="phlyght.log", filemode="a+", level=10, force=True)
logger.enable("INFO")
logger.enable("ERROR")
logger.enable("WARNING")
logger.enable("DEBUG")


class HueRouter(Router):
    async def on_light_update(self, light: HueEntsV2.Light):
        # print(light)
        return True

    async def on_button_update(self, button: HueEntsV2.Button):

        if button.id == self.r_button.id:
            gradient = None
            mirek = None
            color = None
            brightness = 100.0
            alternate_brightness = False
            match button.button.last_event:
                case "short_release":
                    color = Attributes.LightColor(xy=_XY(x=random(), y=random()))
                    mirek = randint(153, 500)
                    alternate_brightness = True

                case "long_release":
                    mirek = 500
                    brightness = 100.0
                    color = Attributes.LightColor(xy=_XY(x=0.99, y=0.99))
                    gradient = Attributes.Gradient(
                        points=[
                            Attributes.ColorPointColor(
                                color=Attributes.ColorPoint(
                                    xy=Attributes.XY(x=0.99, y=0.88)
                                )
                            ),
                            Attributes.ColorPointColor(
                                color=Attributes.ColorPoint(
                                    xy=Attributes.XY(x=0.88, y=0.99)
                                )
                            ),
                        ],
                        points_capable=2,
                    )
                case "repeat":
                    brightness = 50.0
                    color = Attributes.LightColor(xy=_XY(x=random(), y=random()))

            for _light in [
                self.r_curtain,
                self.r_lamp,
                self.r_desk,
                self.r_under,
                self.r_monitor,
            ]:
                if color:
                    _light.color = color

                if brightness:
                    if alternate_brightness:
                        if _light.dimming.brightness < 30:
                            brightness = 75.0
                        else:
                            brightness = 5.0

                    _light.dimming = Attributes.Dimming(brightness=brightness)
                if mirek:
                    _light.color_temperature = Attributes.ColorTemp(mirek=mirek)
                if gradient:
                    _light.gradient = gradient
                await _light.update()

    async def on_grouped_light_update(self, grouped_light: HueEntsV2.GroupedLight):
        ...

    async def on_motion_update(self, motion: HueEntsV2.Motion):
        print(motion)

    async def _shift(self, light: HueEntsV2.Light):
        while get_running_loop().is_running():
            # We can set the values by explicitly setting the attributes
            light.color = Attributes.LightColor(xy=_XY(x=random(), y=random()))
            await light.update()
            await sleep(0.3)

    async def on_ready(self):  # This will be called once, right after startup
        logger.info("Router is ready")
        await self.dump("config.yaml")
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


router = HueRouter(max_cache_size=64)  # , hue_api_key="", hue_bridge_ip="")
router.run()
