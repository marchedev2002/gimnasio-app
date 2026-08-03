import os
import calendar
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file 
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash
import mysql.connector
from datetime import date, timedelta, datetime
from config import DB_CONFIG, SECRET_KEY, NOMBRE_GIMNASIO
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

app = Flask(__name__)
app.secret_key = SECRET_KEY
@app.context_processor
def inject_nombre_gimnasio():
    """Inyecta el nombre del gimnasio en todas las plantillas."""
    return dict(nombre_gimnasio=NOMBRE_GIMNASIO)

# Carpeta donde se guardan las fotos de los socios
CARPETA_FOTOS = os.path.join(app.root_path, 'static', 'fotos')
EXTENSIONES_PERMITIDAS = {'jpg', 'jpeg', 'png'}


def extension_valida(nombre_archivo):
    """Chequea que el archivo subido sea una imagen permitida."""
    return '.' in nombre_archivo and \
           nombre_archivo.rsplit('.', 1)[1].lower() in EXTENSIONES_PERMITIDAS


def guardar_foto(dni, archivo):
    """
    Guarda la foto subida usando el DNI como nombre de archivo,
    para que siempre quede asociada al socio correcto.
    Devuelve el nombre de archivo guardado, o None si no se subió nada.
    """
    if archivo and archivo.filename != '' and extension_valida(archivo.filename):
        extension = archivo.filename.rsplit('.', 1)[1].lower()
        nombre_archivo = secure_filename(f"{dni}.{extension}")
        ruta_completa = os.path.join(CARPETA_FOTOS, nombre_archivo)
        archivo.save(ruta_completa)
        return nombre_archivo
    return None

def calcular_siguiente_vencimiento(fecha_base, dia_vencimiento):
    """
    Calcula la próxima fecha de vencimiento: un mes después de fecha_base,
    siempre anclada al mismo día del mes (dia_vencimiento), sin importar
    qué día se haya efectuado el pago real.
    """
    mes = fecha_base.month + 1
    anio = fecha_base.year
    if mes > 12:
        mes = 1
        anio += 1
    ultimo_dia_del_mes = calendar.monthrange(anio, mes)[1]
    dia = min(dia_vencimiento, ultimo_dia_del_mes)  # por si el día no existe en ese mes (ej: 31 en febrero)
    return date(anio, mes, dia)



def get_connection():
    """Abre una conexión nueva a la base de datos MySQL."""
    return mysql.connector.connect(**DB_CONFIG)

def login_requerido(vista):
    """Decorador que bloquea el acceso a una ruta si no hay sesion iniciada"""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if 'usuario' not in session:
            return redirect(url_for('login'))
        return vista(*args, **kwargs)
    return envoltura

@app.route('/')
@login_requerido
def index():
    """Página inicial: dashboard con buscador de DNI y estadísticas generales."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    hoy = date.today()
    cursor.execute("""
        SELECT COUNT(*) AS total,
               SUM(CASE WHEN fecha_proximo_vencimiento IS NOT NULL
                        AND fecha_proximo_vencimiento >= %s THEN 1 ELSE 0 END) AS al_dia
        FROM USUARIO
    """, (hoy,))
    stats = cursor.fetchone()

    cursor.close()
    conn.close()

    total_socios = stats['total'] or 0
    total_al_dia = stats['al_dia'] or 0
    total_vencidos = total_socios - total_al_dia

    return render_template(
        'index.html',
        total_socios=total_socios,
        total_al_dia=total_al_dia,
        total_vencidos=total_vencidos
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Pagina de inicio de sesion para el personal"""
    if request.method == 'GET':
        return render_template('login.html')
    usuario_ingresado = request.form.get('usuario', '').strip()
    password_ingresado = request.form.get('password', '')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PERSONAL WHERE usuario = %s", (usuario_ingresado,))
    personal = cursor.fetchone()
    cursor.close()
    conn.close()

    if personal and check_password_hash(personal['password_hash'], password_ingresado):
        session['usuario'] = personal['usuario']
        session['nombre'] = personal['nombre']
        return redirect(url_for('index'))

    return render_template('login.html', error="Usuario o contraseña incorrectos.")

@app.route('/logout')
@login_requerido
def logout():
    """Cierra la sesion del personal"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/buscar', methods=['POST'])
@login_requerido
def buscar():
    """Recibe el DNI por teclado (formulario) y redirige a la ficha del socio."""
    dni = request.form.get('dni', '').strip()

    if not dni:
        return render_template('index.html', error="Por favor ingresá un DNI.")

    return redirect(url_for('ver_socio', dni=dni))

@app.route('/nuevo', methods=['GET', 'POST'])
@login_requerido
def nuevo_socio():
    """Formulario para dar de alta un nuevo socio."""
    if request.method == 'GET':
        return render_template('form_socio.html', modo='nuevo', usuario=None)

    dni = request.form.get('dni', '').strip()
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()

    if not dni or not nombre or not apellido:
        return render_template(
            'form_socio.html',
            modo='nuevo',
            usuario=None,
            error="DNI, nombre y apellido son obligatorios."
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return render_template(
            'form_socio.html',
            modo='nuevo',
            usuario=None,
            error="Ya existe un socio con ese DNI."
        )

    nombre_foto = guardar_foto(dni, request.files.get('foto'))

    dia_vencimiento_nuevo = date.today().day

    cursor.execute("""
        INSERT INTO USUARIO (dni, nombre, apellido, telefono, email, foto, dia_vencimiento, fecha_proximo_vencimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (dni, nombre, apellido, telefono or None, email or None, nombre_foto, dia_vencimiento_nuevo, None))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('ver_socio', dni=dni, mensaje="Socio dado de alta correctamente."))

@app.route('/editar/<dni>', methods=['GET', 'POST'])
@login_requerido
def editar_socio(dni):
    """Formulario para editar los datos de un socio existente."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()

        if not usuario:
            return render_template('index.html', error=f"No se encontró ningún socio con DNI {dni}.")

        return render_template('form_socio.html', modo='editar', usuario=usuario)

    # POST: procesar la edición
    nombre = request.form.get('nombre', '').strip()
    apellido = request.form.get('apellido', '').strip()
    telefono = request.form.get('telefono', '').strip()
    email = request.form.get('email', '').strip()

    if not nombre or not apellido:
        cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
        usuario = cursor.fetchone()
        cursor.close()
        conn.close()
        return render_template(
            'form_socio.html', modo='editar', usuario=usuario,
            error="Nombre y apellido son obligatorios."
        )

    # Si subieron una foto nueva, la guardamos y actualizamos el campo
    nombre_foto_nuevo = guardar_foto(dni, request.files.get('foto'))

    if nombre_foto_nuevo:
        cursor.execute("""
            UPDATE USUARIO
            SET nombre = %s, apellido = %s, telefono = %s, email = %s, foto = %s
            WHERE dni = %s
        """, (nombre, apellido, telefono or None, email or None, nombre_foto_nuevo, dni))
    else:
        cursor.execute("""
            UPDATE USUARIO
            SET nombre = %s, apellido = %s, telefono = %s, email = %s
            WHERE dni = %s
        """, (nombre, apellido, telefono or None, email or None, dni))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('ver_socio', dni=dni, mensaje='edicion'))


@app.route('/socio/<dni>')
@login_requerido
def ver_socio(dni):
    """Muestra la ficha de un socio, usando su día de vencimiento fijo."""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        return render_template('index.html', error=f"No se encontró ningún socio con DNI {dni}.")

    hoy = date.today()
    membresia_al_dia = (
        usuario['fecha_proximo_vencimiento'] is not None
        and usuario['fecha_proximo_vencimiento'] >= hoy
    )

    cursor.execute("""
        SELECT PAGO.id_pago, PAGO.fecha_pago, MES.nombre_mes, PAGO.anio,
               PRECIO.tipo_membresia, PRECIO.monto
        FROM PAGO
        JOIN MES ON PAGO.id_mes = MES.id_mes
        JOIN PRECIO ON PAGO.id_precio = PRECIO.id_precio
        WHERE PAGO.dni = %s
        ORDER BY PAGO.fecha_pago DESC
    """, (dni,))
    historial_pagos = cursor.fetchall()

    cursor.close()
    conn.close()

    mensaje = request.args.get('mensaje')

    return render_template(
        'resultado.html',
        usuario=usuario,
        membresia_al_dia=membresia_al_dia,
        historial_pagos=historial_pagos,
        mensaje=mensaje
    )

@app.route('/pago/nuevo', methods=['GET','POST'])
@login_requerido
def nuevo_pago():
    """Formulario para registrar un nuevo pago de un socio"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cursor.execute("SELECT dni, nombre, apellido FROM USUARIO ORDER BY apellido, nombre")
        socios = cursor.fetchall()

        cursor.execute("SELECT id_mes, nombre_mes FROM MES ORDER BY id_mes")
        meses = cursor.fetchall()

        cursor.execute("SELECT id_precio, tipo_membresia, monto FROM PRECIO ORDER BY tipo_membresia")
        precios = cursor.fetchall()

        cursor.close()
        conn.close()

        hoy = date.today()
        dni_preseleccionado = request.args.get('dni', '')

        return render_template(
            'form_pago.html',
            socios=socios,
            meses=meses,
            precios=precios,
            dni_preseleccionado=dni_preseleccionado,
            mes_actual = hoy.month,
            anio_actual = hoy.year,
            fecha_hoy=hoy.isoformat()
        )

    #POST
    dni = request.form.get('dni', '').strip()
    id_mes = request.form.get('id_mes', '').strip()
    anio = request.form.get('anio', '').strip()
    id_precio = request.form.get('id_precio', '').strip()
    fecha_pago = request.form.get('fecha_pago', '').strip()

    if not dni or not id_mes or not anio or not id_precio or not fecha_pago:
        cursor.execute("SELECT dni, nombre, apellido FROM USUARIO ORDER BY apellido, nombre")
        socios = cursor.fetchall()

        cursor.execute("SELECT id_mes, nombre_mes FROM MES ORDER BY id_mes")
        meses = cursor.fetchall()

        cursor.execute("SELECT id_precio, tipo_membresia, monto FROM PRECIO ORDER BY tipo_membresia")
        precios = cursor.fetchall()

        cursor.close()
        conn.close()

        hoy = date.today()
        return render_template(
            'form_pago.html',
            socios=socios,
            meses=meses,
            precios=precios,
            dni_preseleccionado=dni,
            mes_actual = hoy.month,
            anio_actual = hoy.year,
            fecha_hoy=hoy.isoformat(),
            error="Todos los campos son obligatorios."
        )

    cursor.execute("""
        INSERT INTO PAGO (dni, id_mes, anio, id_precio, fecha_pago)
        VALUES (%s, %s, %s, %s, %s)
    """, (dni, id_mes, anio, id_precio, fecha_pago))

    # Calcular el vencimiento en base al MES/AÑO que se está pagando (no a la fecha de hoy)
    cursor.execute("SELECT dia_vencimiento FROM USUARIO WHERE dni = %s", (dni,))
    socio = cursor.fetchone()
    dia_vto = socio['dia_vencimiento']

    id_mes_int = int(id_mes)
    anio_int = int(anio)

    # El "día ancla" puede no existir en todos los meses (ej: día 31 en un mes de 30 días)
    ultimo_dia_mes_pagado = calendar.monthrange(anio_int, id_mes_int)[1]
    dia_ajustado = min(dia_vto, ultimo_dia_mes_pagado)
    fecha_periodo_pagado = date(anio_int, id_mes_int, dia_ajustado)

    # El vencimiento queda en el mismo día del MES SIGUIENTE al que se pagó
    nueva_fecha_vencimiento = calcular_siguiente_vencimiento(fecha_periodo_pagado, dia_vto)

    cursor.execute(
        "UPDATE USUARIO SET fecha_proximo_vencimiento = %s WHERE dni = %s",
        (nueva_fecha_vencimiento, dni)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('ver_socio', dni=dni, mensaje="pago"))

@app.route('/socios')
@login_requerido
def listado_socios():
    """Muestra el listado completo de todos los socios con su estado y filtros"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    hoy = date.today()

    cursor.execute("""
        SELECT dni, nombre, apellido, foto, fecha_proximo_vencimiento,
               CASE WHEN fecha_proximo_vencimiento IS NOT NULL AND fecha_proximo_vencimiento >= %s
                    THEN 1 ELSE 0 END AS al_dia
        FROM USUARIO
        ORDER BY apellido, nombre
    """, (hoy,))

    todos = cursor.fetchall()
    cursor.close()
    conn.close()

    total_al_dia = sum(1 for s in todos if s['al_dia'] == 1)
    total_vencidos = len(todos) - total_al_dia

    busqueda = request.args.get('buscar', '').strip().lower()
    filtro = request.args.get('filtro', 'todos')

    socios = todos

    if busqueda:
        socios = [
            s for s in socios
            if busqueda in s['nombre'].lower() or busqueda in s['apellido'].lower() or busqueda in s['dni'].lower()
        ]

    if filtro == 'al_dia':
        socios = [s for s in socios if s['al_dia'] == 1]
    elif filtro == 'vencidos':
        socios = [s for s in socios if s['al_dia'] == 0]

    return render_template(
        'listado.html',
        socios=socios,
        total_al_dia=total_al_dia,
        total_vencidos=total_vencidos,
        busqueda=busqueda,
        filtro=filtro
    )


@app.route('/eliminar/<dni>', methods=['GET','POST'])
@login_requerido
def eliminar_socio(dni):
    """Elmina un socio y sus pagos de la base"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        return render_template('index.html', error=f"No se encontró ningún socio con DNI {dni}.")

    if request.method == 'GET':
        cursor.close()
        conn.close()
        return render_template('confirmar_eliminar.html', usuario=usuario)

    cursor.execute("DELETE FROM PAGO WHERE dni = %s", (dni,))
    cursor.execute("DELETE FROM ASISTENCIA WHERE dni = %s", (dni,))
    
    cursor.execute("DELETE FROM USUARIO WHERE dni = %s",(dni,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for('listado_socios', mensaje='baja'))

@app.route('/alertas')
@login_requerido
def alertas():
    """Muestra socios vencidos y por vencer, según el día fijo de cada uno."""
    dias_limite = request.args.get('dias', 5)
    try:
        dias_limite = int(dias_limite)
    except ValueError:
        dias_limite = 5

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT dni, nombre, apellido, foto, fecha_proximo_vencimiento
        FROM USUARIO
        ORDER BY apellido, nombre
    """)
    todos = cursor.fetchall()

    cursor.close()
    conn.close()

    hoy = date.today()

    vencidos = [
        s for s in todos
        if s['fecha_proximo_vencimiento'] is None or s['fecha_proximo_vencimiento'] < hoy
    ]

    por_vencer = [
        s for s in todos
        if s['fecha_proximo_vencimiento'] is not None
        and hoy <= s['fecha_proximo_vencimiento'] <= hoy + timedelta(days=dias_limite)
    ]

    return render_template(
        'alertas.html',
        vencidos=vencidos,
        por_vencer=por_vencer,
        dias_limite=dias_limite
    )

@app.route('/reportes')
@login_requerido
def reportes():
    """Pantalla para elegir el mes/año y generar el reporte de pagos"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id_mes, nombre_mes FROM MES ORDER BY id_mes")
    meses = cursor.fetchall()
    cursor.close()
    conn.close()

    hoy = date.today()
    return render_template(
        'reportes.html',
        meses=meses,
        mes_actual=hoy.month,
        anio_actual=hoy.year
    )

@app.route('/reportes/exportar')
@login_requerido
def exportar_reporte():
    """Genera un Excel con todos los pagos del mes/año seleccionado."""
    mes = request.args.get('mes', date.today().month, type=int)
    anio = request.args.get('anio', date.today().year, type=int)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT PAGO.fecha_pago, MES.nombre_mes, PAGO.anio, PRECIO.tipo_membresia, PRECIO.monto,
               USUARIO.dni, USUARIO.nombre, USUARIO.apellido
        FROM PAGO
        JOIN MES ON PAGO.id_mes = MES.id_mes
        JOIN PRECIO ON PAGO.id_precio = PRECIO.id_precio
        JOIN USUARIO ON PAGO.dni = USUARIO.dni
        WHERE PAGO.id_mes = %s AND PAGO.anio = %s
        ORDER BY PAGO.fecha_pago ASC
    """, (mes, anio))
    pagos = cursor.fetchall()
    cursor.close()
    conn.close()

    wb = Workbook()
    ws = wb.active
    ws.tittle = "Pagos"

    encabezados = ['DNI', 'Nombre', 'Apellido', 'Mes', 'Año', 'Plan', 'Monto', 'Fecha de pago']
    ws.append(encabezados)

    for celda in ws[1]:
        celda.font = Font(bold=True, color="FFFFFF")
        celda.fill = PatternFill(start_color="E94560", end_color="E94560", fill_type="solid")

    total = 0
    for p in pagos:
        ws.append([
            p['dni'], p['nombre'], p['apellido'], p['nombre_mes'],
            p['anio'], p['tipo_membresia'], float(p['monto']), p['fecha_pago'].strftime('d/%m/%Y')
        ])
        total += float(p['monto'])

    ws.append([])
    ws.append(['', '', '', '', '', 'TOTAL RECAUDADO', total,'' ])
    ws.cell(row=ws.max_row, column=6).font = Font(bold=True)
    ws.cell(row=ws.max_row, column=7).font = Font(bold=True)

    # Ajustar ancho de columnas
    for columna in ws.columns:
        ancho_max = max(len(str(celda.value)) if celda.value else 0 for celda in columna)
        ws.column_dimensions[columna[0].column_letter].width = ancho_max + 3

    archivo_en_memoria = BytesIO()
    wb.save(archivo_en_memoria)
    archivo_en_memoria.seek(0)

    nombre_mes_texto = next((m for m in ['', 'Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio',
                                          'Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                              if False), None)  # placeholder, se resuelve abajo

    nombre_archivo = f"pagos_{mes:02d}-{anio}.xlsx"

    return send_file(
        archivo_en_memoria,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


    if not mes or not anio:
        return redirect(url_for('reportes', error="Por favor seleccioná un mes y un año."))

@app.route('/checkin', methods=['GET'])
@login_requerido
def checkin():
    """Pantalla rápida de ingreso: solo pide el DNI."""
    return render_template('checkin.html')


@app.route('/checkin/procesar', methods=['POST'])
@login_requerido
def procesar_checkin():
    """Registra el ingreso del socio y muestra su estado + visitas del mes."""
    dni = request.form.get('dni', '').strip()

    if not dni:
        return render_template('checkin.html', error="Por favor ingresá un DNI.")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM USUARIO WHERE dni = %s", (dni,))
    usuario = cursor.fetchone()

    if not usuario:
        cursor.close()
        conn.close()
        return render_template('checkin.html', error=f"No se encontró ningún socio con DNI {dni}.")

    # Registrar el ingreso (fecha y hora actuales)
    ahora = datetime.now()
    cursor.execute(
        "INSERT INTO ASISTENCIA (dni, fecha_hora) VALUES (%s, %s)",
        (dni, ahora)
    )
    conn.commit()

    # Estado de la membresía (misma lógica que ya usábamos en ver_socio)
    hoy = date.today()
    membresia_al_dia = (
        usuario['fecha_proximo_vencimiento'] is not None
        and usuario['fecha_proximo_vencimiento'] >= hoy
    )

    # Plan actual del socio: el de su último pago registrado
    cursor.execute("""
        SELECT PRECIO.tipo_membresia, PRECIO.dias_max_mes
        FROM PAGO
        JOIN PRECIO ON PAGO.id_precio = PRECIO.id_precio
        WHERE PAGO.dni = %s
        ORDER BY PAGO.fecha_pago DESC
        LIMIT 1
    """, (dni,))
    plan_actual = cursor.fetchone()

    # Cuántas veces ya asistió este mes calendario
    cursor.execute("""
        SELECT COUNT(*) AS cantidad
        FROM ASISTENCIA
        WHERE dni = %s AND YEAR(fecha_hora) = YEAR(CURDATE()) AND MONTH(fecha_hora) = MONTH(CURDATE())
    """, (dni,))
    visitas_mes = cursor.fetchone()['cantidad']

    cursor.close()
    conn.close()

    excede_limite = (
        plan_actual is not None
        and plan_actual['dias_max_mes'] is not None
        and visitas_mes > plan_actual['dias_max_mes']
    )

    return render_template(
        'resultado_checkin.html',
        usuario=usuario,
        membresia_al_dia=membresia_al_dia,
        hora_ingreso=ahora.strftime('%H:%M'),
        plan_actual=plan_actual,
        visitas_mes=visitas_mes,
        excede_limite=excede_limite
    )


if __name__ == '__main__':
    app.run(debug=False)
