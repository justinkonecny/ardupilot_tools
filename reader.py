import json
import os
import re
from datetime import datetime
from math import sqrt

from pymavlink import mavutil

from constants import *


class Reader:
    def __init__(self):
        self.connection = None
        self.run = False
        self.sd_sensor_data = {
            GROUND_SPEED: [],
            GROUND_COURSE: [],
            AIRSPEED: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: [],
            WIND_SPEED_X: [],
            WIND_SPEED_Y: [],
            WIND_SPEED_Z: [],
            POS_REL_HOME_X: [],
            POS_REL_HOME_Y: [],
            POS_REL_HOME_Z: []
        }
        self.gps_sensor_data = {
            GROUND_SPEED: [],
            GROUND_COURSE: [],
            SAT_COUNT: [],
            VELOCITY_X: [],
            VELOCITY_Y: [],
            VELOCITY_Z: []
        }

    def setup(self):
        # start a connection listening to a UDP port
        print("Starting connection: `%s`" % CONNECTION)
        self.connection = mavutil.mavlink_connection(CONNECTION)

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

            if text[:len(PREFIX_SD)] == PREFIX_SD:
                msg_id = int(text[len(PREFIX_SD)])
                self.handle_sd_msg(msg_id, text[len(PREFIX_SD) + 1:])
            elif text[:len(PREFIX_GPS)] == PREFIX_GPS:
                msg_id = int(text[len(PREFIX_GPS)])
                self.handle_gps_msg(msg_id, text[len(PREFIX_GPS) + 1:])

    def stop_main_loop(self):
        self.run = False

    def handle_sd_msg(self, msg_id: int, text: str):
        """
        "SD0[%lu] GSX: %f; GSY: %f", time_ms, ground_speed.x, ground_speed.y
        "SD1[%lu] AS: %f;  VX: %f", time_ms, airspeed, velocity.x
        "SD2[%lu] VY: %f; VZ: %f", time_ms, velocity.y, velocity.z
        "SD3[%lu] WX: %f; WY: %f", time_ms, wind.x, wind.y,
        "SD4[%lu] WZ: %f; PHX: %f", time_ms, wind.z, pos_rel_home.x
        "SD5[%lu] PHY: %f; PHZ: %f", time_ms, pos_rel_home.y, pos_rel_home.z
        :param msg_id:
        :param text:
        :return:
        """
        match = re.match(REGEX_SD[msg_id], text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        if msg_id == 0:
            gsx, gsy = [float(x) for x in groups[1:]]
            gs = sqrt(pow(gsx, 2) + pow(gsy, 2)) * 100.0  # convert to speed in cm/s
            self.sd_sensor_data[GROUND_SPEED].append((time_ms, gs))

        elif msg_id == 1:
            airspeed, vx = [float(x) for x in groups[1:]]
            self.sd_sensor_data[AIRSPEED].append((time_ms, airspeed))
            self.sd_sensor_data[VELOCITY_X].append((time_ms, vx))

        elif msg_id == 2:
            vy, vz = [float(x) for x in groups[1:]]
            self.sd_sensor_data[VELOCITY_Y].append((time_ms, vy))
            self.sd_sensor_data[VELOCITY_Z].append((time_ms, vz))

        elif msg_id == 3:
            wx, wy = [float(x) for x in groups[1:]]
            self.sd_sensor_data[WIND_SPEED_X].append((time_ms, wx))
            self.sd_sensor_data[WIND_SPEED_Y].append((time_ms, wy))

        elif msg_id == 4:
            wz, phx = [float(x) for x in groups[1:]]
            self.sd_sensor_data[WIND_SPEED_Z].append((time_ms, wz))
            self.sd_sensor_data[POS_REL_HOME_X].append((time_ms, phx))

        elif msg_id == 5:
            phy, phz = [float(x) for x in groups[1:]]
            self.sd_sensor_data[POS_REL_HOME_Y].append((time_ms, phy))
            self.sd_sensor_data[POS_REL_HOME_Z].append((time_ms, phz))

        else:
            print("UNKNOWN MESSAGE WITH ID: %d" % msg_id)

    def handle_gps_msg(self, msg_id: int, text: str):
        """
        "GPS0[%lu] GS: %lu; GC: %f", time_ms, ground_speed, ground_course
        "GPS1[%lu] SC: %u; VX: %f", time_ms, sat_count, velocity.x
        "GPS2[%lu] VY: %f; VZ: %f", time_ms, velocity.y, velocity.z
        :param msg_id:
        :param text:
        :return:
        """
        match = re.match(REGEX_GPS[msg_id], text)
        if match is None:
            return

        groups = match.groups()
        time_ms = int(groups[0])

        if msg_id == 0:
            gs, gc = [float(x) for x in groups[1:]]
            self.gps_sensor_data[GROUND_SPEED].append((time_ms, gs))
            self.gps_sensor_data[GROUND_COURSE].append((time_ms, gc))

        elif msg_id == 1:
            sc, vx = [float(x) for x in groups[1:]]
            self.gps_sensor_data[SAT_COUNT].append((time_ms, sc))
            self.gps_sensor_data[VELOCITY_X].append((time_ms, vx))

        elif msg_id == 2:
            vy, vz = [float(x) for x in groups[1:]]
            self.gps_sensor_data[VELOCITY_Y].append((time_ms, vy))
            self.gps_sensor_data[VELOCITY_Z].append((time_ms, vz))

        else:
            print("UNKNOWN MESSAGE WITH ID: %d" % msg_id)

    def get_sd_log(self, data_key: str = None) -> list:
        return self.sd_sensor_data if data_key is None else self.sd_sensor_data[data_key]

    def get_gps_log(self, data_key: str = None) -> list:
        return self.gps_sensor_data if data_key is None else self.gps_sensor_data[data_key]

    def save_log_file(self, filename: str = None):
        if filename is None:
            curr_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = "out_{}.log".format(curr_time)

        with open(filename, "w") as file:
            output_dict = {
                PREFIX_SD: self.sd_sensor_data,
                PREFIX_GPS: self.gps_sensor_data
            }
            output_str = json.dumps(output_dict)
            file.write(output_str)

        print("Writing log file: %s" % filename)
        return filename

    def load_log_file(self, filename: str = None):
        if filename is None:
            dir_contents = os.listdir(".")
            dir_contents.sort(reverse=True)

            for obj in dir_contents:
                if obj[:3] == "out" and obj[-4:] == ".log":
                    filename = obj
                    break

        if filename is None:
            print("No log files found")
            return

        print("Loading %s" % filename)
        with open(filename, "r") as file:
            content_str = file.read()
            content_dict = json.loads(content_str)
            self.sd_sensor_data = content_dict[PREFIX_SD]
            self.gps_sensor_data = content_dict[PREFIX_GPS]
