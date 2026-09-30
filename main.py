import pygame
import sys
import math
import random

from settings import *
from pathfinding import a_star, manhattan_distance
from level import LEVEL_1_MAP, LEVEL_2_MAP, LEVELS
from enemy import ENEMY_TYPES, create_enemies, update_enemies
from player import (
    create_player,
    update_player,
    move_player,
    dash_player,
    get_dash_status,
)

# ==================================================
# FLOWFORGE - ADAPTIVE AI DUNGEON
# ==================================================

pygame.init()

try:
    pygame.mixer.init()
except pygame.error:
    print("Warning: Audio mixer could not initialize.")


# ==================================================
# AUDIO
# ==================================================

def load_sound(path, volume=0.5):
    try:
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        return sound
    except Exception as e:
        print(f"Could not load {path}: {e}")
        return None


shoot_sound = load_sound("sounds/shoot.wav", 0.30)
explosion_sound = load_sound("sounds/explosion.wav", 0.40)
damage_sound = load_sound("sounds/damage.wav", 0.50)
core_sound = load_sound("sounds/core.wav", 0.50)
win_sound = load_sound("sounds/win.wav", 0.60)


def play_sound(sound):
    if sound is not None:
        sound.play()


# ==================================================
# WINDOW
# ==================================================

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("FLOWFORGE - AI Adaptive Dungeon")
clock = pygame.time.Clock()


# ==================================================
# FONTS
# ==================================================

title_font = pygame.font.Font(None, 40)
hud_font = pygame.font.Font(None, 25)
small_font = pygame.font.Font(None, 18)
big_font = pygame.font.Font(None, 68)


# ==================================================
# GAME VARIABLES
# ==================================================

current_level = 1
dungeon = LEVEL_1_MAP

player = create_player(LEVELS[1]["player"])
player["health"] = 3
player["max_health"] = 3

core_row, core_col = LEVELS[1]["core"]
core_collected = False

exit_row, exit_col = LEVELS[1]["exit"]
exit_unlocked = False

enemies = []
lasers = []
enemy_bullets = []

particles = []
ambient_particles = []

hint_positions = []

move_count = 0
moves_without_progress = 0
last_distance = None
assistance_level = 1

shake_strength = 0
shake_timer = 0

message = ""
message_timer = 0

game_over = False
game_won = False
level_complete = False

dash_trails = []


# ==================================================
# AMBIENT PARTICLES
# ==================================================

for _ in range(100):
    ambient_particles.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "speed": random.uniform(5, 25),
        "size": random.choice([1, 1, 1, 2])
    })


# ==================================================
# PARTICLES
# ==================================================

def create_particles(x, y, color, count, speed, lifetime):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        particle_speed = random.uniform(speed * 0.4, speed)

        particles.append({
            "x": x,
            "y": y,
            "dx": math.cos(angle) * particle_speed,
            "dy": math.sin(angle) * particle_speed,
            "life": random.uniform(lifetime * 0.5, lifetime),
            "max_life": lifetime,
            "color": color
        })


def create_explosion(x, y):
    play_sound(explosion_sound)

    create_particles(x, y, RED, 25, 250, 0.8)
    create_particles(x, y, ORANGE, 15, 180, 0.6)


# ==================================================
# SHOOT LASER
# ==================================================

def shoot_laser():
    global shake_strength, shake_timer

    play_sound(shoot_sound)

    dr, dc = player["direction"]

    # Convert grid direction into pixel direction
    dx = dc
    dy = dr

    lasers.append({
        "x": player["col"] * CELL_SIZE + CELL_SIZE // 2,
        "y": player["row"] * CELL_SIZE + CELL_SIZE // 2,
        "dx": dx,
        "dy": dy,
        "life": 1.2,
        "trail": []
    })

    shake_strength = 4
    shake_timer = 0.12


# ==================================================
# LOAD LEVEL
# ==================================================

def load_level(level):
    global current_level, dungeon
    global player
    global core_row, core_col, core_collected
    global exit_row, exit_col, exit_unlocked
    global enemies, hint_positions
    global moves_without_progress, last_distance
    global assistance_level
    global lasers, enemy_bullets, particles, dash_trails
    global message, message_timer, move_count

    current_level = level

    if level == 1:
        dungeon = LEVEL_1_MAP
    else:
        dungeon = LEVEL_2_MAP

    config = LEVELS[level]

    old_max_health = player.get(
        "max_health", 3) if isinstance(player, dict) else 3

    player = create_player(config["player"])
    player["max_health"] = old_max_health
    player["health"] = old_max_health

    core_row, core_col = config["core"]
    core_collected = False

    exit_row, exit_col = config["exit"]
    exit_unlocked = False

    enemies = create_enemies(config)

    hint_positions = []
    moves_without_progress = 0
    last_distance = None
    assistance_level = 1
    move_count = 0

    lasers = []
    enemy_bullets = []
    particles = []
    dash_trails = []

    message = f"LEVEL {level} STARTED"
    message_timer = 2.5


# ==================================================
# RESTART
# ==================================================

def restart_game():
    global player, game_over, game_won, level_complete

    player = create_player(LEVELS[1]["player"])
    player["health"] = 3
    player["max_health"] = 3

    game_over = False
    game_won = False
    level_complete = False

    load_level(1)


# ==================================================
# INITIAL LEVEL
# ==================================================

load_level(1)


# ==================================================
# MAIN LOOP
# ==================================================

running = True

while running:

    delta_time = clock.tick(FPS) / 1000
    game_time = pygame.time.get_ticks() / 1000

    # ----------------------------------------------
    # TIMERS
    # ----------------------------------------------

    if message_timer > 0:
        message_timer -= delta_time

    update_player(player, delta_time)

    if shake_timer > 0:
        shake_timer -= delta_time
    else:
        shake_strength = 0

    # ----------------------------------------------
    # AMBIENT PARTICLES
    # ----------------------------------------------

    for particle in ambient_particles:
        particle["y"] += particle["speed"] * delta_time

        if particle["y"] > HEIGHT:
            particle["y"] = 0
            particle["x"] = random.randint(0, WIDTH)

    # ----------------------------------------------
    # DASH TRAILS
    # ----------------------------------------------

    for trail in dash_trails[:]:
        trail["life"] -= delta_time
        if trail["life"] <= 0:
            dash_trails.remove(trail)

    # ----------------------------------------------
    # EVENTS
    # ----------------------------------------------

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_r:
                restart_game()
                continue

            if level_complete:
                if event.key == pygame.K_RETURN:
                    level_complete = False
                    load_level(2)
                continue

            if game_over or game_won:
                continue

            # --------------------------------------
            # FIRE
            # --------------------------------------

            if event.key == pygame.K_SPACE:
                shoot_laser()

            # --------------------------------------
            # DASH
            # --------------------------------------

            elif event.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):

                old_row = player["row"]
                old_col = player["col"]

                if dash_player(
                    player,
                    dungeon,
                    ROWS,
                    COLS,
                    dash_distance=3
                ):

                    # Create trail at every crossed cell
                    dr = player["row"] - old_row
                    dc = player["col"] - old_col

                    steps = max(abs(dr), abs(dc))

                    for step in range(steps + 1):
                        row = old_row + (
                            int(step * dr / steps)
                            if steps else 0
                        )
                        col = old_col + (
                            int(step * dc / steps)
                            if steps else 0
                        )

                        dash_trails.append({
                            "row": row,
                            "col": col,
                            "life": 0.35,
                            "max_life": 0.35
                        })

                    shake_strength = 6
                    shake_timer = 0.10

            # --------------------------------------
            # AI HINT
            # --------------------------------------

            elif event.key == pygame.K_h:

                if not core_collected:
                    target = (core_row, core_col)
                else:
                    target = (exit_row, exit_col)

                path = a_star(
                    (player["row"], player["col"]),
                    target,
                    dungeon,
                    ROWS,
                    COLS
                )

                hint_positions = path[1:7]

            # --------------------------------------
            # PLAYER MOVEMENT
            # --------------------------------------

            else:

                dr = 0
                dc = 0

                if event.key in (pygame.K_w, pygame.K_UP):
                    dr = -1

                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    dr = 1

                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    dc = -1

                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    dc = 1

                if dr != 0 or dc != 0:

                    moved = move_player(
                        player,
                        dr,
                        dc,
                        dungeon,
                        ROWS,
                        COLS
                    )

                    if moved:

                        move_count += 1

                        if not core_collected:
                            target = (core_row, core_col)
                        else:
                            target = (exit_row, exit_col)

                        current_distance = manhattan_distance(
                            (player["row"], player["col"]),
                            target
                        )

                        if last_distance is not None:
                            if current_distance < last_distance:
                                moves_without_progress = 0
                            else:
                                moves_without_progress += 1

                        last_distance = current_distance

                        if moves_without_progress <= 2:
                            assistance_level = 1
                        elif moves_without_progress <= 5:
                            assistance_level = 2
                        else:
                            assistance_level = 3

                        if assistance_level >= 2:

                            path = a_star(
                                (player["row"], player["col"]),
                                target,
                                dungeon,
                                ROWS,
                                COLS
                            )

                            if assistance_level == 2:
                                hint_positions = path[1:3]
                            else:
                                hint_positions = path[1:7]

    # ==================================================
    # GAME LOGIC
    # ==================================================

    if not game_over and not game_won and not level_complete:

        # ----------------------------------------------
        # CORE
        # ----------------------------------------------

        if (
            not core_collected
            and player["row"] == core_row
            and player["col"] == core_col
        ):

            core_collected = True
            exit_unlocked = True

            play_sound(core_sound)

            message = "CORE ACQUIRED // EXIT ONLINE"
            message_timer = 3

            create_particles(
                core_col * CELL_SIZE + CELL_SIZE // 2,
                core_row * CELL_SIZE + CELL_SIZE // 2,
                YELLOW,
                45,
                220,
                1
            )

        # ----------------------------------------------
        # ENEMY AI
        # ----------------------------------------------

        update_enemies(
            enemies,
            player["row"],
            player["col"],
            dungeon,
            ROWS,
            COLS,
            current_level,
            LEVELS[current_level],
            assistance_level,
            delta_time,
            enemy_bullets
        )

        # ----------------------------------------------
        # PLAYER LASERS
        # ----------------------------------------------

        for laser in lasers[:]:

            laser["trail"].append((laser["x"], laser["y"]))

            if len(laser["trail"]) > 10:
                laser["trail"].pop(0)

            laser["x"] += laser["dx"] * 600 * delta_time
            laser["y"] += laser["dy"] * 600 * delta_time
            laser["life"] -= delta_time

            laser_col = int(laser["x"] // CELL_SIZE)
            laser_row = int(laser["y"] // CELL_SIZE)

            remove_laser = False

            if (
                laser_row < 0 or laser_row >= ROWS
                or laser_col < 0 or laser_col >= COLS
            ):
                remove_laser = True

            elif dungeon[laser_row][laser_col] == 1:
                remove_laser = True

            else:

                for enemy in enemies:

                    if not enemy["alive"]:
                        continue

                    enemy_x = (
                        enemy["col"] * CELL_SIZE
                        + CELL_SIZE // 2
                    )

                    enemy_y = (
                        enemy["row"] * CELL_SIZE
                        + CELL_SIZE // 2
                    )

                    distance = math.hypot(
                        laser["x"] - enemy_x,
                        laser["y"] - enemy_y
                    )

                    if distance < 24:

                        enemy["health"] -= 1
                        enemy["disabled_timer"] = 0.5

                        create_explosion(enemy_x, enemy_y)

                        remove_laser = True

                        if enemy["health"] <= 0:
                            enemy["alive"] = False
                            enemy["state"] = "DESTROYED"

                        break

            if remove_laser or laser["life"] <= 0:
                if laser in lasers:
                    lasers.remove(laser)

        # ----------------------------------------------
        # ENEMY BULLETS
        # ----------------------------------------------

        for bullet in enemy_bullets[:]:

            bullet["x"] += (
                bullet["dx"]
                * bullet["speed"]
                * delta_time
            )

            bullet["y"] += (
                bullet["dy"]
                * bullet["speed"]
                * delta_time
            )

            bullet["life"] -= delta_time

            bullet_col = int(bullet["x"] // CELL_SIZE)
            bullet_row = int(bullet["y"] // CELL_SIZE)

            remove_bullet = False

            if (
                bullet_row < 0 or bullet_row >= ROWS
                or bullet_col < 0 or bullet_col >= COLS
            ):
                remove_bullet = True

            elif dungeon[bullet_row][bullet_col] == 1:

                create_particles(
                    bullet["x"],
                    bullet["y"],
                    bullet["color"],
                    8,
                    100,
                    0.3
                )

                remove_bullet = True

            else:

                player_x = (
                    player["col"] * CELL_SIZE
                    + CELL_SIZE // 2
                )

                player_y = (
                    player["row"] * CELL_SIZE
                    + CELL_SIZE // 2
                )

                distance = math.hypot(
                    bullet["x"] - player_x,
                    bullet["y"] - player_y
                )

                if (
                    distance < 20
                    and not player["invincible"]
                ):

                    player["health"] -= bullet["damage"]

                    play_sound(damage_sound)

                    player["invincible"] = True

                    # Normal hit invincibility
                    # Dash invincibility is handled by player.py.
                    if not player["is_dashing"]:
                        player["dash_duration_timer"] = max(
                            player["dash_duration_timer"],
                            1.0
                        )

                    create_explosion(player_x, player_y)

                    shake_strength = 10
                    shake_timer = 0.25

                    remove_bullet = True

                    if player["health"] <= 0:
                        player["health"] = 0
                        game_over = True

            if remove_bullet or bullet["life"] <= 0:
                if bullet in enemy_bullets:
                    enemy_bullets.remove(bullet)

        # ----------------------------------------------
        # PARTICLES UPDATE
        # ----------------------------------------------

        for particle in particles[:]:

            particle["x"] += particle["dx"] * delta_time
            particle["y"] += particle["dy"] * delta_time
            particle["life"] -= delta_time

            if particle["life"] <= 0:
                particles.remove(particle)

        # ----------------------------------------------
        # PLAYER CONTACT DAMAGE
        # ----------------------------------------------

        for enemy in enemies:

            if (
                enemy["alive"]
                and enemy["disabled_timer"] <= 0
                and enemy["row"] == player["row"]
                and enemy["col"] == player["col"]
                and not player["invincible"]
            ):

                damage = (
                    2
                    if enemy["type"] == "TANK"
                    else 1
                )

                player["health"] -= damage

                if player["health"] < 0:
                    player["health"] = 0

                play_sound(damage_sound)

                # Give a short normal hit protection.
                player["invincible"] = True
                player["dash_duration_timer"] = 1.0
                player["is_dashing"] = True

                create_explosion(
                    player["col"] * CELL_SIZE + CELL_SIZE // 2,
                    player["row"] * CELL_SIZE + CELL_SIZE // 2
                )

                shake_strength = 10
                shake_timer = 0.25

                if player["health"] <= 0:
                    game_over = True

                break

        # ----------------------------------------------
        # EXIT
        # ----------------------------------------------

        if (
            exit_unlocked
            and player["row"] == exit_row
            and player["col"] == exit_col
        ):

            play_sound(win_sound)

            if current_level == 1:

                level_complete = True

                message = "LEVEL 1 COMPLETE"
                message_timer = 3

            else:
                game_won = True

    # ==================================================
    # SCREEN SHAKE
    # ==================================================

    if shake_timer > 0:

        offset_x = random.randint(
            -int(shake_strength),
            int(shake_strength)
        )

        offset_y = random.randint(
            -int(shake_strength),
            int(shake_strength)
        )

    else:
        offset_x = 0
        offset_y = 0

    # ==================================================
    # DRAW BACKGROUND
    # ==================================================

    screen.fill(BG)

    for particle in ambient_particles:

        pygame.draw.circle(
            screen,
            (50, 70, 100),
            (
                int(particle["x"]),
                int(particle["y"])
            ),
            particle["size"]
        )

    # ==================================================
    # DRAW MAP
    # ==================================================

    for row in range(ROWS):

        for col in range(COLS):

            x = col * CELL_SIZE + offset_x
            y = row * CELL_SIZE + offset_y

            if dungeon[row][col] == 0:

                floor_color = (
                    FLOOR_1
                    if (row + col) % 2 == 0
                    else FLOOR_2
                )

                pygame.draw.rect(
                    screen,
                    floor_color,
                    (x, y, CELL_SIZE, CELL_SIZE)
                )

                pygame.draw.rect(
                    screen,
                    (25, 35, 55),
                    (x, y, CELL_SIZE, CELL_SIZE),
                    1
                )

            else:

                pygame.draw.rect(
                    screen,
                    WALL,
                    (x, y, CELL_SIZE, CELL_SIZE)
                )

                pygame.draw.rect(
                    screen,
                    WALL_BORDER,
                    (
                        x + 2,
                        y + 2,
                        CELL_SIZE - 4,
                        CELL_SIZE - 4
                    ),
                    1
                )

    # ==================================================
    # DRAW DASH TRAILS
    # ==================================================

    for trail in dash_trails:

        ratio = max(0, trail["life"] / trail["max_life"])

        trail_x = (
            trail["col"] * CELL_SIZE
            + CELL_SIZE // 2
            + offset_x
        )

        trail_y = (
            trail["row"] * CELL_SIZE
            + CELL_SIZE // 2
            + offset_y
        )

        pygame.draw.circle(
            screen,
            CYAN,
            (trail_x, trail_y),
            max(3, int(13 * ratio)),
            2
        )

    # ==================================================
    # DRAW AI HINT
    # ==================================================

    for row, col in hint_positions:

        pygame.draw.circle(
            screen,
            YELLOW,
            (
                col * CELL_SIZE + CELL_SIZE // 2 + offset_x,
                row * CELL_SIZE + CELL_SIZE // 2 + offset_y
            ),
            5
        )

    # ==================================================
    # DRAW CORE
    # ==================================================

    if not core_collected:

        core_x = (
            core_col * CELL_SIZE
            + CELL_SIZE // 2
            + offset_x
        )

        core_y = (
            core_row * CELL_SIZE
            + CELL_SIZE // 2
            + offset_y
        )

        pulse = 1 + math.sin(game_time * 4) * 0.15
        radius = int(13 * pulse)

        pygame.draw.circle(
            screen,
            ORANGE,
            (core_x, core_y),
            radius + 8
        )

        pygame.draw.circle(
            screen,
            YELLOW,
            (core_x, core_y),
            radius
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (core_x, core_y),
            4
        )

    # ==================================================
    # DRAW EXIT
    # ==================================================

    exit_x = (
        exit_col * CELL_SIZE
        + CELL_SIZE // 2
        + offset_x
    )

    exit_y = (
        exit_row * CELL_SIZE
        + CELL_SIZE // 2
        + offset_y
    )

    portal_color = (
        GREEN
        if exit_unlocked
        else (80, 90, 110)
    )

    for radius in (16, 11, 6):
        pygame.draw.circle(
            screen,
            portal_color,
            (exit_x, exit_y),
            radius,
            2
        )

    # ==================================================
    # DRAW ENEMIES
    # ==================================================

    for enemy in enemies:

        if not enemy["alive"]:
            continue

        enemy_stats = ENEMY_TYPES[enemy["type"]]
        enemy_color = enemy_stats["color"]

        enemy_x = (
            enemy["col"] * CELL_SIZE
            + CELL_SIZE // 2
            + offset_x
        )

        enemy_y = (
            enemy["row"] * CELL_SIZE
            + CELL_SIZE // 2
            + offset_y
        )

        pygame.draw.circle(
            screen,
            enemy_color,
            (enemy_x, enemy_y),
            21
        )

        if enemy["type"] == "HUNTER":

            points = [
                (enemy_x, enemy_y - 15),
                (enemy_x + 15, enemy_y + 12),
                (enemy_x - 15, enemy_y + 12)
            ]

            pygame.draw.polygon(
                screen,
                RED,
                points
            )

        elif enemy["type"] == "SCOUT":

            pygame.draw.circle(
                screen,
                YELLOW,
                (enemy_x, enemy_y),
                13
            )

            pygame.draw.circle(
                screen,
                WHITE,
                (enemy_x, enemy_y),
                5
            )

        elif enemy["type"] == "TANK":

            pygame.draw.rect(
                screen,
                PURPLE,
                (
                    enemy_x - 14,
                    enemy_y - 14,
                    28,
                    28
                )
            )

            pygame.draw.circle(
                screen,
                WHITE,
                (enemy_x, enemy_y),
                5
            )

        # Health bar
        pygame.draw.rect(
            screen,
            RED_DARK,
            (
                enemy_x - 18,
                enemy_y - 30,
                36,
                5
            )
        )

        health_width = int(
            36
            * enemy["health"]
            / enemy["max_health"]
        )

        pygame.draw.rect(
            screen,
            GREEN,
            (
                enemy_x - 18,
                enemy_y - 30,
                health_width,
                5
            )
        )

        enemy_text = small_font.render(
            enemy["type"],
            True,
            WHITE
        )

        screen.blit(
            enemy_text,
            enemy_text.get_rect(
                center=(enemy_x, enemy_y + 30)
            )
        )

    # ==================================================
    # DRAW PLAYER LASERS
    # ==================================================

    for laser in lasers:

        for point in laser["trail"]:

            pygame.draw.circle(
                screen,
                BLUE,
                (
                    int(point[0] + offset_x),
                    int(point[1] + offset_y)
                ),
                2
            )

        pygame.draw.circle(
            screen,
            CYAN,
            (
                int(laser["x"] + offset_x),
                int(laser["y"] + offset_y)
            ),
            6
        )

    # ==================================================
    # DRAW ENEMY BULLETS
    # ==================================================

    for bullet in enemy_bullets:

        bullet_x = int(
            bullet["x"] + offset_x
        )

        bullet_y = int(
            bullet["y"] + offset_y
        )

        pygame.draw.circle(
            screen,
            bullet["color"],
            (bullet_x, bullet_y),
            9
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (bullet_x, bullet_y),
            3
        )

    # ==================================================
    # DRAW PARTICLES
    # ==================================================

    for particle in particles:

        radius = max(
            1,
            int(
                particle["life"]
                / particle["max_life"]
                * 5
            )
        )

        pygame.draw.circle(
            screen,
            particle["color"],
            (
                int(particle["x"] + offset_x),
                int(particle["y"] + offset_y)
            ),
            radius
        )

    # ==================================================
    # DRAW PLAYER
    # ==================================================

    player_x = (
        player["col"] * CELL_SIZE
        + CELL_SIZE // 2
        + offset_x
    )

    player_y = (
        player["row"] * CELL_SIZE
        + CELL_SIZE // 2
        + offset_y
    )

    draw_player = True

    if (
        player["invincible"]
        and not player["is_dashing"]
        and int(game_time * 10) % 2 == 0
    ):
        draw_player = False

    if draw_player:

        glow_color = CYAN if player["is_dashing"] else BLUE_DARK

        pygame.draw.circle(
            screen,
            glow_color,
            (player_x, player_y),
            24 if player["is_dashing"] else 22
        )

        pygame.draw.circle(
            screen,
            BLUE,
            (player_x, player_y),
            15
        )

        pygame.draw.circle(
            screen,
            WHITE,
            (player_x, player_y),
            5
        )

    # ==================================================
    # HUD
    # ==================================================

    hud = pygame.Surface(
        (WIDTH, 62),
        pygame.SRCALPHA
    )

    hud.fill((5, 8, 18, 225))
    screen.blit(hud, (0, 0))

    title = title_font.render(
        f"FLOWFORGE // LEVEL {current_level}",
        True,
        BLUE
    )

    screen.blit(title, (20, 15))

    health_text = hud_font.render(
        f"HEALTH: {player['health']}/{player['max_health']}",
        True,
        RED
    )

    screen.blit(health_text, (360, 24))

    objective = (
        "FIND CORE"
        if not core_collected
        else "REACH EXIT"
    )

    objective_text = hud_font.render(
        f"OBJECTIVE: {objective}",
        True,
        YELLOW
    )

    screen.blit(objective_text, (500, 24))

    ai_text = hud_font.render(
        f"AI HELP: {assistance_level}",
        True,
        CYAN
    )

    screen.blit(ai_text, (820, 24))

    dash_text = small_font.render(
        f"DASH: {get_dash_status(player)}",
        True,
        GREEN if player["dash_timer"] <= 0 else ORANGE
    )

    screen.blit(dash_text, (20, 68))

    controls = small_font.render(
        "WASD / ARROWS: MOVE    SHIFT: DASH    SPACE: FIRE    H: AI PATH    R: RESTART",
        True,
        DARK_TEXT
    )

    screen.blit(
        controls,
        (20, HEIGHT - 25)
    )

    # ==================================================
    # MESSAGE
    # ==================================================

    if message_timer > 0:

        message_text = hud_font.render(
            message,
            True,
            WHITE
        )

        screen.blit(
            message_text,
            message_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT - 50
                )
            )
        )

    # ==================================================
    # LEVEL COMPLETE
    # ==================================================

    if level_complete:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 50, 80, 200)
        )

        screen.blit(overlay, (0, 0))

        complete_text = big_font.render(
            "LEVEL 1 COMPLETE",
            True,
            GREEN
        )

        next_text = hud_font.render(
            "PRESS ENTER TO BEGIN LEVEL 2",
            True,
            WHITE
        )

        screen.blit(
            complete_text,
            complete_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 - 30
                )
            )
        )

        screen.blit(
            next_text,
            next_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 40
                )
            )
        )

    # ==================================================
    # GAME OVER
    # ==================================================

    if game_over:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (100, 0, 20, 180)
        )

        screen.blit(overlay, (0, 0))

        over_text = big_font.render(
            "SYSTEM FAILURE",
            True,
            RED
        )

        restart_text = hud_font.render(
            "PRESS R TO RESTART",
            True,
            WHITE
        )

        screen.blit(
            over_text,
            over_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 - 25
                )
            )
        )

        screen.blit(
            restart_text,
            restart_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 40
                )
            )
        )

    # ==================================================
    # FINAL WIN
    # ==================================================

    if game_won:

        overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )

        overlay.fill(
            (0, 100, 70, 180)
        )

        screen.blit(overlay, (0, 0))

        win_text = big_font.render(
            "MISSION COMPLETE",
            True,
            GREEN
        )

        subtitle = hud_font.render(
            "FLOWFORGE PROTOCOL SUCCESSFULLY COMPLETED",
            True,
            WHITE
        )

        restart_text = hud_font.render(
            "PRESS R TO PLAY AGAIN",
            True,
            WHITE
        )

        screen.blit(
            win_text,
            win_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 - 40
                )
            )
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 15
                )
            )
        )

        screen.blit(
            restart_text,
            restart_text.get_rect(
                center=(
                    WIDTH // 2,
                    HEIGHT // 2 + 60
                )
            )
        )

    pygame.display.flip()


pygame.quit()
sys.exit()
