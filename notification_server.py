import socket

def start_notification_server(host="127.0.0.1", port=9999):
    """
    Starts a simple TCP server that receives notification messages
    from the email client and prints them.
    """
    print(" Starting Notification Server")

    # Create a TCP/IP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Bind the server to the host and port
        
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((host, port))
        
        # Listen for incoming connections
        server_socket.listen(1)

        print(f"Notification Server listening on {host}:{port}")
        print("Waiting for status updates ")

        while True:
            # Accept incoming client connection
            client_socket, client_address = server_socket.accept()
            print(f"\n[+] Connection established from {client_address[0]}:{client_address[1]}")

            # Receive notification message (max 1024 bytes)
            data = client_socket.recv(1024)
            if data:
                message = data.decode("utf-8").strip()
                print(f" Notification Received: {message}")

            # Close client connection
            client_socket.close()
            print("[-] Client connection closed")

    except KeyboardInterrupt:
        print("\nServer stopped manually (Ctrl+C)")

    except socket.error as e:
        print(f" Socket error: {e}")

    finally:
        server_socket.close()
        print(" Server socket closed safely")


if __name__ == "__main__":
    start_notification_server()

    
    #python notification_server.py