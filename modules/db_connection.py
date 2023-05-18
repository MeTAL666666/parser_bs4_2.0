import psycopg2
from psycopg2 import Error
from configparser import ConfigParser as cp
from typing import Dict
import os
'''
Описание функций:
create_connection_info() - создание конфиг файла для подключения к БД
load_connection_info() - загрузка информации из файла для подключения к БД
create_db() - создание БД
create_table() - создание таблиц
delete_table() - удаление таблиц
main() - основная функция
'''
#Работа с конфиг-файлом для подключения к БД
conn_config = cp()
ini_path = os.getcwd() + "/files/"
ini_filename = os.getcwd() + "/files/db_connection.ini"

# Функция для создания файла поключения при его отсутствии
def create_connection_info(ini_filename):
    conn_config = cp()
    conn_config['postgresql'] = {'host': 'localhost',
                                'database': 'parser',
                                'user': 'postgres',
                                'password':'1'}
    if not os.path.exists(ini_path):
        os.mkdir(ini_path)
    with open(ini_filename, "w") as i_f:
        conn_config.write(i_f)

def load_connection_info(
    ini_filename: str
) -> Dict[str, str]:
    conn_config.read(ini_filename)
    conn_info = {param[0]: param[1] for param in conn_config.items("postgresql")}
    return conn_info

def create_db(
    conn_info: Dict[str, str],
) -> None:
    psql_connection_string = f"user={conn_info['user']} password={conn_info['password']}"
    conn = psycopg2.connect(psql_connection_string)
    cur = conn.cursor()

    conn.autocommit = True
    sql_query = f"CREATE DATABASE {conn_info['database']}"

    try:
        cur.execute(sql_query)
    except Exception as e:
        cur.close()
    else:
        conn.autocommit = False


def create_table(
    sql_query: str, 
    conn: psycopg2.extensions.connection, 
    cur: psycopg2.extensions.cursor
) -> None:
    try:
        cur.execute(sql_query)
    except Exception as e:
        conn.rollback()
    else:
        conn.commit()

def delete_table(
    sql_query: str, 
    conn: psycopg2.extensions.connection, 
    cur: psycopg2.extensions.cursor
) -> None:
    try:
        cur.execute(sql_query)
    except Exception as e:
        conn.rollback()
    else:
        conn.commit()


def main():
    try:
        conn_info = load_connection_info(ini_filename)
    except:
        create_connection_info(ini_filename)
        conn_info = load_connection_info(ini_filename)
    # Создание БД
    create_db(conn_info)

    # Подключение к БД
    connection = psycopg2.connect(**conn_info)
    cursor = connection.cursor()
    # Выполнение SQL-запроса
    cursor.execute("SELECT version();")
    # Получить результат
    record = cursor.fetchone()
    print("Вы подключены к - ", record, "\n")
    
    delete_avito_sql = """
        DELETE FROM avito
    """
    delete_table(delete_avito_sql, connection, cursor)


    # Создание таблицы «avito»
    avito_sql = """
        CREATE TABLE avito (
            Id_объявления BIGINT PRIMARY KEY,
            Размещено CHARACTER VARYING(60),
            Название CHARACTER VARYING(300),
            Текст TEXT,
            Цена BIGINT,
            Рыночная_цена CHARACTER VARYING(350),
            Примечание CHARACTER VARYING(200),
            Телефон CHARACTER VARYING(60),
            Адрес CHARACTER VARYING(300),
            Категория CHARACTER VARYING(300),
            Фото CHARACTER VARYING(250),
            Ссылка CHARACTER VARYING(200),
            Продавец CHARACTER VARYING(300)
        )
    """
    create_table(avito_sql, connection, cursor)


    # Создание таблицы «bazarpnz»
    bazarpnz_sql = """
        CREATE TABLE bazarpnz (
            Id_объявления BIGINT PRIMARY KEY,
            Размещено DATE,
            Название CHARACTER VARYING(300),
            Текст TEXT,
            Цена BIGINT,
            Телефон CHARACTER VARYING(30),
            Адрес CHARACTER VARYING(300),
            Категория CHARACTER VARYING(300),
            Фото CHARACTER VARYING(250),
            Ссылка CHARACTER VARYING(200),
            Продавец CHARACTER VARYING(300)
        )
    """
    create_table(bazarpnz_sql, connection, cursor)

    return (connection, cursor)