import psycopg2
from psycopg2 import extras
import csv
from tqdm import tqdm
import argparse

parser = argparse.ArgumentParser(description='Creación y poblado de tablas')
parser.add_argument('--dbname', help='nombre de la base de datos', default='recomendaciones_steam')
parser.add_argument('--user', help='nombre de usuario en la base de datos', default='postgres')
parser.add_argument('--password', help='contraseña en la base de datos', default='postgres')
parser.add_argument('--host', help='dirección del host', default='localhost')
parser.add_argument('--port', help='puerto del host', default=5432)
args = parser.parse_args()

# Vamos a armar una base de datos en postgresql y cargar los datos obtenidos de los CSV preprocesados.

#Establecer la conexion
with psycopg2.connect(dbname=args.dbname, user=args.user, password=args.password, host=args.host, port=args.port) as conn:
    BATCH_SIZE = 20000

    # Abrir un cursor para poder realizar operaciones de database
    cur = conn.cursor()

    print("Creando tablas")
    cur.execute("CREATE TABLE games (item_id integer PRIMARY KEY, item_name varchar, year_release integer);")
    cur.execute("CREATE TABLE game_genres (item_id integer, genre varchar);")
    cur.execute("CREATE TABLE playtime (user_id varchar, item_id integer, playtime integer);")
    cur.execute("CREATE TABLE reviews (user_id varchar, item_id integer, recommend boolean, year_review integer, sentiment integer);")

    conn.commit()

    print("Insertando datos en la tabla games")
    with open ('preprocesado/output_steam_games.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), BATCH_SIZE)):
            extras.execute_values(cur, "INSERT INTO games (item_id, item_name, year_release) VALUES %s;", data[n : n + BATCH_SIZE], page_size=BATCH_SIZE * 5)

    print("Insertando datos en la tabla game_genres")
    with open ('preprocesado/output_steam_game_genres.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), BATCH_SIZE)):
            extras.execute_values(cur, "INSERT INTO game_genres (item_id, genre) VALUES %s;", data[n : n + BATCH_SIZE], page_size=BATCH_SIZE * 5)
    
    print("Insertando datos en la tabla playtime")    
    with open ('preprocesado/australian_users_items.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), BATCH_SIZE)):
            extras.execute_values(cur, "INSERT INTO playtime (user_id, item_id, playtime) VALUES %s;", data[n : n + BATCH_SIZE], page_size=BATCH_SIZE * 5)
    
    print("Insertando datos en la tabla reviews")
    with open ('preprocesado/australian_user_reviews.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), BATCH_SIZE)):
            extras.execute_values(cur, "INSERT INTO reviews (user_id, item_id, recommend, year_review, sentiment) VALUES %s;", data[n : n + BATCH_SIZE], page_size=BATCH_SIZE * 5)

    print("Insersión completa")
    conn.commit()