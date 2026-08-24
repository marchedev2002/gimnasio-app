def login_como(client, usuario, password):
    return client.post('/login', data={'usuario': usuario, 'password': password}, follow_redirects=True)

def crear_socio(client, dni, nombre, apellido):
    return client.post('/nuevo', data={
        'dni': dni, 'nombre': nombre, 'apellido': apellido,
        'telefono': '', 'email': '', 'dia_vencimiento': '15'
    }, follow_redirects=True)

def test_mismo_dni_en_dos_gimnasios(client):
    """El mismo dni existe en dos gimnasios distintos, cada uno tiene que ver unicamente como su propio socio"""
    login_como(client, 'admin', 'testpass123')
    crear_socio(client, '11111111', 'Socio', 'GimnasioUno')
    client.get('/logout')

    login_como(client, 'admin2_test', 'testpass2_123')
    crear_socio(client, '11111111', 'Socio', 'GimnasioDos')

    rta = client.get('/socio/11111111')
    texto = rta.get_data(as_text=True)

    assert 'GimnasioDos' in texto
    assert 'GimnasioUno' not in texto

def test_no_puede_ver_socio_de_otro_gimnasio(client):
    """Un socio que existe solo en el gimnasio 1 no debe verse desde una sesion iniciada del gimnasio 2"""
    login_como(client, 'admin', 'testpass123')
    crear_socio(client, '22222222', 'Solo', 'GimnasioUno')
    client.get('/logout')

    login_como(client, 'admin2_test', 'testpass2_123')
    rta = client.get('/socio/22222222')
    texto = rta.get_data(as_text=True)

    assert 'Solo GimnasioUno' not in texto
    assert 'No se encontr' in texto

def test_listado_no_mezcla_socios_de_otro_gimnasio(client):
    """El listado de socios de un gimnasio no debe incluir socios de otro."""
    login_como(client, 'admin', 'testpass123')
    crear_socio(client, '33333333', 'Uno', 'DelGimnasioUno')
    client.get('/logout')

    login_como(client, 'admin2_test', 'testpass2_123')
    crear_socio(client, '44444444', 'Dos', 'DelGimnasioDos')

    respuesta = client.get('/socios')
    texto = respuesta.get_data(as_text=True)

    assert 'DelGimnasioDos' in texto
    assert 'DelGimnasioUno' not in texto


def test_no_puede_eliminar_socio_de_otro_gimnasio(client):
    """Intentar eliminar, desde el gimnasio 2, un DNI que en realidad
    pertenece al gimnasio 1, no debe afectar ese registro."""
    login_como(client, 'admin', 'testpass123')
    crear_socio(client, '55555555', 'Protegido', 'GimnasioUno')
    client.get('/logout')

    login_como(client, 'admin2_test', 'testpass2_123')
    client.post('/eliminar/55555555', follow_redirects=True)
    client.get('/logout')

    login_como(client, 'admin', 'testpass123')
    respuesta = client.get('/socio/55555555')

    assert 'Protegido' in respuesta.get_data(as_text=True)


def test_dashboard_cuenta_solo_socios_del_propio_gimnasio(client, app):
    """El contador de 'Socios totales' del dashboard no debe incluir
    socios de otros gimnasios."""
    from app import get_connection

    login_como(client, 'admin', 'testpass123')
    crear_socio(client, '66666666', 'Contador', 'GimnasioUno')
    client.get('/logout')

    login_como(client, 'admin2_test', 'testpass2_123')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total FROM USUARIO WHERE id_gimnasio = 2")
    total_real_gimnasio2 = cursor.fetchone()['total']
    cursor.close()
    conn.close()

    respuesta = client.get('/')
    texto = respuesta.get_data(as_text=True)

    assert str(total_real_gimnasio2) in texto
    # el socio del gimnasio 1 no debería estar contado acá
    assert total_real_gimnasio2 == 0 