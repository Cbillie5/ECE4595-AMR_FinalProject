import pygame
import random
import math

# --- Pygame Setup ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Predator-Prey Herding Simulation")
clock = pygame.time.Clock()

# --- Constants ---
NUM_SHEEP = 30
NUM_PREDATORS = 1
NUM_ROBOTS = 5
NUM_OBSTACLES = 5

MAX_SPEED = 1.0
PREDATOR_SPEED = 1.8
ROBOT_SPEED = 1.5

NEIGHBOR_RADIUS = 70
PREDATOR_AVOID_RADIUS = 35
PANIC_RADIUS = 60
SHEEP_SEPARATION_RADIUS = 20
ROBOT_PUSH_RADIUS = 40
ROBOT_DEFENSE_RADIUS = 150
OBSTACLE_RADIUS = 20
OBSTACLE_AVOID_RADIUS = 40

ALIGNMENT_WEIGHT = 0.8
COHESION_WEIGHT = 0.2
SEPARATION_WEIGHT = 1.2

PREDATOR_AVOID_WEIGHT = 3.0

SHEEP_MAX_HEALTH = 100
PREDATOR_DAMAGE = 5

ROBOT_FORMATION_SPACING = 40
ROBOT_FORMATION_ANGLE = 80

# --- Colors ---
SHEEP_COLOR = (255, 250, 240)
PREDATOR_COLOR = (255, 0, 0)
ROBOT_COLOR = (0, 0, 0)
OBSTACLE_COLOR = (100, 100, 100)
BG_COLOR = (0, 128, 0)

# --- Utilities ---
def limit_vector(vec, max_value):
    x, y = vec
    mag = math.hypot(x, y)
    if mag > max_value:
        return x / mag * max_value, y / mag * max_value
    return x, y

def assign_v_formation(robots, center_x, center_y, predator_x, predator_y):
    mid = len(robots) // 2
    dx = center_x - predator_x
    dy = center_y - predator_y
    dist = math.hypot(dx, dy)
    if dist == 0:
        dx, dy = 0, 1
    else:
        dx /= dist
        dy /= dist

    angle_rad = math.radians(ROBOT_FORMATION_ANGLE)
    for i, robot in enumerate(robots):
        side = -1 if i < mid else 1
        rank = abs(i - mid)
        offset_dx = dx * math.cos(angle_rad) - side * dy * math.sin(angle_rad)
        offset_dy = dx * math.sin(angle_rad) + side * dy * math.cos(angle_rad)
        robot.target_x = center_x + offset_dx * rank * ROBOT_FORMATION_SPACING
        robot.target_y = center_y + offset_dy * rank * ROBOT_FORMATION_SPACING

# --- Obstacle ---
class Obstacle:
    def __init__(self):
        self.x = random.uniform(OBSTACLE_AVOID_RADIUS, WIDTH - OBSTACLE_AVOID_RADIUS)
        self.y = random.uniform(OBSTACLE_AVOID_RADIUS, HEIGHT - OBSTACLE_AVOID_RADIUS)
    def draw(self, surface):
        pygame.draw.circle(surface, OBSTACLE_COLOR, (int(self.x), int(self.y)), OBSTACLE_RADIUS)

# --- Sheep ---
class Sheep:
    def __init__(self):
        self.x = random.uniform(WIDTH / 3, 2 * WIDTH / 3)
        self.y = random.uniform(HEIGHT / 3, 2 * HEIGHT / 3)
        angle = random.uniform(0, 2 * math.pi)
        self.vx = math.cos(angle)
        self.vy = math.sin(angle)
        self.health = SHEEP_MAX_HEALTH
        self.alive = True

    def update(self, sheep_list, predator_list, obstacle_list):
        if not self.alive:
            return

        align_x = align_y = coh_x = coh_y = sep_x = sep_y = avoid_x = avoid_y = 0
        count = 0
        is_panicking = False

        for other in sheep_list:
            if other != self and other.alive:
                dx, dy = other.x - self.x, other.y - self.y
                dist = math.hypot(dx, dy)
                if dist < NEIGHBOR_RADIUS:
                    align_x += other.vx
                    align_y += other.vy
                    coh_x += other.x
                    coh_y += other.y
                    if dist < SHEEP_SEPARATION_RADIUS:
                        sep_x -= dx / dist
                        sep_y -= dy / dist
                    count += 1

        if count:
            align_x, align_y = limit_vector((align_x / count, align_y / count), MAX_SPEED)
            align_x -= self.vx
            align_y -= self.vy
            coh_x, coh_y = coh_x / count - self.x, coh_y / count - self.y
            coh_x, coh_y = limit_vector((coh_x, coh_y), MAX_SPEED)
            coh_x -= self.vx
            coh_y -= self.vy
            sep_x, sep_y = limit_vector((sep_x, sep_y), MAX_SPEED)

        for predator in predator_list:
            dx, dy = predator.x - self.x, predator.y - self.y
            dist = math.hypot(dx, dy)
            if dist < PANIC_RADIUS:
                is_panicking = True
            if 0 < dist < PREDATOR_AVOID_RADIUS:
                avoid_x -= dx / dist
                avoid_y -= dy / dist

        for obs in obstacle_list:
            dx, dy = obs.x - self.x, obs.y - self.y
            dist = math.hypot(dx, dy)
            if 0 < dist < OBSTACLE_AVOID_RADIUS:
                avoid_x -= dx / dist
                avoid_y -= dy / dist

        self.vx += (align_x * ALIGNMENT_WEIGHT + coh_x * COHESION_WEIGHT +
                    sep_x * SEPARATION_WEIGHT + avoid_x * PREDATOR_AVOID_WEIGHT)
        self.vy += (align_y * ALIGNMENT_WEIGHT + coh_y * COHESION_WEIGHT +
                    sep_y * SEPARATION_WEIGHT + avoid_y * PREDATOR_AVOID_WEIGHT)

        # Panic mode: boost speed and random motion
        if is_panicking:
            jitter_angle = random.uniform(0, 2 * math.pi)
            self.vx += math.cos(jitter_angle) * 0.5
            self.vy += math.sin(jitter_angle) * 0.5

        self.vx, self.vy = limit_vector((self.vx, self.vy), MAX_SPEED * (1.5 if is_panicking else 1.0))
        self.x = max(0, min(WIDTH, self.x + self.vx))
        self.y = max(0, min(HEIGHT, self.y + self.vy))

    def draw(self, surface):
        if not self.alive:
            return
        pygame.draw.circle(surface, SHEEP_COLOR, (int(self.x), int(self.y)), 5)
        health_ratio = self.health / SHEEP_MAX_HEALTH
        pygame.draw.rect(surface, (255, 0, 0), (self.x - 10, self.y - 10, 20, 3))
        pygame.draw.rect(surface, (0, 255, 0), (self.x - 10, self.y - 10, 20 * health_ratio, 3))

# --- Predator ---
class Predator:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(0, HEIGHT)

    def update(self, sheep_list):
        alive = [s for s in sheep_list if s.alive]
        if not alive:
            return
        nearest = min(alive, key=lambda s: math.hypot(s.x - self.x, s.y - self.y))
        dx, dy = nearest.x - self.x, nearest.y - self.y
        dist = math.hypot(dx, dy)
        if dist < 10:
            nearest.health -= PREDATOR_DAMAGE
            if nearest.health <= 0:
                nearest.alive = False
        vx, vy = limit_vector((dx, dy), PREDATOR_SPEED)
        self.x = max(0, min(WIDTH, self.x + vx))
        self.y = max(0, min(HEIGHT, self.y + vy))

    def draw(self, surface):
        pygame.draw.circle(surface, PREDATOR_COLOR, (int(self.x), int(self.y)), 7)

# --- Robot ---
class Robot:
    def __init__(self, x, y, id, robots):
        self.x = x
        self.y = y
        self.id = id
        self.robots = robots
        self.target_x = x
        self.target_y = y

    def update(self, sheep_list, predator_list, obstacle_list):
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        steer_x, steer_y = dx, dy

        if predator_list:
            predator = predator_list[0]
            dist = math.hypot(predator.x - self.x, predator.y - self.y)
            if dist < ROBOT_DEFENSE_RADIUS:
                fx = predator.x + (predator.x - self.x) * 0.5
                fy = predator.y + (predator.y - self.y) * 0.5
                steer_x += (fx - self.x) * 0.05
                steer_y += (fy - self.y) * 0.05
            if dist < ROBOT_PUSH_RADIUS:
                repel_x = self.x - predator.x
                repel_y = self.y - predator.y
                repel_mag = math.hypot(repel_x, repel_y)
                if repel_mag > 0:
                    repel_x /= repel_mag
                    repel_y /= repel_mag
                    perp_x, perp_y = -repel_y, repel_x
                    # predator.x -= (repel_x + 0.3 * perp_x) * 2
                    # predator.y -= (repel_y + 0.3 * perp_y) * 2
                    predator.x -= repel_x * 2
                    predator.y -= repel_y * 2

        for obs in obstacle_list:
            dx, dy = obs.x - self.x, obs.y - self.y
            dist = math.hypot(dx, dy)
            if dist < OBSTACLE_AVOID_RADIUS:
                steer_x -= dx / dist
                steer_y -= dy / dist

        steer_x, steer_y = limit_vector((steer_x, steer_y), ROBOT_SPEED)
        self.x = max(0, min(WIDTH, self.x + steer_x))
        self.y = max(0, min(HEIGHT, self.y + steer_y))

    def draw(self, surface):
        pygame.draw.circle(surface, ROBOT_COLOR, (int(self.x), int(self.y)), 6)

# --- Initialization ---
sheep_list = [Sheep() for _ in range(NUM_SHEEP)]
predator_list = [Predator() for _ in range(NUM_PREDATORS)]
robot_list = [Robot(random.randint(0, WIDTH), random.randint(0, HEIGHT), i, None) for i in range(NUM_ROBOTS)]
for r in robot_list:
    r.robots = robot_list
obstacle_list = [Obstacle() for _ in range(NUM_OBSTACLES)]

# --- Main Loop ---
running = True
while running:
    clock.tick(60)
    screen.fill(BG_COLOR)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Draw obstacles
    for obs in obstacle_list:
        obs.draw(screen)

    # Update & draw sheep
    for sheep in sheep_list:
        sheep.update(sheep_list, predator_list, obstacle_list)
        sheep.draw(screen)

    # Update & draw predator
    if any(s.alive for s in sheep_list):
        for predator in predator_list:
            predator.update(sheep_list)
            predator.draw(screen)

    # Assign V-formation toward predator
    alive_sheep = [s for s in sheep_list if s.alive]
    if alive_sheep and predator_list:
        cx = sum(s.x for s in alive_sheep) / len(alive_sheep)
        cy = sum(s.y for s in alive_sheep) / len(alive_sheep)
        predator = predator_list[0]
        assign_v_formation(robot_list, cx, cy, predator.x, predator.y)

    # Update & draw robots
    for robot in robot_list:
        robot.update(sheep_list, predator_list, obstacle_list)
        robot.draw(screen)

    # Display stats
    font = pygame.font.SysFont(None, 24)
    alive_count = sum(s.alive for s in sheep_list)
    text = font.render(f"Sheep Remaining: {alive_count}", True, (255, 255, 255))
    screen.blit(text, (10, 10))

    pygame.display.flip()

pygame.quit()