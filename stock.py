import sqlite3
import streamlit as st

# Conectar a la base de datos SQLite
def conectar_db():
    return sqlite3.connect('inventario.db')

# Crear tablas si no existen
def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            ubicacion TEXT
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maquina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            hospital_id INTEGER,
            FOREIGN KEY(hospital_id) REFERENCES hospital(id)
        );
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repuesto (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            ubicacion TEXT,  -- Nuevo campo para la ubicación física del repuesto
            stock INTEGER DEFAULT 0,
            maquina_id INTEGER,
            FOREIGN KEY(maquina_id) REFERENCES maquina(id)
        );
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movimiento_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repuesto_id INTEGER,
            cantidad INTEGER,
            tipo TEXT,
            fecha TEXT,
            FOREIGN KEY(repuesto_id) REFERENCES repuesto(id)
        );
    ''')

    conexion.commit()
    conexion.close()

# Función para agregar un hospital
def agregar_hospital(nombre, ubicacion):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO hospital (nombre, ubicacion) VALUES (?, ?)', (nombre, ubicacion))
    conexion.commit()
    conexion.close()

# Función para agregar una máquina a un hospital
def agregar_maquina(nombre, hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO maquina (nombre, hospital_id) VALUES (?, ?)', (nombre, hospital_id))
    conexion.commit()
    conexion.close()

# Función para agregar un repuesto a una máquina
def agregar_repuesto(nombre, descripcion, ubicacion, stock, maquina_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO repuesto (nombre, descripcion, ubicacion, stock, maquina_id) VALUES (?, ?, ?, ?, ?)', 
                   (nombre, descripcion, ubicacion, stock, maquina_id))
    conexion.commit()
    conexion.close()

# Función para registrar una entrada de stock
def registrar_entrada(repuesto_id, cantidad):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('UPDATE repuesto SET stock = stock + ? WHERE id = ?', (cantidad, repuesto_id))
    cursor.execute('INSERT INTO movimiento_stock (repuesto_id, cantidad, tipo, fecha) VALUES (?, ?, "entrada", date("now"))', 
                   (repuesto_id, cantidad))
    conexion.commit()
    conexion.close()

# Función para mostrar el stock actual según hospital y máquina
def ver_stock(hospital_id=None, maquina_id=None):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    query = '''
        SELECT repuesto.nombre, repuesto.descripcion, repuesto.ubicacion, repuesto.stock, maquina.nombre, hospital.nombre
        FROM repuesto
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
    '''
    
    params = []
    
    if hospital_id and maquina_id:
        query += ' WHERE hospital.id = ? AND maquina.id = ?'
        params = [hospital_id, maquina_id]
    elif hospital_id:
        query += ' WHERE hospital.id = ?'
        params = [hospital_id]

    cursor.execute(query, params)
    repuestos = cursor.fetchall()
    conexion.close()
    return repuestos

# Función para obtener la lista de hospitales
def obtener_hospitales():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre, ubicacion FROM hospital')
    hospitales = cursor.fetchall()
    conexion.close()
    return hospitales

# Función para obtener las máquinas de un hospital
def obtener_maquinas(hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre FROM maquina WHERE hospital_id = ?', (hospital_id,))
    maquinas = cursor.fetchall()
    conexion.close()
    return maquinas

# Función para obtener los repuestos
def obtener_repuestos(maquina_id=None):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    if maquina_id:
        cursor.execute('SELECT id, nombre FROM repuesto WHERE maquina_id = ?', (maquina_id,))
    else:
        cursor.execute('SELECT id, nombre FROM repuesto')
    
    repuestos = cursor.fetchall()
    conexion.close()
    return repuestos

# Interfaz con Streamlit
def interfaz_principal():
    st.title("Gestión de Stock de Repuestos - Radioterapia")

    # Pestañas para las diferentes funcionalidades
    opcion = st.sidebar.selectbox("Selecciona una opción", ["Ver Stock", "Registrar Entrada", "Registrar Salida", 
                                                            "Agregar Hospital", "Ver Hospitales", 
                                                            "Agregar Máquina", "Ver Máquinas por Hospital", 
                                                            "Buscar Repuesto"])

    if opcion == "Registrar Entrada":
        st.header("Registrar Entrada de Stock")
        
        # Seleccionar hospital y máquina
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        maquina_id = st.selectbox("Selecciona una Máquina", [m[0] for m in maquinas], format_func=lambda x: dict(maquinas)[x])
        
        # Obtener lista de repuestos de la máquina seleccionada
        repuestos = obtener_repuestos(maquina_id)
        repuesto_nombres = [r[1] for r in repuestos]
        
        # Campo de selección de repuesto o nuevo repuesto
        repuesto_seleccionado = st.selectbox("Selecciona un Repuesto o Escribe uno Nuevo", repuesto_nombres + ["Nuevo Repuesto"])
        
        # Si se selecciona "Nuevo Repuesto", permitir al usuario agregarlo
        if repuesto_seleccionado == "Nuevo Repuesto":
            st.subheader("Agregar Nuevo Repuesto")
            nombre_nuevo_repuesto = st.text_input("Nombre del Nuevo Repuesto")
            descripcion_nuevo_repuesto = st.text_input("Descripción del Repuesto")
            ubicacion_nueva_repuesto = st.text_input("Ubicación del Repuesto")  # Nueva ubicación
            cantidad_nueva = st.number_input("Cantidad Inicial", min_value=0)

            if st.button("Agregar y Registrar Entrada"):
                if nombre_nuevo_repuesto and descripcion_nuevo_repuesto and ubicacion_nueva_repuesto:
                    agregar_repuesto(nombre_nuevo_repuesto, descripcion_nuevo_repuesto, ubicacion_nueva_repuesto, cantidad_nueva, maquina_id)
                    st.success(f"Repuesto '{nombre_nuevo_repuesto}' agregado correctamente con {cantidad_nueva} unidades en {ubicacion_nueva_repuesto}.")
                else:
                    st.error("Debes completar el nombre, descripción y ubicación del repuesto.")
        else:
            # Si selecciona un repuesto existente, registrar la entrada
            cantidad = st.number_input("Cantidad a Ingresar", min_value=1)
            repuesto_id = dict((r[1], r[0]) for r in repuestos)[repuesto_seleccionado]

            if st.button("Registrar Entrada"):
                registrar_entrada(repuesto_id, cantidad)
                st.success(f"Entrada de {cantidad} unidades registrada para el repuesto '{repuesto_seleccionado}'.")

    elif opcion == "Ver Stock":
        st.header("Stock por Hospital y Máquina")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        maquina_id = st.selectbox("Selecciona una Máquina", [m[0] for m in maquinas], format_func=lambda x: dict(maquinas)[x])
        
        repuestos = ver_stock(hospital_id, maquina_id)
        for repuesto in repuestos:
            st.write(f"Repuesto: {repuesto[0]} | Descripción: {repuesto[1]} | Ubicación: {repuesto[2]} | Stock: {repuesto[3]} | Máquina: {repuesto[4]} | Hospital: {repuesto[5]}")
    
    # Las demás funcionalidades se mantienen iguales (Registrar Salida, Agregar Hospital, etc.)

# Ejecutar la aplicación
if __name__ == "__main__":
    crear_tablas()  # Crear las tablas la primera vez que se ejecuta
    interfaz_principal()
