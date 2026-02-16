import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="your db password",
        database="pollution_db"
    )
    return connection
