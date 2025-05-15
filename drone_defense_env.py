import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
import math

WIDTH, HEIGHT = 800, 600
NUM_SHEEP = 2  # Start small for curriculum learning

class DroneDefenseEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.action_space = spaces.Discrete(9)
        low = np.zeros(14, dtype=np.float32)
        high = np.array([WIDTH, HEIGHT] * 7, dtype=np.float32)
        self.observation_space = spaces.Box(low, high, dtype=np.float32)
        self.prev_sheep_count = NUM_SHEEP

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.predator = np.array([random.uniform(0, WIDTH), random.uniform(0, HEIGHT)])
        self.drone = np.array([random.uniform(0, WIDTH), random.uniform(0, HEIGHT)])
        self.sheep = [np.array([random.uniform(0, WIDTH), random.uniform(0, HEIGHT)]) for _ in range(NUM_SHEEP)]
        self.steps = 0
        self.prev_sheep_count = NUM_SHEEP
        return self._get_obs(), {}

    def _get_obs(self):
        flat_sheep = [coord for s in self.sheep for coord in s]
        while len(flat_sheep) < 10:
            flat_sheep.extend([0.0, 0.0])
        return np.array(list(self.predator) + list(self.drone) + flat_sheep, dtype=np.float32)

    def step(self, action):
        self.steps += 1
        dx, dy = self._action_to_vector(action)
        self.drone += np.array([dx, dy]) * 5
        self.drone = np.clip(self.drone, 0, [WIDTH, HEIGHT])

        # Move predator toward nearest sheep
        if self.sheep:
            nearest = min(self.sheep, key=lambda s: np.linalg.norm(s - self.predator))
            direction = nearest - self.predator
            if np.linalg.norm(direction) > 0:
                self.predator += (direction / np.linalg.norm(direction)) * 2.5

            # Predator gets repelled if drone is too close
            repel_vec = self.predator - self.drone
            dist = np.linalg.norm(repel_vec)
            if dist < 40:
                self.predator += (repel_vec / dist) * 3 if dist > 0 else np.zeros(2)

            self.predator = np.clip(self.predator, 0, [WIDTH, HEIGHT])

            # Kill sheep if predator gets too close
            if np.linalg.norm(nearest - self.predator) < 10:
                self.sheep = [s for s in self.sheep if not np.array_equal(s, nearest)]

        # --- Reward Logic ---
        reward = 0

        # Reward for proximity to sheep
        if self.sheep:
            for s in self.sheep:
                dist_pred = np.linalg.norm(s - self.predator)
                dist_drone = np.linalg.norm(s - self.drone)

                if dist_pred < 100:
                    reward += max(0, (100 - dist_drone) / 100) * 1.0  # scaled bonus

                # Super bonus for being directly between
                pred_vec = self.predator - s
                drone_vec = self.drone - s
                angle = self._angle_between(pred_vec, drone_vec)
                if angle < 0.4:
                    reward += 2.5

        # Small penalty for sheep dying
        sheep_killed = self.prev_sheep_count - len(self.sheep)
        reward -= sheep_killed * 0.5  # less harsh than before
        self.prev_sheep_count = len(self.sheep)

        # Time penalty
        reward -= 0.005

        # Minor shaping
        dist = np.linalg.norm(self.drone - self.predator)
        if dist > 200:
            reward -= 0.3 * ((dist - 200) / 200)

        reward -= 0.01  # time penalty
        done = len(self.sheep) == 0 or self.steps >= 500
        return self._get_obs(), reward, done, False, {}

    def _angle_between(self, v1, v2):
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return np.pi
        return np.arccos(np.clip(np.dot(v1, v2) / (norm1 * norm2), -1.0, 1.0))

    def _action_to_vector(self, action):
        directions = [
            (0, 0), (0, -1), (1, -1), (1, 0), (1, 1),
            (0, 1), (-1, 1), (-1, 0), (-1, -1)
        ]
        return directions[action]

    def render(self):
        pass