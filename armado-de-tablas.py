import psycopg2
from psycopg2 import extras
import csv
from tqdm import tqdm

# Vamos a armar una base de datos en postgresql y cargar los datos obtenidos de los CSV preprocesados.

#Establecer la conexion
with psycopg2.connect(dbname="recomendaciones_steam", user="postgres", password="postgres") as conn:
    # Abrir un cursor para poder realizar operaciones de database
    cur = conn.cursor()

    print("Creando tablas")
    cur.execute("CREATE TABLE IF NOT EXISTS games (item_id integer PRIMARY KEY, item_name varchar, year_release integer);")
    cur.execute("CREATE TABLE IF NOT EXISTS game_genres (item_id integer, genre varchar);")
    cur.execute("CREATE TABLE IF NOT EXISTS playtime (user_id varchar, item_id integer, playtime integer);")
    cur.execute("CREATE TABLE IF NOT EXISTS reviews (user_id varchar, item_id integer, recommend boolean, year_review integer, sentiment integer);")

    conn.commit()

    print("Insertando datos en la tabla games")
    with open ('preprocesado/output_steam_games.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), 5000)):
            extras.execute_values(cur, "INSERT INTO games (item_id, item_name, year_release) VALUES %s;", data[n : n + 5000])

    print("Insertando datos en la tabla game_genres")
    with open ('preprocesado/output_steam_game_genres.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), 5000)):
            extras.execute_values(cur, "INSERT INTO game_genres (item_id, genre) VALUES %s;", data[n : n + 5000])
    
    print("Insertando datos en la tabla playtime")    
    with open ('preprocesado/australian_users_items.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), 5000)):
            extras.execute_values(cur, "INSERT INTO playtime (user_id, item_id, playtime) VALUES %s;", data[n : n + 5000])
    
    print("Insertando datos en la tabla reviews")
    with open ('preprocesado/australian_user_reviews.csv') as f:
        data = list(csv.reader(f))[1:]
        for n in tqdm(range(0, len(data), 5000)):
            extras.execute_values(cur, "INSERT INTO reviews (user_id, item_id, recommend, year_review, sentiment) VALUES %s;", data[n : n + 5000])

    print("Insersión completa")
    conn.commit()