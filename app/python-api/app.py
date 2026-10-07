"""DELIBERATELY VULNERABLE practice app. Never deploy. Exists only to be scanned."""
import sqlite3
import subprocess

from flask import Flask, request

app = Flask(__name__)

# BUG 1
app.config["SECRET_KEY"] = "super-secret-key-123"


@app.route("/user")
def get_user():
    # BUG 2
    username = request.args.get("name", "")
    conn = sqlite3.connect("users.db")
    query = f"SELECT * FROM users WHERE name = '{username}'"
    rows = conn.execute(query).fetchall()
    return str(rows)


@app.route("/ping")
def ping():
    # BUG 3
    output = subprocess.check_output(f"ping -c 1 {host}", shell=True)
    return output


if __name__ == "__main__":
    # BUG 4
    app.run(debug=True)