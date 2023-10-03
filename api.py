import psycopg2
from fastapi import FastAPI
from recomendador import recomendar_similares
import os

POSTGRES_DBNAME = os.environ['POSTGRES_DBNAME']
POSTGRES_USER = os.environ['POSTGRES_USER']
POSTGRES_PASSWORD = os.environ['POSTGRES_PASSWORD']
POSTGRES_HOST = os.environ['POSTGRES_HOST']

app = FastAPI()

@app.get("/recommended/{item_id}")
def recommended(item_id):
    return { 'recommended': recomendar_similares(item_id) }

# Funcion PlayTimeGenre
@app.get("/playtimegenre/{genero}")
def PlayTimeGenre(genero):
        with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT games.year_release AS anio
                            FROM games JOIN game_genres ON games.item_id = game_genres.item_id
                            JOIN playtime ON games.item_id = playtime.item_id
                            GROUP BY game_genres.genre, anio
                            HAVING genre = %s
                            ORDER by SUM(playtime.playtime) DESC
                            LIMIT 1;''', (genero,))
            
            (anio,) = cur.fetchone()
        return {"Año de lanzamiento con más horas jugadas para el género ": anio}        


# Funcion UserForGenre
@app.get("/userforgenre/{genero}")
def UserForGenre(genero):
        with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT playtime.user_id AS usuario, SUM(playtime.playtime)/60 AS hrs_jugadas
                            FROM (SELECT * FROM game_genres 
                                WHERE genre = %s) as genres
                            JOIN games ON games.item_id = genres.item_id
                            JOIN playtime ON games.item_id = playtime.item_id
                            GROUP BY usuario
                            ORDER BY hrs_jugadas DESC
                            LIMIT 1;''', (genero,))
            
            (usuario, _) = cur.fetchone()

            cur.execute('''SELECT t. anio, t.hrs_jugadas
                            FROM (SELECT playtime.user_id as usuario, games.year_release as anio, SUM(playtime.playtime)/60 AS hrs_jugadas
			                        FROM (SELECT * FROM game_genres 
	 				                WHERE genre = 'Action') as genres
			                    JOIN games ON games.item_id = genres.item_id
                                JOIN playtime ON games.item_id = playtime.item_id
                                GROUP BY usuario, anio) AS t
                            WHERE t.usuario = %s
                            GROUP BY t.usuario, t.anio, t.hrs_jugadas
                            ORDER BY t.anio DESC;''', (usuario,))
            anios_hora_tuplas = cur.fetchall()

            # La query devuelve un array de tuplas (anio, horas). Quiero convertir esto a un diccionario donde las claves son
            # los anios y los valores las horas jugadas.
            horas_por_anio = {}

            for anio_horas in anios_hora_tuplas:
                 horas_por_anio[anio_horas[0]] = anio_horas[1]

        return {'genero': genero, 'usuario': usuario, 'horas_por_anio': horas_por_anio}


# Funcion UsersRecommend
@app.get("/usersrecommend/{anio}")
def UsersRecoommend(anio):
    anio_int = int(anio)
    with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
        cur = conn.cursor()
        cur.execute('''SELECT games.item_name
                        FROM (SELECT item_id, year_review as anio, count(recommend) as recomendaciones, count(sentiment) as sentiment
                                FROM reviews
                                WHERE recommend = True AND sentiment >= 1
                                GROUP BY item_id, year_review) AS r
                        JOIN games ON r.item_id = games.item_id
                        GROUP BY games.item_id, games.item_name, r.anio, r.recomendaciones, r.sentiment
                        HAVING anio = %s
                        ORDER BY r.recomendaciones DESC
                        LIMIT 3;''', (anio_int,))
        
        juegos = cur.fetchall()
        print(juegos)
        (puesto1, ) = juegos[0]
        (puesto2, ) = juegos[1]
        (puesto3, ) = juegos[2]
        
        top3_juegos = {'Puesto 1': puesto1, 'Puesto 2': puesto2, 'Puesto 3': puesto3}

    return {"Los juegos mas recomendados del año": top3_juegos}


# Funcion UsersNotRecommend
@app.get("/usersnotrecommend/{anio}")
def UsersNotRecoommend(anio):
    anio_int = int(anio)
    with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
        cur = conn.cursor()
        cur.execute('''SELECT games.item_name
                        FROM (SELECT item_id, year_review as anio, count(recommend) as recomendaciones, count(sentiment) as sentiment
                                FROM reviews
                                WHERE recommend = False AND sentiment =0
                                GROUP BY item_id, year_review) AS r
                        JOIN games ON r.item_id = games.item_id
                        GROUP BY games.item_id, games.item_name, r.anio, r.recomendaciones, r.sentiment
                        HAVING anio = %s
                        ORDER BY r.recomendaciones DESC
                        LIMIT 3;''', (anio_int,))
        
        juegos = cur.fetchall()
        print(juegos)
        (puesto1, ) = juegos[0]
        (puesto2, ) = juegos[1]
        (puesto3, ) = juegos[2]
        
        top3_juegos = {'Puesto 1': puesto1, 'Puesto 2': puesto2, 'Puesto 3': puesto3}

    return {"Los juegos menos recomendados del año": top3_juegos}


# Funcion SentimentAnalysis
@app.get("/sentimentanalysis/{anio}")
def SentimentAnalysis(anio):
        anio_int = int(anio)
        with psycopg2.connect(dbname=POSTGRES_DBNAME, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST) as conn:
            cur = conn.cursor()
            cur.execute('''SELECT count(r.sentiment) as positivos
                            FROM (SELECT item_id, sentiment
                                    FROM reviews
                                    WHERE sentiment =2) AS r
                            JOIN games ON r.item_id = games.item_id
                            GROUP BY games.year_release
                            HAVING games.year_release =%s;''', (anio_int,))
            (positivas,) = cur.fetchone()
            cur.execute('''SELECT count(r.sentiment) as positivos
                            FROM (SELECT item_id, sentiment
                                    FROM reviews
                                    WHERE sentiment =1) AS r
                            JOIN games ON r.item_id = games.item_id
                            GROUP BY games.year_release
                            HAVING games.year_release =%s;''', (anio_int,))
            (neutras,) = cur.fetchone()
            cur.execute('''SELECT count(r.sentiment) as positivos
                            FROM (SELECT item_id, sentiment
                                    FROM reviews
                                    WHERE sentiment =0) AS r
                            JOIN games ON r.item_id = games.item_id
                            GROUP BY games.year_release
                            HAVING games.year_release =%s;''', (anio_int,))
            (negativas,) = cur.fetchone()
            print(positivas)
        return {"Positivas": positivas, "Neutras": neutras, "Negativas": negativas}