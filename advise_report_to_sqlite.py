import pandas as pd
import sqlite3
from os import path


def main(excel_file: str, db_file: str, table_name: str) -> None:
    df = pd.read_excel(excel_file)

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    columns = df.columns
    print("Columns from Excel:", columns)  # Debug print

    # Clean column names to ensure they are valid SQLite identifiers
    cleaned_columns = [col.replace(' ', '_').replace(
        '(', '').replace(')', '') for col in columns]
    print("Cleaned Columns:", cleaned_columns)  # Debug print

    create_table_query = f'''
    CREATE TABLE IF NOT EXISTS {table_name} (
        {", ".join([f"{col} TEXT" for col in cleaned_columns])}
    );
    '''
    print("Create Table Query:", create_table_query)  # Debug print

    cursor.execute(create_table_query)

    # Rename columns in DataFrame to match cleaned column names
    df.columns = cleaned_columns

    df.to_sql(table_name, conn, if_exists='append', index=False)

    conn.commit()
    conn.close()


if __name__ == '__main__':
    base_files_dir = path.join(path.dirname(
        __file__), 'base-files', 'external')
    excel_file = 'Vista de búsqueda avanzada de puntaje 03-07-2024 15-23-58.xlsx'
    db_file = 'advise.db'
    table_name = 'advise'

    main(path.join(base_files_dir, excel_file), db_file, table_name)
