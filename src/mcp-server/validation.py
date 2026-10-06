import re

def validate_grid_id(grid_id: int) -> int:
    if not isinstance(grid_id, int):
        raise ValueError("grid_id must be an integer")

    if grid_id <= 0:
        raise ValueError("grid_id must be positive")

    return grid_id

def validate_limit(limit: int) -> int:
    if not isinstance(limit, int):
        raise ValueError("limit must be an integer")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    return limit
