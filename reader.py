import json
import os
import re
import socket
from datetime import datetime

from pymavlink import mavutil

from constants import *


class Reader:
    def __init__(self):
        self.connection = None
        self.run = False
        self.sd_sensor_data = {
            GROUND_SPEED: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: [],
        }
        self.gps_sensor_data = {
            GROUND_SPEED: [],
            SAT_COUNT: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: []
        }
        self.spf_data = {
            GROUND_SPEED_DIFF: [],
            VELOCITY_X_DIFF: [],
            VELOCITY_Y_DIFF: [],
            VELOCITY_Z_DIFF: []
        }

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

            if text[:len(MSG_PREFIX_SPF)] == MSG_PREFIX_SPF:
                # handle spoofing alert messages
                self.handle_spf_msg(text[len(MSG_PREFIX_SPF):])
            elif text[:len(MSG_PREFIX_SD)] == MSG_PREFIX_SD:
                # handle sensor data messages
                msg_id = int(text[len(MSG_PREFIX_SD)])
                self.handle_sd_msg(msg_id, text[len(MSG_PREFIX_SD) + 1:])
            elif text[:len(MSG_PREFIX_GPS)] == MSG_PREFIX_GPS:
                # handle gps data messages
                msg_id = int(text[len(MSG_PREFIX_GPS)])
                self.handle_gps_msg(msg_id, text[len(MSG_PREFIX_GPS) + 1:])

    def stop_main_loop(self):
        self.run = False

    def handle_sd_msg(self, msg_id: int, text: str):
        """
        "S0[%lu]%d;%d;%d;%d", time_ms, sd_ground_speed, sd_velocity_x, sd_velocity_y, sd_velocity_z
        :param msg_id:
        :param text:
        :return:
        """
        match = re.match(REGEX_SD, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        if msg_id == 0:
            gs, vx, vy, vz = [float(x) for x in groups[1:]]
            self.sd_sensor_data[GROUND_SPEED].append((time_ms, gs))
            self.sd_sensor_data[VELOCITY_X].append((time_ms, vx))
            self.sd_sensor_data[VELOCITY_Y].append((time_ms, vy))
            self.sd_sensor_data[VELOCITY_Z].append((time_ms, vz))
        else:
            print("UNKNOWN MESSAGE WITH ID: %d" % msg_id)

    def handle_gps_msg(self, msg_id: int, text: str):
        """
        "G0[%lu]%d;%u;%d;%d;%d", time_ms, gps_ground_speed, gps_sat_count, gps_velocity_x, gps_velocity_y, gps_velocity_z
        :param msg_id:
        :param text:
        :return:
        """
        match = re.match(REGEX_GPS, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        if msg_id == 0:
            gs, sc, vx, vy, vz = [float(x) for x in groups[1:]]
            self.gps_sensor_data[GROUND_SPEED].append((time_ms, gs))
            self.gps_sensor_data[SAT_COUNT].append((time_ms, sc))
            self.gps_sensor_data[VELOCITY_X].append((time_ms, vx))
            self.gps_sensor_data[VELOCITY_Y].append((time_ms, vy))
            self.gps_sensor_data[VELOCITY_Z].append((time_ms, vz))
        else:
            print("UNKNOWN MESSAGE WITH ID: %d" % msg_id)

    def handle_spf_msg(self, text: str):
        """
        "SPF[%lu]%d;%d;%d;%d",
            time_ms,
            defender.spoof_state.ground_speed_diff,
            defender.spoof_state.velocity_x_diff,
            defender.spoof_state.velocity_y_diff,
            defender.spoof_state.velocity_z_diff
        :param text:
        :return:
        """

        match = re.match(REGEX_SPF, text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        gsd, vxd, vyd, vzd = [float(x) for x in groups[1:]]
        self.spf_data[GROUND_SPEED_DIFF].append((time_ms, gsd))
        self.spf_data[VELOCITY_X_DIFF].append((time_ms, vxd))
        self.spf_data[VELOCITY_Y_DIFF].append((time_ms, vyd))
        self.spf_data[VELOCITY_Z_DIFF].append((time_ms, vzd))

    def get_sd_log_by_key(self, data_key: str) -> list:
        return self.sd_sensor_data[data_key]

    def get_gps_log_by_key(self, data_key: str) -> list:
        return self.gps_sensor_data[data_key]

    def get_spf_log_by_key(self, data_key: str) -> list:
        return self.spf_data[data_key]

    def get_sd_log_full(self) -> dict:
        return self.sd_sensor_data

    def get_gps_log_full(self) -> dict:
        return self.gps_sensor_data

    def get_spf_log_full(self) -> dict:
        return self.spf_data

    def save_log_file(self, filename: str = None):
        if filename is None:
            curr_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = "out_{}.log".format(curr_time)

        with open("logs/{}".format(filename), "w") as file:
            output_dict = {
                PREFIX_SD: self.sd_sensor_data,
                PREFIX_GPS: self.gps_sensor_data,
                PREFIX_SPF: self.spf_data
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
            self.sd_sensor_data = content_dict[PREFIX_SD]
            self.gps_sensor_data = content_dict[PREFIX_GPS]
            self.spf_data = content_dict[PREFIX_SPF]
