import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2


env_path = Path(__file__).resolve().parent.parent / '.env'
if sys.platform.startswith("linux") and env_path.exists():
    load_dotenv(env_path)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def create_tables():
    table_sql = [
        """
        CREATE TABLE IF NOT EXISTS rainguage (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            location TEXT NOT NULL,
            latitude DECIMAL(9, 6) NOT NULL,
            longitude DECIMAL(9, 6) NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS rainfall (
            id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            time TIMESTAMP NOT NULL,
            rainfall DECIMAL(10, 2) NOT NULL,
            rainguage_id INTEGER NOT NULL,
            CONSTRAINT fk_rainguage
                FOREIGN KEY (rainguage_id)
                REFERENCES rainguage(id)
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS logs (
            log_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            time TIMESTAMP NOT NULL,
            user_email TEXT NOT NULL,
            log_type TEXT NOT NULL,
            log_message TEXT NOT NULL
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            email_address TEXT NOT NULL,
            password TEXT NOT NULL,
            registered BOOLEAN NOT NULL,
            registration_code TEXT
        );
        """,
    ]

    with get_connection() as conn:
        with conn.cursor() as cursor:
            for statement in table_sql:
                cursor.execute(statement)


if __name__ == "__main__":
    try:
        create_tables()
        print("Database tables created successfully.")
    except Exception as error:
        print(f"Failed to create tables: {error}", file=sys.stderr)
        sys.exit(1)
