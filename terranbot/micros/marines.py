from sc2 import UnitTypeId
from sc2.units import Units
from sharpy.managers.combat2 import Action, MoveType
from sharpy.managers.combat2.terran import MicroBio


class MarineMicro(MicroBio):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        action = super().group_solve_combat(units, current_command)
        marine_center = units.center

        if (
            self.move_type == MoveType.Assault
            or self.move_type == MoveType.SearchAndDestroy
            and self.engaged_power.ground_presence > 5
        ):
            tanks = self.group.units.of_type({UnitTypeId.SIEGETANKSIEGED, UnitTypeId.SIEGETANK})
            if tanks:
                tank_center = tanks.center
                d = marine_center.distance_to(tank_center)
                if d > 7:
                    return Action(tank_center, False)
        return action
