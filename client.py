import socket
import sys
import select
import codecs

# Application version number
VERSION = "3.0"

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

# The encryption technique used by this client.
ENCRYPTION = "ROT13"
# Whether encryption is toggled on or off by the user.
ENCRYPTION_ON = True

def main():
    # First we want to make an alias for the user, and send it to the server.
    # The initial alias is temp by default
    ALIAS = "temp"

    successfully_registered = False
    while not successfully_registered:
        user_alias = raw_input("-->Provide your alias for the chat.\nreg: ")
        message = generate_packet(VERSION, ALIAS, "", "reg", user_alias)
        server.send(message)
        try:
            server_message = server.recv(512)
            print server_message
            successfully_registered = True
            ALIAS = user_alias
        except:
            print "-->Alias was not successfully registered"
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
                message = server.recv(512)
                print message
            else:
                user_input = raw_input()
                dest_client, request_verb, message = parse_user_input(user_input)
                # If the user is toggling encryption, we need to implement toggle, and do not need
                # to send a packet to the server.
                if request_verb == "enc":
                    ENCRYPTION_ON = not ENCRYPTION_ON
                    if ENCRYPTION_ON:
                        print "-->Encryption is toggled on."
                    else:
                        print "-->Encryption is toggled off."
                else:
                    # The encryption technique header field will be the value of ENCRYPTION variable if
                    # encryption is toggled on, and "cleartext" if toggled off.
                    header_enc = ENCRYPTION if ENCRYPTION_ON else "cleartext"
                    packet = generate_packet(VERSION, ALIAS, dest_client, request_verb, header_enc, message)
                    server.send(packet)
                    if request_verb == "bye":
                        server.close()
                        exit()


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
        # If the user wants to toggle encryption
        elif pre_colon == "enc:":
            return "", "enc", ""
        # If the user wants to disconnect from the chat
        elif pre_colon == "bye":
            return "", "bye", ""
        # The pre-colon input should be the destination client. If the
        # user doesn't exist then the server will return an error msg
        else:
            return pre_colon, "one", message


def generate_packet(version, source_client, dest_client, request_verb, header_enc, message):
    """
    This function generates an ASCII encoded packet that conforms to the header and
    data format outlined in the application's RFC.

    :param version: number representing application version
    :param source_client: string representing alias of user
    :param dest_client: string representing alias of intended recipient
    :param request_verb: string representing action requested of server
    :param header_enc: string representing encryption technique employed
    :param message: string representing message to be sent
    :return: ASCII encoded
    """

    # If encryption is toggled on, we want to first encrypt the message
    if ENCRYPTION_ON:
        message = encrypt_rot13(message)

    # ljust() appends spaces to a string (left-justified) to give it the total width specified.
    header = version.ljust(3) + source_client.ljust(30) + dest_client.ljust(30) \
        + request_verb.ljust(3) + header_enc.ljust(32) + "".ljust(190) + message.ljust(255)

    return header.encode("utf-8")


def encrypt_rot13(message):
    return codecs.encode(message, "rot_13")

main()


