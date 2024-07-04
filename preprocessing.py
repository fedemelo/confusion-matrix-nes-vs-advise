"""
Builds a SQLite database with all undergraduate students, their Advise scores and their passed credits percentage.

Assumption: An student is considered undergraduate if and only if it has an advise score.

1. The most recent advise report, as an SQL database advise.db, is read as a DataFrame.

2. A CSV file with the passed credits percentage is produced from the NESObservatory connection microservice.
```sql
SELECT CODIGO_ESTUDIANTE,  PORCENTAJE_CREDITOS_APROBADOS, PERIODO_EVALUADO FROM BlobStorage WHERE PERIODO_EVALUADO IN (202410, 202320)
```
It is processed into a DataFrame and the most recent entry for each student is kept. 
It is filtered to only include undergraduate students.

3. The columns CODIGO_ESTUDIANTE, INDICE_MONITOREO_ADVISE, and PORCENTAJE_CREDITOS_APROBADOS are stored in a SQLite database, undergraduate_students.db.
"""


import sqlite3
import pandas as pd
from os import path

STUDENT_CODE_COLUMN = 'CODIGO_ESTUDIANTE'
ADVISE_SCORE_COLUMN = 'INDICE_MONITOREO_ADVISE'
CURRENT_DIR = path.dirname(path.abspath(__file__))


def read_advise_report() -> pd.DataFrame:
    """
    Reads the most recent advise report from advise.db and returns a DataFrame with the student code and advise score.
    Ensures that only the most recent entry for each student is kept.
    """
    advise_conn = sqlite3.connect(path.join(CURRENT_DIR, 'advise.db'))
    advise_query = """
    SELECT ID_ERP_Alumno_Contacto, Valor_de_puntaje 
    FROM advise 
    ORDER BY Fecha_de_creación DESC
    """
    advise_df = pd.read_sql_query(advise_query, advise_conn)
    advise_df = advise_df.rename(columns={
                                 'ID_ERP_Alumno_Contacto': STUDENT_CODE_COLUMN, 'Valor_de_puntaje': ADVISE_SCORE_COLUMN})

    advise_df[STUDENT_CODE_COLUMN] = advise_df[STUDENT_CODE_COLUMN].astype(int)
    advise_df[ADVISE_SCORE_COLUMN] = advise_df[ADVISE_SCORE_COLUMN].astype(int)

    advise_df = advise_df.drop_duplicates(
        subset=[STUDENT_CODE_COLUMN], keep='first')
    advise_conn.close()
    return advise_df


def read_passed_credits_pct() -> pd.DataFrame:
    """
    Reads the passed credits percentage CSV file and returns a DataFrame with the student code and passed credits percentage.
    Ensures that only the most recent entry for each student is kept.
    """
    csv_passed_credits_pct_path = path.join(
        CURRENT_DIR, 'base-files', 'own', 'code-passed-credits-pct-period.csv')
    passed_credits_pct_df = pd.read_csv(csv_passed_credits_pct_path)

    passed_credits_pct_df = passed_credits_pct_df.sort_values(
        'PERIODO_EVALUADO', ascending=False)
    passed_credits_pct_df = passed_credits_pct_df.drop_duplicates(
        subset=[STUDENT_CODE_COLUMN], keep='first')

    passed_credits_pct_df['PORCENTAJE_CREDITOS_APROBADOS'] = passed_credits_pct_df['PORCENTAJE_CREDITOS_APROBADOS'].str.replace(
        ',', '.').astype(float)

    return passed_credits_pct_df


def filter_passed_credits_pct(passed_credits_pct_df: pd.DataFrame, advise_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the passed credits percentage DataFrame to only include undergraduate students.
    """
    undergrad_students = advise_df[STUDENT_CODE_COLUMN].tolist()
    return passed_credits_pct_df[passed_credits_pct_df[STUDENT_CODE_COLUMN].isin(undergrad_students)]


def store_undergraduate_students(advise_df: pd.DataFrame, undergrad_credits_df: pd.DataFrame):
    """
    Merges the advise DataFrame and the passed credits percentage DataFrame and stores the result in a SQLite database.
    """
    merged_df = pd.merge(advise_df, undergrad_credits_df,
                         on=STUDENT_CODE_COLUMN, how='inner')

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
    no_advise_score = undergrad_students_df[undergrad_students_df[ADVISE_SCORE_COLUMN].isnull(
    )]
    no_advise_count = len(no_advise_score)
    print(f'Students with no advise score: {no_advise_count}')
    _display_count(no_advise_count, no_advise_score)

    # No passed credits percentage
    no_passed_credits_pct = undergrad_students_df[undergrad_students_df['PORCENTAJE_CREDITOS_APROBADOS'].isnull(
    )]
    no_passed_credits_count = len(no_passed_credits_pct)
    print(
        f'Students with no passed credits percentage: {no_passed_credits_count}')
    _display_count(no_passed_credits_count, no_passed_credits_pct)

    # Passed credits percentage is not from latest period
    not_latest_period = undergrad_students_df[undergrad_students_df['PERIODO_EVALUADO'] != 202410]
    not_latest_period_count = len(not_latest_period)
    print(
        f'Students with passed credits percentage not from latest period: {not_latest_period_count}')
    _display_count(not_latest_period_count, not_latest_period)

    # Student has no login
    no_login = undergrad_students_df[undergrad_students_df['LOGIN'] == '']
    no_login_count = len(no_login)
    if no_login_count > 0:
        print(f'Students with no login: {no_login_count}')
        _display_count(no_login_count, no_login)

    undergrad_students_conn.close()


def main():
    advise_df = read_advise_report()
    passed_credits_pct_df = read_passed_credits_pct()
    undergrad_credits_df = filter_passed_credits_pct(
        passed_credits_pct_df, advise_df)
    store_undergraduate_students(advise_df, undergrad_credits_df)
    check_data_quality(path.join(CURRENT_DIR, 'undergraduate_students.db'))


if __name__ == '__main__':
    main()
