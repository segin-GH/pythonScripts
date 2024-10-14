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
def start_and_pause_sheet_acquisition(uart, request):
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
    "start_and_pause_sheet_acquisition, expected_len",
    [
        ("a", 125),
        ("b", 250),
        ("c", 500),
        ("d", 1020),
    ],  # fix: this test d is should be 1000
    indirect=[
        "start_and_pause_sheet_acquisition"
    ],  # Indirectly parametrize the fixture
)
def test_sampling_sps(start_and_pause_sheet_acquisition, expected_len):
    received_len, received_data = start_and_pause_sheet_acquisition
    assert received_len == pytest.approx(expected_len, abs=10)
