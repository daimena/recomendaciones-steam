import psycopg2
from psycopg2 import extras
import csv
from tqdm import tqdm

with psycopg2.connect(dbname="recomendaciones_steam", user="postgres", password="postgres") as conn:
    cur = conn.cursor()

    print("Creando nuevas tablas auxiliares")
    cur.execute("CREATE TABLE IF NOT EXISTS games_aux (item_id integer REFERENCES games, overall_review_sentiment float, norm_average_playtime float);")

    conn.commit()

    # La columna overall_review_sentiment contiene la relación entre reseñas positivas y la suma de positivas y negativas (ignorando neutras). Un valor de 1
    # indica que no hay reseñas negativas, y un valor de 0 indica que no hay reseñas positivas. Un valor de 0.5 indica que hay misma cantidad de positivas y
    # negativas.
    # La columna norm_average_playtime contiene el promedio de tiempo jugado para cada juego, normalizado respecto al tiempo máximo. Notar que tiempos de juego
    # insignificantes ya han sido removidos de la tabla. Tiempos outliers superiores a 200 horas se acotan a un valor maximo de 200 horas. Para normalizar,
    # trabajamos con el logaritmo de los tiempos de juego debido a la naturaleza del histograma de tiempos de juego.

    print("Insertando datos en tablas")
    cur.execute('''
        INSERT INTO games_aux (item_id, overall_review_sentiment, norm_average_playtime)
        SELECT sent.item_id AS item_id, sent.overall_review_sentiment AS overall_review_sentiment, play.norm_average_playtime AS norm_average_playtime
        FROM
        (
            SELECT t.item_id, (t.positive * 1.0)/(t.positive+t.negative) AS overall_review_sentiment
                FROM(
                    SELECT COALESCE(pos.item_id, neg.item_id) AS item_id, COALESCE(neg.negative, 0) AS negative, COALESCE(pos.positive, 0) AS positive
                    FROM 
                        (SELECT item_id, COUNT(item_id) AS negative FROM reviews WHERE sentiment = 0 GROUP BY item_id) AS neg 
                    FULL JOIN
                        (SELECT item_id, COUNT(item_id) AS positive FROM reviews WHERE sentiment = 2 GROUP BY item_id) AS pos 
                    ON neg.item_id = pos.item_id
                ) AS t
        ) AS sent
        JOIN
        (
            SELECT p.item_id, p.average / MAX(p.average) OVER () AS norm_average_playtime
            FROM (
                SELECT item_id, LOG(AVG(LEAST(playtime, 200 * 60))) AS average 
                FROM playtime 
                GROUP BY item_id
            ) AS p
        ) AS play
        ON sent.item_id = play.item_id;
    ''')

    print("Insersión completa")
    conn.commit()