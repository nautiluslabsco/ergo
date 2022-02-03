import datetime
import time


def ping():
    print(f"{datetime.datetime.now().strftime('%H:%M:%S')} ping")
    time.sleep(40 * 60)
    return True
