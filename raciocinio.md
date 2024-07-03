Hola a todos, 

Estuve mirando cómo filtrar los estudiantes en NES y cómo hacer la matriz de confusión. Como temíamos, no hay una forma fácil para determinar si un estudiante es de pregrado o no. 

Se me ocurrió lo siguiente: la información de matrículas en el Blob Storage incluye únicamente pagos de estudiantes en periodos en los que estaban en pregrado. Con eso, filtrando todos los pagos de 2024-10, se tiene una lista de estudiantes que 14666 se matricularon a pregrado el semestre pasado (o, como mínimo, lo intentaron).

Esa lista de estudiantes la crucé con todos los estudiantes en el Blob para los que tenemos calculado el porcentaje de créditos aprobados, que es lo que para la matriz estamos usando como verdad absoluta. Esa es la población que estoy tomando como estudiantes actuales de pregrado.

Eso me dio XXXXX estudiantes de pregrado.



Un caveat importante es que si para algún estudiante no tenemos su Advise, automáticamente lo tomo como si fuese un negativo, pues al final del día Advise no lo está detectando. I.e.: Si advise no lo tiene y su porcentaje de créditos aprobados es bajo, lo tomo como falso negativo; si su porcentaje de créditos aprobados es alto, lo tomo como verdadero negativo. 

Esto se puede cambiar si consideran que hay una mejor forma de manejarlo.



Para poder jugar con los parámetros de la matriz, como mencionamos en la reu, la desplegué aquí: https://confusion-matrix-nes-vs-advise.streamlit.app/. Se pueden cambiar, en vivo, los valores que usamos como puntos de inflexión, tanto de porcentaje de créditos aprobados (actualmente 75%) como de Advise (actualmente 64). Eso cambia automáticamente la matriz




--------


Hice eso y me di cuenta de que:

En total, con base en la info de matrículas, hubieron 14665 estudiantes de pregrado únicos que pagaron algo de matrícula en 2024-10.

De esos, 5206 los podemos poner en la matriz. Peeero hay 9458 estudiantes que pagaron su matricula este semestre como estudiantes de pregrado, pero no están:
- En ninguno de los dos archivos de Manuel
- En el archivo de Criterios del Blob (esto, creo yo, causa de lo anterior)

Entonces, la matriz se puede hacer con solo pregrado, pero iría solo con 5206 estudiantes de pregrado
Nos quedan colgando 9458, que dónde está su advise??


--------

Buenas noticias:

Ya te tengo el listado de exactamente quiénes pueden estar en NES que aparecerán cuando les demos click.
Quiénes? Pues las entries únicas del performance file.
Ahora, para que encima sean pregrado, los cruzo con las entries únicas del de matrículas.
