import socket
import sys
from thread import *
from utility import parse_data, generate_packet, crypt_rot13

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

    clientsocket.send("-->SERVER: You've entered the chat!")
    while True:
        # Header + data will always be a fixed size of 512 bytes. The
        # thread will block until a message is received from
        # the client socket.
        try:
            data = clientsocket.recv(512)
            # Data should be parsed based on proper header and data format
            parsed_data = parse_data(data)
            # parsed_data returns a tuple of strings that represent all the header and
            # data fields in the users message. server_action will perform some action
            # based on the request verb and other header info.
            server_action(clientsocket, address, data)

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


def server_action(clientsocket, address, packet):
    """
    The purpose of this function is to perform an action based on the
    request verb provided by the user. This function will be called
    every time a message is received from connected client sockets.

    :param clientsocket: the client's socket object connected to the server
    :param address: the client's IPv4 address
    :param packet: the packet sent by the source client
    :return: Nothing
    """

    # First parse the packet for the relevant header information
    version, source_client, dest_client, request_verb, header_enc, message = parse_data(packet)

    # If the user is initially registering their alias
    if source_client == "temp" and request_verb == "reg":
        user_alias = message[:30]
        users[user_alias] = clientsocket
        server_msg = "Alias successfully registered!"
        # If user has encrypted their message, we should encrypt our message back to them
        if header_enc == "ROT13":
            server_msg = crypt_rot13(server_msg)
        server_packet = generate_packet(version, "SERVER", source_client, "svr", header_enc, server_msg)
        clientsocket.send(server_packet)
        for alias, socket in users.iteritems():
            if alias != user_alias:
                server_msg = user_alias + " has entered the chat!"
                if header_enc == "ROT13":
                    server_msg = crypt_rot13(server_msg)
                server_packet = generate_packet(version, "SERVER", source_client, "svr", header_enc, server_msg)
                socket.send(server_packet)

    # If the user is re-registering their alias, we simply change the name
    # of the key being used for the socket in the users dictionary.
    elif request_verb == "reg":
        alias = message[:30]
        users[alias] = users[source_client]
        del users[source_client]

    # If the message is to be sent to a particular user
    elif request_verb == "one":
        users[dest_client].send(packet)
        print source_client + " -> " + dest_client + ": " + message

    # If the message is to be sent to all users
    elif request_verb == "all":
        for alias, socket in users.iteritems():
            if alias != source_client:
                socket.send(packet)
                print source_client + " -> " + alias + ": " + message

    # If the user requests a list of all other users
    elif request_verb == "who":
        user_list = "Active users: "
        for alias, socket in users.iteritems():
            if alias != source_client:
                user_list += (alias + ", ")
        if header_enc == "ROT13":
            user_list = crypt_rot13(user_list)
        server_packet = generate_packet(version, "SERVER", source_client, "svr", header_enc, user_list)
        users[source_client].send(server_packet)

    # If the user requests to disconnect from the chat
    elif request_verb == "bye":
        for alias, socket in users.iteritems():
            if alias != source_client:
                server_msg = source_client + " has left the chat!"
                if header_enc == "ROT13":
                    server_msg = crypt_rot13(server_msg)
                server_packet = generate_packet(version, "SERVER", source_client, "svr", header_enc, server_msg)
                socket.send(server_packet)
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
