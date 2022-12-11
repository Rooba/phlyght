from asyncio import get_running_loop, sleep, create_task
from uuid import UUID

from phlyght import HueEntsV2, Router
from phlyght import models
from rich import print
from random import random, randint

from uvloop import install

install()


class HueRouter(Router):
    async def on_light_update(self, light: HueEntsV2.Light):
        print(f"A light was updated: {light}")

    async def on_button_update(self, button: HueEntsV2.Button):
        print(f"A button was pressed: {button}")

    async def on_grouped_light_update(self, grouped_light: HueEntsV2.GroupedLight):
        print(f"A grouped light was updated: {grouped_light}")

    async def on_ready(self):
        create_task(self._random_cycle("1795db24-4b81-4763-a6db-1d0d44373599"))
        await sleep(0.3)
        create_task(self._random_cycle("3c9d5ba7-ea43-45f8-a823-f3b32168776d"))
        await sleep(0.3)
        create_task(self._random_cycle("93a1533e-bfeb-4103-a150-180943a3ff3b"))
        await sleep(0.3)
        create_task(self._random_cycle("a9093d1b-8508-4311-8d8a-62b5389dae30"))
        await sleep(0.3)
        create_task(self._random_cycle("e3b73801-9040-440c-9284-fa16ac3d8713"))
        await sleep(0.3)

    async def _random_cycle(self, id: str):
        while get_running_loop().is_running():
            await self.set_light(
                id,
                HueEntsV2.Light(
                    color=models.LightColor(xy=models._XY(x=random(), y=random())),
                    on=models.On(on=True),
                    dimming=models.Dimming(brightness=randint(25, 100)),
                    effects=models.LightEffect(effect="candle"),
                ),
            )
            await sleep(0.5)
        return


router = HueRouter(
    "your access key",
    bridge_ip="https://your gateway address",
    max_cache_size=1024,
)
router.run()
