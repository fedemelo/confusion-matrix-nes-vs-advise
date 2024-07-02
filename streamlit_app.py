from streamlit import title, slider, markdown, write, pyplot
from sklearn.metrics import confusion_matrix
from pandas import DataFrame
from matplotlib import pyplot as plt
from seaborn import heatmap


title("Matriz de confusión: Porcentaje de créditos aprobados vs. Puntaje Advise")

threshold_percentage_of_passed_credits = slider(
    "Porcentaje de créditos aprobados máximo que determina riesgo:", 1, 100, 75)
threshold_advise = slider(
    "Puntaje Advise máximo que determina riesgo:", 1, 100, 64)


data = {
    'percentage_of_passed_credits': [
        40, 40, 40, 40, 40, 100, 100, 100, 30,  30, 100, 100, 100, 100],
    'advise_score': [
        20, 20, 20, 20, 20, 100, 100, 100, 100, 100, 10, 10, 10, 10]
}
# percentage_of_passed_credits: 100 and advise_score: 100 -> true negative (3)
# percentage_of_passed_credits: 100 and advise_score: 10 -> false positive (4)
# percentage_of_passed_credits: 30 and advise_score: 100 -> false negative (2)
# percentage_of_passed_credits: 40 and advise_score: 20 -> true positive (5)


df = DataFrame(data)

y_true = (df['percentage_of_passed_credits'] <=
          threshold_percentage_of_passed_credits).astype(int)
y_pred = (df['advise_score'] <= threshold_advise).astype(int)

cm = confusion_matrix(y_true=y_true, y_pred=y_pred)
print(cm)

write("Matriz de Confusión:")

fig, ax = plt.subplots()
heatmap(cm, annot=True, fmt='d', cmap='Greens', ax=ax,
        xticklabels=[r'No en riesgo, Advise', r'En riesgo, Advise'],
        yticklabels=[r'No en riesgo, % créditos', r'En riesgo, % créditos'])
ax.set_xlabel('Puntaje Advise', labelpad=15)
ax.set_ylabel('Porcentaje de créditos aprobados', labelpad=15)
pyplot(fig)

markdown("""
Se utiliza el *porcentaje de créditos aprobados* para determinar si un estudiante realmente está en riesgo. Se cataloga a un estudiante como "en riesgo" si su porcentaje de créditos aprobados con respecto a los inscritos es menor o igual al {0}%. 

Se realiza el contraste con el *puntaje Advise*. Se considera que un estudiante está en riesgo si su puntaje Advise es menor o igual a {1}.

- **Verdadero Positivo (VP):** El puntaje Advise es menor o igual a {1} y los créditos aprobados son menores o iguales al {0}%. Advise ha detectado correctamente que el estudiante está en riesgo.
- **Falso Positivo (FP):** El puntaje Advise es menor o igual a {1}, pero el porcentaje de créditos aprobados es mayor al {0}%. Advise ha catalogado al estudiante como en riesgo incorrectamente.
- **Verdadero Negativo (VN):** El puntaje Advise es mayor a {1} y los créditos aprobados son mayores al {0}%. Advise indica correctamente que el estudiante no está en riesgo.
- **Falso Negativo (FN):** El puntaje Advise es mayor a {1}, pero el porcentaje de créditos aprobados es menor o igual al {0}%. Advise ha pasado por alto a un estudiante en riesgo.
""".format(threshold_percentage_of_passed_credits, threshold_advise))
