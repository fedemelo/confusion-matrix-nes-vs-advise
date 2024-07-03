import json
import pandas as pd
import sqlite3
from os import path


def write_unique_codes_from_file(source_codes_file: str, destination_file_name: str, logs_file: str) -> None:
    """
    Read a list of codes from a CSV file, write all unique codes to another CSV file.

    """
    with open(source_codes_file) as f:
        f.readline()  # Skip the header
        codes = f.readlines()
    write_log_entry(logs_file, {
        'Number of students, with duplicates, who paid an enrollment in 2024-10': len(codes)})

    unique_codes = list(set(map(int, codes)))
    write_log_entry(logs_file, {
        'Number of students, without duplicates, who paid an enrollment in 2024-10': len(unique_codes)})

    with open(destination_file_name, 'w') as f:
        f.write('\n'.join(map(str, unique_codes)))


def load_all_blob_data(csv_file: str) -> pd.DataFrame:
    """
    Load all data from the CSV file that contains the blob data.
    The columns are:
    - CODIGO_ESTUDIANTE
    - PERIODO_EVALUADO
    - INDICE_MONITOREO_ADVISE
    - PORCENTAJE_CREDITOS_APROBADOS
    """
    df = pd.read_csv(csv_file, delimiter=',', decimal=',')

    df['INDICE_MONITOREO_ADVISE'] = df['INDICE_MONITOREO_ADVISE'].replace({
                                                                          "": None})
    df['PORCENTAJE_CREDITOS_APROBADOS'] = df['PORCENTAJE_CREDITOS_APROBADOS'].replace({
                                                                                      "": None})
    df['INDICE_MONITOREO_ADVISE'] = pd.to_numeric(
        df['INDICE_MONITOREO_ADVISE'])
    df['PORCENTAJE_CREDITOS_APROBADOS'] = pd.to_numeric(
        df['PORCENTAJE_CREDITOS_APROBADOS'])

    df['CODIGO_ESTUDIANTE'] = df['CODIGO_ESTUDIANTE'].astype(int)

    return df


def handle_duplicates_in_blob_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Only keep one entry for each code. Prefer the most recent period that has both Advise and Credits.
    If there is no entry with both Advise and Credits, keep the most recent entry with Credits.
    If there is no entry with Credits, keep the most recent entry with Advise.
    If there is none, keep the most recent entry.
    """

    def select_most_recent_entry(group) -> pd.DataFrame:
        """
        Select the most recent entry in the group, prioritizing entries with both Advise and Credits.
        Assumes the group is sorted ascending by PERIODO_EVALUADO.
        """
        prioritize_by_both_present = group.dropna(
            subset=['INDICE_MONITOREO_ADVISE', 'PORCENTAJE_CREDITOS_APROBADOS'])
        if not prioritize_by_both_present.empty:
            return prioritize_by_both_present.iloc[-1]

        prioritize_by_only_credits_present = group.dropna(
            subset=['PORCENTAJE_CREDITOS_APROBADOS'])
        if not prioritize_by_only_credits_present.empty:
            return prioritize_by_only_credits_present.iloc[-1]

        prioritize_by_only_advise_present = group.dropna(
            subset=['INDICE_MONITOREO_ADVISE'])
        if not prioritize_by_only_advise_present.empty:
            return prioritize_by_only_advise_present.iloc[-1]

        return group.iloc[-1]

    df_sorted = df.sort_values(by=['CODIGO_ESTUDIANTE', 'PERIODO_EVALUADO'])

    filtered_df = df_sorted.groupby(
        'CODIGO_ESTUDIANTE').apply(select_most_recent_entry)
    # Drop the multi-index created by groupby
    filtered_df = filtered_df.reset_index(drop=True)

    filtered_df = filtered_df.drop(columns=['PERIODO_EVALUADO'])

    return filtered_df


def filter_only_undergradutes(df: pd.DataFrame, codes: list[int], non_undergraduates_file: str, payed_but_not_in_blob_file: str) -> pd.DataFrame:
    """
    Filter the DataFrame to only include students with codes in the given list.
    """
    undegraduates = df[df['CODIGO_ESTUDIANTE'].astype(int).isin(codes)]
    non_undergraduates = df[~df['CODIGO_ESTUDIANTE'].astype(int).isin(codes)]
    open(non_undergraduates_file, 'w').write(
        non_undergraduates.to_csv(index=False))

    payed_but_not_in_blob = pd.DataFrame({'CODIGO_ESTUDIANTE': codes})
    payed_but_not_in_blob = payed_but_not_in_blob[~payed_but_not_in_blob['CODIGO_ESTUDIANTE'].astype(
        int).isin(df['CODIGO_ESTUDIANTE'])]
    open(payed_but_not_in_blob_file, 'w').write(
        payed_but_not_in_blob.to_csv(index=False))

    return undegraduates


def store_dataframe(df: pd.DataFrame, db_file: str) -> None:
    """
    Store the DataFrame in a SQLite database.
    """

    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS undergraduate_students (
            CODIGO_ESTUDIANTE TEXT,
            INDICE_MONITOREO_ADVISE REAL,
            PORCENTAJE_CREDITOS_APROBADOS REAL
        )
    ''')

    for _, row in df.iterrows():
        cursor.execute('''
            INSERT INTO undergraduate_students (CODIGO_ESTUDIANTE, INDICE_MONITOREO_ADVISE, PORCENTAJE_CREDITOS_APROBADOS)
            VALUES (?, ?, ?)
        ''', (row['CODIGO_ESTUDIANTE'], row['INDICE_MONITOREO_ADVISE'], row['PORCENTAJE_CREDITOS_APROBADOS']))

    conn.commit()
    conn.close()


def write_log_entry(logs_file: str, entry: dict) -> None:
    """
    Write an entry to the metadata file.
    """
    with open(logs_file, 'a') as f:
        json.dump(entry, f)
        f.write('\n')


def filter_and_store_data(
    csv_file: str,
    codes_list: list[int],
    db_file: str,
    logs_file: str,
    non_undergraduates_file: str,
    payed_but_not_in_blob_file: str
) -> None:

    df = load_all_blob_data(csv_file)
    write_log_entry(logs_file, {
        'Number of students, with duplicates, from the Blob Storage': len(df)})

    df = handle_duplicates_in_blob_data(df)
    write_log_entry(logs_file, {
        'Number of students, without duplicates, from the Blob Storage': len(df)})

    df = filter_only_undergradutes(
        df, codes_list, non_undergraduates_file, payed_but_not_in_blob_file)
    write_log_entry(
        logs_file, {'Number of undergraduate students without duplicates': len(df)})
    store_dataframe(df, db_file)


def main() -> None:
    generated_files_dir = path.join(path.dirname(__file__), 'generated-files')
    base_files_dir = path.join(path.dirname(__file__), 'base-files')

    logs_file = path.join(generated_files_dir, 'logs.json')

    non_unique_codes_file = path.join(
        base_files_dir, 'matriculas-202410-codes.csv')
    unique_codes_file = path.join(
        generated_files_dir, 'matriculas-202410-codes-unique.csv')

    write_unique_codes_from_file(
        non_unique_codes_file, unique_codes_file, logs_file)
    print(f'Unique codes written to file {unique_codes_file}')

    with open(unique_codes_file) as f:
        f.readline()  # Skip the header
        unique_codes_list = list(map(int, f.readlines()))

    csv_file = path.join(base_files_dir, 'all-rows-from-criterios-file.csv')
    non_undergraduates_file = path.join(
        generated_files_dir, 'non-undergraduates-in-criterios-file.csv')
    payed_but_not_in_blob_file = path.join(
        generated_files_dir, 'in-matriculas-file-but-not-in-criterios-file.csv')
    db_file = path.join(path.dirname(__file__), 'undergraduate_students.db')

    filter_and_store_data(csv_file,
                          unique_codes_list,
                          db_file,
                          logs_file,
                          non_undergraduates_file,
                          payed_but_not_in_blob_file)
    print(f'Data stored in database {db_file}')
    write_log_entry(logs_file, {'Data stored in database': db_file})


if __name__ == '__main__':
    main()
