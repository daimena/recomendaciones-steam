import json
import pandas as pd
import re
import ast
from tqdm import tqdm

def extraccion_reviews():
    ARCHIVO_FUENTE = "raw/australian_user_reviews.json"
    ARCHIVO_DESTINO = "preprocesado/australian_user_reviews.csv"

    print("Cargando", ARCHIVO_FUENTE)

    # El archivo australian_user_reviews.json no respeta el formato JSON, sino que contiene lineas que se corresponden con
    # diccionarios de python. Por eso usamos ast.literal_eval para cargar cada línea.

    users_reviews = []
    with open(ARCHIVO_FUENTE) as f:
        for line in tqdm(f.readlines()):
            users_reviews.append(ast.literal_eval(line))

    # Las reviews están agrupadas por usuario en una sola fila, por lo que las desanidamos para generar una fila por cada
    # review.

    print("Extrayendo reviews")

    reviews = []
    for user_reviews in tqdm(users_reviews):
        for review in user_reviews['reviews']:
            reviews.append([
                user_reviews['user_id'],
                review['item_id'],
                review['posted'],
                review['recommend'],
                review['review']
            ])

    reviews = pd.DataFrame(reviews, columns=['user_id', 'item_id', 'posted', 'recommend', 'review'])

    # El campo 'posted' tiene la fecha de publicación, pero sólo nos interesa el año. Definimos una función que lo extrae.

    def extraer_año(fecha):
        # Las fechas vienen en un formato del estilo 'Posted: July 15, 2013.'. Las fechas del año del dataset (2016) no
        # incluyen el año (por ejemplo, 'Posted: March 23.'). Usamos una expresión regular para extraer el año.
        result = re.search("\w* \d*, (\d*)", fecha)
        if result is not None:
            return int(result.group(1))
        else:
            return 2016

    print("Extrayendo el año de publicación")

    # Reemplazamos la columna 'posted' con una nueva columna 'year'.
    reviews['year'] = reviews.apply(lambda f: extraer_año(f['posted']), axis=1)
    reviews.drop(columns=['posted'], inplace=True)

    reviews.to_csv(ARCHIVO_DESTINO, index=False)

    print("Entidad reviews guardada en", ARCHIVO_DESTINO)

def extraccion_games():
    ARCHIVO_FUENTE = "raw/output_steam_games.json"
    ARCHIVO_DESTINO_JUEGOS = "preprocesado/output_steam_games.csv"
    ARCHIVO_DESTINO_GENEROS = "preprocesado/output_steam_game_genres.csv"

    print("Cargando", ARCHIVO_FUENTE)

    # El archivo output_steam_games.json no respeta el formato JSON, sino que contiene lineas que se corresponden con
    # diccionarios de python. Por eso usamos ast.literal_eval para cargar cada línea.
    games = []
    with open(ARCHIVO_FUENTE) as f:
        for line in tqdm(f.readlines()):
          games.append(json.loads(line))

    # Eventualmente podríamos usar el score de metacritic, los tags, el developer, etc. para mejorar el sistema de
    # recomendaciones, pero por ahora sólo usamos los géneros.
    games = pd.DataFrame(games, columns=['id', 'app_name', 'release_date', 'genres'])
    games.dropna(how='all', inplace=True)
    games.dropna(subset='id', inplace=True)
    games.drop_duplicates(keep='first', subset=['id'], inplace=True)

    # El campo 'release_date' tiene la fecha de publicación, pero sólo nos interesa el áño. Definimos una función que lo
    # extrae
    def extraer_año(date):
        # La fecha de publicación está en formato YYYY-MM-DD. Extraemos el año con una expresión regular
        try:
            result = re.search("(\d*)-\d*-\d*", date)
            return int(result.group(1))
        except:
            # No todos los juegos tienen fecha de publicación, para estos usamos el valor centinela 0 que indica año desconocido
            return 0

    print("Extrayendo el año de publicación")

    # Reemplazamos la columna 'release_date' con una nueva columna 'year'.
    games['year'] = games.apply(lambda f: extraer_año(f['release_date']), axis=1)
    games.drop(columns=['release_date'], inplace=True)

    print("Extrayendo géneros de cada juego")

    # Cada juego tiene múltiples géneros. Queremos separar esto para tener una tabla auxiliar donde cada fila indica
    # un género de un juego.
    games_genres = games[['id', 'genres']]
    games_genres = games_genres.dropna(how='any')
    games_genres = games_genres.explode('genres')
    games_genres.drop_duplicates(keep='first', inplace=True)

    # Como game_genres ya tiene los géneros de cada juego, los podemos sacar de la entidad games.
    games.drop(columns=['genres'], inplace=True)

    games.to_csv(ARCHIVO_DESTINO_JUEGOS, index=False)
    print("Entidad games guardada en", ARCHIVO_DESTINO_JUEGOS)

    games_genres.to_csv(ARCHIVO_DESTINO_GENEROS, index=False)
    print("Entidad genres guardada en", ARCHIVO_DESTINO_GENEROS)

def extraccion_items():
    ARCHIVO_FUENTE = "raw/australian_users_items.json"
    ARCHIVO_DESTINO = "preprocesado/australian_users_items.csv"

    print("Cargando", ARCHIVO_FUENTE)

    # El archivo australian_users_items.json no respeta el formato JSON, sino que contiene lineas que se corresponden con
    # diccionarios de python. Por eso usamos ast.literal_eval para cargar cada línea.

    users_items = []
    with open("raw/australian_users_items.json") as f:
      for line in tqdm(f.readlines()):
          users_items.append(ast.literal_eval(line))

    print("Extrayendo items")

    items = []
    for user_items in tqdm(users_items):
        for item in user_items['items']:
            items.append({
                'user_id': user_items['user_id'],
                'item_id': item['item_id'],
                'playtime_forever': item['playtime_forever']
            })

    items = pd.DataFrame(items, columns=['user_id', 'item_id', 'playtime_forever'])
    items.drop_duplicates(keep='first', inplace=True)

    items.to_csv(ARCHIVO_DESTINO, index=False)
    print("Entidad items guardada en", ARCHIVO_DESTINO)

#extraccion_reviews()
extraccion_games()
extraccion_items()
