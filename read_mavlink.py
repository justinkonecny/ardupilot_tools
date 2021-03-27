from threading import Thread
from time import sleep

from analyze import Analyze
from reader import Reader


def main():
    r = Reader()
    a = Analyze(r)

    read_new_data(r, 30)

    # r.load_log_file()
    # a.cmp_ground_speed()
    # a.cmp_velocity_x()
    # a.cmp_velocity_y()
    # a.cmp_velocity_z()
    # a.show_sat_count()


def read_new_data(r: Reader, time: int = 30):
    # start a connection listening to a UDP port
    r.setup()

    # start reading / analyzing data
    threads = start_threads(r)

    # wait (seconds)
    sleep(time)

    # stop reading / analyzing data
    stop_threads(r, threads)

    r.save_log_file()


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
        print("Unable to start thread, error: %s" % str(e))

    return threads


def stop_threads(r: Reader, threads: list):
    r.stop_main_loop()

    for thread in threads:
        thread.join()


main()
