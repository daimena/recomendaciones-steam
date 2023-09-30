from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax
import pandas as pd
from tqdm import tqdm

print('Cargando el modelo de analisis de sentimientos')
roberta = "cardiffnlp/twitter-roberta-base-sentiment"

model = AutoModelForSequenceClassification.from_pretrained(roberta)
tokenizer = AutoTokenizer.from_pretrained(roberta)

# El modelo trae 3 etiquetas que se corresponden a Negativo, Neutral y Positivo.
# Cuando analiza un string, devuelve el score de cada etiqueta, dado que la suma de los scores sea 1.
# Es decir, que entrega el porcentaje que corresponde a cada sentimiento.
# Defino que muestre las etiiquetas como 0, 1 y 2, porque es el dato que voy a usar.
labels = [0, 1, 2]

def get_sentiment_label(text):
    try:
        # Solo tomo los primeros 140 caracteres de cada review porque el modelo esta pensado para analizar tweets.
        text = text[:140]

        encoded_review = tokenizer(text, return_tensors='pt')
        output = model(**encoded_review)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)

        # Me quedo con la etiqueta que tenga mayor score.
        max = 0
        max_idx = 0
        for idx, score in enumerate(scores):
            if score > max:
                max = score
                max_idx = idx

        return labels[max_idx]
    except:
        # Las reviews que el modelo no pueda analizar (porque estas vacias o tienen solo un caracter, o estan en otros idiomas)
        # defino que devuelva la etiqueta neutra.
        return 1

# Cargo el archivo de reviews en un DataFrame.
reviews = pd.read_csv('preprocesado/australian_user_reviews.csv', encoding='utf8', lineterminator="\n")

print('Analizando las reviews')

with tqdm(total=len(reviews)) as pbar:
    def apply_get_sentiment_label(fila):
        pbar.update()
        return get_sentiment_label(fila['review'])

    reviews['sentiment'] = reviews.apply(apply_get_sentiment_label, axis=1)

# Ahora que tengo una columna nueva con la etiqueta del sentimiento correspondiente a cada review, elimino la columna review
# y actualizo el CSV.
reviews = reviews.drop(columns=['review'])

print('Entidad reviews guardada en preprocesado/australian_user_reviews.csv')
reviews.to_csv('preprocesado/australian_user_reviews.csv', index=False)