from typing import Tuple
from streamlit import title, slider, markdown, write, pyplot
from sklearn.metrics import confusion_matrix
from pandas import DataFrame, read_sql_query
from matplotlib import pyplot as plt
from seaborn import heatmap
from sqlite3 import connect


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
        'SELECT CODIGO_ESTUDIANTE, PORCENTAJE_CREDITOS_APROBADOS, INDICE_MONITOREO_ADVISE FROM undergraduate_students', conn)
    conn.close()
    return df


def preprocess_data(df: DataFrame) -> DataFrame:
    df['PORCENTAJE_CREDITOS_APROBADOS'].fillna(100, inplace=True)
    df['INDICE_MONITOREO_ADVISE'].fillna(100, inplace=True)
    return df


def get_labels(df: DataFrame, threshold_percentage_of_passed_credits: float, threshold_advise: int) -> Tuple[DataFrame, DataFrame]:
    y_true = (df['PORCENTAJE_CREDITOS_APROBADOS'] <=
              threshold_percentage_of_passed_credits).astype(int)
    y_pred = (df['INDICE_MONITOREO_ADVISE'] <= threshold_advise).astype(int)
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
    markdown("""
    Se utiliza el *porcentaje de créditos aprobados* para determinar si un estudiante realmente está en riesgo. Se cataloga a un estudiante como "en riesgo" si su porcentaje de créditos aprobados con respecto a los inscritos es menor o igual al {0}%. 

    Se realiza el contraste con el *puntaje Advise*. Se considera que un estudiante está en riesgo si su puntaje Advise es menor o igual a {1}.

    - **Verdadero Positivo (VP):** El puntaje Advise es menor o igual a {1} y los créditos aprobados son menores o iguales al {0}%. Advise ha detectado correctamente que el estudiante está en riesgo.
    - **Falso Positivo (FP):** El puntaje Advise es menor o igual a {1}, pero el porcentaje de créditos aprobados es mayor al {0}%. Advise ha catalogado al estudiante como en riesgo incorrectamente.
    - **Verdadero Negativo (VN):** El puntaje Advise es mayor a {1} y los créditos aprobados son mayores al {0}%. Advise indica correctamente que el estudiante no está en riesgo.
    - **Falso Negativo (FN):** El puntaje Advise es mayor a {1}, pero el porcentaje de créditos aprobados es menor o igual al {0}%. Advise ha pasado por alto a un estudiante en riesgo.
    """.format(threshold_percentage_of_passed_credits * 100, threshold_advise))


if __name__ == "__main__":
    main()
