# from traceback import format_exc
import datetime

from run_last import run_last

DOCPATH = 'doctmp'

MINUTES_5 = datetime.timedelta(minutes=5)


def run_infinitely():
    while True:
        run_last()


if __name__ == "__main__":
    run_infinitely()
