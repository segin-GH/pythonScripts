#! /usr/bin/python3

import serial

def main():
    arduinoData = serial.Serial('/dev/ttyUSB0',115200)

    while True:
        cmd = input('enter your number : ')
        if cmd == "exit":
            arduinoData.close()
            break
        cmd = cmd + '\r' + '\n'
        arduinoData.write(cmd.encode())



if __name__ == "__main__":
    main()