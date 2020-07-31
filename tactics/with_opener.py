from typing import Union, Callable, List

from sharpy.plans import BuildOrder
from sharpy.plans.acts import ActBase


class WithOpener(BuildOrder):
    def __init__(
        self,
        orders: Union[
            Union[ActBase, Callable[["Knowledge"], bool]], List[Union[ActBase, Callable[["Knowledge"], bool]]]
        ],
        *argv
    ):
        super().__init__(orders, *argv)
        self.opener = self.orders[0]
        self.opener_completed = False

    async def execute(self) -> bool:
        if self.opener_completed:
            return await super().execute()
        else:
            if await self.opener.execute():
                self.opener_completed = True
            return False
