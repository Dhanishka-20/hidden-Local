from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

INTENT_FILE = os.path.join(os.path.dirname(__file__), "intents.json")

with open(INTENT_FILE) as f:
    intents = json.load(f)

sentences = []
labels = []

for intent, examples in intents.items():
    for ex in examples:
        sentences.append(ex)
        labels.append(intent)

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(sentences)


def get_intent(user_input):
    user_vec = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_vec, X)[0]

    best_score = max(similarities)
    best_index = similarities.argmax()

    if best_score < 0.4:
        return None

    return labels[best_index]
