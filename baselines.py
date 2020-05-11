import gym
import json
import datetime as dt
from stable_baselines.common.policies import MlpPolicy
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines import PPO2, A2C, DQN
from stable_baselines.deepq.policies import (
    MlpPolicy as DQNMlpPolicy,
    CnnPolicy as DQNCnnPolicy,
)
from warehouse_env.warehouse import WarehouseEnv

env_layout = "layout2.yml"

# The algorithms require a vectorized environment to run
env = DummyVecEnv([lambda: WarehouseEnv(env_layout)])

# multiprocess environment
# n_cpu = 4
# env = SubprocVecEnv([lambda: WarehouseEnv("layout.yml") for i in range(n_cpu)])

# model = PPO2(MlpPolicy, env, verbose=1)
# model = A2C(MlpPolicy, env, verbose=1)
model = DQN(
    DQNMlpPolicy,
    env,
    verbose=1,
    exploration_fraction=0.8,
    gamma=0.95,
    learning_rate=0.001,
    target_network_update_freq=100,
    prioritized_replay=True
)
model.learn(total_timesteps=100_000)

filename = "mlp_1e5"
model.save(filename)

# model = PPO2.load(filename)
env = WarehouseEnv(env_layout)
state = env.reset()

steps = []
episodes = 100
max_steps = 100
for e in range(episodes):
    for i in range(max_steps):
        action, _states = model.predict(state)
        next_state, rewards, done, info = env.step(action)
        state = next_state
        env.render()
        if done:
            break
    state = env.reset(assertions=False)
    steps.append(i + 1)

print(f"{len([1 for s in steps if s < max_steps])}/{episodes} episode succeeded.")

