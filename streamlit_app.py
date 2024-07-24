from streamlit import header, slider, markdown, write, pyplot, expander, subheader
from sklearn.metrics import confusion_matrix
from pandas import DataFrame, read_sql_query
from matplotlib import pyplot as plt
from seaborn import heatmap
from sqlite3 import connect
from numpy import select
from typing import Tuple


PASSED_CREDITS_PCT_COLUMN = 'PORCENTAJE_CREDITOS_APROBADOS'
ADVISE_SCORE_COLUMN = 'INDICE_MONITOREO_ADVISE'


def main() -> None:
    header("Matriz de confusión: Porcentaje de créditos aprobados vs. Puntaje Advise")

    threshold_percentage_of_passed_credits, threshold_advise = show_sliders()

    df = preprocess_data(load_data_from_db("undergraduate_students.db"))

    cm = build_confusion_matrix(
        df, threshold_percentage_of_passed_credits, threshold_advise)
    display_confusion_matrix(
        cm, threshold_percentage_of_passed_credits, threshold_advise)

    display_matrix_explanation(
        threshold_percentage_of_passed_credits, threshold_advise)

    display_used_students_explanation(df)


def show_sliders() -> Tuple[float, int]:
    with expander("**Pulsa para calibrar los valores de riesgo**"):
        subheader("Calibración de valores de riesgo")
        threshold_percentage_of_passed_credits: float = slider(
            "Porcentaje de créditos aprobados máximo que determina riesgo:", 0, 100, 75, format="%d%%") / 100
        threshold_advise: int = slider(
            "Puntaje Advise máximo que determina riesgo:", 1, 100, 64)
        return threshold_percentage_of_passed_credits, threshold_advise


def load_data_from_db(db_file: str) -> DataFrame:
    conn = connect(db_file)
    df = read_sql_query(
        'SELECT CODIGO_ESTUDIANTE, NOMBRES, APELLIDOS, PORCENTAJE_CREDITOS_APROBADOS, INDICE_MONITOREO_ADVISE FROM undergraduate_students', conn)
    conn.close()
    return df


def preprocess_data(df: DataFrame) -> DataFrame:
    df[PASSED_CREDITS_PCT_COLUMN].fillna(100, inplace=True)
    df[ADVISE_SCORE_COLUMN].fillna(100, inplace=True)
    return df


def build_confusion_matrix(df: DataFrame, threshold_percentage_of_passed_credits: float, threshold_advise: int) -> Tuple[DataFrame, DataFrame, DataFrame]:
    y_true = (df[PASSED_CREDITS_PCT_COLUMN] <=
              threshold_percentage_of_passed_credits).astype(int)
    y_pred = (df[ADVISE_SCORE_COLUMN] <= threshold_advise).astype(int)

    conditions = [
        (y_true == 0) & (y_pred == 0),
        (y_true == 0) & (y_pred == 1),
        (y_true == 1) & (y_pred == 0),
        (y_true == 1) & (y_pred == 1)
    ]
    choices = ['VN', 'FP', 'FN', 'VP']
    df['Resultado'] = select(conditions, choices, default='Unknown')

    return confusion_matrix(y_true=y_true, y_pred=y_pred)


def display_confusion_matrix(cm: DataFrame, threshold_percentage_of_passed_credits: float, threshold_advise: int) -> None:
    subheader("Matriz de confusión")
    write(
        f"Se muestra la matriz de confusión para los valores de riesgo calibrados arriba: el {int(threshold_percentage_of_passed_credits*100)}% de créditos aprobados y un puntaje Advise de {threshold_advise}. Abajo se ofrece una explicación detallada de la matriz.")

    fig, ax = plt.subplots()
    heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=ax,
            xticklabels=[r'No en riesgo, Advise', r'En riesgo, Advise'],
            yticklabels=[r'No en riesgo, % créditos', r'En riesgo, % créditos'])
    ax.set_xlabel('Puntaje Advise', labelpad=15)
    ax.set_ylabel('Porcentaje de créditos aprobados', labelpad=15)
    pyplot(fig)


def display_matrix_explanation(threshold_percentage_of_passed_credits: float, threshold_advise: int) -> None:

    with expander("**Pulsa para leer la explicación de la matriz de confusión**"):
        subheader("Explicación de la matriz de confusión")
        markdown(r"""
Se utiliza el *porcentaje de créditos aprobados* para determinar si un estudiante realmente está en riesgo. Se cataloga a un estudiante como *en riesgo* si su porcentaje de créditos aprobados con respecto a los inscritos es menor o igual al {0}%. 

Se realiza el contraste con el *puntaje Advise*. Se considera que un estudiante está en riesgo si su puntaje Advise es menor o igual a {1}.

Se define la matriz de confusión $M$ de $2 \times 2$, donde las filas corresponden al porcentaje de créditos aprobados y las columnas a Advise. Los índices $0$ corresponden a estudiantes que no están en riesgo y los índices $1$ corresponden a los estudiantes que sí lo están. Por lo tanto:
- {2} corresponde a los **verdaderos negativos** (VN). Los créditos aprobados son mayores al {0}% y el puntaje Advise es mayor a {1}. Advise indica correctamente que el estudiante no está en riesgo.
- {3} corresponde a los **falsos positivos** (FP). El porcentaje de créditos aprobados es mayor al {0}%, pero el puntaje Advise es menor o igual a {1}. Advise ha catalogado al estudiante como en riesgo incorrectamente.
- {4} corresponde a los **falsos negativos** (FN). El porcentaje de créditos aprobados es menor o igual al {0}%, pero el puntaje Advise es mayor a {1}. Advise ha pasado por alto a un estudiante en riesgo.
- {5} corresponde a los **verdaderos positivos** (VP). Los créditos aprobados son menores o iguales al {0}% y el puntaje Advise es menor o igual a {1}. Advise ha detectado correctamente que el estudiante está en riesgo.
    """.format(int(threshold_percentage_of_passed_credits * 100), threshold_advise, r"$M_{0,0}$", r"$M_{0,1}$", r"$M_{1,0}$", r"$M_{1,1}$"))


def display_used_students_explanation(df: DataFrame) -> None:
    subheader("Estudiantes utilizados para el análisis")

    write(
        "Para el análisis, se tomó como muestra todos los estudiantes de pregrado con puntaje Advise calculado para el periodo 2024-10. Los estudiantes en cuestión se pueden visualizar en la tabla a continuación.")

    format_final_df_for_display(df)
    if len(df) == 0:
        write("No hay estudiantes en la base de datos.")
    else:
        write(df.sort_values(by=["Nombres"]))


def format_final_df_for_display(df: DataFrame) -> None:
    df[PASSED_CREDITS_PCT_COLUMN] = df[PASSED_CREDITS_PCT_COLUMN].apply(
        lambda x: f"{x*100:.2f}%")
    df.rename(columns={
        PASSED_CREDITS_PCT_COLUMN: r"% créditos aprobados",
        ADVISE_SCORE_COLUMN: "Puntaje Advise",
        "CODIGO_ESTUDIANTE": "Código",
        "NOMBRES": "Nombres",
        "APELLIDOS": "Apellidos"
    }, inplace=True)

    df["Nombres"] = df["Nombres"].str.title()
    df["Apellidos"] = df["Apellidos"].str.title()

    df.set_index("Código", inplace=True)
    df.index = df.index.map(str)


if __name__ == "__main__":
    main()
