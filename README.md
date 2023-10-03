# Análisis de Datos de Juegos de Steam

Este repositorio contiene múltiples scripts para realizar extracción y transformación de datos crudos extraidos de la plataforma Steam, para luego insertarlos en una base de datos y entrenar un modelo de Machine Learning que genere recomendaciones.

## Prerrequisitos

Los scripts fueron desarrollados con Python 3 v3.8.10, y las siguientes dependendencias, instalables utilizando `pip`:

- [`pandas` v2.0.3](https://pandas.pydata.org/)
- [`tqdm` v4.66.1](https://github.com/tqdm/tqdm)
- [`psycopg2` v2.9.8](https://www.psycopg.org/)

Para comenzar, se deben guardar los archivos crudos `australian_user_reviews.json`, `output_steam_games.json` y `australian_users_items.json` en el directorio [`raw`](./raw).

## Extracción de Datos

El primer paso consiste en preprocesar los archivos JSON del directorio [`raw`](./raw) para transformarlos en archivos CSV que se guardarán en el directorio `preprocesado`. Además de realizar desanidaciones y ajustes menores, aquellos campos que no sean relevantes no serán guardados en los CSV.

```bash
$ python extraccion.py
```

## Analisis de sentimiento

Utilizando el [modelo roBERTa-base para analisis de sentimiento](https://huggingface.co/cardiffnlp/twitter-roberta-base-sentiment), para convertir las reviews del archivo `australian_user_reviews.csv` en  una nueva columna 'sentiment' con el sentimiento de la review de acuerdo a la escala: '0' si es negativo, '1' si es neutro y '2' si es positivo.

```bash
$ python analisis-de-sentimientos.py
```

## Armado y poblado de una base de datos

A partir de los CSVs creados en los pasos anteriores, se pueden crear tablas en una base de datos para realizar consultas.
Con el siguiente script se crean las tablas y se poblan con los datos.
Esto requiere previamente que haya creada una base de datos con nombre `recomendaciones_steam`. Y el usuario y contrasena para la conexion son ambos 'postgres'

Se utilizo [postgreSQl v.12.16](https://www.postgresql.org/) y la libreria [psycopg2](https://pypi.org/project/psycopg2/)

```bash
$ python armado-de-tablas.py
```

Como resultado de este proceso, se obtienen 4 tablas con la siguiente forma:
### Tabla `games`

- `item_id`: primary key
- `item_name`: nombre del juego
- `year_release`: año de lanzamiento, valores sin dato tienen año 0

 Ejemplo:

| item_id | item_name            | year_release|
|  -----  |  ------------------  |  ---------  |
| 761140  | Lost Summoner Kitty  | 2018        |
| 643980  | Ironbound            | 2018        |

### Tabla `game_genres`:

- `item_id`: primary key
- `genre`: genero del juego. Notese que hay solo un genero por fila, por lo que los juegos con mas de un genero, estaran en mas de una fila con el mismo item_id.

Ejemplo:

| item_id | genre  |
|  -----  |  ----  |
| 761140  | Casual |
| 761140  | Action |

### Tabla `reviews`:

- `user_id`: identificador de usuario
- `item_id`: identificador del juego
- `recommend`: booleano que representa si el usuario recomendo (True) el juego o no (False).
- `year_review`: año de publicacion de la review.
- `sentiment`: resultado de la aplicacion del modelo de analisis de sentimiento. Contiene los valores '0' si es negativa, '1' si es neutra y '2' si es positiva.

Ejemplo:

| user_id         | item_id | recommend  | year_review | sentiment|
| ----------------|  -----  |  --------- | ----------- | -------- |
|76561197970982479| 1250    | True       | 2011        |  2       |
| evcentric       | 239030  | True       | 2013        |  2       |


### Tabla `playtime`:

- `user_id`: identificador del usuario
- `item_id`: identificador del juego
- `playtime`: tiempo jugado por el usuario (en minutos).

Ejemplo:

| user_id           | item_id | playtime |
| ----------------- | ------- | -------- |
| 76561197970982479 | 300     | 4733     |
| 76561197970982479 | 240     | 1853     |



## EDA
Se realiza un analisis de los datos, utilizando las librerias: psycopg2, pandas y math.
Las graficas analizadas y sus comentarios se encuentran en un [Jupyter Notebook](pruebas-eda.ipynb).

### Limpieza

A partir de las observaciones fruto del EDA, en el siguiente script se encuentran las modificaciones realizadas a la base de datos y algunas ideas futuras.

```bash
$ python limpieza-de-tablas.py
```

## Recomendador

Con el script `expansion-de-tablas` se crea una tabla auxiliar que contiene los datos que utilizara el recomendador, creada a partir de los datos de las tablas ya existentes en la base de datos.

### Tabla `games_aux`

- `item_id`: identificador del juego, es FOREIGN KEY de la tabla games.
- `overall_sentiment`: relación entre reseñas positivas y la suma de positivas y negativas (ignorando neutras). Un valor de 1 indica que no hay reseñas negativas, y un valor de 0 indica que no hay reseñas positivas. Un valor de 0.5 indica que hay misma cantidad de positivas y negativas.
- `norm_average_playtime`: contiene el logaritmo del promedio de tiempo jugado para cada juego, normalizado respecto al tiempo máximo.

Ejemplo:

| item_id | overall_sentiment | norm_average_playtime|
|  -----  |  ---------------- | -------------------- |
| 10      | 0.80645161290322  | 0.8227510819411121   |
| 20      | 0.63636363636363  | 0.6764002957056057   |

```bash
$ python expansion-de-tablas.py
```

### Funcion Recommend:
Recibe un argumento (identificador de un juego) y entrega 5 juegos similares.
Tiene en cuenta:
- Generos del juego
- Reviews
- El tiempo jugado

Se realiza un primer filtro, importando solo aquellos juegos que compartan al menos un genero con el juego solicitado.
Luego, estos datos se comparan utilizando el modelo de similitud del coseno, se ordenan por orden de similitud descendiente y se entregan los 5 con mayor score.

Se puede ejecutar el recomendador directamente ejecutando `recomendador.py` y pasando un argumento `--item-id`:

```bash
$ python recomendador.py --item-id 10
```

## API
Uitilizando el framework [FastAPI](https://fastapi.tiangolo.com/), se definieron las siguientes consultas para realizar a traves de la API:
- PlayTimeGenre(genero): Rercibe un genero y entrega el año de lanzamiento con más horas jugadas para el género dado.
- UserForGenre(genero): Recibe un genero y entrega el id del usuario con más horas jugadas para el género dado y un listado con las horas jugadas para cada año.
- UsersRecommend(año): Recibe un año y entrega los 3 juegos con más recomendaciones (incluyendo reviews positivas, neutras y que hayan marcado True para 'Recommend').
- UsersNotRecommend(año): Recibe un año y entrega los 3 juegos con más recomendaciones negativas (incluyendo reviewsnegativas y que hayan marcado False para 'Recommend').
- SentimentAnalysis(año): Recibe un año y entrega el numero de reviews positivas, neutras y negativas que se realizaron ese año.
- Recommended(item_id): Recibe un identificador de juego y entrega 5 juegos similares (importando la funcion recommend del scipt [recomendador](recomendador.py))