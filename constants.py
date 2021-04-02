CONNECTION = "udpin:0.0.0.0:14540"

PREFIX_SD = "SD"
PREFIX_GPS = "GPS"

MSG_PREFIX_SD = "S"
MSG_PREFIX_GPS = "G"

GROUND_SPEED = "GS"
VELOCITY_X = "VX"
VELOCITY_Y = "VY"
VELOCITY_Z = "VZ"
SAT_COUNT = "SC"

REGEX_SD = (
    "\[(.+)\](.+);(.+);(.+);(.+)",  # "S0[%lu]%d;%d;%d;%d": gs, vx, vy, vz
)

REGEX_GPS = (
    "\[(.+)\](.+);(.+);(.+);(.+);(.+)",  # "G0[%lu]%d;%u;%d;%d;%d" : gs, sc, vx, vy, vz
)
