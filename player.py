# ==========================================
# PLAYER SYSTEM
# ==========================================

from settings import CELL_SIZE


# ==========================================
# CREATE PLAYER
# ==========================================

def create_player(start_position):

    return {

        "row": start_position[0],
        "col": start_position[1],

        "health": 5,
        "max_health": 5,

        # Direction player is facing
        "direction": (0, 1),

        # ----------------------------------
        # DASH
        # ----------------------------------

        "dash_cooldown": 1.5,
        "dash_timer": 0,

        "is_dashing": False,

        "dash_duration": 0.18,
        "dash_duration_timer": 0,

        # Temporary protection during dash
        "invincible": False

    }


# ==========================================
# UPDATE DASH COOLDOWN
# ==========================================

def update_player(player, delta_time):

    if player["dash_timer"] > 0:

        player["dash_timer"] -= delta_time

        if player["dash_timer"] < 0:
            player["dash_timer"] = 0

    if player["is_dashing"]:

        player["dash_duration_timer"] -= delta_time

        if player["dash_duration_timer"] <= 0:

            player["is_dashing"] = False
            player["invincible"] = False


# ==========================================
# MOVE PLAYER
# ==========================================

def move_player(

    player,

    dr,
    dc,

    dungeon,

    rows,
    cols

):

    new_row = player["row"] + dr
    new_col = player["col"] + dc

    # Save direction
    if dr != 0 or dc != 0:

        player["direction"] = (
            dr,
            dc
        )

    # Check boundaries
    if not (

        0 <= new_row < rows
        and
        0 <= new_col < cols

    ):

        return False

    # Check wall
    if dungeon[new_row][new_col] == 1:

        return False

    player["row"] = new_row
    player["col"] = new_col

    return True


# ==========================================
# DASH PLAYER
# ==========================================

def dash_player(

    player,

    dungeon,

    rows,
    cols,

    dash_distance=3

):

    # Dash still cooling down
    if player["dash_timer"] > 0:

        return False

    dr, dc = player["direction"]

    # No movement direction yet
    if dr == 0 and dc == 0:

        return False

    start_row = player["row"]
    start_col = player["col"]

    # Move multiple cells
    for _ in range(dash_distance):

        new_row = player["row"] + dr
        new_col = player["col"] + dc

        # Stop at boundaries
        if not (

            0 <= new_row < rows
            and
            0 <= new_col < cols

        ):

            break

        # Stop at wall
        if dungeon[new_row][new_col] == 1:

            break

        player["row"] = new_row
        player["col"] = new_col

    # Player didn't move
    if (

        player["row"] == start_row
        and
        player["col"] == start_col

    ):

        return False

    # Start cooldown
    player["dash_timer"] = (
        player["dash_cooldown"]
    )

    # Start dash state
    player["is_dashing"] = True

    player["dash_duration_timer"] = (
        player["dash_duration"]
    )

    # Temporary invincibility
    player["invincible"] = True

    return True


# ==========================================
# DASH STATUS
# ==========================================

def get_dash_status(player):

    if player["dash_timer"] <= 0:

        return "READY"

    return f"{player['dash_timer']:.1f}s"
