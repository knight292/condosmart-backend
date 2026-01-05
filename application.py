# Archivo de entrada para Elastic Beanstalk
# Este archivo es requerido por EB para aplicaciones Python
import os
import sys

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar la aplicación FastAPI
from app.main import app

# Elastic Beanstalk busca 'application' por defecto
# Para FastAPI con uvicorn, necesitamos usar el objeto app directamente
application = app
