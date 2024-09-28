import psycopg2
import os
import streamlit as st
import pandas as pd

# Función para conectar a la base de datos PostgreSQL
def conectar_db():
    # Obtener la URL de conexión desde la variable de entorno
    DATABASE_URL = os.getenv('DATABASE_URL')
    
    # Establecer la conexión usando psycopg2
    conexion = psycopg2.connect(DATABASE_URL)
    return conexion
    
# Crear tablas si no existen
def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Crear tabla hospital
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS hospital (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        ubicacion TEXT
    );
    ''')

    # Crear tabla maquina (con clave foránea hacia hospital)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS maquina (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        hospital_id INTEGER NOT NULL,
        FOREIGN KEY (hospital_id) REFERENCES hospital(id) ON DELETE CASCADE
    );
    ''')

    # Crear tabla repuesto (con clave foránea hacia maquina)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS repuesto (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        stock INTEGER DEFAULT 0,
        ubicacion TEXT,
        maquina_id INTEGER NOT NULL,
        FOREIGN KEY (maquina_id) REFERENCES maquina(id) ON DELETE CASCADE
    );
    ''')

    # Crear tabla movimiento_stock (con claves foráneas hacia repuesto)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimiento_stock (
        id SERIAL PRIMARY KEY,
        repuesto_id INTEGER NOT NULL,
        cantidad INTEGER,
        tipo TEXT,
        fecha DATE,
        FOREIGN KEY (repuesto_id) REFERENCES repuesto(id) ON DELETE CASCADE
    );
    ''')

    conexion.commit()
    cursor.close()
    conexion.close()

# Función para cargar los repuestos desde excel
def cargar_repuestos_desde_excel(df, maquina_id):
    # Definir las columnas requeridas
    columnas_requeridas = ['nombre', 'descripcion', 'stock', 'ubicacion']

    # Mantener solo las columnas requeridas
    df = df[columnas_requeridas]

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        for index, row in df.iterrows():
            nombre = row['nombre']
            descripcion = row['descripcion']
            stock = row['stock']
            ubicacion = row['ubicacion']

            # Verificar si el repuesto ya existe en la misma máquina
            cursor.execute('''
                SELECT id FROM repuesto 
                WHERE nombre = %s AND maquina_id = %s
            ''', (nombre, maquina_id))
            repuesto_existente = cursor.fetchone()

            if repuesto_existente:
                # Si el repuesto ya existe, actualizar el stock
                repuesto_id = repuesto_existente[0]
                cursor.execute('''
                    UPDATE repuesto SET stock = stock + %s, descripcion = %s, ubicacion = %s WHERE id = %s
                ''', (stock, descripcion, ubicacion, repuesto_id))
                st.info(f"Repuesto '{nombre}' ya existe. Stock actualizado.")
            else:
                # Si no existe, insertar un nuevo repuesto
                cursor.execute('''
                    INSERT INTO repuesto (nombre, descripcion, stock, ubicacion, maquina_id) 
                    VALUES (%s, %s, %s, %s, %s)
                ''', (nombre, descripcion, stock, ubicacion, maquina_id))
                st.success(f"Repuesto '{nombre}' añadido correctamente.")
        
        # Confirmar los cambios en la base de datos
        conexion.commit()

    except Exception as e:
        conexion.rollback()
        st.error(f"Error al cargar los repuestos: {e}")
    finally:
        conexion.close()


def agregar_columna_ubicacion():
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Agregar la columna ubicacion a la tabla repuesto si no existe
    cursor.execute('''
    ALTER TABLE repuesto
    ADD COLUMN IF NOT EXISTS ubicacion TEXT;
    ''')

    conexion.commit()
    cursor.close()
    conexion.close()



# Función para verificar si un hospital ya existe
def verificar_hospital(nombre, ubicacion):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM hospital WHERE nombre = %s AND ubicacion = %s', (nombre, ubicacion))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado > 0

# Función para verificar si una máquina ya existe en el hospital
def verificar_maquina(nombre, hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM maquina WHERE nombre = %s AND hospital_id = %s', (nombre, hospital_id))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado > 0

# Función para agregar un hospital
def agregar_hospital(nombre, ubicacion):
    if verificar_hospital(nombre, ubicacion):
        st.warning(f"El hospital '{nombre}' ya existe en la ubicación '{ubicacion}'.")
    else:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('INSERT INTO hospital (nombre, ubicacion) VALUES (%s, %s)', (nombre, ubicacion))
        conexion.commit()
        conexion.close()
        st.success(f"Hospital '{nombre}' agregado correctamente en la ubicación '{ubicacion}'.")

# Función para agregar una máquina a un hospital
def agregar_maquina(nombre, hospital_id):
    if verificar_maquina(nombre, hospital_id):
        st.warning(f"La máquina '{nombre}' ya existe en este hospital.")
    else:
        conexion = conectar_db()
        cursor = conexion.cursor()
        cursor.execute('INSERT INTO maquina (nombre, hospital_id) VALUES (%s, %s)', (nombre, hospital_id))
        conexion.commit()
        conexion.close()
        st.success(f"Máquina '{nombre}' agregada correctamente.")

# Función para agregar un repuesto a una máquina
def agregar_repuesto(nombre, descripcion, ubicacion, stock, maquina_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO repuesto (nombre, descripcion, ubicacion, stock, maquina_id) VALUES (%s, %s, %s, %s, %s)', 
                   (nombre, descripcion, ubicacion, stock, maquina_id))
    conexion.commit()
    conexion.close()

# Función para eliminar un repuesto
def eliminar_repuesto(repuesto_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Verificar si el repuesto existe antes de eliminarlo
        cursor.execute('SELECT * FROM repuesto WHERE id = %s', (repuesto_id,))
        repuesto = cursor.fetchone()
        if not repuesto:
            print(f"El repuesto con ID {repuesto_id} no existe.")
            return

        # Eliminar el repuesto
        cursor.execute('DELETE FROM repuesto WHERE id = %s', (repuesto_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados con ID {repuesto_id}.")

        conexion.commit()
        print(f"Operación de eliminación confirmada en la base de datos.")

    except psycopg2.Error as e:
        print(f"Error durante la eliminación del repuesto: {e}")
        conexion.rollback()

    finally:
        conexion.close()

# Función para eliminar una máquina y sus repuestos
def eliminar_maquina(maquina_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Verificar si la máquina existe antes de eliminarla
        cursor.execute('SELECT * FROM maquina WHERE id = %s', (maquina_id,))
        maquina = cursor.fetchone()
        if not maquina:
            print(f"La máquina con ID {maquina_id} no existe.")
            st.write(f"La máquina con ID {maquina_id} no existe.")
            return

        # Eliminar todos los repuestos asociados a la máquina
        cursor.execute('DELETE FROM repuesto WHERE maquina_id = %s', (maquina_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados para la máquina con ID {maquina_id}.")
        st.write(f"{repuestos_eliminados} repuestos eliminados para la máquina con ID {maquina_id}.")  # Verificar eliminación de repuestos

        # Eliminar la máquina
        cursor.execute('DELETE FROM maquina WHERE id = %s', (maquina_id,))
        maquinas_eliminadas = cursor.rowcount
        print(f"{maquinas_eliminadas} máquinas eliminadas con ID {maquina_id}.")
        st.write(f"{maquinas_eliminadas} máquinas eliminadas con ID {maquina_id}.")  # Verificar eliminación de la máquina

        conexion.commit()
        print("Operación de eliminación confirmada en la base de datos.")
        st.write("Operación de eliminación confirmada en la base de datos.")

    except psycopg2.Error as e:
        print(f"Error durante la eliminación de la máquina: {e}")
        st.error(f"Error durante la eliminación de la máquina: {e}")
        conexion.rollback()

    finally:
        conexion.close()

def ejecutar_sql_comando(comando):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute(comando)
        conexion.commit()
        print(f"Comando ejecutado: {comando}")
    except psycopg2.Error as e:
        print(f"Error ejecutando el comando: {e}")
    finally:
        conexion.close()



# Función para registrar una entrada de stock
def registrar_entrada(hospital_id, maquina_id, repuesto_seleccionado, cantidad, nombre_repuesto=None, descripcion_repuesto=None, ubicacion_repuesto=None):
    conexion = conectar_db()
    cursor = conexion.cursor()

    # Verificar si se seleccionó "Nuevo Repuesto"
    if repuesto_seleccionado == "Nuevo Repuesto":
        # Verificar si el repuesto ya existe en la misma máquina
        cursor.execute('''
            SELECT id FROM repuesto 
            WHERE nombre = %s AND maquina_id = %s
        ''', (nombre_repuesto, maquina_id))
        repuesto_existente = cursor.fetchone()

        if repuesto_existente:
            # Si el repuesto ya existe, actualizamos el stock
            repuesto_id = repuesto_existente[0]
            cursor.execute('UPDATE repuesto SET stock = stock + %s WHERE id = %s', (cantidad, repuesto_id))
            st.success(f"El repuesto '{nombre_repuesto}' ya existe. Stock actualizado.")
        else:
            # Si no existe, creamos uno nuevo
            cursor.execute('''
                INSERT INTO repuesto (nombre, descripcion, stock, ubicacion, maquina_id) 
                VALUES (%s, %s, %s, %s, %s)
            ''', (nombre_repuesto, descripcion_repuesto, cantidad, ubicacion_repuesto, maquina_id))
            st.success(f"Nuevo repuesto '{nombre_repuesto}' creado con éxito y stock actualizado.")
    else:
        # Si no es un nuevo repuesto, es uno existente, simplemente actualizamos el stock
        cursor.execute('UPDATE repuesto SET stock = stock + %s WHERE id = %s', (cantidad, repuesto_seleccionado))
        st.success("Stock actualizado para el repuesto seleccionado.")

    conexion.commit()
    conexion.close()


# Función para registrar una salida de stock
def registrar_salida(repuesto_id, cantidad):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Actualizar el stock del repuesto existente (disminuir stock)
        cursor.execute('UPDATE repuesto SET stock = stock - %s WHERE id = %s', (cantidad, repuesto_id))

        #Registrar el movimiento de salida en la tabla movimienot_stock
        cursor.execute('''
            INSERT INTO movimiento_stock (repuesto_id, cantidad, tipo, fecha)
            VALUES (%s, %s, %s, CURRENT_DATE) 
        ''', (repuesto_id, cantidad, 'salida'))
        conexion.commit()
        st.success(f"Salida de {cantidad} unidades del repuesto con ID {repuesto_id} registrada correctamente.")
    except psycopg2.Error as e:
        st.error(f"Error al registrar la salida de stock: {e}")
        conexion.rollback()
    finally:
        conexion.close()

# Función para mostrar el stock actual según hospital y máquina
def ver_stock(hospital_id=None, maquina_id=None):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    query = '''
        SELECT repuesto.nombre, repuesto.descripcion, repuesto.stock, maquina.nombre, hospital.nombre
        FROM repuesto
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
    '''
    
    params = []
    
    if hospital_id and maquina_id:
        query += ' WHERE hospital.id = %s AND maquina.id = %s'
        params = [hospital_id, maquina_id]
    elif hospital_id:
        query += ' WHERE hospital.id = %s'
        params = [hospital_id]

    cursor.execute(query, params)
    repuestos = cursor.fetchall()
    conexion.close()
    return repuestos

# Función para buscar un repuesto por nombre y mostrar dónde está
def buscar_repuesto(nombre_repuesto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT repuesto.nombre, repuesto.descripcion, repuesto.ubicacion, repuesto.stock, maquina.nombre, hospital.nombre
        FROM repuesto
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
        WHERE repuesto.nombre LIKE %s
    ''', ('%' + nombre_repuesto + '%',))
    resultados = cursor.fetchall()
    conexion.close()
    return resultados

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
    cursor.execute('SELECT id, nombre FROM maquina WHERE hospital_id = %s', (hospital_id,))
    maquinas = cursor.fetchall()
    conexion.close()
    return maquinas

# Función para obtener los repuestos
def obtener_repuestos(maquina_id=None):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    if maquina_id:
        cursor.execute('SELECT id, nombre FROM repuesto WHERE maquina_id = %s', (maquina_id,))
    else:
        cursor.execute('SELECT id, nombre FROM repuesto')
    
    repuestos = cursor.fetchall()
    conexion.close()
    return repuestos

def listar_maquinas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM maquina')
    maquinas = cursor.fetchall()
    conexion.close()
    return maquinas

def listar_repuestos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT * FROM repuesto')
    repuestos = cursor.fetchall()
    conexion.close()
    return repuestos


# Función para listar todos los hospitales
def listar_hospitales():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT id, nombre, ubicacion FROM hospital')
    hospitales = cursor.fetchall()
    conexion.close()
    return hospitales

# Función para eliminar un hospital específico
def eliminar_hospital(hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    try:
        # Verificar si el hospital existe
        cursor.execute('SELECT * FROM hospital WHERE id = %s', (hospital_id,))
        hospital = cursor.fetchone()
        if not hospital:
            print(f"El hospital con ID {hospital_id} no existe.")
            return

        # Eliminar el hospital
        cursor.execute('DELETE FROM hospital WHERE id = %s', (hospital_id,))
        print(f"Hospital con ID {hospital_id} eliminado.")

        conexion.commit()
        print(f"El hospital ha sido eliminado correctamente.")
        
    except psycopg2.Error as e:
        print(f"Error durante la eliminación del hospital: {e}")
        conexion.rollback()

    finally:
        conexion.close()
def listar_tablas_y_claves():
    conexion = conectar_db()
    cursor = conexion.cursor()

    print("Tablas en la base de datos:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tablas = cursor.fetchall()
    for tabla in tablas:
        print(f"Tabla: {tabla[0]}")

    print("\nClaves foráneas en la base de datos:")
    for tabla in tablas:
        cursor.execute(f"PRAGMA foreign_key_list({tabla[0]});")
        claves_foraneas = cursor.fetchall()
        if claves_foraneas:
            for clave in claves_foraneas:
                print(f"Tabla {tabla[0]}: {clave}")
        else:
            print(f"Tabla {tabla[0]} no tiene claves foráneas.")

    conexion.close()

# Función para mostrar registro de movimientos.
def obtener_movimientos():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # Consulta SQL para obtener los movimientos
    cursor.execute('''
        SELECT movimiento_stock.repuesto_id, repuesto.nombre, repuesto.descripcion, movimiento_stock.cantidad, 
               movimiento_stock.tipo, movimiento_stock.fecha, maquina.nombre AS maquina, hospital.nombre AS hospital
        FROM movimiento_stock
        JOIN repuesto ON movimiento_stock.repuesto_id = repuesto.id
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
        ORDER BY movimiento_stock.fecha DESC;
    ''')

    # Obtener todos los registros
    movimientos = cursor.fetchall()
    conexion.close()
    return movimientos



# Interfaz con Streamlit
def interfaz_principal():
    st.title("Gestión de Extra-Stock")

    # Pestañas para las diferentes funcionalidades
    opcion = st.sidebar.selectbox("Selecciona una opción", ["Ver Stock", "Buscar Repuesto", "Registrar Entrada", "Registrar Salida", 
                                                            "Cargar repuestos desde Excel", "Ver Hospitales", "Agregar Hospital", 
                                                            "Ver Máquinas por Hospital", "Agregar Máquina", 
                                                            "Ver Movimientos", "Eliminar Repuesto", 
                                                            "Eliminar Máquina", "Eliminar Hospital"])
                                                            

    if opcion == "Registrar Entrada":
        st.header("Registrar Entrada de Stock")
    
        # Obtener lista de hospitales
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
    
        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        maquina_seleccionada = st.selectbox("Selecciona una Máquina", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
        maquina_id = maquina_seleccionada[0]
    
        # Obtener los repuestos asociados a la máquina seleccionada
        repuestos = obtener_repuestos(maquina_id)
    
        # Agregar "Nuevo Repuesto" como la primera opción
        repuesto_opciones = ["Nuevo Repuesto"] + [r[1] for r in repuestos]
        repuesto_seleccionado = st.selectbox("Selecciona un Repuesto o crea uno nuevo", repuesto_opciones)
    
        # Ingresar la cantidad para registrar
        cantidad = st.number_input("Cantidad a ingresar", min_value=1, step=1)
    
        # Si se selecciona "Nuevo Repuesto", mostrar campos adicionales para el nuevo repuesto
        if repuesto_seleccionado == "Nuevo Repuesto":
            nombre_repuesto = st.text_input("Nombre del nuevo repuesto")
            descripcion_repuesto = st.text_input("Descripción del nuevo repuesto")
            ubicacion_repuesto = st.text_input("Ubicación del nuevo repuesto")
    
            # Validar que los campos no estén vacíos
            if nombre_repuesto and descripcion_repuesto and ubicacion_repuesto:
                if st.button("Registrar nuevo repuesto y entrada"):
                    registrar_entrada(hospital_id, maquina_id, repuesto_seleccionado, cantidad, nombre_repuesto, descripcion_repuesto, ubicacion_repuesto)
            else:
                st.warning("Por favor, completa todos los campos para el nuevo repuesto.")
        else:
            # Si no se selecciona "Nuevo Repuesto", registrar entrada para un repuesto existente
            if st.button("Registrar entrada"):
                registrar_entrada(hospital_id, maquina_id, repuesto_seleccionado, cantidad)

    
    elif opcion == "Cargar repuestos desde Excel":
        st.header("Cargar Repuestos desde un archivo Excel")
    
        # Subir el archivo Excel
        archivo_excel = st.file_uploader("Sube un archivo Excel", type=["xlsx"])
    
        if archivo_excel is not None:
            # Leer el archivo Excel
            df = pd.read_excel(archivo_excel)
    
            # Validar que el archivo tenga las columnas necesarias
            columnas_requeridas = ['nombre', 'descripcion', 'stock', 'ubicacion']
            if all(col in df.columns for col in columnas_requeridas):
                st.success("Archivo cargado correctamente con las columnas necesarias.")
                
                # Mostrar los datos del archivo Excel
                st.write("Datos cargados desde el archivo:")
                st.dataframe(df)
    
                # Seleccionar un hospital
                hospitales = obtener_hospitales()
                hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
    
                # Seleccionar una máquina del hospital seleccionado
                maquinas = obtener_maquinas(hospital_id)
                maquina_seleccionada = st.selectbox("Selecciona una Máquina", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
                maquina_id = maquina_seleccionada[0]
    
                if st.button("Cargar repuestos en la base de datos"):
                    # Insertar los datos del Excel en la base de datos
                    cargar_repuestos_desde_excel(df, maquina_id)
            else:
                st.error(f"El archivo Excel debe contener las siguientes columnas: {', '.join(columnas_requeridas)}.")

    
    elif opcion == "Registrar Salida":
        st.header("Registrar Salida de Stock")
    
        # Obtener lista de hospitales
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
    
        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        maquina_seleccionada = st.selectbox("Selecciona una Máquina", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
        maquina_id = maquina_seleccionada[0]
    
        # Obtener los repuestos asociados a la máquina seleccionada
        repuestos = obtener_repuestos(maquina_id)
        
        if repuestos:
            repuesto_nombre = st.selectbox("Selecciona un Repuesto", [r[1] for r in repuestos])
    
            # Comprobar que se ha seleccionado un repuesto antes de proceder
            if repuesto_nombre:
                # Mapear el nombre del repuesto a su ID
                repuesto_id = dict((r[1], r[0]) for r in repuestos).get(repuesto_nombre)
    
                # Campo para ingresar la cantidad de salida
                cantidad = st.number_input("Cantidad a retirar", min_value=1, step=1)
    
                if st.button(f"Registrar salida de {cantidad} unidades de {repuesto_nombre}"):
                    if repuesto_id is not None:
                        registrar_salida(repuesto_id, cantidad)
                        st.success(f"Salida de {cantidad} unidades del repuesto '{repuesto_nombre}' registrada correctamente.")
                    else:
                        st.error("Error: No se pudo encontrar el ID del repuesto seleccionado.")
            else:
                st.error("Error: Debes seleccionar un repuesto.")
        else:
            st.info("No hay repuestos disponibles para esta máquina.")

    elif opcion == "Ver Movimientos":
        st.header("Registro de Movimientos de Stock")
    
        # Obtener la lista de movimientos
        movimientos = obtener_movimientos()
    
        # Verificar si hay movimientos en el registro
        if movimientos:
            # Mostrar los movimientos en una tabla
            st.write("Movimientos registrados:")
            st.table([{
                "Repuesto": movimiento[1],
                "Descripción": movimiento[2],
                "Cantidad": movimiento[3],
                "Tipo": movimiento[4],
                "Fecha": movimiento[5],
                "Máquina": movimiento[6],
                "Hospital": movimiento[7]
            } for movimiento in movimientos])
        else:
            st.info("No se encontraron movimientos registrados.")

    
    elif opcion == "Eliminar Repuesto":
        st.header("Eliminar Repuesto")

        # Obtener lista de hospitales
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])

        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        maquina_seleccionada = st.selectbox("Selecciona una Máquina", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
        maquina_id = maquina_seleccionada[0]

        # Obtener los repuestos asociados a la máquina seleccionada
        repuestos = obtener_repuestos(maquina_id)
        if repuestos:
            # Mostrar menú desplegable de repuestos con nombre y ID
            repuesto_seleccionado = st.selectbox("Selecciona un Repuesto para eliminar", repuestos, format_func=lambda x: f"ID: {x[0]} | Repuesto: {x[1]}")
            
            # Extraer el ID del repuesto seleccionado y verificar que lo estamos obteniendo correctamente
            repuesto_id = repuesto_seleccionado[0]
            st.write(f"ID del repuesto seleccionado: {repuesto_id}")  # Esto mostrará el ID seleccionado para verificar

            if st.button(f"Eliminar Repuesto '{repuesto_seleccionado[1]}'"):
                # Realizamos la eliminación directamente sin botón de confirmación adicional
                eliminar_repuesto(repuesto_id)
                st.success(f"Repuesto '{repuesto_seleccionado[1]}' eliminado correctamente.")

                # Refrescar la lista de repuestos después de la eliminación
                repuestos_actualizados = obtener_repuestos(maquina_id)
                if not repuestos_actualizados:
                    st.info(f"No quedan repuestos en la máquina seleccionada.")
                else:
                    st.write("Repuestos restantes:")
                    for repuesto in repuestos_actualizados:
                        st.write(f"Repuesto: {repuesto[1]}")
        else:
            st.info("No hay repuestos disponibles para eliminar en esta máquina.")

    
    elif opcion == "Eliminar Máquina":
        st.header("Eliminar Máquina")
        
        # Obtener lista de hospitales
        hospitales = obtener_hospitales()
        st.write(f"Hospitales disponibles: {hospitales}")  # Para depurar la lista de hospitales
    
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        st.write(f"Hospital seleccionado: {hospital_id}")  # Para verificar el hospital seleccionado
        
        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        st.write(f"Máquinas disponibles en el hospital {hospital_id}: {maquinas}")  # Para depurar la lista de máquinas
        
        if maquinas:
            # Mostrar menú desplegable de máquinas con nombre y ID
            maquina_seleccionada = st.selectbox("Selecciona una Máquina para eliminar", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
            st.write(f"Máquina seleccionada: {maquina_seleccionada}")  # Verificar la máquina seleccionada
            
            # Extraer el ID de la máquina seleccionada
            maquina_id = maquina_seleccionada[0]
            st.write(f"ID de la máquina seleccionada: {maquina_id}")  # Verificar el ID de la máquina
    
            # Inicializar el estado de confirmación en session_state
            if "confirmar_eliminacion" not in st.session_state:
                st.session_state.confirmar_eliminacion = False
    
            # Primer botón: iniciar la confirmación de eliminación
            if not st.session_state.confirmar_eliminacion:
                if st.button(f"Eliminar Máquina '{maquina_seleccionada[1]}'"):
                    st.warning(f"Estás a punto de eliminar la máquina '{maquina_seleccionada[1]}' y todos sus repuestos. Confirma la eliminación.")
                    st.session_state.confirmar_eliminacion = True  # Cambiar estado para confirmar la eliminación
    
            # Segundo paso: si se confirmó la eliminación, mostrar el botón para realizarla
            if st.session_state.confirmar_eliminacion:
                st.write("Confirmación recibida. Listo para eliminar.")
                if st.button(f"Confirmar eliminación de la máquina '{maquina_seleccionada[1]}'"):
                    st.write(f"Eliminando la máquina con ID {maquina_id}")  # Confirmación antes de eliminar
                    
                    # Aquí llamamos a la función eliminar_maquina
                    try:
                        eliminar_maquina(maquina_id)
                        st.success(f"Máquina '{maquina_seleccionada[1]}' eliminada correctamente junto con todos sus repuestos.")
                        st.write("Máquina eliminada correctamente.")  # Confirmación de éxito
    
                        # Reiniciar el estado de confirmación
                        st.session_state.confirmar_eliminacion = False
    
                        # Refrescar la lista de máquinas después de la eliminación
                        maquinas_actualizadas = obtener_maquinas(hospital_id)
                        st.write(f"Máquinas actualizadas en el hospital {hospital_id}: {maquinas_actualizadas}")  # Para depurar después de la eliminación
    
                        if not maquinas_actualizadas:
                            st.info(f"No quedan máquinas en el hospital seleccionado.")
                        else:
                            st.write("Máquinas restantes:")
                            for maquina in maquinas_actualizadas:
                                st.write(f"Máquina: {maquina[1]}")
                    except Exception as e:
                        st.error(f"Error al eliminar la máquina: {e}")  # Mostrar error en caso de fallo
                        st.write(f"Error al ejecutar la eliminación: {e}")  # Mostrar el error específico
    
        else:
            st.info("No hay máquinas disponibles para eliminar en este hospital.")





    elif opcion == "Ver Stock":
        st.header("Stock por Hospital y Máquina")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        maquina_id = st.selectbox("Selecciona una Máquina", [m[0] for m in maquinas], format_func=lambda x: dict(maquinas)[x])
        
        repuestos = ver_stock(hospital_id, maquina_id)
        for repuesto in repuestos:
            st.write(f"Repuesto: {repuesto[0]} | Descripción: {repuesto[1]} | Ubicación: {repuesto[4]} | Stock: {repuesto[2]}")

    elif opcion == "Agregar Hospital":
        st.header("Agregar Hospital")
        nombre = st.text_input("Nombre del Hospital")
        ubicacion = st.text_input("Ubicación del Hospital")
        if st.button("Agregar Hospital"):
            agregar_hospital(nombre, ubicacion)

    elif opcion == "Ver Hospitales":
        st.header("Lista de Hospitales")
        hospitales = obtener_hospitales()
        for hospital in hospitales:
            st.write(f"Nombre: {hospital[1]} | Ubicación: {hospital[2]}")

    elif opcion == "Agregar Máquina":
        st.header("Agregar Máquina")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        nombre = st.text_input("Nombre de la Máquina")
        if st.button("Agregar Máquina"):
            agregar_maquina(nombre, hospital_id)

    elif opcion == "Ver Máquinas por Hospital":
        st.header("Ver Máquinas por Hospital")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        for maquina in maquinas:
            st.write(f"Máquina: {maquina[1]}")

    elif opcion == "Buscar Repuesto":
        st.header("Buscar Repuesto")
        nombre_repuesto = st.text_input("Nombre del Repuesto")
        if st.button("Buscar"):
            resultados = buscar_repuesto(nombre_repuesto)
            if resultados:
                for resultado in resultados:
                    st.write(f"Repuesto: {resultado[0]} | Descripción: {resultado[1]} | Ubicación: {resultado[2]} | Stock: {resultado[3]} | Máquina: {resultado[4]} | Hospital: {resultado[5]}")
            else:
                st.warning("No se encontró el repuesto.")
    elif opcion == "Ver Maquinas":
        st.header("Listado de Máquinas")
        maquinas = listar_maquinas()
        if maquinas:
            for maquina in maquinas:
                st.write(f"ID: {maquina[0]}, Nombre: {maquina[1]}, ID de Hospital: {maquina[2]}")
        else:
            st.info("No se encontraron máquinas.")
    elif opcion == "Ver Repuestos":
        st.header("Listado de Repuestos")
        repuestos = listar_repuestos()
        if repuestos:
            for repuesto in repuestos:
                st.write(f"ID: {repuesto[0]}, Nombre: {repuesto[1]}, Máquina ID: {repuesto[4]}, Stock: {repuesto[3]}")
        else:
            st.info("No se encontraron repuestos.")
    elif opcion == "Eliminar Hospital":
        st.header("Eliminar Hospital")
        
        hospitales = listar_hospitales()
        if hospitales:
            hospital_seleccionado = st.selectbox("Selecciona un Hospital para eliminar", [h[0] for h in hospitales], 
                                                format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
            if st.button("Eliminar Hospital"):
                eliminar_hospital(hospital_seleccionado)
                st.success(f"Hospital con ID {hospital_seleccionado} ha sido eliminado. Verifica en la lista actualizada.")
        else:
            st.info("No se encontraron hospitales para eliminar.")

    elif opcion == "Eliminar Máquina Manual":
        st.header("Eliminar Máquina Manual")
        maquina_id = st.text_input("Ingresa el ID de la máquina a eliminar")
        
        if st.button("Eliminar Máquina"):
            ejecutar_sql_comando(f"DELETE FROM maquina WHERE id = {maquina_id}")

    elif opcion == "Eliminar Repuesto Manual":
        st.header("Eliminar Repuesto Manual")
        repuesto_id = st.text_input("Ingresa el ID del repuesto a eliminar (solo números)")

        if st.button("Eliminar Repuesto"):
            if repuesto_id.isdigit():
                ejecutar_sql_comando(f"DELETE FROM repuesto WHERE id = {repuesto_id}")
            else:
                st.error("El ID del repuesto debe ser un número.")



# Ejecutar la aplicación
if __name__ == "__main__":
    crear_tablas()  # Crear las tablas la primera vez que se ejecuta
    agregar_columna_ubicacion()  # Agregar la columna 'ubicacion' si no existe
    interfaz_principal()
    
    

