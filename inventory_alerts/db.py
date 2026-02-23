import os
import psycopg


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def connect_db(*, autocommit: bool = True) -> psycopg.Connection:
    db_url = require_env("DATABASE_URL")
    return psycopg.connect(db_url, autocommit=autocommit)


def run_sql_file(conn: psycopg.Connection, path: str) -> None:
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    conn.execute(sql)
