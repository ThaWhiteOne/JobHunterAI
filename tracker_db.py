import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


VALID_STATUSES = (
    "saved",
    "generated",
    "applied",
    "interview",
    "rejected",
    "offer",
)


def connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(db_path: Path) -> None:
    with closing(connect(db_path)) as connection:
        with connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    position TEXT NOT NULL,
                    url TEXT,
                    role TEXT,
                    status TEXT NOT NULL,
                    notes TEXT,
                    output_dir TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            ensure_output_dir_column(connection)


def ensure_output_dir_column(connection: sqlite3.Connection) -> None:
    columns = {
        row["name"]
        for row in connection.execute("PRAGMA table_info(jobs)").fetchall()
    }
    if "output_dir" not in columns:
        connection.execute("ALTER TABLE jobs ADD COLUMN output_dir TEXT")


def validate_status(status: str) -> None:
    if status not in VALID_STATUSES:
        allowed_statuses = ", ".join(VALID_STATUSES)
        raise ValueError(f"Invalid status '{status}'. Use one of: {allowed_statuses}")


def add_job(
    db_path: Path,
    company: str,
    position: str,
    url: str = "",
    role: str = "",
    status: str = "saved",
    notes: str = "",
    output_dir: str = "",
) -> int:
    company = company.strip()
    position = position.strip()
    status = status.strip().lower()

    if not company:
        raise ValueError("Company is required.")
    if not position:
        raise ValueError("Position is required.")

    validate_status(status)
    initialize_database(db_path)
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    with closing(connect(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                """
                INSERT INTO jobs
                    (
                        company, position, url, role, status, notes,
                        output_dir, created_at
                    )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    company,
                    position,
                    url.strip(),
                    role.strip(),
                    status,
                    notes.strip(),
                    output_dir.strip(),
                    created_at,
                ),
            )
            return int(cursor.lastrowid)


def list_jobs(
    db_path: Path,
    status_filter: str = "",
    role_filter: str = "",
) -> list[dict[str, str | int]]:
    initialize_database(db_path)
    status_filter = status_filter.strip().lower()
    if status_filter:
        validate_status(status_filter)
    role_filter = role_filter.strip().lower()

    query = """
        SELECT
            id, company, position, url, role, status, notes,
            output_dir, created_at
        FROM jobs
    """
    filters = []
    parameters = []
    if status_filter:
        filters.append("status = ?")
        parameters.append(status_filter)
    if role_filter:
        filters.append("LOWER(role) = ?")
        parameters.append(role_filter)
    if filters:
        query += " WHERE " + " AND ".join(filters)
    query += " ORDER BY id DESC"

    with closing(connect(db_path)) as connection:
        rows = connection.execute(query, parameters).fetchall()

    return [dict(row) for row in rows]


def update_job_status(db_path: Path, job_id: int, status: str) -> None:
    status = status.strip().lower()
    validate_status(status)
    initialize_database(db_path)

    with closing(connect(db_path)) as connection:
        with connection:
            cursor = connection.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status, job_id),
            )

    if cursor.rowcount == 0:
        raise ValueError(f"No job found with id {job_id}.")
