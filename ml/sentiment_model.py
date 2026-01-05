import pandas as pd
from textblob import TextBlob

# Load dataset
df = pd.read_csv("ml/vendors_dataset.csv")

# Function to get sentiment score
def get_sentiment(text):
    analysis = TextBlob(text)
    return analysis.sentiment.polarity  # range: -1 to +1

# Apply sentiment analysis
df["sentiment_score"] = df["description"].apply(get_sentiment)

# Normalize rating (1–5 → 0–1)
df["normalized_rating"] = df["rating"] / 5

# Final score formula (IMPORTANT)
df["final_score"] = (0.6 * df["normalized_rating"]) + (0.4 * df["sentiment_score"])

# Sort vendors by score
ranked_vendors = df.sort_values(by="final_score", ascending=False)

# Save ranked output
ranked_vendors.to_csv("ml/ranked_vendors.csv", index=False)

print("✅ Vendor ranking completed")
print(ranked_vendors[["name", "final_score"]])
