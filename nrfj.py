import argparse
import subprocess
import sys

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"  # Reset color to default


def print_info(message):
    print(f"{GREEN}[INFO]{RESET} {message}")


def print_error(message):
    print(f"{RED}[ERROR]{RESET} {message}")
    sys.exit(1)


# nrfjprog --recover -f NRF53 --coprocessor CP_NETWORK --snr 1050092818


def run_command(command, description):
    print_info(f"{description}...")
    print_info(f"Command to run: {command}")
    result = subprocess.run(command, shell=True, stdout=sys.stdout, stderr=sys.stderr)
    if result.returncode != 0:
        print_error(f"Failed: {description}")


def main():
    parser = argparse.ArgumentParser(description="Nordic nRF53 JLink Flasher")
    parser.add_argument(
        "-d", "--dev", choices=["app", "net"], help="Core to target (app/net)"
    )
    parser.add_argument(
        "-r", "--recover", help="Recover the specified core", action="store_true"
    )
    parser.add_argument("-f", "--file", help="Hex file to flash (*.hex)")
    parser.add_argument("--pinreset", help="Reset the device only", action="store_true")

    args = parser.parse_args()

    # If only --pinreset is given, reset and exit
    if args.pinreset and not (args.dev or args.recover or args.file):
        run_command("nrfjprog --pinreset -f NRF53", "Resetting device")
        sys.exit(0)

    # Get Programmer ID
    result = subprocess.run(
        "nrfjprog --ids", shell=True, capture_output=True, text=True
    )
    programmer_id = result.stdout.strip()

    if not programmer_id:
        print_error("No connected devices found.")

    print_info(f"Programmer ID: {programmer_id}")

    # Recover Core
    if args.recover:
        cmd = f"nrfjprog --recover -f NRF53"
        if args.dev == "net":
            cmd += " --coprocessor CP_NETWORK"

        cmd += f" --snr {programmer_id}"
        run_command(cmd, f"Recovering {args.dev} core")

    # Flash Core
    if args.file:
        if not args.dev:
            print_error("--dev is required when using --file")

        cmd = f"nrfjprog --program {args.file} --sectorerase --verify -f NRF53 --snr {programmer_id}"
        if args.dev == "app":
            cmd += " --qspisectorerase"
        elif args.dev == "net":
            cmd += " --coprocessor CP_NETWORK"
        run_command(cmd, f"Flashing {args.dev} core with {args.file}")

    # Reset automatically if recover or flash was performed
    if args.recover or args.file:
        run_command(
            f"nrfjprog --pinreset -f NRF53 --snr {programmer_id}",
            "Resetting device after operation",
        )

    # If --pinreset was manually provided, reset again
    if args.pinreset:
        run_command(
            f"nrfjprog --pinreset -f NRF53 --snr {programmer_id}",
            "Manual reset requested",
        )


if __name__ == "__main__":
    main()
