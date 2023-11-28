from flask import Flask
from flask import request
from flask_cors import CORS
import json
import subprocess

import asyncio

app = Flask(__name__)

CORS(app)

ssh_server = None

@app.route("/start_server", methods=['POST'])
async def start_server():
    global ssh_server

    params = json.loads(request.data.decode('utf-8'))
    server_port = params['server_port']
    target_host = params['target_host']
    target_port = params['target_port']
    ssh_version = params['ssh_version']

    args_to_pass = ['--port', server_port, '--target-host', target_host, '--target-port', target_port]

    if ssh_version:
        args_to_pass.extend(*['ssh-version', ssh_version])

    file_to_run = "app/server/main.py"

    try:
        ssh_server = await asyncio.create_subprocess_exec('python', file_to_run, *args_to_pass)
    except FileNotFoundError:
        print(f"Error: File '{file_to_run}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

    return {'success': 'ok'}

@app.route("/stop_server", methods=['GET'])
def stop_server():
    global ssh_server

    ssh_server.stop()

    ssh_server = None

    return {"success": "ok"}

if __name__ == "__main__":
    app.run(debug=True)