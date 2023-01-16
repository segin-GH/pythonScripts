#! /usr/bin/python3

# import serial

# if __name__ == "__main__":
#     ser = serial.Serial(
#         port='/dev/ttyUSB0',
#         baudrate=115200,
#         # bytesize=serial.EIGHTBITS,
#         # parity=serial.PARITY_NONE,
#         # stopbits=serial.STOPBITS_ONE,
#         # xonxoff=False,
#         # rtscts=False,
#         # dsrdtr=False
#     )

#     ser.isOpen()

#     while True:
#         input_data = input("Enter data to send (type 'exit' to exit): ")
#         if input_data == 'exit':
#             ser.close()
#             break
#         ser.write(input_data.encode())


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