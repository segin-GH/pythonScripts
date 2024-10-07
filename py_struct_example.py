import struct
from cerialWriter import SerialWrap
from bin_printer import BinaryFileReader
import time
import zlib
import hashlib


class FrameGenerator:
    ESC_CHAR = 0x7D
    SOF_CHAR = 0xAA
    EOF_CHAR = 0x55
    XOR_MASK = 0x20

    def add_escape_sequence(self, data):
        """
        Add escape sequence to the data by escaping special characters.
        """
        escaped_data = bytearray()
        for byte in data:
            if byte in [self.SOF_CHAR, self.EOF_CHAR, self.ESC_CHAR]:
                escaped_data.append(self.ESC_CHAR)  # Insert escape character
                escaped_data.append(
                    byte ^ self.XOR_MASK
                )  # XOR and add the flipped byte
            else:
                escaped_data.append(byte)
        return bytes(escaped_data)

    def remove_escape_sequence(self, data):
        """
        Remove escape sequences from the data by reversing the escaping process.
        """
        unescaped_data = bytearray()
        i = 0
        while i < len(data):
            if data[i] == self.ESC_CHAR:
                # XOR the next byte with the mask to restore original value
                i += 1
                unescaped_data.append(data[i] ^ self.XOR_MASK)
            else:
                unescaped_data.append(data[i])
            i += 1
        return bytes(unescaped_data)

    def create_frame(self, soh, ssoh, ver, cmd, eot, id, buff):
        """
        Create a frame with the buffer after the cmd field, using little-endian ordering.

        Format: <SOF> <VER> <CMD> <SUB-SOF> <LEN> <DATA> <ID> <CRC> <EOT>
        """

        _len = len(buff)

        # Step 1: Pack the frame without CRC
        frmt_without_crc = f">BBHBH{_len}sB"
        packd_frm_without_crc = struct.pack(
            frmt_without_crc, soh, ver, cmd, ssoh, _len, buff, id
        )

        # Step 2: Calculate CRC on the frame till <ID>
        _crc = zlib.crc32(packd_frm_without_crc)

        # Step 3: Pack the full frame with CRC and EOT
        frmt_with_crc = f">BBHBH{_len}sBIB"
        packd_frm_with_crc = struct.pack(
            frmt_with_crc, soh, ver, cmd, ssoh, _len, buff, id, _crc, eot
        )
        print(f"Pkd frm 2 (with CRC): {packd_frm_with_crc.hex()}")

        # Step 4: Escape special characters in the frame excluding SOF and EOF
        escaped_frm = bytearray([soh])  # Add SOF (not escaped)
        escaped_frm.extend(
            self.add_escape_sequence(packd_frm_with_crc[1:-1])
        )  # Escape the middle part
        escaped_frm.append(eot)  # Add EOF (not escaped)

        return bytes(escaped_frm)

    def unpack_frame(self, packed_data):
        """
        Unpack a frame with the buffer after the cmd field, using little-endian ordering.

        Parameters:
        - packed_data: Packed binary data (bytes)

        Returns:
        - A dictionary containing the unpacked values: soh, ver, length, cmd, buffer_data, crc, eot
        """

        unescaped_data = self.remove_escape_sequence(packed_data)

        print(f"Pkd frm 3: {unescaped_data.hex()}")

        fixed_format_before_buffer = ">BBHBH"
        fixed_format_after_buffer = ">BIB"

        # Unpack the fields before the buffer
        fixed_size_before_buffer = struct.calcsize(fixed_format_before_buffer)
        soh, ver, cmd, ssoh, length = struct.unpack_from(
            fixed_format_before_buffer, unescaped_data, 0
        )

        # The buffer is located between the fixed fields before and after
        buffer_start = fixed_size_before_buffer
        buffer_data = unescaped_data[buffer_start : buffer_start + length]

        # Unpack the fields after the buffer
        id, crc, eot = struct.unpack_from(
            fixed_format_after_buffer, unescaped_data, buffer_start + length
        )

        unpacked_frame = {
            "soh": soh,
            "ver": ver,
            "length": length,
            "cmd": cmd,
            "ssoh": ssoh,
            "buffer_data": buffer_data,
            "crc": crc,
            "id": id,
            "eot": eot,
        }

        for key, value in unpacked_frame.items():
            # If the value is a byte string (like buffer_data), convert each byte to hex
            if isinstance(value, bytes):
                hex_value = " ".join(f"{byte:02x}" for byte in value)
                print(f"{key}: {hex_value}")
            else:
                print(f"{key}: {value:02x}")  # Print in hex format with '0x' prefix

        print("")
        return unpacked_frame

    def sha256_checksum(self, file_path):
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            # Read and update the hash in chunks to avoid memory overload with large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        return sha256_hash.hexdigest()


if __name__ == "__main__":
    # Example Usage
    frame_gen = FrameGenerator()
    ser = SerialWrap("/dev/ttyUSB1", 115200)

    soh = 0xAA
    ssoh = 0x01
    ver = 0x01
    cmd = 0x02
    eot = 0x55
    id = 1

    reader = BinaryFileReader("app_update.bin")

    reader.open_file()
    total_pack = reader.get_total_packets(512)
    print(f"Total packets: {total_pack}")

    packed_frame = frame_gen.create_frame(
        soh, ssoh, ver, 0xF1, eot, id, struct.pack(">H", total_pack)
    )

    ser.send_bytes(packed_frame)

    # ack = False
    # while not ack:
    #     # Read data from serial until 0x55 is received
    #     data = ser.read_until(b"\x55")
    #
    #     # Ensure data is not empty and ends with 0x55
    #     if data and data.endswith(b"\x55"):
    #         # Unpack the frame
    #         data = frame_gen.unpack_frame(data)
    #
    #         # Check if the command in the frame is 0xF1
    #         if data["cmd"] == 0xF1 and data["ssoh"] == 0x04:
    #             print("Received ACK for total packets")
    #             ack = True
    #     else:
    #         print("No response received")

    i = 0
    while True:
        bytes_read = reader.read_bytes(512)
        if bytes_read is None:
            print("\nEnd of file reached.")
            break

        packed_frame = frame_gen.create_frame(
            soh, ssoh, ver, 0xF2, eot, id, bytes(bytes_read)
        )

        ser.send_bytes(packed_frame)
        time.sleep(0.2)
        i += 1
        print(f"Sent frame {i}")

        ack = False
        while not ack:
            # Read data from serial until 0x55 is received
            data = ser.read_until(b"\x55")

            # Ensure data is not empty and ends with 0x55
            if data and data.endswith(b"\x55"):
                # Unpack the frame
                data = frame_gen.unpack_frame(data)

                # Check if the command in the frame is 0xF1
                if data["cmd"] == 0xF2 and data["ssoh"] == 0x04:
                    print("Received ACK for total packets")
                    ack = True
            else:
                print("No response received")

    reader.close_file()

    # SHA 256 checksum
    sha256 = frame_gen.sha256_checksum("app_update.bin")
    print(f" SHA-256: {sha256}")
    packed_frame = frame_gen.create_frame(
        soh, ssoh, ver, 0xF3, eot, id, bytes.fromhex(sha256)
    )
    ser.send_bytes(packed_frame)
