# /usr/bin/env python3


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
    # ser.start_serial_rx_demon()
    # CONFIG <36 bytes uuid>
    # S1-XXXXXX 36byte UUID Epoch Time"

    counter = 0
    error = 0

    uuid = "b9a98712-8b1d-43a3-a459-fe00003d28c7"
    device_id = "S1-00340"

    uuid = "3e13025b-77c8-4d2d-a854-f0a1c51abec3"
    device_id = "S1-00372"

    uuid = "7174c019-04d1-470c-87e6-a4d8be023347"
    device_id = "S1-00334"

    uuid = "4e669dcc-d4b4-412f-98d6-17b35a7d83a5"
    device_id = "S1-00349"

    uuid = "2571f078-96e4-46da-9be1-8359f07b90d5"
    device_id = "DP-11829"

    uuid = "f9c4cfbf-d6ba-48a7-9371-10d3c994bd5f"
    device_id = "S1-00303"

    uuid = "b1d60cc0-6037-4346-9779-e507129c280a"
    device_id = "S1-00312"

    uuid = "b418b64e-d0b8-4d1f-820d-aebb5aef1fa2"
    device_id = "S1-00400"

    uuid = "96aac5c3-f703-4fb5-83ec-323ed9740b2a"
    device_id = "S1-00369"

    uuid = "743423e4-c869-4590-9c3e-46a1f415203c"
    device_id = "S1-00322"

    uuid = "b871e4cc-92c5-401f-8289-1529df355b63"
    device_id = "S1-00337"

    uuid = "2d458b0e-0ccc-471b-8f0f-3985e63dcb2c"
    device_id = "S1-00348"

    uuid = "9d5f24f4-b5b5-41dd-80bd-d7e1cfdc4c45"
    device_id = "DOZ-00306"

    uuid = "8e22c68e-d82a-4b64-9314-a3b37506f0ad"
    device_id = "DOZ-00100"

    uuid = "f4db74f4-d890-4a00-9019-b15bcb1ca17d"
    device_id = "DOZ-00101"

    uuid = "de5ff551-69c3-4a8f-ab55-0ca95ad7bcc2"
    device_id = "DOZ-00102"

    uuid = "1ff15a61-526f-4d5b-9970-3f5f5f42f94c"
    device_id = "DOZ-00103"

    uuid = "d8666727-9118-4b14-9fdf-5833348e184d"
    device_id = "DOZ-10007"

    uuid = "9381a8f2-2fb7-43ea-b06d-c0921bd159da"
    device_id = "DOZ-10314"

    uuid = "ea810e0d-a17e-4022-b0c4-32015bf3523c"
    device_id = "DOZ-10085"

    uuid = "9fc903df-fc64-482a-82ad-9f090c71c5f4"
    device_id = "DOZ-16109"

    uuid = "8d0df6e1-0415-4427-b378-7167187859b8"
    device_id = "DOZ-16108"

    uuid = "ef3a47f0-b7cc-4d50-82c1-d832ebf64398"
    device_id = "DOZ-16107"

    uuid = "7fdaae5f-5593-4906-95f6-cffcedf76e57"
    device_id = "DOZ-16103"

    while True:
        # CONFIG d7ec18f3-fad7-4975-ae7a-45e92fcaa7df S1-12345 1740670496
        cmd = f"CONFIG {uuid} {device_id} {int(time.time())}\n"
        ser.send_asci(cmd)
        time.sleep(1)

        while True:
            elapsed_time, data_len, data = ser.read_bytes(500)
            if data_len > 0:
                print(f"Received {data_len} bytes in {elapsed_time} seconds")
                break
            else:
                print("No data received, retrying...")
                time.sleep(1)
        break
