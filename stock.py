<<<<<<< HEAD
import psycopg2
import os
import streamlit as st

# Conectar a la base de datos SQLite
def conectar_db():
    DATABASE_URL = os.getenv("DATABASE_URL") # Render configurará automáticamente esta variable
    conexion = psycopg2.connect(DATABASE_URL)
    return conexion

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
            ubicacion TEXT,
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

# Función para verificar si un hospital ya existe
def verificar_hospital(nombre, ubicacion):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM hospital WHERE nombre = ? AND ubicacion = ?', (nombre, ubicacion))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado > 0

# Función para verificar si una máquina ya existe en el hospital
def verificar_maquina(nombre, hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM maquina WHERE nombre = ? AND hospital_id = ?', (nombre, hospital_id))
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
        cursor.execute('INSERT INTO hospital (nombre, ubicacion) VALUES (?, ?)', (nombre, ubicacion))
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
        cursor.execute('INSERT INTO maquina (nombre, hospital_id) VALUES (?, ?)', (nombre, hospital_id))
        conexion.commit()
        conexion.close()
        st.success(f"Máquina '{nombre}' agregada correctamente.")

# Función para agregar un repuesto a una máquina
def agregar_repuesto(nombre, descripcion, ubicacion, stock, maquina_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO repuesto (nombre, descripcion, ubicacion, stock, maquina_id) VALUES (?, ?, ?, ?, ?)', 
                   (nombre, descripcion, ubicacion, stock, maquina_id))
    conexion.commit()
    conexion.close()

# Función para eliminar un repuesto
def eliminar_repuesto(repuesto_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Verificar si el repuesto existe antes de eliminarlo
        cursor.execute('SELECT * FROM repuesto WHERE id = ?', (repuesto_id,))
        repuesto = cursor.fetchone()
        if not repuesto:
            print(f"El repuesto con ID {repuesto_id} no existe.")
            return

        # Eliminar el repuesto
        cursor.execute('DELETE FROM repuesto WHERE id = ?', (repuesto_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados con ID {repuesto_id}.")

        conexion.commit()
        print(f"Operación de eliminación confirmada en la base de datos.")

    except sqlite3.Error as e:
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
        cursor.execute('SELECT * FROM maquina WHERE id = ?', (maquina_id,))
        maquina = cursor.fetchone()
        if not maquina:
            print(f"La máquina con ID {maquina_id} no existe.")
            return

        # Eliminar todos los repuestos asociados a la máquina
        cursor.execute('DELETE FROM repuesto WHERE maquina_id = ?', (maquina_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados para la máquina con ID {maquina_id}.")

        # Eliminar la máquina
        cursor.execute('DELETE FROM maquina WHERE id = ?', (maquina_id,))
        maquinas_eliminadas = cursor.rowcount
        print(f"{maquinas_eliminadas} máquinas eliminadas con ID {maquina_id}.")

        conexion.commit()
        print("Operación de eliminación confirmada en la base de datos.")

    except sqlite3.Error as e:
        print(f"Error durante la eliminación de la máquina: {e}")
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
    except sqlite3.Error as e:
        print(f"Error ejecutando el comando: {e}")
    finally:
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

# Función para registrar una salida de stock
def registrar_salida(repuesto_id, cantidad):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('UPDATE repuesto SET stock = stock - ? WHERE id = ?', (cantidad, repuesto_id))
    cursor.execute('INSERT INTO movimiento_stock (repuesto_id, cantidad, tipo, fecha) VALUES (?, ?, "salida", date("now"))', 
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

# Función para buscar un repuesto por nombre y mostrar dónde está
def buscar_repuesto(nombre_repuesto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT repuesto.nombre, repuesto.descripcion, repuesto.ubicacion, repuesto.stock, maquina.nombre, hospital.nombre
        FROM repuesto
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
        WHERE repuesto.nombre LIKE ?
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
        cursor.execute('SELECT * FROM hospital WHERE id = ?', (hospital_id,))
        hospital = cursor.fetchone()
        if not hospital:
            print(f"El hospital con ID {hospital_id} no existe.")
            return

        # Eliminar el hospital
        cursor.execute('DELETE FROM hospital WHERE id = ?', (hospital_id,))
        print(f"Hospital con ID {hospital_id} eliminado.")

        conexion.commit()
        print(f"El hospital ha sido eliminado correctamente.")
        
    except sqlite3.Error as e:
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

# Interfaz con Streamlit
def interfaz_principal():
    st.title("Gestión de Extra-Stock de Repuestos")

    # Pestañas para las diferentes funcionalidades
    opcion = st.sidebar.selectbox("Selecciona una opción", ["Ver Stock", "Buscar Repuesto", "Registrar Entrada", "Registrar Salida", 
                                                            "Ver Repuestos", "Ver Hospitales", "Agregar Hospital", 
                                                            "Ver Maquinas", "Agregar Máquina",  
                                                             "Ver Máquinas por Hospital", 
                                                             "Eliminar Repuesto", 
                                                            "Eliminar Máquina", "Eliminar Hospital", "Eliminar Máquina Manual", "Eliminar Repuesto Manual"])
                                                            

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

    elif opcion == "Registrar Salida":
        st.header("Registrar Salida de Stock")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        maquina_id = st.selectbox("Selecciona una Máquina", [m[0] for m in maquinas], format_func=lambda x: dict(maquinas)[x])
        
        repuestos = obtener_repuestos(maquina_id)
        repuesto_nombre = st.selectbox("Selecciona un Repuesto", [r[1] for r in repuestos])
        repuesto_id = dict((r[1], r[0]) for r in repuestos)[repuesto_nombre]
        
        cantidad = st.number_input("Cantidad a Sacar", min_value=1)
        if st.button("Registrar Salida"):
            registrar_salida(repuesto_id, cantidad)
            st.success(f"Salida de {cantidad} unidades registrada para el repuesto '{repuesto_nombre}'.")

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
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        
        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        if maquinas:
            # Mostrar menú desplegable de máquinas con nombre y ID
            maquina_seleccionada = st.selectbox("Selecciona una Máquina para eliminar", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
            
            # Extraer el ID de la máquina seleccionada
            maquina_id = maquina_seleccionada[0]

            if st.button(f"Eliminar Máquina '{maquina_seleccionada[1]}'"):
                st.warning(f"Estás a punto de eliminar la máquina '{maquina_seleccionada[1]}' y todos sus repuestos. Confirma la eliminación.")
                
                if st.button(f"Confirmar eliminación de la máquina '{maquina_seleccionada[1]}'"):
                    eliminar_maquina(maquina_id)
                    st.success(f"Máquina '{maquina_seleccionada[1]}' eliminada correctamente junto con todos sus repuestos.")

                    # Refrescar la lista de máquinas después de la eliminación
                    maquinas_actualizadas = obtener_maquinas(hospital_id)
                    if not maquinas_actualizadas:
                        st.info(f"No quedan máquinas en el hospital seleccionado.")
                    else:
                        st.write("Máquinas restantes:")
                        for maquina in maquinas_actualizadas:
                            st.write(f"Máquina: {maquina[1]}")
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
            st.write(f"Repuesto: {repuesto[0]} | Descripción: {repuesto[1]} | Ubicación: {repuesto[2]} | Stock: {repuesto[3]}")

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
    interfaz_principal()
    port=int(os.environ.get('PORT', 8501))
    st.run(host='0.0.0.0', port=port)
    

=======
import psycopg2
import os
import streamlit as st

# Conectar a la base de datos SQLite
def conectar_db():
    DATABASE_URL = os.getenv("DATABASE_URL") # Render configurará automáticamente esta variable
    conexion = psycopg2.connect(DATABASE_URL)
    return conexion

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
            ubicacion TEXT,
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

# Función para verificar si un hospital ya existe
def verificar_hospital(nombre, ubicacion):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM hospital WHERE nombre = ? AND ubicacion = ?', (nombre, ubicacion))
    resultado = cursor.fetchone()[0]
    conexion.close()
    return resultado > 0

# Función para verificar si una máquina ya existe en el hospital
def verificar_maquina(nombre, hospital_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('SELECT COUNT(*) FROM maquina WHERE nombre = ? AND hospital_id = ?', (nombre, hospital_id))
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
        cursor.execute('INSERT INTO hospital (nombre, ubicacion) VALUES (?, ?)', (nombre, ubicacion))
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
        cursor.execute('INSERT INTO maquina (nombre, hospital_id) VALUES (?, ?)', (nombre, hospital_id))
        conexion.commit()
        conexion.close()
        st.success(f"Máquina '{nombre}' agregada correctamente.")

# Función para agregar un repuesto a una máquina
def agregar_repuesto(nombre, descripcion, ubicacion, stock, maquina_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('INSERT INTO repuesto (nombre, descripcion, ubicacion, stock, maquina_id) VALUES (?, ?, ?, ?, ?)', 
                   (nombre, descripcion, ubicacion, stock, maquina_id))
    conexion.commit()
    conexion.close()

# Función para eliminar un repuesto
def eliminar_repuesto(repuesto_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        # Verificar si el repuesto existe antes de eliminarlo
        cursor.execute('SELECT * FROM repuesto WHERE id = ?', (repuesto_id,))
        repuesto = cursor.fetchone()
        if not repuesto:
            print(f"El repuesto con ID {repuesto_id} no existe.")
            return

        # Eliminar el repuesto
        cursor.execute('DELETE FROM repuesto WHERE id = ?', (repuesto_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados con ID {repuesto_id}.")

        conexion.commit()
        print(f"Operación de eliminación confirmada en la base de datos.")

    except sqlite3.Error as e:
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
        cursor.execute('SELECT * FROM maquina WHERE id = ?', (maquina_id,))
        maquina = cursor.fetchone()
        if not maquina:
            print(f"La máquina con ID {maquina_id} no existe.")
            return

        # Eliminar todos los repuestos asociados a la máquina
        cursor.execute('DELETE FROM repuesto WHERE maquina_id = ?', (maquina_id,))
        repuestos_eliminados = cursor.rowcount
        print(f"{repuestos_eliminados} repuestos eliminados para la máquina con ID {maquina_id}.")

        # Eliminar la máquina
        cursor.execute('DELETE FROM maquina WHERE id = ?', (maquina_id,))
        maquinas_eliminadas = cursor.rowcount
        print(f"{maquinas_eliminadas} máquinas eliminadas con ID {maquina_id}.")

        conexion.commit()
        print("Operación de eliminación confirmada en la base de datos.")

    except sqlite3.Error as e:
        print(f"Error durante la eliminación de la máquina: {e}")
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
    except sqlite3.Error as e:
        print(f"Error ejecutando el comando: {e}")
    finally:
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

# Función para registrar una salida de stock
def registrar_salida(repuesto_id, cantidad):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('UPDATE repuesto SET stock = stock - ? WHERE id = ?', (cantidad, repuesto_id))
    cursor.execute('INSERT INTO movimiento_stock (repuesto_id, cantidad, tipo, fecha) VALUES (?, ?, "salida", date("now"))', 
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

# Función para buscar un repuesto por nombre y mostrar dónde está
def buscar_repuesto(nombre_repuesto):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute('''
        SELECT repuesto.nombre, repuesto.descripcion, repuesto.ubicacion, repuesto.stock, maquina.nombre, hospital.nombre
        FROM repuesto
        JOIN maquina ON repuesto.maquina_id = maquina.id
        JOIN hospital ON maquina.hospital_id = hospital.id
        WHERE repuesto.nombre LIKE ?
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
        cursor.execute('SELECT * FROM hospital WHERE id = ?', (hospital_id,))
        hospital = cursor.fetchone()
        if not hospital:
            print(f"El hospital con ID {hospital_id} no existe.")
            return

        # Eliminar el hospital
        cursor.execute('DELETE FROM hospital WHERE id = ?', (hospital_id,))
        print(f"Hospital con ID {hospital_id} eliminado.")

        conexion.commit()
        print(f"El hospital ha sido eliminado correctamente.")
        
    except sqlite3.Error as e:
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

# Interfaz con Streamlit
def interfaz_principal():
    st.title("Gestión de Extra-Stock de Repuestos")

    # Pestañas para las diferentes funcionalidades
    opcion = st.sidebar.selectbox("Selecciona una opción", ["Ver Stock", "Buscar Repuesto", "Registrar Entrada", "Registrar Salida", 
                                                            "Ver Repuestos", "Ver Hospitales", "Agregar Hospital", 
                                                            "Ver Maquinas", "Agregar Máquina",  
                                                             "Ver Máquinas por Hospital", 
                                                             "Eliminar Repuesto", 
                                                            "Eliminar Máquina", "Eliminar Hospital", "Eliminar Máquina Manual", "Eliminar Repuesto Manual"])
                                                            

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

    elif opcion == "Registrar Salida":
        st.header("Registrar Salida de Stock")
        hospitales = obtener_hospitales()
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        maquinas = obtener_maquinas(hospital_id)
        maquina_id = st.selectbox("Selecciona una Máquina", [m[0] for m in maquinas], format_func=lambda x: dict(maquinas)[x])
        
        repuestos = obtener_repuestos(maquina_id)
        repuesto_nombre = st.selectbox("Selecciona un Repuesto", [r[1] for r in repuestos])
        repuesto_id = dict((r[1], r[0]) for r in repuestos)[repuesto_nombre]
        
        cantidad = st.number_input("Cantidad a Sacar", min_value=1)
        if st.button("Registrar Salida"):
            registrar_salida(repuesto_id, cantidad)
            st.success(f"Salida de {cantidad} unidades registrada para el repuesto '{repuesto_nombre}'.")

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
        hospital_id = st.selectbox("Selecciona un Hospital", [h[0] for h in hospitales], format_func=lambda x: dict((h[0], f"{h[1]} - {h[2]}") for h in hospitales)[x])
        
        # Obtener las máquinas asociadas al hospital seleccionado
        maquinas = obtener_maquinas(hospital_id)
        if maquinas:
            # Mostrar menú desplegable de máquinas con nombre y ID
            maquina_seleccionada = st.selectbox("Selecciona una Máquina para eliminar", maquinas, format_func=lambda x: f"ID: {x[0]} | Máquina: {x[1]}")
            
            # Extraer el ID de la máquina seleccionada
            maquina_id = maquina_seleccionada[0]

            if st.button(f"Eliminar Máquina '{maquina_seleccionada[1]}'"):
                st.warning(f"Estás a punto de eliminar la máquina '{maquina_seleccionada[1]}' y todos sus repuestos. Confirma la eliminación.")
                
                if st.button(f"Confirmar eliminación de la máquina '{maquina_seleccionada[1]}'"):
                    eliminar_maquina(maquina_id)
                    st.success(f"Máquina '{maquina_seleccionada[1]}' eliminada correctamente junto con todos sus repuestos.")

                    # Refrescar la lista de máquinas después de la eliminación
                    maquinas_actualizadas = obtener_maquinas(hospital_id)
                    if not maquinas_actualizadas:
                        st.info(f"No quedan máquinas en el hospital seleccionado.")
                    else:
                        st.write("Máquinas restantes:")
                        for maquina in maquinas_actualizadas:
                            st.write(f"Máquina: {maquina[1]}")
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
            st.write(f"Repuesto: {repuesto[0]} | Descripción: {repuesto[1]} | Ubicación: {repuesto[2]} | Stock: {repuesto[3]}")

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
    st.run(port=8501, host='0.0.0.0')
    crear_tablas()  # Crear las tablas la primera vez que se ejecuta
    interfaz_principal()
    

>>>>>>> 8acf24affc182c0d9512e1dd8a34ce3f9fc52abb
