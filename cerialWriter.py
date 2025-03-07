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
        self.__ANSI_GREEN = "\033[92m"
        self.__ANSI_RESET = "\033[0m"

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
                        # Convert timestamp to human-readable format
                        human_time = time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(time.time())
                        )
                        # Add green color using ANSI escape codes
                        green_text = f"{self.__ANSI_GREEN}{data.decode('utf-8', 'ignore')}{self.__ANSI_RESET}"
                        print(f"{human_time} >> {green_text}")
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
            self.__ser.write(data.encode("utf-8"))
        except ValueError:
            print(f"Error: '{data}' could not be converted to hex.")

    def send_bytes(self, data):
        try:
            print(f"Sending >> {data}")
            self.__ser.write(bytearray(data))

        except ValueError:
            print(f"Error: '{data}' could not be sent.")

    def send_asci(self, data: str):
        try:
            print(f"Sending >> {data}")
            self.__ser.write(data.encode("utf-8"))
        except ValueError:
            print(f"Error: '{data}' could not be converted to ASCII.")

    def read_until(
        self,
        term=b"\x55",
    ):
        self.__ser.timeout = None
        data = self.__ser.read_until(term)
        return data

    def read_until_timeout(self, timeout=2):
        """Reads data from the serial port until the specified timeout in seconds."""
        self.__ser.timeout = None  # Disable internal timeout for manual handling

        start_time = time.time()  # Record the start time data = b""

        while time.time() - start_time < timeout:
            if self.__ser.in_waiting > 0:  # If there's data available in the buffer
                chunk = self.__ser.read(self.__ser.in_waiting)  # Read available data
                if chunk:
                    data += chunk
            else:
                time.sleep(0.01)  # Sleep briefly to avoid CPU overload
        return data

    def read_bytes_in_array(self, timeout=1):
        """Reads data from the serial port until the specified timeout in seconds."""
        self.__ser.timeout = 0

        start_time = time.time()
        data = b""
        data_len = 0

        while time.time() - start_time < timeout:
            data_len = self.__ser.in_waiting
            if data_len > 0:
                chunk = self.__ser.read(data_len)
                if len(chunk) > 0:
                    data += chunk

        # print(f"Data received: {data}")
        return len(data), data

    def read_bytes(self, length: int):
        self.__ser.timeout = 0
        start_time = time.time()
        data = b""
        length = length * 2  # Convert to bytes

        while len(data) < length:
            data_len = self.__ser.in_waiting
            if data_len > 0:
                # Read as much as possible, but not more than needed to reach 500 bytes
                chunk_size = min(data_len, length - len(data))
                chunk = self.__ser.read(chunk_size)
                if len(chunk) > 0:
                    data += chunk

        end_time = time.time()
        elapsed_time = end_time - start_time

        # Limit the returned data to exactly 500 bytes (in case more than 500 bytes were read)
        data = data[:length]

        print(f"Data received: {len(data)} bytes")
        print(f"Elapsed time: {round(elapsed_time, 0)} seconds")

        return round(elapsed_time), len(data), data

    def close_port(self):
        if self.__ser is not None and self.__ser.is_open:
            print(f"Flushing and closing port {self.__serial_port}")
            self.__ser.flush()  # Ensure all data is sent
            self.__ser.close()  # Close the port

    def flush_buffer(self):
        self.__ser.reset_input_buffer()


if __name__ == "__main__":
    ser = SerialWrap("/dev/ttyUSB0", 115200)
    ser.start_serial_rx_demon()
    # CONFIG <36 bytes uuid>
    # S1-XXXXXX 36byte UUID Epoch Time"
    ser.send_asci("FORMATSDCARD\r")

    while True:
        time.sleep(1)
