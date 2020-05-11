import gym
from gym import spaces
import numpy as np
import math
import yaml
import random
import itertools
import time
from warehouse_env.transaction import create_new_transaction
from warehouse_env.agent import Agent
from warehouse_env.bins import Bin, StagingIn, StagingOut
from warehouse_env.constants import (
    MOVE_UP,
    MOVE_DOWN,
    MOVE_LEFT,
    MOVE_RIGHT,
    PICK_T,
    PUT_T,
)
from warehouse_env.vis import WarehouseGui


class WarehouseEnv(gym.Env):
    """Custom Environment that follows gym interface"""

    metadata = {"render.modes": ["human"]}

    def __init__(self, layout_path="layout.yml"):
        # Define action and observation space
        super(WarehouseEnv, self).__init__()
        # They must be gym.spaces objects    # Example when using discrete actions:
        # Example for using image as input:

        self.actions = [MOVE_LEFT, MOVE_DOWN, MOVE_RIGHT, MOVE_UP]

        with open(layout_path, "r") as f:
            try:
                self.layout = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print(exc)

        self.max_items_in_env = self.layout["bin-slot-size"] * len(self.layout["bins"])

        # actions are zero based so this is ok
        self.load_actions = [
            len(self.actions) + i for i in range(self.max_items_in_env)
        ]
        self.unload_actions = [
            len(self.actions) + len(self.load_actions) + i
            for i in range(self.max_items_in_env)
        ]

        self.actions += self.load_actions + self.unload_actions

        assert self.max_items_in_env * 2 + 4 == len(self.actions)

        self.action_space = spaces.Discrete(len(self.actions))

        self.n_channels = 3 + self.max_items_in_env * 2
        self.shape = (self.layout["height"], self.layout["width"], self.n_channels)
        self.observation_space = spaces.Box(
            low=-1, high=1, shape=self.shape, dtype=np.uint8
        )

        self.bins = self._create_bins(self.layout["bins"], self.layout["bin-slot-size"])
        self.staging_in = StagingIn(
            self.layout["staging-in"]["position"], self.layout["staging-in"]["loading"]
        )
        self.staging_out = StagingOut(
            self.layout["staging-out"]["position"],
            self.layout["staging-out"]["loading"],
        )

        self.blocked_positions = []
        for b in self.bins:
            self.blocked_positions.append(b.pos)
        self.blocked_positions.append(self.staging_in.pos)
        self.blocked_positions.append(self.staging_out.pos)

        self.agent = Agent(
            self.layout["agent-start"]["position"],
            self.layout["height"],
            self.layout["width"],
            self.layout["bin-slot-size"],
            self.blocked_positions,
        )

        self.transaction = None

        self.item_counter = 0
        self.invalid_action_counter = 0

        self.gui = WarehouseGui([self.layout["height"], self.layout["width"]], self.max_items_in_env)

    def _print_state(self):

        state = self._next_state()
        for i in range(self.n_channels):
            print(state[:, :, i])
        # time.sleep(2)

    def _next_state(self):
        state = np.zeros(shape=self.shape, dtype=np.int8)

        # Blocked Positions
        for pos in self.blocked_positions:
            state[pos[0], pos[1], 0] = 1

        # Agent Position and Slot
        state[self.agent.agent_pos[0], self.agent.agent_pos[1], 1] = 1

        # Agent Position and Slot
        if self.agent.loaded_item:
            state[
                self.agent.agent_pos[0],
                self.agent.agent_pos[1],
                1 + self.agent.loaded_item.slot,
            ] = 1

        # Bin Layers
        for b in self.bins:
            for slot in b.get_slots().keys():
                for p in b.loading_positions:
                    state[p[0], p[1], self.max_items_in_env + 1 + slot] = 1

            if self.staging_in.put_transaction is not None:
                for item in self.staging_in.put_transaction.items:
                    for p in b.loading_positions:
                        state[p[0], p[1], self.max_items_in_env + 1 + item.slot] = -1

        # Staging In
        for slot in self.staging_in.get_slots().keys():
            for p in self.staging_in.loading_positions:
                state[p[0], p[1], self.max_items_in_env + 1 + slot] = 1

        # Staging Out
        for slot in self.staging_out.incoming:
            for p in self.staging_out.loading_positions:
                state[p[0], p[1], self.max_items_in_env + 1 + slot] = -1

        return state

    def reset(self, assertions=True):
        # Reset the state of the environment to an initial state

        print("Reset called - Invalid Actions: " + str(self.invalid_action_counter))
        self.invalid_action_counter = 0
        self.staging_in.put_transaction = None
        self.staging_out.pick_transaction = None

        if assertions:
            assert (
                self.agent.loaded_item is None
            ), "New Transaction can only be generated if agent has no item"
            assert len(self.staging_in.get_slots()) == 0
            assert len(self.staging_out.incoming) == 0
        else:
            self.agent.loaded_item = None
            self.staging_in._slots = {}
            self.staging_out.incoming = []

        self.transaction = create_new_transaction(
            self.max_items_in_env, self.layout["bin-slot-size"], self.bins
        )
        if self.transaction.get_type() == PICK_T:
            self.staging_out.apply_pick(self.transaction)
        elif self.transaction.get_type() == PUT_T:
            self.staging_in.apply_put(self.transaction)
        else:
            raise AssertionError("Transaction must be either pick or put transaction.")
        return self._next_state()

    def step(self, action):
        state = self._next_state()
        # Execute one time step within the environment
        if (
            action == MOVE_UP
            or action == MOVE_DOWN
            or action == MOVE_LEFT
            or action == MOVE_RIGHT
        ):
            reward = self.agent.move(action)
        elif action >= self.load_actions[0] and action <= self.load_actions[-1]:
            reward = self.agent.load_item(
                self.bins,
                self.staging_in,
                self.staging_out,
                slot=(action - self.load_actions[0] + 1),
            )
        elif action >= self.unload_actions[0] and action <= self.unload_actions[-1]:
            reward = self.agent.unload_item(
                self.bins,
                self.staging_in,
                self.staging_out,
                slot=(action - self.unload_actions[0] + 1),
            )
        else:
            raise AssertionError("Invalid action Type.")

        next_state = self._next_state()
        done = self._is_episode_done()
        # self._print_state()
        if reward < 0:
            self.invalid_action_counter += 1
            assert np.array_equal(state, next_state)
        return next_state, reward, done, {}

    def render(self, mode="human", close=False):
        # Render the environment to the screen
        # print(self.item_counter)
        # for b in self.bins:
        #     print(b.to_string())
        # print(self.agent.to_string())
        # print(self.staging_in.to_string())
        # print(self.staging_out.to_string())

        self.gui.frame_step(self.agent, self.bins, self.staging_in, self.staging_out, self.transaction)
        pass

    def _create_bins(self, bin_config, bin_size):
        bins = []
        for b in bin_config:
            bins.append(Bin(b["position"], b["loading"]))
        return bins

    def _is_episode_done(self):
        if self.transaction.get_type() == PICK_T:
            done = self.staging_out.is_current_transaction_done()
            count = len(self.transaction.slot_ids)
        elif self.transaction.get_type() == PUT_T:
            done = self.staging_in.is_current_transaction_done(self.bins)
            count = len(self.transaction.items)
        else:
            raise AssertionError("Transaction must be either pick or put transaction.")

        if done:
            self.item_counter += count
        return done

