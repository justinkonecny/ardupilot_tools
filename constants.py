CONNECTION = "udpin:0.0.0.0:14540"

PREFIX_SD = "SD"
PREFIX_GPS = "GPS"
PREFIX_SPF = "SPF"

MSG_PREFIX_SD = "S"
MSG_PREFIX_GPS = "G"
MSG_PREFIX_SPF = "SPF"

GROUND_SPEED = "GS"
VELOCITY_X = "VX"
VELOCITY_Y = "VY"
VELOCITY_Z = "VZ"
SAT_COUNT = "SC"

GROUND_SPEED_DIFF = "GSD"
VELOCITY_X_DIFF = "VXD"
VELOCITY_Y_DIFF = "VYD"
VELOCITY_Z_DIFF = "VZD"

REGEX_SD = "\[(.+)\](.+);(.+);(.+);(.+)"  # "S0[%lu]%d;%d;%d;%d": gs, vx, vy, vz

REGEX_GPS = "\[(.+)\](.+);(.+);(.+);(.+);(.+)"  # "G0[%lu]%d;%u;%d;%d;%d": gs, sc, vx, vy, vz

REGEX_SPF = "\[(.+)\](.+);(.+);(.+);(.+)"  # "SPF[%lu]%d;%d;%d;%d": gs_diff, vx_diff, vy_diff, vz_diff
