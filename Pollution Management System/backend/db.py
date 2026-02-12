import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Rs@969383",
        database="pollution_db"
    )
    return connection