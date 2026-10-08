"""Practice app - FIXED version (was deliberately vulnerable). Never deploy."""
import ipaddress
import os
import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)

# FIX 1: the secret comes from an environment variable, not from the code.
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]


@app.route("/user")
def get_user():
    # FIX 2: parameterized query. The "?" placeholder keeps user input as data.
    username = request.args.get("name", "")
    conn = sqlite3.connect("users.db")
    rows = conn.execute("SELECT * FROM users WHERE name = ?", (username,)).fetchall()
    return str(rows)


@app.route("/ping")
def ping():
    # FIX 3: no shell, and the input must be a valid IP address.
    host = request.args.get("host", "127.0.0.1")
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return "Invalid IP address", 400
    output = subprocess.check_output(["ping", "-c", "1", str(ip)])
    return output


if __name__ == "__main__":
    # FIX 4: debug mode is off unless someone turns it on deliberately.
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")