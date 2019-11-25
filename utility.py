"""
This file contains the utility functions used by the client and server
applications.
"""
import codecs


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

    # ljust() appends spaces to a string (left-justified) to give it the total width specified.
    header = version.ljust(3) + source_client.ljust(30) + dest_client.ljust(30) \
        + request_verb.ljust(3) + header_enc.ljust(32) + "".ljust(158) + message.ljust(256)

    return header.encode("utf-8")


def parse_data(data):
    """
    This function will parse the binary data (in ASCII) based on the header field sizes
    outlined in the application's RFC.

    :param data: 512 bytes of binary data received from the client socket, representing
    the ASCII encoded message, both the header and the data.
    :return: a tuple of strings representing the parsed header fields and data.
    """

    # Note that the data will be in ASCII at this point
    version = data[0:3]
    source_client = data[3:33]
    dest_client = data[33:63]
    request_verb = data[63:66]
    header_enc = data[66:98]
    message = data[256:]

    # We want to decode everything before we use the string values in future code
    return version.decode("utf-8").strip(), source_client.decode("utf-8").strip(), \
           dest_client.decode("utf-8").strip(), request_verb.decode("utf-8").strip(), \
           header_enc.decode("utf-8").strip(), message.decode("utf-8").strip()


def crypt_rot13(message):
    return codecs.encode(message, "rot_13")
