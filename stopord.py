import nltk

nltk.download("stopwords")
danish_stopwords = nltk.corpus.stopwords.words("danish")

print(danish_stopwords)