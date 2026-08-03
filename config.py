import os

DB_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('DB_PASSWORD'),
    'database': os.environ.get('DB_NAME')
}

SECRET_KEY = os.environ.get('SECRET_KEY', 'cambiar-esto-en-desarrollo-local')
NOMBRE_GIMNASIO = os.environ.get('NOMBRE_GIMNASIO', 'Le Corps Gym')