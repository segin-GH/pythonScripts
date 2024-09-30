class BinaryFileReader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.file = None

    def open_file(self):
        try:
            self.file = open(self.file_path, "rb")
        except FileNotFoundError:
            raise FileNotFoundError(
                f"tried opening the void. {self.file_path} not found."
            )

    def close_file(self):
        if self.file:
            self.file.close()

    def read_bytes(self, num_bytes):
        """Reads a specific number of bytes and returns them as a list of integers."""
        if not self.file:
            raise Exception("File not opened. Call open_file() first.")

        data = self.file.read(num_bytes)
        if not data:
            return None  # End of file reached

        # Return the byte in a list
        return list(data)


def main():
    reader = BinaryFileReader("app_update.bin")
    reader.open_file()

    # Example: Read 16 bytes at a time in a loop
    while True:
        bytes_read = reader.read_bytes(512)
        if bytes_read is None:
            print("\nEnd of file reached.")
            break
        # print in hex
        print(f"Bytes read ({len(bytes_read)}): {bytes_read}")

    reader.close_file()


if __name__ == "__main__":
    main()
