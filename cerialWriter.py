#! /usr/bin/env python3


from serial import Serial
from serial import SerialException
from serial import SerialTimeoutException

import time


class SerialWrap:
    def __init__(self, port: str, baud: int = 115200, timeout: int = 0):
        self.__ser = None
        self.__serail_port = None
        self.__serail_baud = None

        if not isinstance(port, str):
            print("Error: port not valid")
            return None

        if not isinstance(baud, int):
            print("Error: baud not valid")
            return None

        try:
            self.__ser = Serial(port, baud)
            self.__serail_port = port
            self.__serail_baud = baud

        except ValueError:
            print("How hard is it to provide proper values??")
            return None
        except SerialException:
            print(f"Port not found! bro did you connect {port} it ?? ")
            return None

    def __del__(self):
        self.close_port()

    def send_hex(self, data: str, end_fmt: str = "\r\n"):
        try:
            # Convert each character in the string to its ASCII hex value
            hex_data = "".join(
                f"{ord(c):02X}" for c in data
            )  # Convert each char to hex and concatenate

            # Print the hex equivalent for debugging
            print(f"Sending >> {hex_data}")

            # Send the hex data over the serial interface, appending the end format
            self.__ser.write(bytes.fromhex(hex_data))

        except ValueError:
            print(f"Error: '{data}' could not be converted to hex.")

    def send_bytes(self, data):
        try:
            # print(f"Sending >> {data}")
            self.__ser.write(bytearray(data))

        except ValueError:
            print(f"Error: '{data}' could not be sent.")

    def send_asci(self):
        pass

    def read_until(self, term="\r\n"):
        data = self.__ser.read_until(term.encode())
        return data.decode()

    def read_until_timeout(self, timeout=2):
        self.__ser.timeout = timeout  # Set the timeout in seconds
        end_time = time.time() + timeout
        data = b""

        print(f"Reading data for up to {timeout} seconds...")
        while time.time() < end_time:
            try:
                # Read one byte at a time
                byte = self.__ser.read(1)
                if byte:
                    data += byte
                else:
                    # No data received, continue waiting
                    pass
            except SerialTimeoutException:
                print("Read timeout.")
                break

        print("Finished reading.")
        return data

    def close_port(self):
        if self.__ser is not None and self.__ser.is_open:
            print(f"Flushing and closing port {self.__serail_port}")
            self.__ser.flush()  # Ensure all data is sent
            self.__ser.close()  # Close the port


if __name__ == "__main__":
    ser = SerialWrap("/dev/ttyUSB1", 115200)
    ser.send_hex(data="F")
    data = ser.read_until_timeout()
    print(data)
