# Sistema de Socios - Gimnasio (v1)

Versión funcional inicial: buscás por DNI y te muestra los datos del socio,
su foto y si tiene la membresía al día o vencida.

## Estructura del proyecto

```
gimnasio_app/
├── app.py                 <- Backend Flask (la lógica)
├── config.py               <- Datos de conexión a MySQL (EDITAR)
├── schema.sql               <- Script para crear la base de datos
├── requirements.txt
├── templates/
│   ├── index.html           <- Pantalla de búsqueda
│   └── resultado.html       <- Pantalla de resultado
└── static/
    ├── css/style.css
    └── fotos/                <- Acá van las fotos de los socios
```

## Paso 1: Crear la base de datos

1. Abrí **MySQL Workbench** y conectate a tu servidor local.
2. Archivo -> Open SQL Script -> seleccioná `schema.sql`.
3. Ejecutalo completo (ícono del rayo ⚡ o Ctrl+Shift+Enter).
4. Esto crea la base `gimnasio_db` con las tablas USUARIO, PAGO, MES y
   PRECIO, más 2 socios de ejemplo para probar (uno al día, uno vencido).

## Paso 2: Configurar la conexión

Abrí `config.py` y completá tu usuario y contraseña de MySQL:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'TU_PASSWORD_ACA',
    'database': 'gimnasio_db'
}
```

## Paso 3: Instalar dependencias

Necesitás Python instalado. Abrí una terminal en la carpeta `gimnasio_app` y corré:

```bash
pip install -r requirements.txt
```

## Paso 4: Ejecutar la aplicación

```bash
python app.py
```

Te va a mostrar algo como `Running on http://127.0.0.1:5000`.
Abrí esa dirección en el navegador.

## Paso 5: Probar

Con los datos de ejemplo del `schema.sql` podés probar:

- **DNI 40123456** (Juan Pérez) → Membresía **AL DÍA** (pagó julio 2026)
- **DNI 38987654** (María Gómez) → Membresía **VENCIDA** (pagó junio pero no julio)

## Cómo cargar fotos de socios

1. Guardá la foto del socio en `static/fotos/`, por ejemplo `40123456.jpg`.
2. En MySQL Workbench, actualizá ese registro:
   ```sql
   UPDATE USUARIO SET foto = '40123456.jpg' WHERE dni = '40123456';
   ```
3. Si un socio no tiene foto cargada (`foto` es NULL), se muestra automáticamente
   un ícono genérico (`sin-foto.png`).

## Cómo cargar un socio nuevo (por ahora, manual en Workbench)

```sql
INSERT INTO USUARIO (dni, nombre, apellido, telefono, email, foto)
VALUES ('12345678', 'Nombre', 'Apellido', '341-1234567', 'mail@mail.com', NULL);
```

## Cómo registrar un pago (por ahora, manual en Workbench)

```sql
-- id_mes: 1=Enero ... 12=Diciembre
-- id_precio: revisar tabla PRECIO para ver los ID de cada plan
INSERT INTO PAGO (dni, id_mes, anio, id_precio, fecha_pago)
VALUES ('12345678', 7, 2026, 1, '2026-07-15');
```

## Próximos pasos sugeridos (para cuando quieras seguir mejorando)

1. **Formulario para dar de alta socios nuevos** desde la web (en vez de SQL manual).
2. **Formulario para registrar pagos** desde la web, con subida de foto incluida.
3. **Listado general** de todos los socios con su estado (al día / vencido).
4. **Alertas** de socios próximos a vencer (ej: faltan 3 días).
5. Login con usuario/contraseña para el personal del gimnasio.
6. Pasar de `debug=True` a un servidor de producción cuando esté listo para usarse en el día a día.

Cualquier error o duda que te aparezca al ejecutarlo, mandámelo tal cual
aparece en la terminal y lo resolvemos.
