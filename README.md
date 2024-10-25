# Matriz de confusión: Porcentaje de créditos aprobados vs. Puntaje Advise

Matriz de confusión que compara el porcentaje de créditos aprobados con el puntaje Advise de los estudiantes de la Universidad de los Andes, tomando el porcentaje de créditos aprobados como la verdad absoluta y el puntaje Advise como la predicción.

La documentación técnica está en inglés, como es convencional, pero la aplicación está en español.

# Documentation

## Live Application

The application is deployed on Streamlit Cloud and can be accessed in https://confusion-matrix-nes-vs-advise.streamlit.app/.

The application deploys automatically when a new commit is pushed to the `main` branch.

## Local Setup

1. Create a virtual environment

   ```shell
   python3.11 -m venv venv
   ```

2. Activate the virtual environment

   Unix:

   ```shell
   source venv/bin/activate
   ```

   Windows:

   ```batch
   venv\Scripts\activate.bat
   ```

3. Install dependencies

   ```shell
   pip install -r requirements.txt
   ```

4. Run the app

   ```
   streamlit run streamlit_app.py
   ```

The server should be running at http://localhost:8501.


## Updating the Information

1. Recover the most recent Advise report either from the email or from the Blob Storage. Store it in the `./base-files/external` directory.

2. Update the Advise scores in the `./advise.db` SQLite database by running the `advise_report_to_sqlite.py` script.

   Before running the script, change the `ADVISE_REPORT_NAME` variable to the current report name.

   ```shell
   python advise_report_to_sqlite.py
   ```

3. Update the `code-passed-credits-pct-period.csv` file in the `./base-files/own` directory with the most recent information. The query used in the Observatory-Connection microservice is:

   ```sql
   SELECT 
   CODIGO_ESTUDIANTE, LOGIN, NOMBRES, APELLIDOS, PORCENTAJE_CREDITOS_APROBADOS, PERIODO_EVALUADO
   FROM 
   BlobStorage 
   WHERE PERIODO_EVALUADO IN (202410, 202419, 202420);
   ```

4. Build the `undergraduate_students.db` SQLite database with all undergraduate students, their Advise scores and their passed credits percentage, by running the `preprocessing` script.

   ```shell
   python preprocessing.py
   ```

5. Run the application locally to check that everything is working as expected.

   ```shell
   streamlit run streamlit_app.py
   ```
