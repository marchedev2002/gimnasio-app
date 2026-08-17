def login(client):
    return client.post('/login', data={
        'usuario': 'admin',
        'password': 'testpass123'
    }, follow_redirects=True)


def test_alta_socio_exitosa(client):
    login(client)

    response = client.post('/nuevo', data={
        'dni': '99999999',
        'nombre': 'Test',
        'apellido': 'Automatico',
        'telefono': '',
        'email': '',
        'dia_vencimiento': '15'  
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Test Automatico' in response.data

def test_no_permite_dni_duplicado(client):
    login(client)

    datos_socio = {
        'dni': '99999999', 'nombre': 'Test', 'apellido': 'Uno',
        'telefono': '', 'email': '', 'dia_vencimiento': '15'
    }

    client.post('/nuevo', data=datos_socio, follow_redirects=True)
    respuesta_duplicado = client.post('/nuevo', data=datos_socio, follow_redirects=True)

    assert 'Ya existe un socio' in respuesta_duplicado.get_data(as_text=True)

def test_checkin_requiere_login(client):
    """Si nadie esta logueado, /checkin tiene que redirigir a login"""
    response = client.get('/checkin', follow_redirects=False)

    assert response.status_code ==  302
    assert '/login' in response.headers['Location']