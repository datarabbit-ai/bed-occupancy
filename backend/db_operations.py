import sqlite3


def get_connection() -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database.
    :return: sqlite3.Connection object
    :raises Exception: If the connection fails.
    """

    db_path = "../db/hospital.db"

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        print(f"Failed to connect: {e}")
        raise


def close_connection(conn: sqlite3.Connection) -> None:
    """
    Closes the connection to the SQLite database.
    :param conn: The connection object to close.
    :return: None
    """
    conn.close()
