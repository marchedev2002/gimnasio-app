import subprocess
import os
from datetime import datetime
from config import DB_CONFIG

# Ruta al ejecutable mysqldump.exe
# Normalmente está en: C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe
# AJUSTÁ esta ruta según donde lo tengas instalado
RUTA_MYSQLDUMP = r"C:\Archivos de programa\MySQL\MySQL Server 8.0\bin\mysqldump.exe"

CARPETA_BACKUPS = os.path.join(os.path.dirname(__file__), 'backups')
os.makedirs(CARPETA_BACKUPS, exist_ok=True)


def hacer_backup():
    fecha = datetime.now().strftime('%Y-%m-%d_%H-%M')
    nombre_archivo = f"backup_gimnasio_{fecha}.sql"
    ruta_completa = os.path.join(CARPETA_BACKUPS, nombre_archivo)

    comando = [
        RUTA_MYSQLDUMP,
        f"-u{DB_CONFIG['user']}",
        f"-p{DB_CONFIG['password']}",
        DB_CONFIG['database']
    ]

    with open(ruta_completa, 'w', encoding='utf-8') as archivo_salida:
        resultado = subprocess.run(comando, stdout=archivo_salida, stderr=subprocess.PIPE, text=True)

    if resultado.returncode == 0:
        print(f"✅ Backup creado: {ruta_completa}")
    else:
        print(f"❌ Error al hacer el backup: {resultado.stderr}")


if __name__ == '__main__':
    hacer_backup()