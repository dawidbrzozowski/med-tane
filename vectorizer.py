from typing import List, Set
from sklearn.feature_extraction.text import CountVectorizer

import nltk


class TextVectorizer:

    def __init__(self, texts: List[str], n: int = 100):
        self._n = n
        self._stemmer = nltk.stem.PorterStemmer()
        top_n_words = self._get_top_n_words(texts, n)
        self._words = {word: i for i, word in enumerate(top_n_words)}

    def vectorize_text(self, text: str) -> List[int]:
        """
        Creates a list of size n (defined in constructor) with binary values.
        :param text: string to be processed into a vector.
        :return: vector of size n with binary values.
        """
        text = self._stem_text(text)
        result = self._n * [0]
        for word in text.split():
            if word in self._words:
                result[self._words[word]] = 1
        return result

    def _get_top_n_words(self, texts: List[str], n: int) -> Set[str]:
        """
        :param texts: list of texts from which the top N important attributes will be extracted.
        :param n: the number of attributes to be extracted.
        :return: top n attributes (words).
        """
        vec = CountVectorizer(max_features=n)
        stemmed_texts = [self._stem_text(text) for text in texts]
        vec.fit(stemmed_texts)
        return vec.vocabulary_.keys()

    def _stem(self, word: str) -> str:
        return self._stemmer.stem(word)

    def _stem_text(self, text: str) -> str:
        text_split = text.split()
        stemmed_text = [self._stem(word) for word in text_split]
        return ' '.join(stemmed_text)
