import pandas as pd
import sqlite3
from os import path


def store_excel_to_sqlite(excel_file: str, db_file: str, table_name: str,) -> None:
    """
    Reads an Excel file and writes its contents to a SQLite database.

    Parameters
    ----------
    excel_file : str
        The path to the Excel file.
    db_file : str
        The path to the SQLite database file.
    table_name : str
        The name of the table to be created in the database.
    """
    df = pd.read_excel(excel_file)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    columns = df.columns

    # Clean column names to ensure they are valid SQLite identifiers
    cleaned_columns = [col.replace(' ', '_').replace(
        '(', '').replace(')', '') for col in columns]

    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        {", ".join([f"{col} TEXT" for col in cleaned_columns])}
    );
    '''

    cursor.execute(create_table_query)

    # Rename columns in DataFrame to match cleaned column names
    df.columns = cleaned_columns

    df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.commit()
    conn.close()


def main() -> None:
    """
    Reads the Advise report Excel file and writes its contents to a SQLite database.

    The Advise report Excel is either provided by email or downloaded from the Blob,
    and is named `Vista de búsqueda avanzada de la persona DD-MM-YYYY XX-YY-ZZ.xlsx`.
    """
    base_files_dir = path.join(path.dirname(
        __file__), 'base-files', 'external')
    ADVISE_REPORT_NAME = 'Vista de búsqueda avanzada de la persona 25-10-2024 11-40-32.xlsx'
    db_file = 'advise.db'
    table_name = 'advise'

    store_excel_to_sqlite(path.join(base_files_dir, ADVISE_REPORT_NAME), db_file, table_name)


if __name__ == '__main__':
    main()
