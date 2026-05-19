import sqlite3

def db():
    conn = sqlite3.connect("parking.db")
    conn.row_factory = sqlite3.Row
    return conn