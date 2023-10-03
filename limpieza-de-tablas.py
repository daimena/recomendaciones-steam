import psycopg2

with psycopg2.connect(dbname="recomendaciones_steam", user="postgres", password="postgres") as conn:
    cur = conn.cursor()

    # En la tabla playtime hay muchas entradas con duración de jugado 0. Esto probablemente se debe a que
    # muchos usuarios son regalados juegos, o los adquieren en bundles, y nunca los juegan. Eliminamos
    # esta información por no ser relevante.
    # Además, eliminamos entradas de playtime de duración menor a 60 minutos, por considerar similarmente
    # que no son relevantes para un analisis estadístico de duración de juego (teniendo en cuenta valores 
    # estandar de tiempo de jugado).
    
    print("Eliminando entradas con tiempo de juego menor a 60 minutos")
    cur.execute("DELETE FROM playtime WHERE playtime < 60")

    # Tambien se encuentran playtimes que no corresponden a ningun juego que se conozca. Esta informacion
    # es inutil ya que nunca podra ser usada para una recomendacion.
    # Lo mismo ocurre con la tabla de reviews.
    print("Eliminando entradas que no corresponden a un juego conocido")
    cur.execute("DELETE FROM playtime WHERE item_id NOT IN (SELECT item_id FROM games);")
    cur.execute("DELETE FROM reviews WHERE item_id NOT IN (SELECT item_id FROM games);")

    # TODO: en este momento podriamos ejecutar ALTER TABLE para agregar restricciones de foreign key a las tablas
    # playtime y review.

    # TODO: considerar eliminar reviews de usuarios con un tiempo de juego menor a cierto valor.

    print("Limpieza completa")
    conn.commit()