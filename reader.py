import json
import os
import re
import socket
from datetime import datetime
from threading import Lock

from pymavlink import mavutil

from constants import *


class Reader:
    def __init__(self, lock: Lock):
        self.mutex = lock
        self.connection = None
        self.run = False
        self.inhibited_data = {
            GROUND_SPEED: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: [],
            ALTITUDE: [],
        }
        self.uninhibited_data = {
            GROUND_SPEED: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: [],
            ALTITUDE: [],
        }
        self.gps_data = {
            GROUND_SPEED: [],
            SAT_COUNT: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: [],
            ALTITUDE: [],
        }
        self.spf_data = {
            GROUND_SPEED_DIFF: [],
            VELOCITY_X_DIFF: [],
            VELOCITY_Y_DIFF: [],
            VELOCITY_Z_DIFF: [],
            ALTITUDE_DIFF: [],
        }
        self.init_alt = 0

    def setup(self):
        # start a connection listening to a UDP port
        print("Starting connection: `%s`" % CONNECTION)
        self.connection = mavutil.mavlink_connection(CONNECTION)

        init_size = self.connection.port.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        self.connection.port.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, init_size * 8)
        new_size = self.connection.port.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
        print("Updating SO_RCVBUF from %d to %d" % (init_size, new_size))

        # wait for the first heartbeat
        # this sets the system and component ID of remote system for the link
        print("Waiting for heartbeat...")
        self.connection.wait_heartbeat()
        print("Heartbeat from system (system %u)" % self.connection.target_system)
        self.run = True

    def run_main_loop(self):
        while self.run:
            mavlink_msg = self.connection.recv_match(type="STATUSTEXT", blocking=True)
            text = mavlink_msg.text
            if len(text) < 8:
                continue

            if text[:len(MSG_PREFIX_INIT_ALT)] == MSG_PREFIX_INIT_ALT:
                # handle initial altitude messages
                self.handle_init_alt_msg(text)

            elif text[:len(MSG_PREFIX_SPF)] == MSG_PREFIX_SPF:
                # handle spoofing alert messages
                self.handle_spf_msg(text[len(MSG_PREFIX_SPF):])

            elif text[:len(MSG_PREFIX_EKF_U)] == MSG_PREFIX_EKF_U:
                # handle fused ahrs ekf (with gps) sensor data messages
                self.handle_uninhibited_msg(text[len(MSG_PREFIX_EKF_U):])

            elif text[:len(MSG_PREFIX_EKF_I)] == MSG_PREFIX_EKF_I:
                # handle custom ekf (without gps) sensor data messages
                self.handle_inhibited_msg(text[len(MSG_PREFIX_EKF_I):])

            elif text[:len(MSG_PREFIX_GPS)] == MSG_PREFIX_GPS:
                # handle gps data messages
                self.handle_gps_msg(text[len(MSG_PREFIX_GPS):])

    def stop_main_loop(self):
        self.run = False

    def handle_init_alt_msg(self, text: str):
        match = re.match(REGEX_INIT_ALT, text)
        if match is None:
            return

        groups = match.groups()
        init_alt_cm = int(groups[0])
        print("Setting initial altitude to %d cm" % init_alt_cm)
        self.init_alt = init_alt_cm

    def handle_uninhibited_msg(self, text: str):
        """
        "U[%lu]%d;%d;%d;%d;%d", time_ms, f_ground_speed, f_velocity_x, f_velocity_y,
                    f_velocity_z, f_alt
        :param text:
        :return:
        """
        match = re.match(REGEX_EKF_U, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        gs, vx, vy, vz, alt = [float(x) for x in groups[1:]]
        self.mutex.acquire()
        self.uninhibited_data[GROUND_SPEED].append((time_ms, gs))
        self.uninhibited_data[VELOCITY_X].append((time_ms, vx))
        self.uninhibited_data[VELOCITY_Y].append((time_ms, vy))
        self.uninhibited_data[VELOCITY_Z].append((time_ms, vz))
        self.uninhibited_data[ALTITUDE].append((time_ms, alt))
        self.mutex.release()

    def handle_inhibited_msg(self, text: str):
        """
        "I[%lu]%d;%d;%d;%d;%d", time_ms, spf_ground_speed, spf_velocity_x, spf_velocity_y,
                    spf_velocity_z, spf_alt
        :param text:
        :return:
        """
        match = re.match(REGEX_EKF_I, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        gs, vx, vy, vz, alt = [float(x) for x in groups[1:]]
        self.mutex.acquire()
        self.inhibited_data[GROUND_SPEED].append((time_ms, gs))
        self.inhibited_data[VELOCITY_X].append((time_ms, vx))
        self.inhibited_data[VELOCITY_Y].append((time_ms, vy))
        self.inhibited_data[VELOCITY_Z].append((time_ms, vz))
        self.inhibited_data[ALTITUDE].append((time_ms, alt))
        self.mutex.release()

    def handle_gps_msg(self, text: str):
        """
        "G[%lu]%d;%u;%d;%d;%d;%d", time_ms, gps_ground_speed, gps_sat_count,
                    gps_velocity_x, gps_velocity_y, gps_velocity_z, gps_alt
        :param text:
        :return:
        """
        match = re.match(REGEX_GPS, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        gs, sc, vx, vy, vz, alt = [float(x) for x in groups[1:]]
        self.mutex.acquire()
        self.gps_data[GROUND_SPEED].append((time_ms, gs))
        self.gps_data[SAT_COUNT].append((time_ms, sc))
        self.gps_data[VELOCITY_X].append((time_ms, vx))
        self.gps_data[VELOCITY_Y].append((time_ms, vy))
        self.gps_data[VELOCITY_Z].append((time_ms, vz))
        self.gps_data[ALTITUDE].append((time_ms, alt))
        self.mutex.release()

    def handle_spf_msg(self, text: str):
        """
        "SPF[%lu]%d;%d;%d;%d;%d",
                        time_ms,
                        defender.spoof_state.ground_speed_diff,
                        defender.spoof_state.velocity_x_diff,
                        defender.spoof_state.velocity_y_diff,
                        defender.spoof_state.velocity_z_diff
                        defender.spoof_state.altitude_diff
        :param text:
        :return:
        """

        match = re.match(REGEX_SPF, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        gsd, vxd, vyd, vzd, altd = [float(x) for x in groups[1:]]
        self.mutex.acquire()
        self.spf_data[GROUND_SPEED_DIFF].append((time_ms, gsd))
        self.spf_data[VELOCITY_X_DIFF].append((time_ms, vxd))
        self.spf_data[VELOCITY_Y_DIFF].append((time_ms, vyd))
        self.spf_data[VELOCITY_Z_DIFF].append((time_ms, vzd))
        self.spf_data[ALTITUDE_DIFF].append((time_ms, altd))
        self.mutex.release()

    def get_uninhibited_log_by_key(self, data_key: str, start: int = 0) -> list:
        self.mutex.acquire()
        ret_list = self.uninhibited_data[data_key][start:]
        self.mutex.release()
        return ret_list

    def get_inhibited_log_by_key(self, data_key: str, start: int = 0) -> list:
        self.mutex.acquire()
        ret_list = self.inhibited_data[data_key][start:]
        self.mutex.release()
        return ret_list

    def get_gps_log_by_key(self, data_key: str, start: int = 0) -> list:
        self.mutex.acquire()
        ret_list = self.gps_data[data_key][start:]
        self.mutex.release()
        return ret_list

    def get_spf_log_by_key(self, data_key: str) -> list:
        return self.spf_data[data_key]

    def get_uninhibited_log_full(self) -> dict:
        return self.uninhibited_data

    def get_inhibited_log_full(self) -> dict:
        return self.inhibited_data

    def get_gps_log_full(self) -> dict:
        return self.gps_data

    def get_spf_log_full(self) -> dict:
        return self.spf_data

    def save_log_file(self, filename: str = None):
        curr_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = "out_{}.log".format(curr_time) if filename is None else "out_{}_{}.log".format(curr_time, filename)

        with open("logs/{}".format(filename), "w") as file:
            output_dict = {
                PREFIX_EKF_U: self.uninhibited_data,
                PREFIX_EKF_I: self.inhibited_data,
                PREFIX_GPS: self.gps_data,
                PREFIX_SPF: self.spf_data,
                PREFIX_INIT_ALT: self.init_alt
            }
            output_str = json.dumps(output_dict)
            file.write(output_str)

        print("Writing log file: %s" % filename)
        return filename

    def load_log_file(self, filename: str = None):
        if filename is None:
            dir_contents = os.listdir("logs")
            dir_contents.sort(reverse=True)

            for obj in dir_contents:
                if obj[:3] == "out" and obj[-4:] == ".log":
                    filename = obj
                    break

        if filename is None:
            print("No log files found")
            return

        print("Loading %s" % filename)
        with open("logs/{}".format(filename), "r") as file:
            content_str = file.read()
            content_dict = json.loads(content_str)
            self.mutex.acquire()
            self.uninhibited_data = content_dict[PREFIX_EKF_U]
            self.inhibited_data = content_dict[PREFIX_EKF_I]
            self.gps_data = content_dict[PREFIX_GPS]
            self.spf_data = content_dict[PREFIX_SPF]
            self.init_alt = content_dict[PREFIX_INIT_ALT]

            if self.init_alt > 0:
                print("Updating GPS Initial Altitude to %d cm" % self.init_alt)
                self.gps_data[ALTITUDE] = [(time, float(alt) - self.init_alt) for time, alt in self.gps_data[ALTITUDE]]

            self.mutex.release()
