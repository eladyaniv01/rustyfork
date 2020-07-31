from sharpy.general.extended_ramp import ExtendedRamp, RampPosition
from sharpy.general.zone import Zone
from sharpy.plans.acts import ActBase, BuildPosition
from sc2 import UnitTypeId, Race, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class BlockMain(BuildPosition):

    def __init__(self):
        self.completed = False
        self.created_once = False
        self.center: Point2 = None
        self.danger = False
        super().__init__(UnitTypeId.PYLON, None, True, False)

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        ramp: ExtendedRamp = self.knowledge.base_ramp
        self.position = ramp.positions.get(RampPosition.PylonBlockVsProtoss, None)
        natural: Zone = self.knowledge.expansion_zones[1]
        self.center = natural.center_location

    async def execute(self) -> bool:
        if not self.position or self.knowledge.enemy_race != Race.Protoss:
            return True

        pylons: Units = self.cache.own_in_range(self.position, 1).of_type(UnitTypeId.PYLON)
        if pylons:
            self.created_once = True
            pylon = pylons[0]

            if pylon.build_progress > 0.95:
                self.do(pylon(AbilityId.CANCEL_BUILDINPROGRESS))
                self.completed = True
                return True

        if self.created_once:
            return True

        enemies = self.cache.enemy_in_range(self.center, 35)
        adept_danger = enemies.of_type({UnitTypeId.ADEPT, UnitTypeId.ADEPTPHASESHIFT})

        if len(adept_danger) > 1 and len(adept_danger) + 1 >= len(enemies):
            self.danger = True  # Probably an adept dive

        if self.danger:
            return await super().execute()

        return True
