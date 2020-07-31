from typing import Optional

from sc2 import UnitTypeId
from sharpy.plans.acts import GridBuilding


class Building(GridBuilding):
    def __init__(
        self,
        unit_type: UnitTypeId,
        to_count: int = 1,
        iterator: Optional[int] = None,
        priority: bool = False,
        allow_wall: bool = True,
    ):

        super().__init__(unit_type, to_count, iterator, priority, allow_wall)
        self.consider_worker_production = False
