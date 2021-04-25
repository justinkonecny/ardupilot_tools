from math import sqrt
from threading import Lock

import matplotlib.pyplot as plt

from constants import *
from reader import Reader


class Analyzer:
    def __init__(self, r: Reader, lock: Lock):
        self.r = r
        self.mutex = lock
        self.run = False

    def cmp_ground_speed(self):
        key = GROUND_SPEED
        title = "Ground Speed"
        y_label = "Speed (cm/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_x(self):
        key = VELOCITY_X
        title = "Velocity (X)"
        y_label = "Velocity (cm/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_y(self):
        key = VELOCITY_Y
        title = "Velocity (Y)"
        y_label = "Velocity (cm/s)"
        self.compare_value(key, title, y_label)

    def cmp_velocity_z(self):
        key = VELOCITY_Z
        title = "Velocity (Z)"
        y_label = "Velocity (cm/s)"
        self.compare_value(key, title, y_label)

    def cmp_altitude(self):
        key = ALTITUDE
        title = "Altitude"
        y_label = "Altitude (cm)"
        self.compare_value(key, title, y_label)

    def show_sat_count(self):
        gps_sc_raw = self.r.get_gps_log_by_key(SAT_COUNT)  # list of (time_ms, count)
        if len(gps_sc_raw) == 0:
            return

        gps_list_time, gps_list_count = self.get_plot_values(gps_sc_raw)

        title = "Satellite Count"
        x_label = "Time (ms)"
        y_label = "Satellite Count"
        self.create_plot(title, x_label, y_label, gps_list_time, gps_list_count)

    def show_spf_diff(self):
        spf_gs_raw = self.r.get_spf_log_by_key(GROUND_SPEED_DIFF)  # list of (time_ms, diff)
        spf_vx_raw = self.r.get_spf_log_by_key(VELOCITY_X_DIFF)  # list of (time_ms, diff)
        spf_vy_raw = self.r.get_spf_log_by_key(VELOCITY_Y_DIFF)  # list of (time_ms, diff)
        spf_vz_raw = self.r.get_spf_log_by_key(VELOCITY_Z_DIFF)  # list of (time_ms, diff)
        spf_alt_raw = self.r.get_spf_log_by_key(ALTITUDE_DIFF)  # list of (time_ms, diff)

        if len(spf_gs_raw) == 0 \
                and len(spf_vx_raw) == 0 \
                and len(spf_vy_raw) == 0 \
                and len(spf_vz_raw) == 0 \
                and len(spf_alt_raw) == 0:
            return

        spf_list_time, spf_list_gsd = self.get_plot_values(spf_gs_raw)
        _, spf_list_vxd = self.get_plot_values(spf_vx_raw)
        _, spf_list_vyd = self.get_plot_values(spf_vy_raw)
        _, spf_list_vzd = self.get_plot_values(spf_vz_raw)
        _, spf_list_altd = self.get_plot_values(spf_alt_raw)

        title = "SPF Threshold Differences"
        x_label = "Time (ms)"
        y_label = "Threshold Differences (cm)"

        self.create_spf_plot(title, x_label, y_label, spf_list_time, spf_list_gsd, spf_list_vxd, spf_list_vyd, spf_list_vzd, spf_list_altd)

    def compare_value(self, key, title, y_label):
        uninhibited_raw = self.r.get_uninhibited_log_by_key(key)  # list of (time_ms, val)
        inhibited_raw = self.r.get_inhibited_log_by_key(key)  # list of (time_ms, val)
        gps_raw = self.r.get_gps_log_by_key(key)  # list of (time_ms, val)
        if len(inhibited_raw) == 0 or len(gps_raw) == 0:
            return

        uninhibited_list_time, uninhibited_list_val = self.get_plot_values(uninhibited_raw)
        inhibited_list_time, inhibited_list_val = self.get_plot_values(inhibited_raw)
        gps_list_time, gps_list_val = self.get_plot_values(gps_raw)

        uninhibited_time = int((uninhibited_list_time[-1] - uninhibited_list_time[0]) / 1000)
        inhibited_time = int((inhibited_list_time[-1] - inhibited_list_time[0]) / 1000)
        gps_time = int((gps_list_time[-1] - gps_list_time[0]) / 1000)
        max_time = max(uninhibited_time, gps_time, inhibited_time)

        print("%s (%d sec): (%d inhibited, %d uninhibited, %d GPS)" % (title.ljust(13), max_time, len(inhibited_raw), len(uninhibited_raw), len(gps_raw)))

        self.create_comparison_plot(title, "Time (ms)", y_label, uninhibited_list_time, uninhibited_list_val, inhibited_list_time, inhibited_list_val,
                                    gps_list_time, gps_list_val)

    def get_plot_values(self, tuple_list: list) -> tuple:
        list_time = []
        list_val = []
        for t in tuple_list:
            list_time.append(t[0])
            list_val.append(t[1])

        return list_time, list_val

    def create_comparison_plot(self, title, x_label, y_label, unin_x_vals, unin_y_vals, in_x_vals, in_y_vals, gps_x_vals, gps_y_vals):
        plt.plot(unin_x_vals, unin_y_vals, color="green", label="Uninhibited (w/ GPS)", markersize=4, marker='o', linestyle='dashed')
        plt.plot(in_x_vals, in_y_vals, color="red", label="Inhibited (w/o GPS)", markersize=5, marker='*')
        plt.plot(gps_x_vals, gps_y_vals, color="blue", label="GPS", markersize=4, marker='o', linestyle='dashed')

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend()
        plt.show()

    def create_spf_plot(self, title, x_label, y_label, x_vals, gsd_vals, vxd_vals, vyd_vals, vzd_vals, altd_vals):
        plt.plot(x_vals, gsd_vals, color="orange", label="Ground Speed Diff", markersize=4, marker='o')
        plt.plot(x_vals, vxd_vals, color="blue", label="Velocity X Diff", markersize=4, marker='o')
        plt.plot(x_vals, vyd_vals, color="red", label="Velocity Y Diff", markersize=4, marker='o')
        plt.plot(x_vals, vzd_vals, color="green", label="Velocity Z Diff", markersize=4, marker='o')
        plt.plot(x_vals, altd_vals, color="yellow", label="Altitude Diff", markersize=4, marker='o')

        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend()
        plt.show()

    def create_plot(self, title, x_label, y_label, x_vals, y_vals, x_lim: tuple = None, y_lim: tuple = None):
        plt.plot(x_vals, y_vals, color="blue", markersize=4, marker='o')
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)

        if x_lim and len(x_lim) == 2:
            plt.xlim(x_lim)
        if y_lim and len(y_lim) == 2:
            plt.ylim(y_lim)

        plt.show()

    def get_time_dict(self, tuple_list: list) -> dict:
        time_dict = {}
        for t in tuple_list:
            time_dict[t[0]] = t[1]
        return time_dict

    def get_max_thresholds(self) -> dict:
        inhibited_logs = self.r.get_inhibited_log_full()
        gps_logs = self.r.get_gps_log_full()
        thresholds = {}

        for key, tuple_list_sd in inhibited_logs.items():
            if len(tuple_list_sd) == 0 or key not in gps_logs:
                continue

            gps_time_dict = self.get_time_dict(gps_logs[key])

            for t_sd in tuple_list_sd:
                time_ms = t_sd[0]
                val_sd = t_sd[1]
                val_gps = gps_time_dict.get(time_ms)

                if val_gps is None:
                    continue

                diff = abs(val_sd - val_gps)
                thresholds[key] = diff

        return thresholds

    def get_all_csv_list(self) -> dict:
        inhibited_logs = self.r.get_inhibited_log_full()
        gps_logs = self.r.get_gps_log_full()
        all_csvs = {}

        for key, tuple_list_sd in inhibited_logs.items():
            if len(tuple_list_sd) == 0 or key not in gps_logs:
                continue

            gps_time_dict = self.get_time_dict(gps_logs[key])

            tuple_list_sc = self.r.get_gps_log_by_key(SAT_COUNT)
            sc_time_dict = self.get_time_dict(tuple_list_sc)

            plot_time_list = []
            plot_diff_list = []
            plot_diff_sq_list = []

            csv = ["Time (ms),SD Value,GPS Value,Satellite Count,Difference,Difference Squared,,Average Difference,Average Difference Squared\n"]

            for t_sd in tuple_list_sd:
                time_ms = t_sd[0]
                val_sd = t_sd[1]

                val_gps = gps_time_dict.get(time_ms)
                val_sc = sc_time_dict.get(time_ms)

                if val_gps is None:
                    continue
                if val_sc is None:
                    val_sc = ""

                diff = abs(val_sd - val_gps)
                diff_sq = diff ** 2

                plot_time_list.append(time_ms)
                plot_diff_list.append(diff)
                plot_diff_sq_list.append(diff_sq)

                line = "{},{},{},{},{},{}\n".format(time_ms, val_sd, val_gps, val_sc, diff, diff_sq)
                csv.append(line)

            diff_avg = sum(plot_diff_list) / len(plot_diff_list)
            diff_sq_avg = sqrt(sum(plot_diff_sq_list) / len(plot_diff_sq_list))

            csv[1] = csv[1][:-1] + ",,{},{}\n".format(diff_avg, diff_sq_avg)

            all_csvs[key] = csv

            y_lim = (0, 600)
            self.create_plot("IEKF2/GPS Diff {}".format(key), "Time (ms)", "Difference (cm)", plot_time_list, plot_diff_list, None, y_lim)
            # self.create_plot("IEKF2/GPS Diff {}".format(key), "Time (ms)", "Difference Squared", plot_time_list, plot_diff_sq_list, None, y_lim)

        return all_csvs
