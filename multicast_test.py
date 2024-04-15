import socket
import binascii
import struct

# the multicast address you're so fond of
multicast_group = '232.10.10.10'
port = 3333
message = binascii.unhexlify('010008100102030405060708')  # your secret hex message
#message = binascii.unhexlify('000008000102030405060708')  # your secret hex message

# creating a socket like you're trying to make fire with two sticks
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
# setting TTL, because apparently, we want this packet to barely make it out the door
ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

try:
    # attempting to send your message into the digital void
    sent = sock.sendto(message, (multicast_group, port))
    print(f"Attempted to send bytes, and this time the network noticed: {sent}")
except Exception as e:
    # oh look, an error, how utterly predictable
    print(f"Well, this didn't work. Here's why: {e}")
finally:
    # closing the socket with the elegance of a rhino on ice
    sock.close()

