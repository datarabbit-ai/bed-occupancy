import os

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import RealDictCursor

load_dotenv()


def get_connection() -> psycopg2.extensions.connection:
    """
    Establishes a connection to the PostgreSQL database.
    :return: psycopg2.extensions.connection object
    :raises Exception: If the connection fails.
    """

    db_name = os.getenv("POSTGRES_DB")
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")

    try:
        conn = psycopg2.connect(dbname=db_name, user=db_user, password=db_password, host=db_host, port=db_port)
        conn.cursor_factory = RealDictCursor
        return conn
    except Exception as e:
        print(f"Failed to connect: {e}")
        raise


def close_connection(conn: psycopg2.extensions.connection) -> None:
    """
    Closes the connection to the PostgreSQL database.
    :param conn: The connection object to close.
    :return: None
    """
    conn.close()
