import socket
import sys
from thread import *
import hashlib

# AF_INET refers to the use of IPv4, SOCK_STREAM refers to TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# When the server script is started from the command line,
# we want to pass it 2 arguments for the script,
# and port number.
if len(sys.argv) != 2:
    print("Correct usage: <script> <port>")
    exit()

# We want to grab the IPv4 address of the host domain that is running this server
HOST = socket.gethostbyname(socket.gethostname())
print "Hosting on " + HOST
PORT = int(sys.argv[1])

# The server socket is bound to the corresponding host and port
server.bind((HOST, PORT))

# The users dictionary will be populated with key value pairs,
# the values being the socket connected to the server, and the
# key being the alias provided by the user.
users = {}


def user_thread(clientsocket, address):
    """
     This function defines the code that will be run for each new thread
     that is generated when a client socket connects to the server.

    :param clientsocket: the socket object of the connected client
    :param address: the IPv4 address of the connected client
    :return:
    """

    clientsocket.send("-->You've entered the chat!")
    while True:
        # Header + data will always be a fixed size of 512 bytes. The
        # thread will block until a message is received from
        # the client socket.
        try:
            data = clientsocket.recv(512)
            # Data should be parsed based on proper header and data format
            source_client, dest_client, request_verb, checksum, message = parse_data(data)
            # server_action will perform some action based on the request verb and other header info.
            server_action(clientsocket, address, source_client, dest_client, request_verb,
                          checksum, message)

        except Exception as e:
            print e


def server_live():
    """
    When this function is called, the server is live. It will accept connections,
    and start a new thread for each connected client. The number of connections is
    managed so that only 5 connections can be active at once.

    :return: Nothing
    """

    # Listen for connections
    server.listen(5)

    # The server will accept up to 5 connections

    while True:
        if len(users) < 5:
            clientsocket, address = server.accept()
            print "connection from {} was established!".format(address)

            # A new thread will be created for each user that connects, in order to listen
            # to users concurrently.
            start_new_thread(user_thread, (clientsocket, address))
        else:
            continue


def parse_data(data):
    """
    This function will parse the binary data (in ASCII) based on the header field sizes
    outlined in the application's RFC.

    :param data: 512 bytes of binary data received from the client socket, representing
    the ASCII encoded message, both the header and the data.
    :return: a tuple of strings representing the parsed header fields and data.
    """

    # Note that the data will be in ASCII at this point
    source_client = data[3:33]
    dest_client = data[33:63]
    request_verb = data[63:66]
    checksum = data[66:98]
    message = data[256:]

    # We want to decode everything before we use the string values in future code
    return source_client.decode("utf-8").strip(), dest_client.decode("utf-8").strip(), \
           request_verb.decode("utf-8").strip(), checksum.decode("utf-8").strip(), message.decode("utf-8").strip()


def verify_checksum(message, header_checksum):
    """
    This function compares the checksum in the header with a checksum generated
    based on the message received. If they are the same, then the checksum has
    been verified. If they are different, then packet corruption has occurred.

    :param message: string representing message sent by client
    :param header_checksum: string representing hexadecimal checksum provided
    in packet header
    :return: boolean representing outcome of checksum verification
    """

    checksum = hashlib.md5()
    checksum.update(message)

    if checksum.hexdigest() == header_checksum:
        return True
    return False


def server_action(clientsocket, address, source_client, dest_client, request_verb, checksum, message):
    """
    The purpose of this function is to perform an action based on the
    request verb provided by the user. This function will be called
    every time a message is received from connected client sockets.

    :param clientsocket: the client's socket object connected to the server
    :param address: the client's IPv4 address
    :param source_client: string representing user alias
    :param dest_client: string representing alias of intended recipient
    :param request_verb: string representing action requested of server
    :param checksum: string representing hexadecimal checksum for message
    :param message: string representing message sent by user
    :return: Nothing
    """

    # First we want to verify that there was no packet corruption
    if not verify_checksum(message, checksum):
        clientsocket.send("RESEND")

    # If the user is initially registering their alias
    elif source_client == "temp" and request_verb == "reg":
        user_alias = message[:30]
        users[user_alias] = clientsocket
        clientsocket.send("-->Alias successfully registered!")
        for alias, socket in users.iteritems():
            if alias != user_alias:
                socket.send("-->" + user_alias + " has entered the chat!")

    # If the user is re-registering their alias, we simply change the name
    # of the key being used for the socket in the users dictionary.
    elif request_verb == "reg":
        alias = message[:30]
        users[alias] = users[source_client]
        del users[source_client]

    # If the message is to be sent to a particular user
    elif request_verb == "one":
        users[dest_client].send("-->From " + source_client + ": " + message)

    # If the message is to be sent to all users
    elif request_verb == "all":
        for alias, socket in users.iteritems():
            if alias != source_client:
                socket.send("-->From " + source_client + ": " + message)

    # If the user requests a list of all other users
    elif request_verb == "who":
        user_list = "Active users: "
        for alias, socket in users.iteritems():
            if alias != source_client:
                user_list += (alias + ", ")
        # Send user list to source client socket
        users[source_client].send("-->" + user_list)

    # If the user requests to disconnect from the chat
    elif request_verb == "bye":
        for alias, socket in users.iteritems():
            if alias != source_client:
                socket.send("-->" + source_client + " has left the chat!")
        # Remove from active users list
        users.pop(source_client, None)
        print "{} has disconnected.".format(address)
        # Kill the thread
        exit()

    # If the request verb was anything else, the server will do nothing
    else:
        pass


# Make the server live
server_live()
