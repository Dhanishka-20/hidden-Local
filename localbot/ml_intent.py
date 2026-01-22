from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

INTENT_FILE = os.path.join(os.path.dirname(__file__), "intents.json")

with open(INTENT_FILE, encoding="utf-8") as f:
    intents = json.load(f)

sentences = []
labels = []

for intent, examples in intents.items():
    for ex in examples:
        sentences.append(ex.lower())
        labels.append(intent)

# ML Vectorizer
vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X = vectorizer.fit_transform(sentences)


def get_intent(user_input):
    user_input = user_input.lower().strip()

    user_vec = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_vec, X)[0]

    best_score = similarities.max()
    best_index = similarities.argmax()

    # 🔥 LOWER THRESHOLD (VERY IMPORTANT)
    if best_score < 0.2:
        return None

    return labels[best_index]
