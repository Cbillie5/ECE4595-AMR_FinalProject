from stable_baselines3 import PPO
from drone_defense_env import DroneDefenseEnv
from reward_logger import RewardLogger
import pickle

env = DroneDefenseEnv()
model = PPO("MlpPolicy", env, verbose=1)
logger = RewardLogger()
model.learn(total_timesteps=500_000, callback=logger)

model.save("ppo_drone_defense")

