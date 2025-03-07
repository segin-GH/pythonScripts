import time
import pytest
from cerialWriter import SerialWrap


@pytest.fixture(scope="module")
def uart():
    # Start the serial for testing
    ser = SerialWrap("/dev/ttyUSB1", 115200)
    yield ser
    ser.close_port()


@pytest.fixture(scope="module")
def start_and_pause_sheet_acquisition_sps(uart, request):
    input_value = request.param

    uart.send_hex("P")  # Pause data acquisition

    uart.send_hex("4")
    uart.send_hex(input_value)

    uart.send_hex("S")
    time.sleep(1)
    uart.flush_buffer()

    data_len, data = uart.read_bytes_in_array(timeout=1)
    uart.send_hex("P")

    return (data_len / 2), data  # Assuming data_len is in bytes, return half


@pytest.fixture(scope="module")
def start_and_pause_sheet_acquisition_frame_len(uart, request):
    input_value = request.param

    # Send commands via UART
    uart.send_hex("P")
    uart.send_hex("4")
    uart.send_hex(input_value)
    uart.send_hex("S")

    time.sleep(1)  # Simulate waiting time for the acquisition
    uart.flush_buffer()  # Flush any buffer before reading

    # Convert input_value ('a', 'b', 'c', 'd') to the corresponding length
    length_to_read = {"a": 125, "b": 250, "c": 500, "d": 1000}[
        input_value
    ]  # Map input_value to the byte length directly

    # Read the specified number of bytes
    elapsed_time, data_len, data = uart.read_bytes(length_to_read)

    uart.send_hex("P")  # Pause again

    return elapsed_time, (data_len / 2), data  # Adjust data length as needed


def test_version(uart):
    uart.send_hex("F")

    received_data = uart.read_until_timeout(timeout=1)
    assert received_data == b"0.bs.001"


def test_sheet_status(uart):
    uart.send_hex("C")

    recived_data = uart.read_until_timeout(timeout=1)
    assert recived_data == b"0"


def test_pause_sheet_acquasition(uart):
    uart.send_hex("P")

    recived_data = uart.read_until_timeout(timeout=1)
    assert recived_data == b""


@pytest.mark.parametrize(
    "start_and_pause_sheet_acquisition_sps, expected_len",
    [
        ("a", 125),
        ("b", 250),
        ("c", 500),
        ("d", 1020),
    ],  # fix: this test d is should be 1000
    indirect=[
        "start_and_pause_sheet_acquisition_sps"
    ],  # Indirectly parametrize the fixture
)
def test_sampling_sps(start_and_pause_sheet_acquisition_sps, expected_len):
    received_len, received_data = start_and_pause_sheet_acquisition_sps
    assert received_len == pytest.approx(expected_len, abs=10)


@pytest.mark.parametrize(
    "start_and_pause_sheet_acquisition_frame_len, expected_len",
    [
        ("a", 125),
        ("b", 250),
        ("c", 500),
        ("d", 1000),
    ],  # fix: this test d is should be 1000
    indirect=[
        "start_and_pause_sheet_acquisition_frame_len"
    ],  # Indirectly parametrize the fixture
)
def test_sampling_frame_len(start_and_pause_sheet_acquisition_frame_len, expected_len):
    elapsed_time, received_len, received_data = (
        start_and_pause_sheet_acquisition_frame_len
    )
    assert received_len == pytest.approx(expected_len, abs=10)
    assert elapsed_time == pytest.approx(1, abs=0.1)
