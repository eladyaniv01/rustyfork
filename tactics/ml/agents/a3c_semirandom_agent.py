import logging
from random import randint
from typing import Callable, List, Tuple

from numpy.core.multiarray import ndarray

logger = logging.getLogger(__name__)

from tactics.ml.agents import A3CAgent


class SemiRandomA3CAgent(A3CAgent):
    def __init__(self, env_name: str, state_size, action_size, log_print: Callable[[str], None] = print):
        super().__init__(env_name, state_size, action_size, log_print=log_print)

        self.start_drones = randint(12, 18)
        self.second_drones = randint(20, 30)
        self.go_hatch = randint(200, 500)

        count = randint(3, 10)
        self.action_states: List[Tuple[int, int]] = []
        time = 30
        while time < 30 * 60:
            time = randint(time + 1, time + 30)
            min_action_size = 0
            if time < 2 * 60:
                tmp_action_size = 2
            elif time < 4 * 60:
                tmp_action_size = 4
            elif time < 8 * 60:
                tmp_action_size = 7
            elif time < 12 * 60:
                if randint(0, 1) == 0:
                    min_action_size = 0
                    tmp_action_size = 2
                else:
                    min_action_size = 3
                    tmp_action_size = 12
            else:
                if randint(0, 3) == 0:
                    min_action_size = 0
                    tmp_action_size = 2
                else:
                    min_action_size = 3
                    tmp_action_size = self.action_size - 1

            self.action_states.append((time, randint(min_action_size, tmp_action_size)))

    def choose_action(self, state: ndarray, reward: float) -> int:
        """Choose and return the next action.
        """
        self.evaluate_prev_action_reward(reward)

        self.prev_action = self.scripted_action(state)
        self.prev_state = state

        self.ep_steps += 1

        return self.prev_action

    def scripted_action(self, state: ndarray) -> int:
        action = 0
        for action_state in self.action_states:
            action = action_state[1]
            if state[0] < action_state[0]:
                break

        return action

    def scripted_action_roach(self, state: ndarray) -> int:
        if state[5] < self.start_drones or (state[9] > 1 and state[5] < self.second_drones and state[6] > 8):
            return 1  # Drones
        elif state[10] < 1:
            return 3  # Lings / pool first
        elif state[4] < 1 and state[7] < state[9]:
            return 2  # queens
        elif state[4] < 1 and state[3] > self.go_hatch:
            return 0  # hatcheries
        elif state[6] < 10:
            return 3  # Lings
        return 4  # Go roach
