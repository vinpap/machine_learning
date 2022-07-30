"""This is the script used to train the deep learning model that allows JERRY
to recognize user intents. It uses Keras for the model itself, as well as matplotlib
to visualize the training data"""

import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy as np
from keras.models import Sequential
from keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import SGD
import random
import logging
import matplotlib.pyplot as plt


logging.basicConfig(filename='training.log',  level=logging.INFO)
lemmatizer = WordNetLemmatizer()


# some words can be ignored in the vocabulary, if you wish.
ignore_words = []





def plot_training(training_history):

    """This function is used to visualize the training data. Especially useful
    when you want to find the right parameters for your model."""

    plt.plot(training_history.history['accuracy'])
    plt.plot(training_history.history['val_accuracy'])
    plt.title('model accuracy')
    plt.ylabel('accuracy')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()


    plt.plot(training_history.history['loss'])
    plt.plot(training_history.history['val_loss'])
    plt.title('model loss')
    plt.ylabel('loss')
    plt.xlabel('epoch')
    plt.legend(['train', 'test'], loc='upper left')
    plt.show()


words = []
intents = []
documents = []

training_data_file = open('training_set.json').read()
training_samples = json.loads(training_data_file)


for sample in training_samples:

    """These lines create the vocabulary as well as the list of intents we are going
    to use."""
    w = nltk.word_tokenize(sample[0])
    words.extend(w)

    documents.append((w, sample[1]))


    if sample[1] not in intents:
        intents.append(sample[1])


words = [lemmatizer.lemmatize(w.lower()) for w in words if w not in ignore_words]
words = sorted(list(set(words)))

intents = sorted(list(set(intents)))

# Saving everything so that Jerry can use these data later
pickle.dump(words,open('words.pkl','wb'))
pickle.dump(intents,open('intents.pkl','wb'))


logging.info("Training with the following classes:")
for i in intents:
    logging.info(i)


training = []
# creating an empty array for our output
output_empty = [0] * len(intents)

# here we turn each sentence in the training set into a bag-of-words vector
for doc in documents:

    bag = []
    # list of tokenized words for the pattern
    pattern_words = doc[0]
    pattern_words = [lemmatizer.lemmatize(word.lower()) for word in pattern_words]

    # we add a 1 in the vecor for each word if it's in the sentence, otherwise 0
    for w in words:
        bag.append(1) if w in pattern_words else bag.append(0)


    output_row = list(output_empty)
    output_row[intents.index(doc[1])] = 1

    training.append([bag, output_row])

random.shuffle(training)
training = np.array(training)

# Splitting our data into independent values and values to predict
train_x = list(training[:,0])
train_y = list(training[:,1])
logging.info("Training data preprocessed")

logging.info("Training model.\n Hidden layer 1: 128 nodes\nHidden layer 2: 256 nodes")


# Create model - 3 layers. First layer 128 neurons, second layer 64 neurons and 3rd output layer contains number of neurons
# equal to number of intents to predict output intent with softmax. Dropout is added
# after each hidden layer to help avoid overfitting
model = Sequential()
model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(256, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(len(train_y[0]), activation='softmax'))

# compiling model. SGD is the training algorithm used here
sgd = SGD(lr=0.002, decay=1e-6, momentum=0.9, nesterov=True)
model.compile(loss='categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

# training and saving the model
hist = model.fit(np.array(train_x), np.array(train_y), validation_split=0.33, epochs=40, batch_size=3, verbose=1)
model.save('jerry_model.h5', hist)
logging.info("Model created. Visualizing training data...")
plot_training(hist)
