
import serial
import serial.tools.list_ports


class Cerial:
    # A class that handles all the serial stuff

    def __init__(self, port=None, baudrate=115200, port_index=1):
        # it creates an instance of serial.Serial class and sets the port and baudrate
        if port is None:
            print("Automatically Selecting port")
            ports = serial.tools.list_ports.comports()
            if (len(ports) == 0):
                raise Exception("No Serial ports found.")
            else:
                print("Available ports:")
                for i, port in enumerate(ports):
                    print(f"{i+1}. {port.device}")
                print(f"Connecting to {ports[port_index-1].device}")
                self.ser = serial.Serial(ports[port_index-1].device, baudrate)
                print(f"Connected to {ports[port_index-1].device}")

        else:
            self.ser = serial.Serial(port, baudrate)

    def send_data(self, data):
        # a function that write to the serial with "carriage return and new line"
        self.ser.write(data.encode())

    def close_port(self):
        # a function that closes the serial port
        self.ser.close()

    def read_until(self, termination='\n'):
        # a function that reads data from the serial port until the termination character is found
        data = self.ser.read_until(termination.encode())
        return data.decode()

    def read_line(self):
        # a function that reads data from the serial port until a newline character is found
        data = self.ser.readline()
        return data.decode()


if __name__ == "__main__":
    # can also be used as a script
    cerialOne = Cerial()
    while (True):
        cerialOne.read_line()
