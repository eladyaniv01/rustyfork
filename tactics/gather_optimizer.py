from typing import List, Dict, Union, Optional

from sharpy.general.zone import Zone
from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sharpy.tools import IntervalFunc
from sc2 import UnitTypeId, Race
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.knowledges import Knowledge

from sharpy.managers.roles import UnitTask
from sharpy.general.extended_power import ExtendedPower
from sc2.units import Units


class PlanGatherOptimizer(ActBase):
    """
    Moves knowledge.gather_point to the base that is closest to enemy
    """

    def __init__(self):
        self.gather_point: Point2 = None
        self.updater: IntervalFunc = None
        self.enabled = True  # Allows disabling gather point setter for proxies for example
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        # We don't need to update the gather point every frame
        self.updater = IntervalFunc(self.ai, self.update_gather_point, 0.5)
        self.gather_point = self.knowledge.gather_point

    async def execute(self) -> bool:
        if self.enabled:
            self.knowledge.gather_point = self.updater.execute()
        return True

    def update_gather_point(self) -> Point2:
        gather_point = self.knowledge.gather_point
        enemies: Units = self.knowledge.known_enemy_units
        enemies = enemies.filter(self.filter_unit)

        if not enemies:
            # impossible to figure out a enemy center
            # Let's use enemy zone gather points instead
            enemy_center = self.knowledge.enemy_start_location
            for zone in self.knowledge.enemy_expansion_zones:
                if zone.is_enemys:
                    enemy_center = zone.gather_point
        else:
            enemy_center = enemies.center

        best_distance: Optional[float] = None
        for zone in self.knowledge.expansion_zones:  # type: Zone
            if zone.is_ours:
                d = zone.gather_point.distance_to(enemy_center)
                # TODO: Use pathfinding to determine distances?
                # path = zone.paths.get(natural?)
                if best_distance is None or d < best_distance:
                    gather_point = zone.gather_point
                    best_distance = d

        return gather_point

    def filter_unit(self, unit: Unit) -> bool:
        if unit.is_structure:
            return False
        if unit.type_id in self.unit_values.combat_ignore:
            return False
        if unit.type_id in self.unit_values.worker_types:
            return False
        return True
