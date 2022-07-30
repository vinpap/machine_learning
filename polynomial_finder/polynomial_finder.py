from statistics import mean
import math
import csv
import random
import matplotlib.pyplot as plt
import numpy as np


degrees = 9


def get_initial_population():


    return np.random.uniform(-1024,1024,(1000, degrees+1))


def load_training_data():

    training_samples = []
    with open('training.csv', newline='') as training_csv_file:

        csv_reader = csv.reader(training_csv_file, delimiter=' ', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for row in csv_reader :
            training_samples.append(row)

    return training_samples


def calculate_normalized_square_error(predicted_values, actual_values):


    mse = np.square(np.subtract(actual_values[:,1], predicted_values[:,1])).mean()
    rmse = math.sqrt(mse)


    normalized_rmse = (rmse/(np.amax(actual_values[:,1])-np.amin(actual_values[:,1])))
    return normalized_rmse

def assess_candidate(candidate, training_data):

    predicted_values = []
    for i in training_data:
        prediction = 0
        for j in range(len(candidate)):
            prediction += candidate[j]*math.pow(i[0], len(candidate)-1-j)
        predicted_values.append([i[0], prediction])

    predicted_values = np.array(predicted_values)


    nrmse = calculate_normalized_square_error(predicted_values, training_data)
    return nrmse


def assess_generation(generation, training_data, generation_nbr):

    candidates_fitness = []


    for candidate in generation:

        candidates_fitness.append(assess_candidate(candidate, training_data))

    generation_mean_fitness = mean(candidates_fitness)
    candidates_fitness = np.array(candidates_fitness)
    candidates_fitness = np.reshape(candidates_fitness, (-1, 1))
    generation = np.append(generation, candidates_fitness, axis = 1)

    ind = np.argsort(generation[:,-1])
    sorted_array = generation[ind]
    best_candidate = sorted_array[0]



    print("Training with generation ", str(generation_nbr), " - average fitness: ", str(generation_mean_fitness), " - best candidate fitness: ", str(best_candidate[-1]))
    return (best_candidate, generation, generation_mean_fitness)

def create_next_generation(current_generation):

    ind = np.argsort(current_generation[:,-1])

    sorted_array = current_generation[ind]
    best_candidates = np.array_split(sorted_array, 2)[0]
    best_candidates = np.delete(best_candidates, -1, 1)
    np.random.shuffle(best_candidates)

    couples_nbr = len(best_candidates)//2
    couples = np.split(best_candidates, couples_nbr)

    children = []

    for c in couples:

        splitting_point = random.randint(1, degrees)
        child = np.concatenate((c[0][:splitting_point], c[1][splitting_point:]))
        mutation_factor = random.randint(1, 10)
        if mutation_factor==1:
            child[random.randint(0, len(child)-1)] = random.uniform(-1024,1024)
        children.append(child)

    new_generation = np.random.uniform(-1024,1024,(750, degrees+1))

    new_generation = np.concatenate((new_generation, children), axis=0)

    return new_generation



current_population = get_initial_population()
training_data = np.array(load_training_data()).astype(np.float)
testing_data = np.array(load_testing_data()).astype(np.float)

generation_nbr = 1
generations_nbr_history = []
generations_fitness_history = []
best_candidate_fitness_history = []
current_best_candidate = 0
best_candidate_overall = 0

while generation_nbr<=1000 :
    generations_nbr_history.append(generation_nbr)
    current_best_candidate, tested_generation, generation_fitness = assess_generation(current_population, training_data, generation_nbr)
    generations_fitness_history.append(generation_fitness)
    if (type(best_candidate_overall) != np.array) or (best_candidate_overall[-1] > current_best_candidate[-1]):
        best_candidate_overall = current_best_candidate

    best_candidate_fitness_history.append(best_candidate_overall[-1])
    if best_candidate_overall[-1] <= 0.001: break
    current_population = create_next_generation(tested_generation)
    generation_nbr+=1

best_candidate_overall = np.delete(best_candidate_overall, -1)
print("Best candidate overall: ")
print(best_candidate_overall)
plt.plot(generations_nbr_history, generations_fitness_history)
plt.plot(generations_nbr_history, best_candidate_fitness_history)
plt.xlabel('Generations')
plt.ylabel('Fitness (normalized RMSE)')
plt.show()
