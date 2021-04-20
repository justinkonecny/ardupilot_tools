CONNECTION = "udpin:0.0.0.0:14540"

PREFIX_EKF_U = "EKF_U"
PREFIX_EKF_I = "EKF_I"
PREFIX_GPS = "GPS"
PREFIX_SPF = "SPF"
PREFIX_INIT_ALT = "INIT_ALT"

MSG_PREFIX_EKF_U = "U"
MSG_PREFIX_EKF_I = "I"
MSG_PREFIX_GPS = "G"
MSG_PREFIX_SPF = "SPF"

MSG_PREFIX_INIT_ALT = "Setting"

GROUND_SPEED = "GS"
VELOCITY_X = "VX"
VELOCITY_Y = "VY"
VELOCITY_Z = "VZ"
SAT_COUNT = "SC"
ALTITUDE = "ALT"

GROUND_SPEED_DIFF = "GSD"
VELOCITY_X_DIFF = "VXD"
VELOCITY_Y_DIFF = "VYD"
VELOCITY_Z_DIFF = "VZD"
ALTITUDE_DIFF = "ALTD"

REGEX_EKF_U = "\[(.+)\](.+);(.+);(.+);(.+);(.+)"  # "U[%lu]%d;%d;%d;%d;%d": gs, vx, vy, vz, alt
REGEX_EKF_I = "\[(.+)\](.+);(.+);(.+);(.+);(.+)"  # "I[%lu]%d;%d;%d;%d;%d": gs, vx, vy, vz, alt

REGEX_GPS = "\[(.+)\](.+);(.+);(.+);(.+);(.+);(.+)"  # "G[%lu]%d;%u;%d;%d;%d;%d": gs, sc, vx, vy, vz, alt

REGEX_SPF = "\[(.+)\](.+);(.+);(.+);(.+);(.+)"  # "SPF[%lu]%d;%d;%d;%d;%d": gs_diff, vx_diff, vy_diff, vz_diff, alt_diff

REGEX_INIT_ALT = "Setting GPS Initial Altitude: (.+) cm"