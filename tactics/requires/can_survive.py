from sharpy.knowledges import Knowledge
from sharpy.plans.require import RequireCustom


class CanSurvive(RequireCustom):
    def __init__(self):
        super().__init__(CanSurvive.can_survive)

    def can_survive(knowledge: Knowledge) -> bool:
        for zone in knowledge.zone_manager.expansion_zones:
            if zone.is_ours and zone.is_under_attack and zone.power_balance < -4:
                return False

        return knowledge.game_analyzer.army_can_survive


class CanSurviveSafe(RequireCustom):
    def __init__(self):
        super().__init__(CanSurvive.can_survive)

    def can_survive(knowledge: Knowledge) -> bool:
        for zone in knowledge.zone_manager.expansion_zones:
            if zone.is_ours and zone.is_under_attack and zone.power_balance < 4:
                return False

        return knowledge.game_analyzer.army_at_least_small_advantage
