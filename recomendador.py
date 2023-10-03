import psycopg2
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import argparse
import os

POSTGRES_DBNAME = os.environ['POSTGRES_DBNAME']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_HOST = os.environ['POSTGRES_HOST']

def recomendar_similares(item_id):
    item_id = int(item_id)

    # Vamos a realizar un analisis de similitud utilizando los géneros de los juegos, el sentimiento global
    # obtenido de las reviews, y el tiempo de juego promedio.

    df = pd.DataFrame(get_candidatos(item_id), columns=['item_id', 'genre', 'sentiment', 'playtime'])

    # Utilizamos One Hot Encoding para crear nuevas columnas por cada género, de modo que se pueda realizar
    # el análisis de comparación por similitud de coseno.
    df = one_hot_encoding(df, 'genre').groupby(['item_id', 'sentiment', 'playtime']).any().reset_index()
    df.set_index('item_id', inplace=True)

    df['similitud'] = calcular_similitud(df, item_id)
    
    # Una vez que tenemos la columna de similitud, eliminamos la entrada correspondiente al juego requerido
    # (la cual debería tener similitud de 1), y tomamos las siguiente 5 mayores.
    
    df = df.drop([item_id]).nlargest(5, columns='similitud')
    item_ids = [int(id) for id in df.index]

    # Conociendo ya los juegos más similares, podemos traer el resto de información relevante acerca de ellos
    # (nombre, año de publicación, etc.).
    return get_games_metadata((item_ids))

def get_candidatos(item_id):
    # Necesitamos obtener la información relevante de los juegos para poder realizar una comparación por
    # similitud. Sin embargo, para evitar procesar el dataset entero realizamos un prefiltrado de modo que
    # sólo sean considerados aquellos juegos que comparten al menos un género con el juego objetivo.
    # Nótese que no todos los juegos tienen reviews o playtime, pero estos valores son requeridos por el
    # modelo. En caso de faltar, colocamos el valor 0.
    with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT candidatos.item_id,  game_genres.genre, COALESCE(games_aux.overall_review_sentiment, 0), COALESCE(games_aux.norm_average_playtime, 0)
            FROM (
                SELECT item_id
                FROM game_genres
                WHERE 
                    genre IN (
                        SELECT genre from game_genres WHERE item_id = %s
                    )
                GROUP BY item_id
            ) AS candidatos
            LEFT JOIN game_genres
                ON candidatos.item_id = game_genres.item_id
            LEFT JOIN games_aux
                ON candidatos.item_id = games_aux.item_id;
            ''', (item_id,))

    return cur.fetchall()

def one_hot_encoding(df, columna):
    dummies = pd.get_dummies(df[columna])
    combine = pd.concat([df, dummies], axis=1)
    return combine.drop(columns=[columna])

def calcular_similitud(df, item_id):
    input = df.loc[item_id].values.reshape(1, -1)
    return df.apply(lambda f: cosine_similarity(f.values.reshape(1, -1), input)[0][0], axis=1)

def get_games_metadata(item_ids):
    with psycopg2.connect(dbname="recomendaciones_steam", user="postgres", password="postgres") as conn:
        cur = conn.cursor()
        cur.execute('''
            SELECT item_name
            FROM games
            WHERE item_id = ANY(%s)
            ''', (item_ids,))

    return [name for (name,) in cur.fetchall()]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recomendado de juegos')
    parser.add_argument('--item-id', help='ID del juego', required=True)
    args = parser.parse_args()
    print(recomendar_similares(args.item_id))