import re
from math import sqrt
from time import sleep
from threading import Thread

from pymavlink.dialects.v20 import common as mavlink2
from pymavlink import mavutil

CONNECTION = "udpin:0.0.0.0:14540"

PREFIX_SD = "[SD]"
PREFIX_GPS = "[GPS]"

GROUND_SPEED = "GS"
GROUND_COURSE = "GC"
AIRSPEED = "AS"


class Reader:
    def __init__(self):
        self.connection = None
        self.run = False
        self.sd_sensor_data = {
            GROUND_SPEED: [],
            GROUND_COURSE: [],
            AIRSPEED: [],
        }
        self.gps_sensor_data = {
            GROUND_SPEED: [],
            GROUND_COURSE: [],
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
            if len(text) < 5:
                continue

            if text[:4] == PREFIX_SD:
                self.handle_sd_msg(text[len(PREFIX_SD):])
            elif text[:5] == PREFIX_GPS:
                self.handle_gps_msg(text[len(PREFIX_GPS):])

    def stop_main_loop(self):
        self.run = False

    def handle_sd_msg(self, text: str):
        """
        gcs().send_text(MAV_SEVERITY_INFO, "[SD] GSX: %f; GSY: %f; AS: %f", ground_speed.x, ground_speed.y, airspeed);
        gcs().send_text(MAV_SEVERITY_INFO, "[SD] VX: %f; VY: %f; VZ: %f", velocity.x, velocity.y, velocity.z);
        gcs().send_text(MAV_SEVERITY_INFO, "[SD] WX: %f; WY: %f; WZ: %f", wind.x, wind.y, wind.z);
        gcs().send_text(MAV_SEVERITY_INFO, "[SD] PHX: %f; PHY: %f; PHZ: %f", pos_rel_home.x, pos_rel_home.y, pos_rel_home.z);
        :param text:
        :return:
        """
        match = re.match("[(.+)]GSX: (.+); GSY: (.+); AS: (.+)", text)
        if match is None:
            return

        time_ms, gsx, gsy, airspeed = match.groups()
        gsx = float(gsx)
        gsy = float(gsy)
        airspeed = float(airspeed)
        gs = sqrt(pow(gsx, 2) + pow(gsy, 2)) * 100.0

        self.sd_sensor_data[GROUND_SPEED].append(gs)
        self.sd_sensor_data[AIRSPEED].append(airspeed)

    def handle_gps_msg(self, text: str):
        """
        gcs().send_text(MAV_SEVERITY_INFO, "[GPS] GS: %lu; GC: %f", ground_speed, ground_course);
        gcs().send_text(MAV_SEVERITY_INFO, "[GPS] SC: %u; VX: %f; VY: %f; VZ: %f", sat_count, velocity.x, velocity.y, velocity.z);
        :param text:
        :return:
        """
        match = re.match("[(.+)]GS: (.+); GC: (.+)", text)
        if match is None:
            return

        time_ms, gs, gc = match.groups()
        gs = float(gs)
        gc = float(gc)
        self.gps_sensor_data[GROUND_SPEED].append(gs)
        self.gps_sensor_data[GROUND_COURSE].append(gc)

    def get_sd_log(self, data_key: str):
        return self.sd_sensor_data[data_key]

    def get_gps_log(self, data_key: str):
        return self.gps_sensor_data[data_key]


class Analyze:
    def __init__(self, r: Reader):
        self.r = r

    def print_ground_speed(self):
        list_sd_speed = self.r.get_sd_log(GROUND_SPEED)
        list_gps_speed = self.r.get_gps_log(GROUND_SPEED)

        for i in range(min(len(list_sd_speed), len(list_gps_speed))):
            sd_speed = list_sd_speed[i]
            gps_speed = list_gps_speed[i]
            print("GS_SD: %f cm/s    GS_GPS: %f cm/s" % (sd_speed, gps_speed))


def main():
    r = Reader()
    a = Analyze(r)

    # start a connection listening to a UDP port
    r.setup()

    threads = start_threads(r)

    sleep(60)
    r.stop_main_loop()
    terminate_threads(threads)

    a.print_ground_speed()


def start_threads(r: Reader):
    threads = []

    try:
        t_read_loop = Thread(target=r.run_main_loop)
        # t_analyze_loop = Thread(target=r.analyze_data)

        t_read_loop.start()
        # t_analyze_loop.start()

        threads.append(t_read_loop)
        # threads.append(t_analyze_loop)
    except RuntimeError as e:
        print("Unable to start thread: %s" % str(e))

    return threads


def terminate_threads(threads: list):
    for thread in threads:
        thread.join()


main()
