import matplotlib.pyplot as plt
import numpy as np
import pickle

# Load reward logger data
with open("episode_rewards.pkl", "rb") as f:
    episode_rewards = pickle.load(f)

# Plot
plt.figure(figsize=(10, 4))
plt.plot(episode_rewards, label="Episode Reward", alpha=0.7)
plt.title("Training Episode Rewards (RL Drone)")
plt.xlabel("Episode")
plt.ylabel("Total Reward")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()