from constants import *
from reader import Reader

import matplotlib.pyplot as plt


class Analyze:
    def __init__(self, r: Reader):
        self.r = r

    def cmp_ground_speed(self):
        sd_list_time = []
        sd_list_gs = []
        for t in self.r.get_sd_log(GROUND_SPEED):  # list of (time_ms, gs)
            sd_list_time.append(t[0])
            sd_list_gs.append(t[1])

        gps_list_time = []
        gps_list_gs = []
        for t in self.r.get_gps_log(GROUND_SPEED):  # list of (time_ms, gs)
            gps_list_time.append(t[0])
            gps_list_gs.append(t[1])

        plt.plot(sd_list_time, sd_list_gs, color="green", label="Sensors")
        plt.plot(gps_list_time, gps_list_gs, color="red", label="GPS")
        plt.xlabel("Time (ms)")
        plt.ylabel("Speed (cm/s)")
        plt.title("Ground Speed")
        plt.legend()
        plt.show()
