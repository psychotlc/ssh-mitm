from binascii import hexlify
import socket
import sys
import traceback


import paramiko
from paramiko.util import u

from app.server.server_interface import Server

class SSHConnection():

    def __init__(self, client_port, target_host, target_port, emit_function, ssh_version=None):
        self.client_port   = client_port
        self.target_host   = target_host
        self.target_port   = target_port
        self.ssh_version   = ssh_version if ssh_version else "SSH-2.0-OpenSSH_8.2p1"
        self.emit_function = emit_function
        self.server_exists = False



    async def create_server(self):
        host_key = paramiko.RSAKey(filename=".ssh/test_rsa.key")

        # setup logging
        paramiko.util.log_to_file(f"log_file.log")

        host_key = paramiko.RSAKey(filename=".ssh/test_rsa.key")

        print("Read key: " + u(hexlify(host_key.get_fingerprint())))

        DoGSSAPIKeyExchange = True

        # now connect
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.client_port))
        except Exception as e:
            self.emit_function('log_from_server', "*** Bind failed: " + str(e))
            print("*** Bind failed: " + str(e))
            traceback.print_exc()

        try:
            sock.listen(100)
            self.emit_function('log_from_server', "Listening for connection ...")
            print("Listening for connection ...")
            client, addr = sock.accept()
        except Exception as e:
            self.emit_function('log_from_server', "*** Listen/accept failed: " + str(e))
            print("*** Listen/accept failed: " + str(e))
            traceback.print_exc()

        print("Got a connection!")

        try:
            self.t = paramiko.Transport(client, gss_kex=DoGSSAPIKeyExchange)
            self.t.set_gss_host(socket.getfqdn(""))
            self.t.local_version = self.ssh_version
            
            try:
                self.t.load_server_moduli()
            except:
                self.emit_function('log_from_server', "(Failed to load moduli -- gex will be unsupported.)")
                print("(Failed to load moduli -- gex will be unsupported.)")
                raise
            self.t.add_server_key(host_key)

            server = Server(self.t, self.target_host, self.target_port)
            try:
                self.t.start_server(server=server)
                self.server_exists = True
            except paramiko.SSHException:
                self.emit_function('log_from_server', "*** SSH negotiation failed.")
                print("*** SSH negotiation failed.")
            
            

            server.event.wait(30)
            self.emit_function('log_from_server', "Authenticated!")
            print("Authenticated!")

        except Exception as e:
            self.emit_function('log_from_server', "*** Caught exception: " + str(e.__class__) + ": " + str(e))
            print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
            traceback.print_exc()
            try:
                self.t.close()
            except:
                pass
    