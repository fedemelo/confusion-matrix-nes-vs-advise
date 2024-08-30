"""
Builds a SQLite database with all undergraduate students, their Advise scores and their passed credits percentage.

Assumption: An student is considered undergraduate if and only if it has an advise score.

1. The most recent advise report, as an SQL database advise.db, is read as a DataFrame.

2. A CSV file with the passed credits percentage, named `code-passed-credits-pct-period.csv`, is produced from the NESObservatory connection microservice.

```sql
SELECT 
CODIGO_ESTUDIANTE, LOGIN, NOMBRES, APELLIDOS, PORCENTAJE_CREDITOS_APROBADOS, PERIODO_EVALUADO
FROM 
BlobStorage 
WHERE PERIODO_EVALUADO IN (202410, 202320);
```
It is processed into a DataFrame and the most recent entry for each student is kept. 
It is filtered to only include undergraduate students.

3. The columns CODIGO_ESTUDIANTE, INDICE_MONITOREO_ADVISE, and PORCENTAJE_CREDITOS_APROBADOS are stored in a SQLite database, undergraduate_students.db.
"""


import sqlite3
import pandas as pd
from os import path

ADVISE_REPORT_STUDENT_CODE_COLUMN = 'ID_ERP'
ADVISE_REPORT_ADVISE_COLUMN = 'Índice_de_Monitoreo'
ADVISE_REPORT_LEVEL_COLUMN = 'Nivel_académico'
ADVISE_REPORT_LATEST_DATE_COLUMN = 'Do_Not_Modify_Fecha_de_modificación'
ADVISE_REPORT_UNDERGRADUATE_VALUE = 'PREGRADO'

BLOB_STUDENT_CODE_COLUMN = 'CODIGO_ESTUDIANTE'
BLOB_ADVISE_COLUMN = 'INDICE_MONITOREO_ADVISE'
BLOB_PASSED_CREDITS_PCT_COLUMN = 'PORCENTAJE_CREDITOS_APROBADOS'
BLOB_PERIOD_COLUMN = 'PERIODO_EVALUADO'
BLOB_LOGIN_COLUMN = 'LOGIN'


CURRENT_DIR = path.dirname(path.abspath(__file__))


def read_advise_report() -> pd.DataFrame:
    """
    Reads the most recent advise report from advise.db and returns a DataFrame with the student code and advise score.
    Ensures that only the most recent entry for each student is kept.
    """
    advise_conn = sqlite3.connect(path.join(CURRENT_DIR, 'advise.db'))
    advise_query = f"""
    SELECT {ADVISE_REPORT_STUDENT_CODE_COLUMN}, {ADVISE_REPORT_ADVISE_COLUMN}, {ADVISE_REPORT_LEVEL_COLUMN}
    FROM advise 
    ORDER BY {ADVISE_REPORT_LATEST_DATE_COLUMN} DESC
    """
    advise_df = pd.read_sql_query(advise_query, advise_conn)
    advise_df = advise_df.rename(columns={
                                 ADVISE_REPORT_STUDENT_CODE_COLUMN: BLOB_STUDENT_CODE_COLUMN, ADVISE_REPORT_ADVISE_COLUMN: BLOB_ADVISE_COLUMN})

    advise_df[BLOB_STUDENT_CODE_COLUMN] = advise_df[BLOB_STUDENT_CODE_COLUMN].astype(
        int)
    advise_df[BLOB_ADVISE_COLUMN] = advise_df[BLOB_ADVISE_COLUMN].astype(int)

    advise_df = advise_df.drop_duplicates(
        subset=[BLOB_STUDENT_CODE_COLUMN], keep='first')
    advise_conn.close()
    return advise_df


def filter_advise_report(advise_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter the advise DataFrame to only include undergraduate students.
    """
    return advise_df[advise_df[ADVISE_REPORT_LEVEL_COLUMN] == ADVISE_REPORT_UNDERGRADUATE_VALUE]


def read_passed_credits_pct() -> pd.DataFrame:
    """
    Reads the passed credits percentage CSV file and returns a DataFrame with the student code and passed credits percentage.
    Ensures that only the most recent entry for each student is kept.
    """
    csv_passed_credits_pct_path = path.join(
        CURRENT_DIR, 'base-files', 'own', 'code-passed-credits-pct-period.csv')
    passed_credits_pct_df = pd.read_csv(csv_passed_credits_pct_path)

    passed_credits_pct_df = passed_credits_pct_df.sort_values(
        BLOB_PERIOD_COLUMN, ascending=False)
    passed_credits_pct_df = passed_credits_pct_df.drop_duplicates(
        subset=[BLOB_STUDENT_CODE_COLUMN], keep='first')

    passed_credits_pct_df[BLOB_PASSED_CREDITS_PCT_COLUMN] = passed_credits_pct_df[BLOB_PASSED_CREDITS_PCT_COLUMN].str.replace(
        ',', '.').astype(float)

    return passed_credits_pct_df


def filter_passed_credits_pct(passed_credits_pct_df: pd.DataFrame, advise_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the passed credits percentage DataFrame to only include undergraduate students.
    """
    undergrad_students = advise_df[BLOB_STUDENT_CODE_COLUMN].tolist()
    return passed_credits_pct_df[passed_credits_pct_df[BLOB_STUDENT_CODE_COLUMN].isin(undergrad_students)]


def store_undergraduate_students(advise_df: pd.DataFrame, undergrad_credits_df: pd.DataFrame):
    """
    Merges the advise DataFrame and the passed credits percentage DataFrame and stores the result in a SQLite database.
    """
    merged_df = pd.merge(advise_df, undergrad_credits_df,
                         on=BLOB_STUDENT_CODE_COLUMN, how='inner')

    output_conn = sqlite3.connect(
        path.join(CURRENT_DIR, 'undergraduate_students.db'))
    merged_df.to_sql('undergraduate_students', output_conn,
                     if_exists='replace', index=False)
    output_conn.close()


def check_data_quality(undergraduate_students_db_path: str):
    """
    Checks the data quality of the undergraduate students database after it has been built.
    """
    def _display_count(count: int, df: pd.DataFrame):
        if count == 0:
            return
        elif count > 0 and count < 5:
            print(df)
        else:
            print(df.head())

    undergrad_students_conn = sqlite3.connect(undergraduate_students_db_path)
    undergrad_students_df = pd.read_sql_query(
        "SELECT * FROM undergraduate_students", undergrad_students_conn)

    # Missing values
    missing_values = undergrad_students_df.isnull().sum()
    if missing_values.sum() > 0:
        print('Missing values found:')
        print(missing_values)

    # Duplicates
    duplicates = undergrad_students_df.duplicated().sum()
    if duplicates > 0:
        print('Duplicates found:', duplicates)

    # No advise score
    no_advise_score = undergrad_students_df[undergrad_students_df[BLOB_ADVISE_COLUMN].isnull(
    )]
    no_advise_count = len(no_advise_score)
    print(f'Students with no advise score: {no_advise_count}')
    _display_count(no_advise_count, no_advise_score)

    # No passed credits percentage
    no_passed_credits_pct = undergrad_students_df[undergrad_students_df[BLOB_PASSED_CREDITS_PCT_COLUMN].isnull(
    )]
    no_passed_credits_count = len(no_passed_credits_pct)
    print(
        f'Students with no passed credits percentage: {no_passed_credits_count}')
    _display_count(no_passed_credits_count, no_passed_credits_pct)

    # Passed credits percentage is not from latest period
    not_latest_period = undergrad_students_df[undergrad_students_df[BLOB_PERIOD_COLUMN] != 202410]
    not_latest_period_count = len(not_latest_period)
    print(
        f'Students with passed credits percentage not from latest period: {not_latest_period_count}')
    _display_count(not_latest_period_count, not_latest_period)

    # Student has no login
    no_login = undergrad_students_df[undergrad_students_df[BLOB_LOGIN_COLUMN] == '']
    no_login_count = len(no_login)
    if no_login_count > 0:
        print(f'Students with no login: {no_login_count}')
        _display_count(no_login_count, no_login)

    undergrad_students_conn.close()


def main():
    advise_df = read_advise_report()
    advise_df = filter_advise_report(advise_df)
    passed_credits_pct_df = read_passed_credits_pct()
    undergrad_credits_df = filter_passed_credits_pct(
        passed_credits_pct_df, advise_df)
    store_undergraduate_students(advise_df, undergrad_credits_df)
    check_data_quality(path.join(CURRENT_DIR, 'undergraduate_students.db'))


if __name__ == '__main__':
    main()
