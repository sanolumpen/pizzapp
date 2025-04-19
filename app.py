# app.py
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'clave_secreta'

# Configuración de la base de datos
def get_db_connection():
    conn = sqlite3.connect('inventario.db')
    conn.row_factory = sqlite3.Row
    return conn

# Crear tablas en la base de datos
def setup_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Crear tablas   
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insumos (
            id INTEGER PRIMARY KEY,
            nombre TEXT UNIQUE NOT NULL
        )
    ''')
 #Crear tabla de marcas   
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS marcas (
        id INTEGER PRIMARY KEY,
        nombre TEXT UNIQUE NOT NULL
    )
    ''')
#Crear tabla de presentaciones
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presentaciones (
        id INTEGER PRIMARY KEY,
        descripcion TEXT UNIQUE NOT NULL
    )
    ''')
# Crear tabla de inventario
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY,
        insumo_id INTEGER NOT NULL,
        marca_id INTEGER NOT NULL,
        presentacion_id INTEGER NOT NULL,
        precio REAL NOT NULL,
        fecha_compra TEXT NOT NULL,
        fecha_vencimiento TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        FOREIGN KEY (insumo_id) REFERENCES insumos (id),
        FOREIGN KEY (marca_id) REFERENCES marcas (id),
        FOREIGN KEY (presentacion_id) REFERENCES presentaciones (id)
        )
    ''')

    # Datos iniciales
    insumos = [('Harina',), ('Azúcar',), ('Sal',), ('Queso Mozzarella',), ('Salsa de Tomate',), ('Aceitunas',), ('Levadura',), ('Aceite de Girasol',)]
    marcas = [('Morixe',), ('Marolio',), ('La Campagnola',), ('Levex',), ('Arcor',), ('Cañuelas',), ('Barraza',), ('Día',), ('Arrivata',), ('Festa',), ('Dos Anclas',), 
              ('Verónica',), ('Natura',), ('Favorita',), ('Blancaflor',), ('Dimax',), ('Chacabuco',), ('Ledesma',), ('Chango',)]
    presentaciones = [('10kg',), ('5kg',), ('2,5kg',),('1kg',), ('500g',), ('250g',), ('2L',), ('1L',), ('1.5L',), ('400g',), ('200g',), ('100g',)]

    # Insertar datos iniciales si las tablas están vacías
    cursor.execute('SELECT COUNT(*) FROM insumos')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO insumos (nombre) VALUES (?)', insumos)
    
    cursor.execute('SELECT COUNT(*) FROM marcas')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO marcas (nombre) VALUES (?)', marcas)

    cursor.execute('SELECT COUNT(*) FROM presentaciones')
    if cursor.fetchone()[0] == 0:
        cursor.executemany('INSERT INTO presentaciones (descripcion) VALUES (?)', presentaciones)
    
    conn.commit()
    conn.close()

# Crear la base de datos al inicar
setup_database()

# Rutas
# home
@app.route('/')
def home():
    return render_template('home.html')
    conn = get_db_connection()
    cursor = conn.cursor()

    #Obtener todos los items de inventario con sus relaciones
    cursor.execute('''
        SELECT
            inventario.id,
            insumos.nombre as insumo,
            marcas.nombre as marca,
            presentaciones.descripcion as presentacion,
            inventario.precio,
            inventario.fecha_compra,
            inventario.fecha_vencimiento,
            inventario.cantidad
                    
               
        FROM inventario 
        JOIN insumos ON inventario.insumo_id = insumos.id
        JOIN marcas ON inventario.marca_id = marcas.id
        JOIN presentaciones ON inventario.presentacion_id = presentaciones.id
    ''')

    items = cursor.fetchall()
    conn.close()
    
    return render_template('index.html', items=items)
# inventario
@app.route('/inventario')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener los datos del inventario
    cursor.execute('''
        SELECT i.nombre AS insumo, m.nombre AS marca, p.descripcion AS presentacion, 
               inv.precio, inv.fecha_compra, inv.fecha_vencimiento, inv.cantidad
        FROM inventario inv
        JOIN insumos i ON inv.insumo_id = i.id
        JOIN marcas m ON inv.marca_id = m.id
        JOIN presentaciones p ON inv.presentacion_id = p.id
    ''')
    items = cursor.fetchall()
    conn.close()

    return render_template('inventario.html', items=items)
# nuevo item
@app.route('/nuevo', methods=['GET', 'POST'])
def nuevo():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Obtener los datos del formulario
        insumo_id = request.form['insumo_id']
        marca_id = request.form['marca_id']
        presentacion_id = request.form['presentacion_id']
        precio = request.form['precio']
        fecha_compra = request.form['fecha_compra']
        fecha_vencimiento = request.form['fecha_vencimiento']
        cantidad = request.form['cantidad']

        # Validar que los campos no estén vacíos
        if not insumo_id or not marca_id or not presentacion_id or not precio or not fecha_compra or not fecha_vencimiento or not cantidad:
            flash('Todos los campos son obligatorios.', 'error')
            return redirect(url_for('nuevo'))

        # Insertar nuevo ítem en la tabla de inventario
        try:
            cursor.execute('''
                INSERT INTO inventario (insumo_id, marca_id, presentacion_id, precio, fecha_compra, fecha_vencimiento, cantidad)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (insumo_id, marca_id, presentacion_id, precio, fecha_compra, fecha_vencimiento, cantidad))
            conn.commit()
            flash('Ítem agregado con éxito!', 'success')
        except sqlite3.Error as e:
            flash(f'Error al agregar el ítem: {e}', 'error')
        finally:
            conn.close()
            return redirect(url_for('index'))

    # Si es GET, obtener los datos necesarios para el formulario
    cursor.execute('SELECT id, nombre FROM insumos')
    insumos = cursor.fetchall()

    cursor.execute('SELECT id, nombre FROM marcas')
    marcas = cursor.fetchall()

    cursor.execute('SELECT id, descripcion FROM presentaciones')
    presentaciones = cursor.fetchall()

    conn.close()
    return render_template('nuevo.html', insumos=insumos, marcas=marcas, presentaciones=presentaciones)# editar item

# editar item
@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        insumo_id = request.form['insumo_id']
        marca_id = request.form['marca_id']
        presentacion_id = request.form['presentacion_id']
        precio = request.form['precio']
        fecha_compra = request.form['fecha_compra']
        fecha_vencimiento = request.form['fecha_vencimiento']
        cantidad = request.form['cantidad']

        # Actualizar el item en la tabla de inventario
        cursor.execute('''
            UPDATE inventario
            SET insumo_id = ?, marca_id = ?, presentacion_id = ?, precio = ?, fecha_compra = ?, fecha_vencimiento = ?, cantidad = ?
            WHERE id = ?
        ''', (insumo_id, marca_id, presentacion_id, precio, fecha_compra, fecha_vencimiento, cantidad, id))

        conn.commit()
        conn.close()

        flash('Ítem actualizado con éxito!')
        return redirect(url_for('index'))

    # Si es GET, mostrar el formulario con los datos del item a editar
    cursor.execute('SELECT * FROM inventario WHERE id = ?', (id,))
    item = cursor.fetchone()

    # Obtener insumos
    cursor.execute('SELECT id, nombre FROM insumos')
    insumos = cursor.fetchall()
      # Obtener marcas
    cursor.execute('SELECT id, nombre FROM marcas')
    marcas = cursor.fetchall()
      # Obtener presentaciones
    cursor.execute('SELECT id, descripcion FROM presentaciones')
    presentaciones = cursor.fetchall()

    conn.close()
    return render_template('formulario.html', insumos=insumos, marcas=marcas,
                           presentaciones=presentaciones, item=item, editar=True)

# eliminar item
@app.route('/eliminar/<int:id>', methods=['POST'])
def eliminar(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Eliminar el item de la tabla de inventario
    cursor.execute('DELETE FROM inventario WHERE id = ?', (id,))

    conn.commit()
    conn.close()

    flash('Ítem eliminado con éxito!')
    return redirect(url_for('index'))

# configuracion
@app.route('/configuracion')
def configuracion():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obtener insumos
    cursor.execute('SELECT id, nombre FROM insumos')
    insumos = cursor.fetchall()
      # Obtener marcas
    cursor.execute('SELECT id, nombre FROM marcas')
    marcas = cursor.fetchall()
      # Obtener presentaciones
    cursor.execute('SELECT id, descripcion FROM presentaciones')
    presentaciones = cursor.fetchall()

    conn.close()
    return render_template('configuracion.html', insumos=insumos, marcas=marcas,
                           presentaciones=presentaciones)

# filepath: d:\PizzApp\App.py
@app.route('/agregar_insumo', methods=['GET', 'POST'])
def agregar_insumo():
    if request.method == 'POST':
        # Handle form submission
        insumo_nombre = request.form['nombre']
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if the insumo already exists
        cursor.execute('SELECT COUNT(*) FROM insumos WHERE nombre = ?', (insumo_nombre,))
        if cursor.fetchone()[0] > 0:
            conn.close()
            flash('El insumo ya existe. Por favor, ingrese un nombre diferente.', 'error')
            return redirect(url_for('agregar_insumo'))
        # Insert new insumo into the database
        cursor.execute('INSERT INTO insumos (nombre) VALUES (?)', (insumo_nombre,))
        conn.commit()
        conn.close()
        flash('Insumo agregado con éxito!')
        return redirect(url_for('index'))
    return render_template('agregar_insumo.html')

# agregar marca
@app.route('/agregar_marca', methods=['POST'])
def agregar_marca():
    conn = get_db_connection()
    cursor = conn.cursor()

    nombre = request.form['nombre']

    # Check if the marca already exists
    cursor.execute('SELECT COUNT(*) FROM marcas WHERE nombre = ?', (nombre,))
    if cursor.fetchone()[0] > 0:
        conn.close()
        flash('La marca ya existe. Por favor, ingrese un nombre diferente.', 'error')
        return redirect(url_for('configuracion'))

    # Insert new marca into the database
    cursor.execute('INSERT INTO marcas (nombre) VALUES (?)', (nombre,))
    conn.commit()
    conn.close()

    flash('Marca agregada con éxito!')
    return redirect(url_for('configuracion'))

# agregar presentacion
@app.route('/agregar_presentacion', methods=['POST'])
def agregar_presentacion():
    conn = get_db_connection()
    cursor = conn.cursor()

    descripcion = request.form['descripcion']

    # Insertar nueva presentación en la tabla de presentaciones
    cursor.execute('INSERT INTO presentaciones (descripcion) VALUES (?)', (descripcion,))

    conn.commit()
    conn.close()

    flash('Presentación agregada con éxito!')
    return redirect(url_for('configuracion'))
#Hacer que los botones sean más grandes

if __name__ == '__main__':
    app.run(debug=True)

