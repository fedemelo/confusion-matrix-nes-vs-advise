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
   $ python -m venv venv
   $ source venv/bin/activate
   ```
   
   The second command, to activate the virtual environment, will only work on Unix. For Windows, use the following command:

   ```bash
   $ venv\Scripts\activate
   ```

2. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

3. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```

The server should be running at http://localhost:8501.