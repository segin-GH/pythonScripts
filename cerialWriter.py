#! /usr/bin/env python3


from serial import Serial
from serial import SerialException
from serial import SerialTimeoutException

import time
import threading


class SerialWrap:
    def __init__(self, port: str, baud: int = 115200, timeout: int = 0):
        self.__ser = None
        self.__serial_port = None
        self.__serial_baud = None
        self.__rx_thread = None
        self.__running = False  # Control the receive thread

        if not isinstance(port, str):
            print("Error: port not valid")
            return None

        if not isinstance(baud, int):
            print("Error: baud not valid")
            return None

        try:
            self.__ser = Serial(port, baud, timeout=timeout)
            self.__serial_port = port
            self.__serial_baud = baud

        except ValueError:
            print("How hard is it to provide proper values??")
            return None
        except SerialException:
            print(f"Port not found! bro did you connect {port} ?? ")
            return None

    def __receive_data(self):
        """Function to continuously receive data from the serial port."""
        while self.__running:
            if self.__ser.in_waiting > 0:
                try:
                    data = self.__ser.read(self.__ser.in_waiting)  # Read available data
                    if data:
                        print(f"{data.decode('utf-8', 'ignore')}")
                except Exception as e:
                    print(f"Error reading data: {e}")
            else:
                # Avoid CPU overload by adding a small sleep
                time.sleep(0.01)

    def start_serial_rx_demon(self):
        """Start the RX thread that listens for incoming serial data."""
        if self.__rx_thread is None or not self.__rx_thread.is_alive():
            self.__running = True
            self.__rx_thread = threading.Thread(target=self.__receive_data, daemon=True)
            self.__rx_thread.start()
            print("Serial receive thread started.")

    def stop_serial_rx_demon(self):
        """Stop the RX thread that listens for incoming serial data."""
        self.__running = False
        if self.__rx_thread is not None:
            self.__rx_thread.join()
            print("Serial receive thread stopped.")

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
            print(f"Sending >> {data}")
            self.__ser.write(bytearray(data))

        except ValueError:
            print(f"Error: '{data}' could not be sent.")

    def send_asci(self):
        pass

    def read_until(self, term=b"\x55"):
        self.__ser.timeout = 3
        data = self.__ser.read_until(term)
        return data

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
    ser.start_serial_rx_demon()
    ser.send_hex("F")

    while True:
        time.sleep(1)
