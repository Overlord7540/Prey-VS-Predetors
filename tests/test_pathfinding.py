from src.ai.pathfinding import a_star, bfs_shortest_path, best_move, score_moves_fcost_panic
from src.core.grid import Grid
from src.data.loader import load_map, load_tiles


def make_grid():
    return Grid(load_map(), load_tiles())


def test_bfs_finds_path_on_open_field():
    grid = make_grid()
    path = bfs_shortest_path(grid, (0, 0), (0, 3))
    assert path is not None
    assert path[0] == (0, 0)
    assert path[-1] == (0, 3)


def test_a_star_avoids_rocks():
    grid = make_grid()
    path = a_star(grid, (6, 8), (9, 8))
    assert path is not None
    for step in path:
        assert grid.is_passable(step)


def test_panic_fcost_prefers_moving_away_from_predator():
    grid = make_grid()
    prey_pos = (0, 0)
    predator_pos = (0, 1)  # predator directly east
    scores = score_moves_fcost_panic(grid, prey_pos, predator_pos, nearest_resource_pos=None)
    move = best_move(scores)
    # moving further from (0,1) should never mean moving toward it
    assert Grid.chebyshev_distance(move, predator_pos) >= Grid.chebyshev_distance(prey_pos, predator_pos)
