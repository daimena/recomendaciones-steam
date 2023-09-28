# Análisis de Datos de Juegos de Steam

Este repositorio contiene múltiples scripts para realizar extracción y transformación de datos crudos extraidos de la plataforma Steam, para luego insertarlos en una base de datos y entranar un modelo de Machine Learning que genere recomendaciones.

## Prerequisitos

Los scripts fueron desarrollados con Python 3 v3.8.10, y las siguientes dependendencias, instalables utilizando `pip`:

- [`pandas` v2.0.3](https://pandas.pydata.org/)
- [`tqdm` v4.66.1](https://github.com/tqdm/tqdm)

Para comenzar, se deben guardar los archivos crudos `australian_user_reviews.json`, `output_steam_games.json` y `australian_users_items.json` en el directorio [`raw`](./raw).

## Extracción de Datos

El primer paso consiste en preprocesar los archivos JSON del directorio [`raw`](./raw) para transformarlos en archivos CSV que se guardarán en el directorio `preprocesado`. Además de realizar desaniaciones y ajustes menores, aquellos campos que no sean relevantes no serán guardados en los CSV.

```bash
$ python extraccion.py
```
