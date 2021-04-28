import os
from collections import defaultdict
from pprint import pprint
from threading import Thread, Lock
from time import sleep

from analyzer import Analyzer
from reader import Reader


# THRESHOLDS (28 April 2021) (3 GPS Flights: "carter_real_gps_alt_thresh"):
# AVG: {'GS': 51, 'VX': 65, 'VY': 49, 'VZ': 33, 'ALT': 251}
# AVG SQS: {'GS': 69, 'VX': 83, 'VY': 64, 'VZ': 39, 'ALT': 259}

def main():
    lock = Lock()

    r = Reader(lock)  # initialize reader
    a = Analyzer(r, lock)  # initialize analyzer

    read_new_data(r, 40, "alt_4000mm_10s_200vz_tp75_2000ms_dc3")  # read and store a new flight log
    show_data(r, a)  # load flight log and show graphs

    # print_thresholds(r, a)  # print the thresholds
    # create_all_csvs(r, a)  # create CSVs from log

    # show_graphs_for_all_logs(r, a)  # show all flight graphs


def create_all_csvs(r: Reader, a: Analyzer):
    diffs = defaultdict(list)
    diffs_sq = defaultdict(list)

    for filename in get_all_log_files():
        r.load_log_file(filename)

        out_folder = "csvs/{}".format(filename[:-4])
        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        all_csvs = a.get_all_csv_list()
        for key, csv_list in all_csvs.items():

            vals = csv_list[1].split(",")[-2:]
            avg_diff = int(float(vals[0]))
            avg_diff_sq = int(float(vals[1]))

            diffs[key].append(avg_diff)
            diffs_sq[key].append(avg_diff_sq)

            with open("{}/{}.csv".format(out_folder, key.lower()), "w") as file:
                for line in csv_list:
                    file.write(line)
    avgs = {}
    avgs_sq = {}

    for key, l in diffs.items():
        avgs[key] = int(sum(l) / len(l))

    for key, l in diffs_sq.items():
        avgs_sq[key] = int(sum(l) / len(l))

    print("AVG:", avgs)
    print("AVG SQS:", avgs_sq)


def get_all_log_files() -> list:
    dir_contents = os.listdir("logs")
    dir_contents.sort(reverse=True)
    return list(filter(lambda f: (f[:3] == "out" and f[-4:] == ".log"), dir_contents))


def print_thresholds(r: Reader, a: Analyzer):
    thresholds = {}
    for filename in get_all_log_files():
        r.load_log_file(filename)
        result = a.get_max_thresholds()
        thresholds[filename] = result
    pprint(thresholds)


def read_new_data(r: Reader, time: int, filename: str = None):
    # start a connection listening to a UDP port
    r.setup()

    # start reading data
    threads = start_threads(r)

    init_time = time

    # wait (seconds)
    while time > 0:
        if time % 5 == 0:
            print("Reading for %d sec" % time)
        r.curr_time = (init_time - time)
        sleep(1)
        time -= 1

    # stop reading / analyzing data
    stop_threads(r, threads)

    # save the data to a log file
    r.save_log_file(filename)


def show_graphs_for_all_logs(r: Reader, a: Analyzer):
    for log in get_all_log_files():
        show_data(r, a, log)
        input("Press any key to continue...")


def show_data(r: Reader, a: Analyzer, log_file: str = None):
    # load the given log file, or the latest
    r.load_log_file(log_file)

    print("SPF TIME:", r.spf_time)

    a.show_sat_count()
    a.cmp_ground_speed()
    a.cmp_velocity_x()
    a.cmp_velocity_y()
    a.cmp_velocity_z()
    a.cmp_altitude()
    a.show_spf_diff()


def start_threads(r: Reader):
    threads = []
    try:
        t_read_loop = Thread(target=r.run_main_loop)
        t_key_monitor = Thread(target=r.read_key_stroke_loop)

        t_read_loop.start()
        t_key_monitor.start()

        threads.append(t_read_loop)
        threads.append(t_key_monitor)
    except RuntimeError as e:
        print("Unable to start thread, error: %s" % str(e))

    return threads


def stop_threads(r: Reader, threads: list):
    print("Stopping all threads")
    r.stop_main_loop()

    for thread in threads:
        thread.join()


main()
