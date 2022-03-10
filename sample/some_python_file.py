import time
import datetime
import logging


def some_function(context, data):
    # time.sleep(60 * 35)
    time.sleep(3)
    print(datetime.datetime.now().strftime("%H:%M:%S"))
    return True
