from typing import Tuple
from streamlit import title, slider, markdown, write, pyplot
from sklearn.metrics import confusion_matrix
from pandas import DataFrame, read_sql_query
from matplotlib import pyplot as plt
from seaborn import heatmap
from sqlite3 import connect


PASSED_CREDITS_PCT_COLUMN = 'PORCENTAJE_CREDITOS_APROBADOS'
ADVISE_SCORE_COLUMN = 'INDICE_MONITOREO_ADVISE'


def main() -> None:
    title("Matriz de confusión: Porcentaje de créditos aprobados vs. Puntaje Advise")

    threshold_percentage_of_passed_credits: float = get_threshold_percentage_of_passed_credits()
    threshold_advise: int = get_threshold_advise()

    df: DataFrame = load_data_from_db("undergraduate_students.db")
    df = preprocess_data(df)

    y_true, y_pred = get_labels(
        df, threshold_percentage_of_passed_credits, threshold_advise)
    cm = confusion_matrix(y_true=y_true, y_pred=y_pred)

    display_confusion_matrix(cm)
    display_markdown(threshold_percentage_of_passed_credits, threshold_advise)


def get_threshold_percentage_of_passed_credits() -> float:
    return slider(
        "Porcentaje de créditos aprobados máximo que determina riesgo:", 0, 100, 75, format="%d%%") / 100


def get_threshold_advise() -> int:
    return slider("Puntaje Advise máximo que determina riesgo:", 1, 100, 64)


def load_data_from_db(db_file: str) -> DataFrame:
    conn = connect(db_file)
    df = read_sql_query(
        'SELECT CODIGO_ESTUDIANTE, LOGIN, PORCENTAJE_CREDITOS_APROBADOS, INDICE_MONITOREO_ADVISE FROM undergraduate_students', conn)
    conn.close()
    return df


def preprocess_data(df: DataFrame) -> DataFrame:
    df[PASSED_CREDITS_PCT_COLUMN].fillna(100, inplace=True)
    df[ADVISE_SCORE_COLUMN].fillna(100, inplace=True)
    return df


def get_labels(df: DataFrame, threshold_percentage_of_passed_credits: float, threshold_advise: int) -> Tuple[DataFrame, DataFrame]:
    y_true = (df[PASSED_CREDITS_PCT_COLUMN] <=
              threshold_percentage_of_passed_credits).astype(int)
    y_pred = (df[ADVISE_SCORE_COLUMN] <= threshold_advise).astype(int)
    return y_true, y_pred


def display_confusion_matrix(cm: DataFrame) -> None:
    write("Matriz de Confusión:")
    fig, ax = plt.subplots()
    heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=ax,
            xticklabels=[r'No en riesgo, Advise', r'En riesgo, Advise'],
            yticklabels=[r'No en riesgo, % créditos', r'En riesgo, % créditos'])
    ax.set_xlabel('Puntaje Advise', labelpad=15)
    ax.set_ylabel('Porcentaje de créditos aprobados', labelpad=15)
    pyplot(fig)


def display_markdown(threshold_percentage_of_passed_credits: float, threshold_advise: int) -> None:
    markdown(r"""
Se utiliza el *porcentaje de créditos aprobados* para determinar si un estudiante realmente está en riesgo. Se cataloga a un estudiante como *en riesgo* si su porcentaje de créditos aprobados con respecto a los inscritos es menor o igual al {0}%. 

Se realiza el contraste con el *puntaje Advise*. Se considera que un estudiante está en riesgo si su puntaje Advise es menor o igual a {1}.

Se define la matriz de confusión $M$ de $2 \times 2$, donde las filas corresponden al porcentaje de créditos aprobados y las columnas a Advise. Los índices $0$ corresponden a estudiantes que no están en riesgo y los índices $1$ corresponden a los estudiantes que sí lo están. Por lo tanto:
- {2} corresponde a los **verdaderos negativos**. Los créditos aprobados son mayores al {0}% y el puntaje Advise es mayor a {1}. Advise indica correctamente que el estudiante no está en riesgo.
- {3} corresponde a los **falsos positivos** (FP). El porcentaje de créditos aprobados es mayor al {0}%, pero el puntaje Advise es menor o igual a {1}. Advise ha catalogado al estudiante como en riesgo incorrectamente.
- {4} corresponde a los **falsos negativos**. El porcentaje de créditos aprobados es menor o igual al {0}%, pero el puntaje Advise es mayor a {1}. Advise ha pasado por alto a un estudiante en riesgo.
- {5} corresponde a los **verdaderos positivos** (VP). Los créditos aprobados son menores o iguales al {0}% y el puntaje Advise es menor o igual a {1}. Advise ha detectado correctamente que el estudiante está en riesgo.
    """.format(threshold_percentage_of_passed_credits * 100, threshold_advise, r"$M_{0,0}$", r"$M_{0,1}$", r"$M_{1,0}$", r"$M_{1,1}$"))


if __name__ == "__main__":
    main()
