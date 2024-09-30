import subprocess

# Running a simple CLI command, for example, 'ls' (Linux/macOS) or 'dir' (Windows)
command = ["mcumgr", "version"]

# command = [
#     "mcumgr",
#     "conn",
#     "add",
#     "testDK",
#     "type=serial",
#     "connstring=dev=/dev/ttyUSB1,baud=115200,mtu=512",
# ]
#
command = ["mcumgr", "-c", "usb1", "image", "list"]

# Run the command and capture the output
result = subprocess.run(
    command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
)

# Print the command's output
print("Output:")
print(result.stdout)


# Print any error messages
if result.stderr:
    print("Errors:")
    print(result.stderr)
