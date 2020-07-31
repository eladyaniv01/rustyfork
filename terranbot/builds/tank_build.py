from sharpy.plans.terran import *
from tactics import *
from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class BuildTanks(BuildOrder):
    def __init__(self):
        self.worker_rushed = False
        self.rush_bunker = BuildPosition(UnitTypeId.BUNKER, Point2((0, 0)), exact=True)
        viking_counters = [
            UnitTypeId.COLOSSUS,
            UnitTypeId.MEDIVAC,
            UnitTypeId.RAVEN,
            UnitTypeId.VOIDRAY,
            UnitTypeId.CARRIER,
            UnitTypeId.TEMPEST,
            UnitTypeId.BROODLORD,
            UnitTypeId.LIBERATOR,
        ]

        warn = WarnBuildMacro(
            [
                (UnitTypeId.SUPPLYDEPOT, 1, 18),
                (UnitTypeId.BARRACKS, 1, 42),
                (UnitTypeId.REFINERY, 1, 44),
                (UnitTypeId.COMMANDCENTER, 2, 60 + 44),
                (UnitTypeId.BARRACKSREACTOR, 1, 120),
                (UnitTypeId.FACTORY, 1, 120 + 21),
            ],
            [],
        )

        scv = [
            Step(None, TerranUnit(UnitTypeId.MARINE, 2, priority=True), skip_until=lambda k: self.worker_rushed),
            Step(None, MorphOrbitals(), skip_until=UnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, Workers(16 + 6), skip=UnitExists(UnitTypeId.COMMANDCENTER, 2)),
            AutoWorker(70),
        ]

        dt_counter = [
            Step(lambda k: k.enemy_units_manager.enemy_cloak_trigger, None),
            Building(UnitTypeId.ENGINEERINGBAY, 1),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.Entrance, 2)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.CenterMineralLine, None)),
        ]
        dt_counter2 = [
            Step(lambda k: k.enemy_units_manager.enemy_cloak_trigger, None),
            Building(UnitTypeId.STARPORT, 2),
            Step(None, BuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
            Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.RAVEN, 1)),
            Step(EnemyUnitExistsAfter(UnitTypeId.BANSHEE), TerranUnit(UnitTypeId.VIKINGFIGHTER, 2)),
            TerranUnit(UnitTypeId.RAVEN, 2),
        ]

        opener = [
            Step(Supply(13), Building(UnitTypeId.SUPPLYDEPOT, 1, priority=True)),
            Building(UnitTypeId.BARRACKS, 1, priority=True),
            StepBuildGas(1, Supply(15)),
            Step(
                None, Building(UnitTypeId.SUPPLYDEPOT, 2, priority=True), skip_until=All([Supply(23), SupplyLeft(0),]),
            ),
            TerranUnit(UnitTypeId.REAPER, 1, only_once=True, priority=True),
            Step(
                None,
                Expand(2, priority=True),
                skip_until=Any(
                    [
                        RequireCustom(lambda k: not k.possible_rush_detected),
                        UnitExists(UnitTypeId.SIEGETANK, 2, include_killed=True),
                    ]
                ),
            ),
            Step(
                None,
                CancelBuilding(UnitTypeId.COMMANDCENTER, 1),
                skip=Any(
                    [
                        RequireCustom(lambda k: not k.possible_rush_detected),
                        UnitExists(UnitTypeId.SIEGETANK, 2, include_killed=True),
                    ]
                ),
            ),
            Step(None, self.rush_bunker, skip_until=lambda k: k.possible_rush_detected),
            Step(None, Building(UnitTypeId.BARRACKS, 2), skip_until=lambda k: k.possible_rush_detected),
            Building(UnitTypeId.SUPPLYDEPOT, 2, priority=True),
            # BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1),
            Building(UnitTypeId.FACTORY, 1),
            BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),
            AutoDepot(),
        ]

        addons = [
            Step(UnitReady(UnitTypeId.BARRACKS, 2), BuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(
                UnitReady(UnitTypeId.BARRACKSTECHLAB, 1), BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1)
            ),
            Step(UnitReady(UnitTypeId.BARRACKS, 3), BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 2)),
            Step(UnitReady(UnitTypeId.BARRACKS, 5), BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 4)),
            BuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1),
        ]

        buildings = SequentialList(
            Step(UnitReady(UnitTypeId.FACTORYTECHLAB), TerranUnit(UnitTypeId.SIEGETANK, 1)),
            Step(
                None,
                DefensiveBuilding(UnitTypeId.BUNKER, DefensePosition.FarEntrance, 1),
                skip_until=UnitExists(UnitTypeId.COMMANDCENTER, 2),
                skip=lambda k: len(k.enemy_townhalls) > 1,
            ),
            Building(UnitTypeId.BARRACKS, 2),
            Step(Supply(35, SupplyType.Workers), BuildGas(3)),
            Step(None, BuildGas(4), skip_until=Minerals(500), skip=Gas(250)),
            Building(UnitTypeId.STARPORT, 1),
            Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 2, priority=True)),
            Building(UnitTypeId.FACTORY, 2),
            Step(None, BuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 2)),
            # BuildStep(None, Building(UnitTypeId.ARMORY, 1)),
            Building(UnitTypeId.BARRACKS, 3),
            Step(Supply(40, SupplyType.Workers), Expand(3)),
            Step(Supply(60, SupplyType.Workers), Building(UnitTypeId.BARRACKS, 5)),
            Step(None, BuildGas(5), skip_until=Minerals(500), skip=Gas(250)),
            Expand(4),
        )

        tech = [
            Step(None, Tech(UpgradeId.STIMPACK, UnitTypeId.BARRACKSTECHLAB)),
            Step(None, Tech(UpgradeId.SHIELDWALL, UnitTypeId.BARRACKSTECHLAB)),
            Building(UnitTypeId.ENGINEERINGBAY),
            Step(
                CanSurvive(),
                BuildOrder(
                    self.Infantry_upgrades_all,
                    Step(
                        CanSurviveSafe(),
                        SequentialList(Building(UnitTypeId.ARMORY), Building(UnitTypeId.ENGINEERINGBAY, 2)),
                        skip_until=Time(60 * 6),
                    ),
                    SequentialList(
                        Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1),
                        Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2),
                        Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL3),
                    ),
                ),
            ),
        ]

        mech = [
            Step(None, TerranUnit(UnitTypeId.CYCLONE, 10, priority=True), skip_until=MostlyAir()),
            TerranUnit(UnitTypeId.SIEGETANK, 2, priority=True),
            TerranUnit(UnitTypeId.SIEGETANK, 20, priority=True),
        ]

        air = [
            Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 2, priority=True)),
            Step(None, TerranUnit(UnitTypeId.VIKINGFIGHTER, 1, priority=True)),
            Step(
                None,
                TerranUnit(UnitTypeId.VIKINGFIGHTER, 3, priority=True),
                skip_until=self.RequireAnyEnemyUnits(viking_counters, 1),
            ),
            Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 4, priority=True)),
            Step(
                None,
                TerranUnit(UnitTypeId.VIKINGFIGHTER, 10, priority=True),
                skip_until=self.RequireAnyEnemyUnits(viking_counters, 4),
            ),
            Step(UnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 6, priority=True)),
        ]

        early_marines = [
            Step(
                UnitExists(UnitTypeId.REAPER, 1, include_killed=True), TerranUnit(UnitTypeId.MARINE, 15, priority=True),
            ),
        ]

        marines = [
            Step(UnitExists(UnitTypeId.REAPER, 1, include_killed=True), TerranUnit(UnitTypeId.MARINE, 20)),
            Step(Minerals(250), TerranUnit(UnitTypeId.MARINE, 100)),
        ]

        use_money = [
            UnitReady(UnitTypeId.BARRACKS, 5),
            Step(Minerals(400), Building(UnitTypeId.BARRACKS, 7)),
            Step(Minerals(500), BuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 5)),
        ]

        super().__init__(
            [
                warn,
                scv,
                opener,
                addons,
                early_marines,
                mech,
                buildings,
                dt_counter,
                dt_counter2,
                tech,
                air,
                marines,
                use_money,
            ]
        )

    async def start(self, knowledge: "Knowledge"):
        self.rush_bunker.position = knowledge.base_ramp.ramp.barracks_in_middle
        await super().start(knowledge)

    async def execute(self) -> bool:
        if not self.worker_rushed and self.ai.time < 120:
            self.worker_rushed = (
                len(
                    self.knowledge.known_enemy_workers.filter(
                        lambda u: u.distance_to(self.ai.start_location)
                        < u.distance_to(self.knowledge.likely_enemy_start_location)
                    )
                )
                > 6
            )

        return await super().execute()
