"""Personal levels start at 1 and require 100 XP per level."""

XP_PER_LEVEL = 100


def level_progress(total_xp):
    level, xp_in_level = divmod(total_xp, XP_PER_LEVEL)
    return {
        "level": level + 1,
        "xp_in_level": xp_in_level,
        "xp_per_level": XP_PER_LEVEL,
        "xp_to_next_level": XP_PER_LEVEL - xp_in_level,
    }
