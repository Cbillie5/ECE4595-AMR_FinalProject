from stable_baselines3.common.callbacks import BaseCallback

class RewardLogger(BaseCallback):
    def __init__(self):
        super().__init__()
        self.episode_rewards = []

    def _on_step(self) -> bool:
        if self.locals.get("drones"):
            self.episode_rewards.append(self.locals["rewards"])
        return True