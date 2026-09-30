import heapq


# ==========================================
# MANHATTAN DISTANCE
# ==========================================

def manhattan_distance(position1, position2):

    return (
        abs(position1[0] - position2[0])
        +
        abs(position1[1] - position2[1])
    )


# ==========================================
# A* PATHFINDING ALGORITHM
# ==========================================

def a_star(start, goal, dungeon, rows, cols):

    open_list = []

    heapq.heappush(
        open_list,
        (0, start)
    )

    came_from = {}

    g_cost = {
        start: 0
    }

    moves = [

        (-1, 0),   # Up
        (1, 0),    # Down
        (0, -1),   # Left
        (0, 1)     # Right

    ]

    while open_list:

        _, current = heapq.heappop(open_list)

        # Goal reached
        if current == goal:

            path = [current]

            while current in came_from:

                current = came_from[current]

                path.append(current)

            path.reverse()

            return path

        row, col = current

        # Check all possible moves
        for dr, dc in moves:

            new_row = row + dr
            new_col = col + dc

            # Check boundaries and walls
            if (

                0 <= new_row < rows
                and
                0 <= new_col < cols
                and
                dungeon[new_row][new_col] == 0

            ):

                neighbor = (
                    new_row,
                    new_col
                )

                new_g = (
                    g_cost[current] + 1
                )

                # Update path if this route is better
                if (

                    neighbor not in g_cost
                    or
                    new_g < g_cost[neighbor]

                ):

                    g_cost[neighbor] = new_g

                    f_cost = (

                        new_g
                        +
                        manhattan_distance(
                            neighbor,
                            goal
                        )

                    )

                    heapq.heappush(

                        open_list,

                        (
                            f_cost,
                            neighbor
                        )

                    )

                    came_from[neighbor] = current

    # No path found
    return []
