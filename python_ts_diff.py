import time
import sys


def time_diff(ts1, ts2):
    """Return the difference btw 2 epoch time in humman readable format"""
    try:
        ts1 = int(ts1)
        ts2 = int(ts2)
    except ValueError:
        print("Invalid timestamp")
        return None

    if ts1 > ts2:
        diff = ts1 - ts2
    else:
        diff = ts2 - ts1
    return time.strftime("%H:%M:%S", time.gmtime(diff))


if __name__ == "__main__":
    if len(sys.argv) > 2:
        ts1 = sys.argv[1]
        ts2 = sys.argv[2]
        print(f"Time difference: {time_diff(ts1, ts2)}")
    else:
        print("Usage: python3 python_ts_diff.py <ts-1> <ts-2>")
