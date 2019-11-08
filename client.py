import socket
import sys
import select
import hashlib
from random import randint

# Application version number
VERSION = "1.0"

# AF_INET refers to the use of IPv4, SOCK_STREAM refers to TCP
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# 3 arguments should be passed from the command line when
# the client is started up
if len(sys.argv) != 3:
    print "Correct usage: <script> <address> <port>"
    exit()

# Grab the server host address and convert it to IPv4
HOST = socket.gethostbyname(sys.argv[1])
# Grab the server port
PORT = int(sys.argv[2])

try:
    # Attempt to connect to the server
    server.connect((HOST, PORT))
except:
    print "Could not establish connection to the chat."
    exit()


def main():
    # For purposes of checksum verification on the server side, if the server
    # sends an error, we want to resend the previous packet
    previous_packet = None

    # First we want to make an alias for the user, and send it to the server.
    # The initial alias is temp by default
    ALIAS = "temp"
    successfully_registered = False
    while not successfully_registered:
        user_alias = raw_input("Provide your alias for the chat.\nreg: ")
        packet = generate_packet(VERSION, ALIAS, "", "reg", user_alias)
        server.send(packet)
        previous_packet = packet
        try:
            server_message = server.recv(512)
            # If there was packet corruption
            if server_message == "RESEND":
                amended_packet = replace_checksum(previous_packet)
                previous_packet = amended_packet
                server.send(amended_packet)
            else:
                print server_message
                successfully_registered = True
                ALIAS = user_alias
        except:
            print "Alias was not successfully registered"
            continue

    input_streams = [sys.stdin, server]

    # Once the user has registered their alias, they can continue normally
    while True:
        """
        Python's select module gives an interface to the unix select() system call. It returns
        the input stream that is ready to be read from a list of input streams that you provide
        to it. Since at any given time we could be receiving input from either the server or the
        user, we need to be able to distinguish which one it is.
        """

        read_streams, write, error = select.select(input_streams, [], [])

        for inputs in read_streams:
            if inputs == server:
                try:
                    message = server.recv(512)
                    if message == "RESEND":
                        amended_packet = replace_checksum(previous_packet)
                        previous_packet = amended_packet
                        server.send(amended_packet)
                    else:
                        print message
                except:
                    print "-->Message could not be sent"
                    continue
            else:
                user_input = raw_input()
                dest_client, request_verb, message = parse_user_input(user_input)
                packet = generate_packet(VERSION, ALIAS, dest_client, request_verb, message)
                previous_packet = packet
                server.send(packet)
                if request_verb == "bye":
                    server.close()
                    exit()


def generate_checksum(data):
    """
    This function generates a checksum based on the data field given to it. It uses
    the md5 hashing function to generate a hexadecimal checksum. For purposes of testing
    the checksum verification process, an incorrect checksum will be returned about 10%
    of the time.

    :param data: string representing user message to be sent.
    :return: string representing data checksum in hexadecimal, based on hash
    """

    rand_num = randint(1, 10)
    if rand_num == 1:
        return ""

    data = data.strip()
    checksum = hashlib.md5()
    checksum.update(data)
    return checksum.hexdigest()


def replace_checksum(packet):
    """
    This function replaces the checksum in a packet to be sent to the server.
    It is used to deal with RESEND errors that are received from the server
    when sent packages are corrupt.

    :param packet: string representing a formatted packet, with header and data
    :return: string representing new packet with replaced checksum in header
    """

    message = packet[256:]
    new_checksum = generate_checksum(message)
    new_packet = (packet[:66] + new_checksum + packet[98:]).encode("utf-8")

    return new_packet


def parse_user_input(user_input):
    """
    This function will parse the user input to determine which request verb is to be
    sent to the server, along with the destination client and message. Since the format
    of the users input should be "verb:message" where verb can be either a destination
    client or action verb, the message is split at the colon and parsed into its two
    components.

    :param user_input: string of user input
    :return: a tuple in the format (dest_client, request_verb, message)
    """

    split_input = user_input.split(":")

    # If the user input is not in the correct format, split_input will not have
    # two string elements. We don't want the server to do anything in this case
    if len(split_input) != 2:
        return "", "", ""
    else:
        pre_colon = split_input[0]
        message = split_input[1]
        # If the user wants to send the message to all other users
        if pre_colon == "all":
            return "", "all", message
        # If the user wants a list of all other users
        elif pre_colon == "who":
            return "", "who", ""
        # If the user wants to disconnect from the chat
        elif pre_colon == "bye":
            return "", "bye", ""
        # The pre-colon input should be the destination client. If the
        # user doesn't exist then the server will return an error msg
        else:
            return pre_colon, "one", message


def generate_packet(version, source_client, dest_client, request_verb, message):
    """
    This function generates an ASCII encoded packet that conforms to the header and
    data format outlined in the application's RFC.

    :param version: number representing application version
    :param source_client: string representing alias of user
    :param dest_client: string representing alias of intended recipient
    :param request_verb: string representing action requested of server
    :param checksum: string representing hexadecimal checksum of message
    :param message: string representing message to be sent
    :return: ASCII encoded
    """

    # The checksum is calculated based on the message
    checksum = generate_checksum(message)

    # ljust() appends spaces to a string (left-justified) to give it the total width specified.
    packet = version.ljust(3) + source_client.ljust(30) + dest_client.ljust(30) \
        + request_verb.ljust(3) + checksum.ljust(32) + "".ljust(158) + message.ljust(256)

    return packet.encode("utf-8")


main()


