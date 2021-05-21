from preproces.vectorizer import TextVectorizer
from utils.file_io import load_json
import random


def is_row_empty(row):
    for element in row:
        if element != 0:
            return False

    return True


def serialise_int_list(row):
    result = ""
    for element in row:
        result = result + str(element) + ","

    return result[:-1]


if __name__ == '__main__':
    dataset = load_json('data/tweets.json')

    preprocessed_dataset = []
    for data in dataset:
        # remove @link
        preprocessed_dataset.append(" ".join(filter(lambda x: x[0] != '@', data.split())))

    v = TextVectorizer(preprocessed_dataset, 20)

    with open("output.txt", "w") as txt_file:

        txt_file.write(serialise_int_list(v.vocab) + "\n")
        random.shuffle(dataset)
        for data_row in dataset:
            vectorised_row = v.vectorize_text(data_row)
            if not is_row_empty(vectorised_row):
                txt_file.write(serialise_int_list(vectorised_row) + "\n")
