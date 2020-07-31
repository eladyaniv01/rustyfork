import logging
import string
import sys
from typing import Optional, List

from sharpy.managers import ManagerBase
from sharpy.knowledges import KnowledgeBot
from sc2 import UnitTypeId
from sc2.data import Result
from sc2.unit import Unit

from terranbot.builds.tank_build import BuildTanks
from sharpy.plans.terran import *
from tactics import *
from .micros import *


class TerranBot(KnowledgeBot):
    # Save result so run_custom.py can access it.
    RESULT: Result = None

    def __init__(self, build: string = "default"):
        super().__init__("Rusty")
        self.attack = PlanZoneAttack(20)
        self.attack.retreat_multiplier = 0.4

    def configure_managers(self) -> Optional[List[ManagerBase]]:
        self.knowledge.combat_manager.default_rules.own_group_distance = 13
        self.knowledge.combat_manager.default_rules.unit_micros[UnitTypeId.MARINE] = MarineMicro()
        self.knowledge.roles.set_tag_each_iteration = True

    async def create_plan(self) -> BuildOrder:
        self.knowledge.data_manager.set_build("tanks")
        worker_scout = Step(None, WorkerScout(), skip_until=UnitExists(UnitTypeId.BARRACKS, 1))

        tactics = [
            PlanGatherOptimizer(),
            WorkerRallyPoint(),
            PlanCancelBuilding(),
            LowerDepots(),
            worker_scout,
            DistributeWorkers(),
            ScanEnemy(),
            CallMule(),
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanWorkerOnlyDefense(),
            PlanMultiDefense(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([BuildTanks(), tactics])
