import time
import serial

# import perf_counter


def readWithDelay(
    *, port="/dev/ttyUSB1", baud=115200, interval=1, sample=250, iters=1000
):
    """
    Reads serialport from port at baud with delay from timerFunc of interval for n iters
    :param port: Serial port
    :param baud: Baudrate
    :param interval: Interval in seconds between read
    :param iters: Number of ierations to repeat
    :return: packets,a list of number of sample bytes in interval for n iters


    """
    #:param timerFunc: Delay function for timing, time.perf_counter is the most accurate

    timerFunc = time.perf_counter()

    ser = serial.Serial("/dev/ttyUSB1", 115200, timeout=1)
    ser.flushInput()

    ser.write(b"P\n")
    time.sleep(1)

    ser.write(b"4\n")  # 3,4,5,6 # gains
    time.sleep(0.5)
    ser.write(b"b\n")
    time.sleep(0.5)
    ser.write(b"S\n")
    ser.flushInput()

    # ser = serial.Serial(port, baud, timeout=0)  # Start serial
    prevTime = timerFunc
    packets = []

    while iters > 0:
        currTime = time.perf_counter()
        # print("I am in loop")
        if currTime > (prevTime + interval):
            wait = ser.in_waiting
            ser.read(wait)
            prevTime = currTime
            packets.append(wait)
            iters -= 1
            print(wait)
            print("Sampling rate:", (wait / interval) / 2)
            # print("loss:",100-((100*(wait/interval/2))/sample))

    return packets


if __name__ == "__main__":
    from clize import run

    run(readWithDelay)
