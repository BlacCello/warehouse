import random
import math
import time
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Conv2D, Flatten
from tensorflow.keras.optimizers import Adam
import huskarl as hk

import matplotlib.pyplot as plt

from warehouse_env.warehouse import WarehouseEnv


class EpsDecay(hk.policy.Policy):
    def __init__(self, eps_min, steps):
        self.eps = 1.0
        self.eps_min = eps_min
        self.eps_decay = math.pow(self.eps_min, 1 / steps)
        self.step = 0

    def act(self, qvals):
        if self.eps > self.eps_min:
            self.eps *= self.eps_decay

        if self.step % 1000 == 0:
            print(self.eps)
        self.step += 1

        if random.random() > self.eps:
            return np.argmax(qvals)
        return random.randrange(len(qvals))


if __name__ == "__main__":
    env_layout = "layout2-2bins.yml"
    # Training Parameters
    lr = 1e-3
    eps_min = 0.1
    eps_steps = 20_000 # 40_000
    memsize = 20_000 # 20_000
    gamma = 0.95
    target_update = 100

    def create_env():
        return WarehouseEnv(env_layout)

    warehouse_env = create_env()

    optimizer = Adam(lr=lr)
    model = Sequential()
    model.add(
        Conv2D(
            32, 3, activation="relu", input_shape=warehouse_env.observation_space.shape
        )
    )
    model.add(Flatten())
    model.add(Flatten(input_shape=warehouse_env.observation_space.shape))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(32, activation="relu"))
    model.add(Dense(warehouse_env.action_space.n, activation="linear"))

    # print model info
    model.summary()

    # Create Deep Q-Learning Network agent

    eps_policy = EpsDecay(eps_min, eps_steps)

    agent = hk.agent.DQN(
        model,
        actions=warehouse_env.action_space.n,
        nsteps=1,
        gamma=gamma,
        memsize=memsize,
        policy=eps_policy,
        target_update=target_update,
    )

    def plot_rewards(episode_rewards, episode_steps, done=False):
        plt.clf()
        plt.xlabel("Step")
        plt.ylabel("Reward")
        plt.title(
            f"Bin-Slot-Size: {warehouse_env.layout['bin-slot-size']}, LR: {lr}, Eps-min: {eps_min} (in {eps_steps} Steps), gamma: {gamma}, memsize: {memsize}, t-update: {target_update}"
        )
        for ed, steps in zip(episode_rewards, episode_steps):
            plt.plot(steps, ed)
        plt.show() if done else plt.pause(
            0.001
        )  # Pause a bit so that the graph is updated

    # Create simulation, train and then test
    sim = hk.Simulation(create_env, agent)

    sim.train(max_steps=20_000, visualize=False, plot=plot_rewards)

    filename = f"32CDDD-{warehouse_env.layout['bin-slot-size']}slotsA.h5"
    agent.save(filename)

    agent.model.load_weights(filename)

    print("### TESTING ###")
    agent.training = False
    env = WarehouseEnv(env_layout)
    state = env.reset()

    steps = []
    episodes = 100
    max_steps = 100
    json_vis = { "initial": state, "episodes": []}
    for e in range(episodes):
        for i in range(max_steps):
            action = agent.act(state)
            next_state, rewards, done, info = env.step(action)
            if np.array_equal(state, next_state):
                i = max_steps
                break
            state = next_state
            env.render()
            time.sleep(0.2)
            if done:
                break
        state = env.reset(assertions=False)
        steps.append(i +1)
        
    # sim.test(max_steps=1000)

    print (f"{len([1 for s in steps if s < max_steps])}/{episodes} episode succeeded.")
