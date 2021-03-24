CONNECTION = "udpin:0.0.0.0:14540"

PREFIX_SD = "SD"
PREFIX_GPS = "GPS"

GROUND_SPEED = "GS"
GROUND_COURSE = "GC"
AIRSPEED = "AS"
VELOCITY_X = "VX"
VELOCITY_Y = "VY"
VELOCITY_Z = "VZ"
WIND_SPEED_X = "WX"
WIND_SPEED_Y = "WY"
WIND_SPEED_Z = "WZ"
POS_REL_HOME_X ="PHX"
POS_REL_HOME_Y ="PHY"
POS_REL_HOME_Z ="PHZ"
SAT_COUNT = "SC"

REGEX_SD = (
    "\[(.+)\] GSX: (.+); GSY: (.+)",
    "\[(.+)\] AS: (.+); VX: (.+)",
    "\[(.+)\] VY: (.+); VZ: (.+)",
    "\[(.+)\] WX: (.+); WY: (.+)",
    "\[(.+)\] WZ: (.+); PHX: (.+)",
    "\[(.+)\] PHY: (.+); PHZ: (.+)"
)

REGEX_GPS = (
    "\[(.+)\] GS: (.+); GC: (.+)",
    "\[(.+)\] SC: (.+); VX: (.+)",
    "\[(.+)\] VY: (.+); VZ: (.+)"
)
