import logging
import os
import pickle
from typing import List, Union, Callable, Tuple

import numpy as np
import tensorflow as tf
from tensorflow.python import keras
from tensorflow.python.keras import layers

from filelock.filelock import FileLock
from tactics.ml.agents import BaseMLAgent
from numpy.core.multiarray import ndarray

logger = logging.getLogger(__name__)

SAVE_DIR = "./data/"


def record(episode, episode_reward, worker_idx, global_ep_reward, total_loss, num_steps):
    """Helper function to store score and print statistics.

    Arguments:
      episode: Current episode
      episode_reward: Reward accumulated over the current episode
      worker_idx: Which thread (worker)
      global_ep_reward: The moving average of the global reward
      total_loss: The total loss accumualted over the current episode
      num_steps: The number of steps the episode took to complete
    """
    if global_ep_reward == 0:
        global_ep_reward = episode_reward
    else:
        global_ep_reward = global_ep_reward * 0.99 + episode_reward * 0.01
    text = (
        f"Episode: {episode} | "
        f"Moving Average Reward: {int(global_ep_reward)} | "
        f"Episode Reward: {int(episode_reward)} | "
        f"Loss: {int(total_loss / float(num_steps) * 1000) / 1000} | "
        f"Steps: {num_steps} | "
        f"Worker: {worker_idx}"
    )
    logger.info(text)
    print(text)
    return global_ep_reward


class ActorCriticModel(keras.Model):
    def __init__(self, state_size, action_size):
        super(ActorCriticModel, self).__init__()
        self.state_size = state_size
        self.action_size = action_size
        self.dense1 = layers.Dense(200, activation="relu")
        self.policy_logits = layers.Dense(action_size)
        self.dense2 = layers.Dense(200, activation="relu")
        self.dense3 = layers.Dense(100, activation="relu")
        self.values = layers.Dense(1)

    def call(self, inputs):
        # Decision making
        mid_x = self.dense1(inputs)
        x = self.dense2(mid_x)
        logits = self.policy_logits(x)

        # values for converging model
        v1 = self.dense3(inputs)
        values = self.values(v1)
        return logits, values


class Memory:
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []

    def store(self, state, action, reward):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)

    def clear(self):
        self.states = []
        self.actions = []
        self.rewards = []


class A3CAgent(BaseMLAgent):
    # Set up global variables across different threads
    episode = 0
    # Moving average reward
    global_moving_average_reward = 0
    best_score = 0

    def __init__(
        self,
        env_name: str,
        state_size,
        action_size,
        learning_rate=0.003,
        gamma=0.999,
        start_temperature=100,
        temperature_episodes=13000,
        log_print: Callable[[str], None] = print,
        mask: List[Tuple[int, float]] = None,
    ):
        """
        Create standard learning A3C agent.

        @param env_name: this is used for naming the model so that different games have different models
        @param state_size: Size of the input observation array. Integer support only for now
        @param action_size: Size of possible output.  Integer support only for now
        @param learning_rate: Learning rate. Something between 0.01 and 0.0001 should be fine
        @param gamma: Should define how meaningful early game actions are to late game rewards
        @param start_temperature: Increases randomness for the softmax action selection probability function
        @param temperature_episodes: How long to use temperature to increase randomness
        @param log_print: custom function for writing logs, defaults to "print"
        """
        super().__init__(state_size, action_size)

        self.mask: List[Tuple[int, float]] = mask
        self.temperature_episodes = temperature_episodes
        self.start_temperature = start_temperature
        self.print = log_print
        tf.enable_eager_execution()  # Required for some numpy code.
        # tf.compat.v1.enable_eager_execution()
        assert env_name is not str

        self.MODEL_NAME = "model_" + env_name
        self.MODEL_FILE_NAME = f"{self.MODEL_NAME}.h5"
        self.MODEL_FILE_PATH = os.path.join(SAVE_DIR, self.MODEL_FILE_NAME)
        self.OPTIMIZER_FILE_NAME = f"{self.MODEL_NAME}.opt.pkl"
        self.OPTIMIZER_FILE_PATH = os.path.join(SAVE_DIR, self.OPTIMIZER_FILE_NAME)
        self.MODEL_FILE_LOCK_PATH = os.path.join(SAVE_DIR, f"{self.MODEL_FILE_NAME}.lock")
        self.GLOBAL_RECORDS_FILE_NAME = f"{self.MODEL_NAME}.records.pkl"
        self.GLOBAL_RECORDS_FILE_PATH = os.path.join(SAVE_DIR, self.GLOBAL_RECORDS_FILE_NAME)
        self.LOG_FILE_NAME = f"{self.MODEL_NAME}.log"
        self.LOG_FILE_PATH = os.path.join(SAVE_DIR, self.LOG_FILE_NAME)

        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)

        with FileLock(self.MODEL_FILE_LOCK_PATH):
            if not os.path.isfile(self.MODEL_FILE_PATH):
                global_model = ActorCriticModel(self.state_size, self.action_size)
                global_model(tf.convert_to_tensor(np.random.random((1, self.state_size)), dtype=tf.float32))
                # global_model(tf.convert_to_tensor(np.zeros((1, self.state_size)), dtype=tf.float32))
                global_model.save_weights(self.MODEL_FILE_PATH)

            if not os.path.isfile(self.OPTIMIZER_FILE_PATH):
                # Create saved optimizer
                with open(self.OPTIMIZER_FILE_PATH, "wb") as f:
                    # pickle.dump(tf.train.AdamOptimizer(learning_rate, use_locking=True), f)
                    pickle.dump(tf.keras.optimizers.Adam(learning_rate=learning_rate), f)

            if not os.path.isfile(self.GLOBAL_RECORDS_FILE_PATH):
                # Create saved global records
                with open(self.GLOBAL_RECORDS_FILE_PATH, "wb") as f:
                    global_records = {
                        "global_episode": 1,
                        "global_moving_average_reward": 0,
                    }
                    pickle.dump(global_records, f)
            else:
                with open(self.GLOBAL_RECORDS_FILE_PATH, "rb") as f:
                    global_records = pickle.load(f)

            self.local_model = ActorCriticModel(self.state_size, self.action_size)
            self.local_model(tf.convert_to_tensor(np.random.random((1, self.state_size)), dtype=tf.float32))
            # self.local_model(tf.convert_to_tensor(np.zeros((1, self.state_size)), dtype=tf.float32))
            self.local_model.load_weights(self.MODEL_FILE_PATH)
        self.episode = global_records["global_episode"]
        self.mem = Memory()

        self.prev_action = None
        self.prev_state = None

        self.ep_reward = 0

        self.ep_steps = 0
        self.time_count = 0
        self.total_step = 0
        self.gamma = gamma

        self.ep_loss = 0

    def evaluate_prev_action_reward(self, reward: float):
        if self.prev_action is not None:
            self.ep_reward += reward
            self.mem.store(self.prev_state, self.prev_action, reward)

    def choose_action(self, state: ndarray, reward: float) -> int:
        """Choose and return the next action.
        """
        self.evaluate_prev_action_reward(reward)

        logits, values = self.local_model(tf.convert_to_tensor(state[None, :], dtype=tf.float32))

        if self.episode < self.temperature_episodes:
            # https://en.wikipedia.org/wiki/Softmax_function#Reinforcement_learning
            # Increases randomness
            logits /= (
                1 + self.start_temperature * (self.temperature_episodes - self.episode) / self.temperature_episodes
            )
        probs = tf.nn.softmax(logits).numpy()

        if self.mask and len(self.mask) > 0:
            for mask in self.mask:
                probs[0][mask[0]] = mask[1]
            probs /= probs.sum()  # Normalization

        self.prev_action = np.random.choice(self.action_size, p=probs[0])
        self.prev_state = state

        self.ep_steps += 1

        return self.prev_action

    def on_end(self, state: List[Union[float, int]], reward: float):
        self.evaluate_prev_action_reward(reward)

        # Calculate gradient wrt to local model. We do so by tracking the
        # variables involved in computing the loss by using tf.GradientTape
        with tf.GradientTape() as tape:
            total_loss = self.compute_loss(True, state, self.mem, self.gamma)
        self.ep_loss += total_loss
        # Calculate local gradients
        grads = tape.gradient(total_loss, self.local_model.trainable_weights)

        with FileLock(self.MODEL_FILE_LOCK_PATH):
            global_model = ActorCriticModel(self.state_size, self.action_size)
            global_model(tf.convert_to_tensor(np.random.random((1, self.state_size)), dtype=tf.float32))
            global_model.load_weights(self.MODEL_FILE_PATH)

            optimizer: tf.keras.optimizers.Optimizer
            with open(self.OPTIMIZER_FILE_PATH, "rb") as f:
                optimizer = pickle.load(f)

            global_records: dict
            with open(self.GLOBAL_RECORDS_FILE_PATH, "rb") as f:
                global_records = pickle.load(f)

            # work with the file as it is now locked

            # Push local gradients to global model
            optimizer.apply_gradients(zip(grads, global_model.trainable_weights))
            # Update local model with new weights
            self.local_model.set_weights(global_model.get_weights())

            self.mem.clear()
            self.time_count = 0

            # if done:  # done and print information
            # Worker.global_moving_average_reward = \
            #     record(Worker.global_episode, self.ep_reward, 1, #self.worker_idx,
            #            Worker.global_moving_average_reward, self.result_queue,
            #            self.ep_loss, ep_steps)
            global_records["global_moving_average_reward"] = record(
                global_records["global_episode"],
                self.ep_reward,
                1,  # self.worker_idx,
                global_records["global_moving_average_reward"],
                self.ep_loss,
                self.ep_steps,
            )
            # We must use a lock to save our model and to print to prevent data races.
            # if self.ep_reward > Worker.best_score:
            # if self.ep_reward > A3CAgent.best_score:
            #     A3CAgent.best_score = self.ep_reward
            #     print("New best score: ".format(A3CAgent.best_score))

            global_model.save_weights(self.MODEL_FILE_PATH)

            # Save optimizer weights.
            with open(self.OPTIMIZER_FILE_PATH, "wb") as f:
                pickle.dump(optimizer, f)

            episode = global_records["global_episode"]
            if episode % 100 == 0:
                # ensure path
                path = os.path.join(SAVE_DIR, f"e{episode}")
                from pathlib import Path

                Path(path).mkdir(parents=True, exist_ok=True)
                # Save backup model
                backup_path = os.path.join(path, self.MODEL_FILE_NAME)
                backup_path_opt = os.path.join(path, self.OPTIMIZER_FILE_NAME)
                backup_path_record = os.path.join(path, self.GLOBAL_RECORDS_FILE_NAME)

                global_model.save_weights(backup_path)

                # Save optimizer weights.
                with open(backup_path_opt, "wb") as f:
                    pickle.dump(optimizer, f)

                with open(backup_path_record, "wb") as f:
                    pickle.dump(global_records, f)

            # Worker.global_episode += 1
            global_records["global_episode"] += 1

            # Save global records
            with open(self.GLOBAL_RECORDS_FILE_PATH, "wb") as f:
                pickle.dump(global_records, f)

        # todo: this isn't how it originally was.
        self.prev_action = None
        self.prev_state = None
        self.ep_reward = 0
        self.ep_steps = 0
        self.time_count = 0
        self.total_step = 0
        self.ep_loss = 0

    def compute_loss(self, done, new_state, memory, gamma):
        if done:
            reward_sum = 0.0  # terminal
        else:
            reward_sum = self.local_model(tf.convert_to_tensor(new_state[None, :], dtype=tf.float32))[-1].numpy()[0]

        # Get discounted rewards
        discounted_rewards = []
        for reward in memory.rewards[::-1]:  # reverse buffer r
            reward_sum = reward + gamma * reward_sum
            discounted_rewards.append(reward_sum)
        discounted_rewards.reverse()

        logits, values = self.local_model(tf.convert_to_tensor(np.vstack(memory.states), dtype=tf.float32))
        # Get our advantages
        advantage = tf.convert_to_tensor(np.array(discounted_rewards)[:, None], dtype=tf.float32) - values
        # Value loss
        value_loss = advantage ** 2

        # Calculate our policy loss
        policy = tf.nn.softmax(logits)
        entropy = tf.nn.softmax_cross_entropy_with_logits_v2(labels=policy, logits=logits)

        policy_loss = tf.nn.sparse_softmax_cross_entropy_with_logits(labels=memory.actions, logits=logits)
        policy_loss *= tf.stop_gradient(advantage)
        policy_loss -= 0.01 * entropy
        total_loss = tf.reduce_mean((0.5 * value_loss + policy_loss))
        # self.print(f'[RL-value_loss] {value_loss} ')
        # self.print(f'[RL-policy] {policy}')
        self.print(f"[RL-entropy] {tf.reduce_mean(entropy)}")
        self.print(f"[RL-policy_loss] {tf.reduce_mean(policy_loss)}")
        self.print(f"[RL-total_loss] {total_loss}")

        return total_loss
