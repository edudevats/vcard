"""
Script para migrar datos de crm.db a app.db
Tablas: user, theme, service, product, gallery_item, card_view, card
"""
import sqlite3
import os

def migrate_data():
    # Rutas a las bases de datos
    source_db = 'instance/crm.db'
    target_db = 'instance/app.db'

    if not os.path.exists(source_db):
        print(f"Error: {source_db} no existe")
        return

    if not os.path.exists(target_db):
        print(f"Error: {target_db} no existe")
        return

    # Conectar a ambas bases de datos
    source_conn = sqlite3.connect(source_db)
    target_conn = sqlite3.connect(target_db)

    source_conn.row_factory = sqlite3.Row
    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    # Tablas en orden de dependencias (user y theme primero, card al final)
    tables_order = ['user', 'theme', 'card', 'service', 'product', 'gallery_item', 'card_view']

    try:
        for table in tables_order:
            print(f"\n--- Procesando tabla: {table} ---")

            # Obtener nombres de columnas de la tabla origen
            source_cursor.execute(f"PRAGMA table_info({table})")
            columns_info = source_cursor.fetchall()

            if not columns_info:
                print(f"Advertencia: Tabla {table} no existe en crm.db")
                continue

            column_names = [col[1] for col in columns_info]

            # Obtener todos los datos de la tabla origen
            source_cursor.execute(f"SELECT * FROM {table}")
            rows = source_cursor.fetchall()

            if not rows:
                print(f"Tabla {table} está vacía en crm.db")
                continue

            print(f"Encontradas {len(rows)} filas en {table}")

            # Verificar si la tabla existe en app.db
            target_cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
            if not target_cursor.fetchone():
                print(f"Advertencia: Tabla {table} no existe en app.db, saltando...")
                continue

            # Obtener columnas de la tabla destino
            target_cursor.execute(f"PRAGMA table_info({table})")
            target_columns_info = target_cursor.fetchall()
            target_column_names = [col[1] for col in target_columns_info]

            # Encontrar columnas comunes
            common_columns = [col for col in column_names if col in target_column_names]

            if not common_columns:
                print(f"Error: No hay columnas comunes entre origen y destino para {table}")
                continue

            print(f"Columnas a migrar: {', '.join(common_columns)}")

            # Limpiar tabla destino antes de insertar (opcional, comentar si no se desea)
            # target_cursor.execute(f"DELETE FROM {table}")
            # print(f"Tabla {table} limpiada en app.db")

            # Insertar datos
            inserted = 0
            skipped = 0

            for row in rows:
                # Construir diccionario con valores de columnas comunes
                values = [row[column_names.index(col)] for col in common_columns]

                placeholders = ','.join(['?' for _ in common_columns])
                columns_str = ','.join(common_columns)

                query = f"INSERT OR IGNORE INTO {table} ({columns_str}) VALUES ({placeholders})"

                try:
                    target_cursor.execute(query, values)
                    if target_cursor.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except sqlite3.IntegrityError as e:
                    print(f"Error de integridad en {table}: {e}")
                    skipped += 1
                except Exception as e:
                    print(f"Error insertando en {table}: {e}")
                    skipped += 1

            target_conn.commit()
            print(f"OK {table}: {inserted} filas insertadas, {skipped} filas omitidas")

        print("\n=== Migración completada ===")

        # Mostrar resumen
        print("\n--- Resumen de registros en app.db ---")
        for table in tables_order:
            try:
                target_cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = target_cursor.fetchone()[0]
                print(f"{table}: {count} registros")
            except:
                print(f"{table}: Tabla no existe")

    except Exception as e:
        print(f"Error durante la migración: {e}")
        target_conn.rollback()

    finally:
        source_conn.close()
        target_conn.close()

if __name__ == '__main__':
    print("=== Iniciando migración de datos ===")
    print("Origen: instance/crm.db")
    print("Destino: instance/app.db")
    print("\nEste script migrará las siguientes tablas:")
    print("- user")
    print("- theme")
    print("- card")
    print("- service")
    print("- product")
    print("- gallery_item")
    print("- card_view")
    print()
    migrate_data()
