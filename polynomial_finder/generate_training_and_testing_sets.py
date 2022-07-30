import random
import math
import csv

"""This script generates training and testing data based on a randomly-generated
polynomial function. Below you can adjust its degree as well as the range
within which the function's coefficients will be selected.
The generated datasets are stored in the training.csv and testing.csv files"""

degree = 9
coef_low_limit = -1024
coef_high_limit = 1024

def generate_polynomial(degree=2):

    polynomial = []

    for i in range(degree+1):

        polynomial.append(random.uniform(coef_low_limit, coef_high_limit))

    print(polynomial)
    return polynomial



def create_datasets(polynomial):

    datasets = []
    training_set = []
    testing_set = []

    for i in range(1000):

        x = random.uniform(-10, 10)
        y = 0

        for j in range(len(polynomial)):

            y += polynomial[j]*math.pow(x, len(polynomial)-1-j)

        training_set.append([x, y])



    for i in range(200):

        x = random.uniform(-10, 10)
        y = 0

        for j in range(len(polynomial)):

            y += polynomial[j]*math.pow(x, len(polynomial)-1-j)

        testing_set.append([x, y])



    datasets.append(training_set)
    datasets.append(testing_set)
    return datasets

def save_datasets(data):

    with open('training.csv', 'w', newline='') as training_csv_file:
        csv_writer = csv.writer(training_csv_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in data[0]:
            csv_writer.writerow([i[0], i[1]])

    with open('testing.csv', 'w', newline='') as testing_csv_file:
        csv_writer = csv.writer(testing_csv_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in data[1]:
            csv_writer.writerow([i[0], i[1]])


data = create_datasets(generate_polynomial(degree))
save_datasets(data)
