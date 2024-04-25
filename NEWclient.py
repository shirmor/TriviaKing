# todo: לשנות את הפורט כך שיהיה שיתופי

import socket
import struct
import sys
import threading
from faker import Faker
import re


Bold = "\033[1m"
Red = "\033[31;1m"
Green = "\033[32;1m"
Yellow = "\033[33;1m"
Blue = "\033[34;1m"
end = "\033[0;1m"


def receive_udp_offer(udp_socket):
    while True:
        try:
            data, server_address = udp_socket.recvfrom(1024)
            magic_cookie = data[:4]
            message_type = data[4]
            if magic_cookie == b'\xab\xcd\xdc\xba' and message_type == 0x02:
                server_name_end = data.find(b'\x00', 5)
                server_name = data[5:server_name_end].decode('utf-8').strip()
                # Extract server port bytes
                server_tcp_port = data[37: 39]
                # Unpack the bytes to get the server TCP port number
                server_tcp_port_number = struct.unpack('!H', server_tcp_port)[0]
                # Extract message
                server_message_start = data.find(b'Received')
                message = data[server_message_start:].decode('utf-8')
                # Define a regular expression pattern to find the IP address after 'address'
                pattern = r'address (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                # Find all matches of the pattern in the text
                server_ip_address = re.search(pattern, message).group(1)
                return magic_cookie, message_type, server_name, server_ip_address, server_tcp_port_number, message
        except Exception as e:
            print("receive_udp_offer:", e)
            break


def receive_tcp_messages(client_socket,  stop_event):
    while not stop_event.is_set():
        try:
            data = client_socket.recv(1024).decode()
            if not data:
                break
            print(data)
            # Check if the received data contains "game over"
            if "game over" in data.lower():
                print("Server disconnected, listening for offer requests...")
                stop_event.is_set()
                break
        except Exception as e:
            print("receive_tcp_messages:", e)
            break


def send_tcp_messages(client_socket,  stop_event):
    while not stop_event.is_set():
        try:
            message = input()
            client_socket.sendall(message.encode())
        except Exception as e:
            print("send_tcp_messages:", e)
            break


def main():
    udp_socket = None
    client_socket = None
    # Send player name to the server
    fake = Faker()
    player_name = fake.name()
    server_udp_port = 13117
    stop_event = threading.Event()
    while True:
        try:
            # Create a UDP socket
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(("", server_udp_port))

            print(f"{Blue}Client started, listening for offer requests...")

            # Listen for offer messages
            magic_cookie, message_type, server_name, server_ip_address, server_tcp_port, message = receive_udp_offer(udp_socket)
            print(message)

            # Connect to the server via TCP
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                client_socket.connect((server_ip_address, server_tcp_port))
            except Exception as e:
                print(e)
            print("Connected to the server.")
            client_socket.sendall(player_name.encode() + b'\n')
            # Start threads for sending and receiving messages
            receive_thread = threading.Thread(target=receive_tcp_messages, args=(client_socket, stop_event))
            send_thread = threading.Thread(target=send_tcp_messages, args=(client_socket, stop_event))
            send_thread.start()
            receive_thread.start()
            send_thread.join()
            receive_thread.join()
            udp_socket.close()
            client_socket.close()
        except Exception as e:
            print("main:", e)
            sys.exit()
        finally:
            if udp_socket:
                udp_socket.close()
            if client_socket:
                client_socket.close()


if __name__ == "__main__":
    main()




