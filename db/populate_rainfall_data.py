import argparse
import csv
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from psycopg2.extras import execute_values

from create_database import get_connection





def default_csv_path() -> Path:
    return Path(__file__).resolve().parents[1] / "app" / "home" / "static" / "Data2.csv"


def decimal_6(value: str) -> Decimal:
    return Decimal(value.strip()).quantize(Decimal("0.000001"))


def load_gauge_map(cursor) -> dict[tuple[str, Decimal, Decimal], int]:
    cursor.execute("SELECT id, location, latitude, longitude FROM rainguage")
    rows = cursor.fetchall()
    gauge_map: dict[tuple[str, Decimal, Decimal], int] = {}

    for row_id, location, latitude, longitude in rows:
        key = (str(location).strip(), decimal_6(str(latitude)), decimal_6(str(longitude)))
        gauge_map[key] = row_id

    return gauge_map


def ensure_gauge(cursor, gauge_map: dict[tuple[str, Decimal, Decimal], int], key: tuple[str, Decimal, Decimal]) -> int:
    existing_id = gauge_map.get(key)
    if existing_id is not None:
        return existing_id

    location, latitude, longitude = key
    cursor.execute(
        """
        INSERT INTO rainguage (location, latitude, longitude)
        VALUES (%s, %s, %s)
        RETURNING id
        """,
        (location, latitude, longitude),
    )
    new_id = cursor.fetchone()[0]
    gauge_map[key] = new_id
    return new_id


def import_csv(csv_path: Path, clear_existing: bool = False) -> tuple[int, int]:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if clear_existing:
                cursor.execute("TRUNCATE TABLE rainfall RESTART IDENTITY")
                cursor.execute("TRUNCATE TABLE rainguage RESTART IDENTITY CASCADE")

            gauge_map = load_gauge_map(cursor)
            initial_gauge_count = len(gauge_map)
            rainfall_rows: list[tuple[datetime, Decimal, int]] = []

            with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)

                required_columns = {"time", "Rainfall", "location", "latitude", "longitude"}
                missing_columns = required_columns - set(reader.fieldnames or [])
                if missing_columns:
                    raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")

                for row_index, row in enumerate(reader, start=2):
                    try:
                        timestamp = datetime.strptime(row["time"].strip(), "%d/%m/%Y %H:%M")
                        location = row["location"].strip()
                        latitude = decimal_6(row["latitude"])
                        longitude = decimal_6(row["longitude"])
                        rainfall_value = Decimal(row["Rainfall"].strip())
                    except (KeyError, AttributeError, InvalidOperation, ValueError) as error:
                        raise ValueError(f"Invalid data on CSV line {row_index}: {error}") from error

                    gauge_key = (location, latitude, longitude)
                    gauge_id = ensure_gauge(cursor, gauge_map, gauge_key)
                    rainfall_rows.append((timestamp, rainfall_value, gauge_id))

            if rainfall_rows:
                execute_values(
                    cursor,
                    "INSERT INTO rainfall (time, rainfall, rainguage_id) VALUES %s",
                    rainfall_rows,
                )

            created_gauges = len(gauge_map) - initial_gauge_count
            return created_gauges, len(rainfall_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate rainguage and rainfall tables from a CSV file.",
    )
    parser.add_argument(
        "--csv",
        default=str(default_csv_path()),
        help="Path to CSV file (default: app/home/static/Data2.csv)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing rows in rainfall and rainguage before import.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv).expanduser().resolve()

    created_gauges, inserted_rainfall_rows = import_csv(csv_path=csv_path, clear_existing=args.clear)

    print(f"Import complete. New rainguage rows: {created_gauges}")
    print(f"Import complete. New rainfall rows: {inserted_rainfall_rows}")


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Failed to import CSV data: {error}", file=sys.stderr)
        sys.exit(1)
