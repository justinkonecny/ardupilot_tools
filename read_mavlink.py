import os
from pprint import pprint
from threading import Thread
from time import sleep

from analyzer import Analyzer
from reader import Reader

"""
{'out_2021-03-27_12-14-27.log': {'GS': 133.55597888344857,
                                 'VX': 1.514674,
                                 'VY': 0.6522990000000001,
                                 'VZ': 0.07494099999999998},
                                 
 'out_2021-03-27_12-18-14.log': {'GS': 986.42560408685,
                                 'VX': 10.07817,
                                 'VY': 0.916002,
                                 'VZ': 0.739931}}
"""


def main():
    r = Reader()
    a = Analyzer(r)

    # read_new_data(r, 30)
    show_data(r, a, "out_2021-03-27_12-14-27.log")
    print_thresholds(r, a)


def print_thresholds(r: Reader, a: Analyzer):
    dir_contents = os.listdir(".")
    dir_contents.sort(reverse=True)
    thresholds = {}
    for filename in dir_contents:
        if filename[:3] == "out" and filename[-4:] == ".log":
            r.load_log_file(filename)
            result = a.get_max_thresholds()
            thresholds[filename] = result
    pprint(thresholds)


def read_new_data(r: Reader, time: int):
    # start a connection listening to a UDP port
    r.setup()

    # start reading data
    threads = start_threads(r)

    # wait (seconds)
    print("Reading for %d seconds" % time)
    sleep(time)

    # stop reading / analyzing data
    stop_threads(r, threads)

    # save the data to a log file
    r.save_log_file()


def show_data(r: Reader, a: Analyzer, log_file: str = None):
    # load the given log file, or the latest
    r.load_log_file(log_file)

    a.show_sat_count()
    a.cmp_ground_speed()
    a.cmp_velocity_x()
    a.cmp_velocity_y()
    a.cmp_velocity_z()


def start_threads(r: Reader):
    threads = []
    try:
        t_read_loop = Thread(target=r.run_main_loop)
        t_read_loop.start()
        threads.append(t_read_loop)
    except RuntimeError as e:
        print("Unable to start thread, error: %s" % str(e))

    return threads


def stop_threads(r: Reader, threads: list):
    print("Stopping all threads")
    r.stop_main_loop()

    for thread in threads:
        thread.join()


main()
