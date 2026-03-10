import threading
import subprocess
import time
from flask_app import app


def run_server():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)


if __name__ == "__main__":

    server = threading.Thread(target=run_server)
    server.daemon = True
    server.start()

    time.sleep(2)

    subprocess.Popen([
        "cmd",
        "/c",
        "start",
        "msedge",
        "--app=http://127.0.0.1:5000"
    ])

    server.join()