import re
import nltk
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from google_play_scraper import reviews_all, Sort
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import google.generativeai as genai
import os

# Download nltk resources (run only once)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("omw-1.4", quiet=True)

# Setup stop words and lemmatizer
stop_words = set(stopwords.words("english"))
lemmatizer = WordNetLemmatizer()

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC6dFuulxltoFeeZtLtHKm9wCTCVo7UliE")
genai.configure(api_key=GEMINI_API_KEY)

def clean_text(text):
    """Cleans review text for NLP processing"""
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r"http\S+|www\S+|https\S+", "", text)
    text = re.sub(r"[^a-z\s]", "", text)
    words = text.split()
    words = [lemmatizer.lemmatize(w) for w in words if w not in stop_words]
    return " ".join(words)

# In-memory cache to avoid repeated LLM calls for the same keywords
topic_cache = {}

def llm_summarize_topic(keywords):
    """
    Convert a list of keywords into a human-readable phrase using Gemini LLM.
    Uses caching to reduce API calls and avoid exceeding quota.
    """
    # Create a consistent key for caching
    key = ",".join(sorted(keywords))

    # Return cached result if available
    if key in topic_cache:
        return topic_cache[key]

    prompt_text = (
        f"Given these keywords from app reviews: {', '.join(keywords)}, "
        f"summarize them into a short, human-understandable topic phrase."
    )

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt_text)
        topic_phrase = response.text.strip()
        topic_cache[key] = topic_phrase  # store in cache
        return topic_phrase
    except Exception as e:
        print(f"LLM summarization failed: {e}")
        # fallback: just join keywords as a readable phrase
        fallback_phrase = " / ".join(keywords)
        topic_cache[key] = fallback_phrase
        return fallback_phrase


def analyze_app_reviews(app_id: str, num_topics=3,save_csv=True):
    """
    Scrape Google Play reviews, perform sentiment analysis, and topic modeling.
    """
    country_codes = ["us", "et", "gb", "de", "fr", "in", "jp", "br", "ng", "za"]
    all_reviews = []

    for country in country_codes:
        try:
            r = reviews_all(app_id, lang="en", country=country, sort=Sort.NEWEST)
            for rr in r:
                rr["country"] = country
            all_reviews.extend(r)
        except Exception as e:
            print(f"Failed to fetch reviews for {country}: {e}")
            continue
    

    if not all_reviews:
        return {"error": "No reviews found"}

    df = pd.DataFrame(all_reviews)[["content", "score", "country"]]
    df["clean_review"] = df["content"].apply(clean_text)

    
    if save_csv:
        # Save cleaned dataframe
        csv_filename = f"cleaned_reviews_{app_id}.csv"
        df.to_csv(csv_filename, index=False)

    # Topic modeling (KMeans on TF-IDF)
    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 3))
    X = vectorizer.fit_transform(df["clean_review"])
    kmeans = KMeans(n_clusters=num_topics, random_state=42, n_init=10)
    df["topic"] = kmeans.fit_predict(X)

    terms = vectorizer.get_feature_names_out()
    topic_phrases = {}

    for i, center in enumerate(kmeans.cluster_centers_):
        # Get top 2 term indices by importance in this cluster
        top_indices = center.argsort()[-2:][::-1]
        # Extract the corresponding terms
        top_terms = [terms[j] for j in top_indices]

        # Summarize using LLM (or fallback to keywords if LLM fails)
        topic_phrases[f"topic_{i}"] = llm_summarize_topic(top_terms)

    # Sentiment labeling
    def label_sentiment(score):
        if score <= 2:
            return "negative"
        elif score == 3:
            return "neutral"
        else:
            return "positive"

    df["sentiment_ml"] = df["score"].apply(label_sentiment)
    sentiment_counts = df["sentiment_ml"].value_counts().to_dict()
    topic_counts = df["topic"].value_counts().to_dict()

    return {
        "total_reviews": len(df),
        "sentiment_distribution": sentiment_counts,
        "topics": topic_phrases,
        "topic_distribution": topic_counts,
    }
