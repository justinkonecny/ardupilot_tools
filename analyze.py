import matplotlib.pyplot as plt
import numpy as np

from constants import *
from reader import Reader


class Analyze:
    def __init__(self, r: Reader):
        self.r = r

    def cmp_ground_speed(self):
        key = GROUND_SPEED
        title = "Ground Speed"
        y_label = "Speed (cm/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_x(self):
        key = VELOCITY_X
        title = "Velocity (X)"
        y_label = "Velocity (m/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_y(self):
        key = VELOCITY_Y
        title = "Velocity (Y)"
        y_label = "Velocity (m/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_z(self):
        key = VELOCITY_Z
        title = "Velocity (Z)"
        y_label = "Velocity (m/s)"
        self.compare_value(key, title, y_label)

    def show_sat_count(self):
        gps_sc_raw = self.r.get_gps_log(SAT_COUNT)  # list of (time_ms, count)
        gps_list_time, gps_list_count = self.get_plot_values(gps_sc_raw)

        title = "Satellite Count"
        x_label = "Time"
        y_label = "Satellite Count"
        self.create_plot(title, x_label, y_label, gps_list_time, gps_list_count)

    def compare_value(self, key, title, y_label):
        sd_raw = self.r.get_sd_log(key)  # list of (time_ms, val)
        sd_list_time, sd_list_val = self.get_plot_values(sd_raw)

        gps_raw = self.r.get_gps_log(key)  # list of (time_ms, val)
        gps_list_time, gps_list_val = self.get_plot_values(gps_raw)

        self.create_comparison_plot(title, "Time (ms)", y_label, sd_list_time, sd_list_val, gps_list_time, gps_list_val)

    def get_plot_values(self, tuple_list: list) -> tuple:
        list_time = []
        list_val = []
        for t in tuple_list:
            list_time.append(t[0])
            list_val.append(t[1])

        return list_time, list_val

    def create_comparison_plot(self, title, x_label, y_label, sd_x_vals, sd_y_vals, gps_x_vals, gps_y_vals):
        x1 = np.array(sd_x_vals)
        y1 = np.array(sd_y_vals)

        x2 = np.array(gps_x_vals)
        y2 = np.array(gps_y_vals)

        plt.plot(x1, y1, color="green", label="Sensors", markersize=4, marker='o')
        plt.plot(x2, y2, color="red", label="GPS", markersize=4, marker='o')

        plt.fill(np.append(x1, x2[::-1]), np.append(y1, y2[::-1]), color="#EEEEEE")

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend()
        plt.show()

    def create_plot(self, title, x_label, y_label, x_vals, y_vals):
        plt.plot(x_vals, y_vals, color="blue", markersize=4, marker='o')
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.show()
