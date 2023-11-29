from flask import Flask
from flask import request
from flask_cors import CORS
import json
import subprocess

from flask_socketio import SocketIO, emit

from app.server.server import SSHConnection

import asyncio
from asyncio import CancelledError

app = Flask(__name__)

CORS(app)
socketio = SocketIO(app, cors_allowed_origins="http://127.0.0.1:8080")

ssh_connection = None
ssh_server = None

async def start_ssh_server(params):
    global ssh_connection
    global ssh_server

    server_port = int(params['serverPort'])
    target_host = params['targetHost']
    target_port = int(params['targetPort'])
    ssh_version = params['sshVersion']

    try:
        if ssh_server and not ssh_server.done():
            ssh_server.cancel()
            try:
                await ssh_server
            except CancelledError:
                print("server turned off")
                socketio.emit('log_from_server', 'server turned off')
            
            

        socketio.emit('log_from_server', 'connection creating')
        ssh_connection = SSHConnection(
            client_port   = server_port,
            target_host   = target_host,
            target_port   = target_port,
            ssh_version   = ssh_version,
            emit_function = socketio.emit
        )
        socketio.emit('log_from_server', 'connection created')

        socketio.emit('log_from_server', 'creating ssh server')

        ssh_server = asyncio.create_task(ssh_connection.create_server())

        await ssh_server
    
    except Exception as e:
        print(f"An error occurred: {e}")

@app.route("/start_server", methods=['POST'])
async def start_server():
    params = json.loads(request.data.decode('utf-8'))
    
    loop = asyncio.get_event_loop()
    await loop.create_task(start_ssh_server(params))


    return {'success': 'ok'}

if __name__ == "__main__":
    app.run(debug=True)