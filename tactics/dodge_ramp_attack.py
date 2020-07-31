from sharpy.general.zone import Zone
from sharpy.managers.combat2 import MoveType
from sharpy.plans.tactics import PlanZoneAttack
from sc2.position import Point2


class DodgeRampAttack(PlanZoneAttack):
    async def execute(self) -> bool:
        enemy_main: Zone = self.knowledge.expansion_zones[-1]
        enemy_natural: Zone = self.knowledge.expansion_zones[-2]

        if enemy_main.is_enemys and not enemy_natural.is_enemys:
            # enemy controls their main, but does not control their natural
            for effect in self.ai.state.effects:
                if effect.id != "FORCEFIELD":
                    continue
                pos: Point2 = self.knowledge.enemy_base_ramp.bottom_center
                for epos in effect.positions:
                    if pos.distance_to_point2(epos) < 5:
                        return await self.small_retreat(enemy_natural)

        return await super().execute()

    async def small_retreat(self, natural: Zone):
        attacking_units = self.knowledge.roles.attacking_units


        for unit in attacking_units:
            self.combat.add_unit(unit)

        path = natural.paths.get(0, None)
        target = natural.center_location

        if path and path.distance > 50:
            target = path.get_index(8)

        self.combat.execute(target, MoveType.DefensiveRetreat)
        return False
