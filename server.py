import socket
import select
import sys
from threading import *


# AF_INET refers to the use of IPv4, SOCK_STREAM refers to TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

"""
When the server script is started from the command line,
we want to pass it 3 arguments for the script, IP address,
and port number.
"""
if len(sys.argv) != 3:
    print("Correct usage: <script> <IP> <port>")
    exit()

IP_ADDRESS = str(sys.argv[1])
PORT = int(sys.argv[2])

server.bind(IP_ADDRESS, PORT)

# The server will listen for up to 5 connections
server.listen(5)

# This list will eventually be populated with the client sockets that have connected
users = []

"""
A new thread will be created for each user that connects, in order to listen
to users concurrently. Below is the function to be executed for every new thread.
"""

def user_thread(socket, addr):
    socket.send("You've entered the chat!")
    while True:
        try:
            # This function receives 2048 bytes of data from the connected socket
            data = socket.recv(2048)
