from binascii import hexlify
import socket
import sys
import traceback


import paramiko
from paramiko.util import u

from argparse import ArgumentParser

from server import Server


if __name__ == "__main__":
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
        required=True,
        help="The target SSH server port. Default is 22."
    )

    parser.add_argument(
        '--ssh-version',
        type=str,
        default="SSH-2.0-OpenSSH_8.2p1",
        help="The SSH version string. Default is 'SSH-2.0-OpenSSH_8.2p1'."
    )

    args = parser.parse_args()

    port = args.port
    target_host = args.target_host
    target_port = args.target_port
    ssh_version = "SSH-2.0-OpenSSH_8.9p1"# ssh_version = args.ssh_version
    
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
        t.local_version = ssh_version
        
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


        if not server.is_channel_exec_request:
            server.check_channel_pty_request(server.channel, 'xterm', 80, 24, 0, 0, '')
            server.check_channel_shell_request(server.channel)

        command = ""

        while command != "exit":
            server.channel.send(server.target_prompt)
            f = server.channel.makefile('rU')

            command = f.readline().strip('\r\n')
            server.exec_command(server.channel, command)
        
        server.channel.close()

    except Exception as e:
        print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
        traceback.print_exc()
        try:
            t.close()
        except:
            pass
        sys.exit(1)