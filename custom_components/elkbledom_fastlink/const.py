from enum import Enum

# =========================================================
# Основные константы
# =========================================================
DOMAIN = "elkbledom_fastlink"
CONF_RESET = "reset"
CONF_DELAY = "delay"

# =========================================================
# Эффекты (анимации)
# =========================================================
class EFFECTS(Enum):
    jump_red_green_blue = 0x87
    jump_red_green_blue_yellow_cyan_magenta_white = 0x88
    crossfade_red_green_blue = 0x89
    crossfade_red_green_blue_yellow_cyan_magenta_white = 0x8A
    crossfade_red = 0x8B
    crossfade_green = 0x8C
    crossfade_blue = 0x8D
    crossfade_yellow = 0x8E
    crossfade_cyan = 0x8F
    crossfade_magenta = 0x90
    crossfade_white = 0x91
    crossfade_red_green = 0x92
    crossfade_red_blue = 0x93
    crossfade_green_blue = 0x94
    blink_red_green_blue_yellow_cyan_magenta_white = 0x95
    blink_red = 0x96
    blink_green = 0x97
    blink_blue = 0x98
    blink_yellow = 0x99
    blink_cyan = 0x9A
    blink_magenta = 0x9B
    blink_white = 0x9C


# =========================================================
# Упрощённые списки и мапы
# =========================================================
EFFECTS_list = [e.name for e in EFFECTS]
EFFECTS_MAP = {e.name: e.value for e in EFFECTS}


# =========================================================
# Дни недели (для таймеров и расписаний)
# =========================================================
class WEEK_DAYS(Enum):
    monday = 0x01
    tuesday = 0x02
    wednesday = 0x04
    thursday = 0x08
    friday = 0x10
    saturday = 0x20
    sunday = 0x40
    all = 0x7F
    week_days = 0x1F
    weekend_days = 0x60
    none = 0x00


# =========================================================
# Проверка (отладка)
# =========================================================
if __name__ == "__main__":
    print("All effects:", EFFECTS_list)
    print("Example: blink_white =", hex(EFFECTS_MAP["blink_white"]))
