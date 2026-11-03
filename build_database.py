"""Rebuild a portfolio-ready relational SQLite database from the CDS 302 movie CSV.

This is a reconstruction based on the original class project, not the original
2024 script. It does not modify the original movies_database.db or movies_final.db.

Usage:
    python3 build_database.py

Place movies.csv in the same directory as this script.
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "movies.csv"
DESTINATION = ROOT / "movies_portfolio.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE Directors (
    Director_ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE
);
CREATE TABLE Companies (
    Company_ID INTEGER PRIMARY KEY,
    Company_Name TEXT NOT NULL UNIQUE
);
CREATE TABLE Genres (
    Genre_ID INTEGER PRIMARY KEY,
    Genre_Name TEXT NOT NULL UNIQUE
);
CREATE TABLE Actors (
    Actor_ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL UNIQUE
);
CREATE TABLE Movies (
    Movie_ID INTEGER PRIMARY KEY,
    Name TEXT NOT NULL,
    Year INTEGER,
    Released TEXT,
    Rating TEXT,
    Score REAL,
    Votes REAL,
    Country TEXT,
    Budget REAL,
    Gross REAL,
    Runtime REAL,
    Writer TEXT,
    Director_ID INTEGER REFERENCES Directors(Director_ID),
    Company_ID INTEGER REFERENCES Companies(Company_ID)
);
CREATE TABLE Movie_Actors (
    Movie_ID INTEGER NOT NULL REFERENCES Movies(Movie_ID),
    Actor_ID INTEGER NOT NULL REFERENCES Actors(Actor_ID),
    PRIMARY KEY (Movie_ID, Actor_ID)
);
CREATE TABLE Movie_Genres (
    Movie_ID INTEGER NOT NULL REFERENCES Movies(Movie_ID),
    Genre_ID INTEGER NOT NULL REFERENCES Genres(Genre_ID),
    PRIMARY KEY (Movie_ID, Genre_ID)
);
"""


def optional_text(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def optional_number(value: str | None, type_: type = float):
    value = optional_text(value)
    return type_(value) if value is not None else None


def lookup_id(conn: sqlite3.Connection, table: str, column: str, value: str | None):
    value = optional_text(value)
    if value is None:
        return None
    # table and column names are internal constants, not arbitrary input
    conn.execute(f'INSERT OR IGNORE INTO {table} ({column}) VALUES (?)', (value,))
    return conn.execute(
        f'SELECT rowid FROM {table} WHERE {column} = ?',
        (value,),
    ).fetchone()[0]


def main() -> None:
    if not SOURCE.exists():
        raise FileNotFoundError(f"Put movies.csv next to this script: {SOURCE}")
    if DESTINATION.exists():
        raise FileExistsError(
            f"{DESTINATION.name} already exists. Rename or remove the GENERATED "
            "database before rebuilding. Original class DBs are never touched."
        )

    try:
        with sqlite3.connect(DESTINATION) as conn:
            conn.executescript(SCHEMA)
            with SOURCE.open(newline="", encoding="utf-8-sig") as fp:
                reader = csv.DictReader(fp)
                for movie_id, row in enumerate(reader, 1):
                    director_id = lookup_id(conn, 'Directors', 'Name', row['director'])
                    company_id = lookup_id(conn, 'Companies', 'Company_Name', row['company'])
                    actor_id = lookup_id(conn, 'Actors', 'Name', row['star'])
                    genre_id = lookup_id(conn, 'Genres', 'Genre_Name', row['genre'])
                    conn.execute("""
                        INSERT INTO Movies (
                            Movie_ID, Name, Year, Released, Rating, Score,
                            Votes, Country, Budget, Gross, Runtime, Writer,
                            Director_ID, Company_ID
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        movie_id, row['name'], optional_number(row['year'], int),
                        optional_text(row['released']), optional_text(row['rating']),
                        optional_number(row['score']), optional_number(row['votes']),
                        optional_text(row['country']), optional_number(row['budget']),
                        optional_number(row['gross']), optional_number(row['runtime']),
                        optional_text(row['writer']), director_id, company_id,
                    ))
                    if actor_id is not None:
                        conn.execute(
                            'INSERT INTO Movie_Actors VALUES (?, ?)', (movie_id, actor_id)
                        )
                    if genre_id is not None:
                        conn.execute(
                            'INSERT INTO Movie_Genres VALUES (?, ?)', (movie_id, genre_id)
                        )
            issues = conn.execute('PRAGMA foreign_key_check').fetchall()
            if issues:
                raise RuntimeError(f"Foreign key check failed: {issues[:3]}")
            count = conn.execute('SELECT COUNT(*) FROM Movies').fetchone()[0]
        print(f"Created {DESTINATION.name}: {count:,} movies; foreign keys verified.")
    except Exception:
        DESTINATION.unlink(missing_ok=True)
        raise


if __name__ == '__main__':
    main()
