"""Compute engagement rate = (likes + comments + shares) / followers."""


def engagement_rate(likes: int, comments: int, shares: int, followers: int | None) -> float | None:
    if not followers or followers <= 0:
        return None
    return round((likes + comments + shares) / followers, 4)
