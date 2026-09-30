from pathfinding import a_star, manhattan_distance
from settings import RED, YELLOW, PURPLE


# ==================================================
# ENEMY TYPES
# ==================================================

ENEMY_TYPES = {

    "HUNTER": {

        "health": 4,
        "color": RED,

        "move_multiplier": 0.70,

        "detection_range": 7,

        "shoot_cooldown": 1.1,

        "bullet_speed": 420,

        "bullet_damage": 1,

        "label": "HUNTER"
    },


    "SCOUT": {

        "health": 2,
        "color": YELLOW,

        "move_multiplier": 0.45,

        "detection_range": 10,

        "shoot_cooldown": 2.2,

        "bullet_speed": 380,

        "bullet_damage": 1,

        "label": "SCOUT"
    },


    "TANK": {

        "health": 8,
        "color": PURPLE,

        "move_multiplier": 1.45,

        "detection_range": 6,

        "shoot_cooldown": 2.5,

        "bullet_speed": 300,

        "bullet_damage": 2,

        "label": "TANK"
    }

}


# ==================================================
# CREATE ENEMIES FOR A LEVEL
# ==================================================

def create_enemies(config):

    enemies = []

    for index, enemy_data in enumerate(
        config["enemy_positions"]
    ):

        position = enemy_data[0]
        enemy_name = enemy_data[1]

        enemy_stats = ENEMY_TYPES[
            enemy_name
        ]

        enemies.append({

            "row": position[0],
            "col": position[1],

            "type": enemy_name,

            "health":
                enemy_stats["health"],

            "max_health":
                enemy_stats["health"],

            "alive": True,

            "state": "PATROL",

            "last_known_position": None,

            "search_timer": 0,

            "detect_timer": 0,

            "patrol_index": 0,

            "patrol_points":
                config["enemy_patrols"][index],

            "timer": 0,

            "disabled_timer": 0,

            "shoot_timer": 0,

            "shoot_cooldown":
                enemy_stats["shoot_cooldown"]

        })

    return enemies


# ==================================================
# MOVE ENEMY USING A*
# ==================================================

def move_enemy_towards(
    enemy,
    target,
    dungeon,
    rows,
    cols
):

    path = a_star(

        (
            enemy["row"],
            enemy["col"]
        ),

        target,

        dungeon,
        rows,
        cols

    )

    if len(path) > 1:

        enemy["row"] = path[1][0]
        enemy["col"] = path[1][1]


# ==================================================
# CREATE ENEMY BULLET
# ==================================================

def create_enemy_bullet(
    enemy,
    player_row,
    player_col,
    cell_size
):

    import math

    enemy_type = ENEMY_TYPES[
        enemy["type"]
    ]

    enemy_x = (
        enemy["col"] * cell_size
        + cell_size // 2
    )

    enemy_y = (
        enemy["row"] * cell_size
        + cell_size // 2
    )

    player_x = (
        player_col * cell_size
        + cell_size // 2
    )

    player_y = (
        player_row * cell_size
        + cell_size // 2
    )

    dx = player_x - enemy_x
    dy = player_y - enemy_y

    distance = math.hypot(dx, dy)

    if distance == 0:
        return None

    dx /= distance
    dy /= distance

    return {

        "x": enemy_x,
        "y": enemy_y,

        "dx": dx,
        "dy": dy,

        "life": 2.5,

        "speed":
            enemy_type["bullet_speed"],

        "damage":
            enemy_type["bullet_damage"],

        "color":
            enemy_type["color"]

    }


# ==================================================
# UPDATE ENEMY AI
# ==================================================

def update_enemies(

    enemies,
    player_row,
    player_col,

    dungeon,
    rows,
    cols,

    current_level,
    level_config,

    assistance_level,
    delta_time,

    enemy_bullets

):

    player_position = (
        player_row,
        player_col
    )

    for enemy in enemies:

        if not enemy["alive"]:
            continue

        enemy_stats = ENEMY_TYPES[
            enemy["type"]
        ]

        # ==========================================
        # DISABLED TIMER
        # ==========================================

        if enemy["disabled_timer"] > 0:

            enemy["disabled_timer"] -= (
                delta_time
            )

        enemy_position = (

            enemy["row"],
            enemy["col"]

        )

        distance_to_player = (

            manhattan_distance(

                enemy_position,

                player_position

            )

        )

        detection_range = (

            enemy_stats[
                "detection_range"
            ]

        )

        # ==========================================
        # STATE CHANGES
        # ==========================================

        if enemy["state"] == "PATROL":

            if (
                distance_to_player
                <= detection_range
            ):

                enemy["state"] = "DETECT"

                enemy["detect_timer"] = 0.6

                enemy[
                    "last_known_position"
                ] = player_position

        elif enemy["state"] == "DETECT":

            enemy[
                "last_known_position"
            ] = player_position

            enemy[
                "detect_timer"
            ] -= delta_time

            if (
                enemy[
                    "detect_timer"
                ] <= 0
            ):

                enemy["state"] = "CHASE"

        elif enemy["state"] == "CHASE":

            if (
                distance_to_player
                <= detection_range
            ):

                enemy[
                    "last_known_position"
                ] = player_position

            else:

                enemy["state"] = "SEARCH"

                enemy[
                    "search_timer"
                ] = 4

        elif enemy["state"] == "SEARCH":

            enemy[
                "search_timer"
            ] -= delta_time

            if (
                distance_to_player
                <= detection_range
            ):

                enemy["state"] = "DETECT"

                enemy[
                    "detect_timer"
                ] = 0.6

            elif (
                enemy[
                    "search_timer"
                ] <= 0
            ):

                enemy["state"] = "PATROL"

        # ==========================================
        # ENEMY SHOOTING
        # ==========================================

        if (

            enemy["state"] == "CHASE"

            and

            enemy[
                "disabled_timer"
            ] <= 0

            and

            distance_to_player
            <= detection_range

        ):

            enemy[
                "shoot_timer"
            ] += delta_time

            if (

                enemy[
                    "shoot_timer"
                ]

                >=

                enemy[
                    "shoot_cooldown"
                ]

            ):

                bullet = create_enemy_bullet(

                    enemy,

                    player_row,
                    player_col,

                    cols * 0 + 40

                )

                if bullet is not None:

                    enemy_bullets.append(
                        bullet
                    )

                enemy[
                    "shoot_timer"
                ] = 0

        else:

            enemy[
                "shoot_timer"
            ] = 0

        # ==========================================
        # ENEMY MOVEMENT SPEED
        # ==========================================

        base_delay = (

            level_config[
                "enemy_delay"
            ]

        )

        enemy_delay = (

            base_delay

            *

            enemy_stats[
                "move_multiplier"
            ]

        )

        if enemy["state"] == "DETECT":

            enemy_delay = 999

        elif enemy["state"] == "CHASE":

            enemy_delay *= 0.85

        elif enemy["state"] == "SEARCH":

            enemy_delay *= 0.95

        # ==========================================
        # ADAPTIVE ASSISTANCE
        # ==========================================

        if assistance_level == 2:

            enemy_delay += 0.12

        elif assistance_level == 3:

            enemy_delay += 0.25

        # ==========================================
        # ENEMY MOVEMENT
        # ==========================================

        if (

            enemy[
                "disabled_timer"
            ] <= 0

        ):

            enemy[
                "timer"
            ] += delta_time

            if (

                enemy[
                    "timer"
                ]

                >=

                enemy_delay

            ):

                # PATROL
                if (

                    enemy["state"]
                    == "PATROL"

                ):

                    patrol_target = (

                        enemy[
                            "patrol_points"
                        ][
                            enemy[
                                "patrol_index"
                            ]
                        ]

                    )

                    if (

                        (
                            enemy["row"],
                            enemy["col"]
                        )

                        ==

                        patrol_target

                    ):

                        enemy[
                            "patrol_index"
                        ] = (

                            enemy[
                                "patrol_index"
                            ]

                            + 1

                        ) % len(

                            enemy[
                                "patrol_points"
                            ]

                        )

                        patrol_target = (

                            enemy[
                                "patrol_points"
                            ][
                                enemy[
                                    "patrol_index"
                                ]
                            ]

                        )

                    move_enemy_towards(

                        enemy,

                        patrol_target,

                        dungeon,
                        rows,
                        cols

                    )

                # CHASE
                elif (

                    enemy["state"]
                    == "CHASE"

                ):

                    move_enemy_towards(

                        enemy,

                        player_position,

                        dungeon,
                        rows,
                        cols

                    )

                # SEARCH
                elif (

                    enemy["state"]
                    == "SEARCH"

                    and

                    enemy[
                        "last_known_position"
                    ]

                    is not None

                ):

                    move_enemy_towards(

                        enemy,

                        enemy[
                            "last_known_position"
                        ],

                        dungeon,
                        rows,
                        cols

                    )

                enemy[
                    "timer"
                ] = 0
