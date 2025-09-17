from typing import List, Tuple
import copy
import random
from .genetic_algorithm import calculate_fitness, order_crossover, mutate

# Aqui podemos unificar funções de GA para o multi-veículo, prioridade, capacidade etc.

def evaluate_population(population: List[List[Tuple[float,float]]]) -> List[float]:
    return [calculate_fitness(individual) for individual in population]

def sort_population_with_fitness(population: List[List[Tuple[float,float]]]) -> Tuple[List[List[Tuple[float,float]]], List[float]]:
    fitness_values = evaluate_population(population)
    sorted_population, sorted_fitness = zip(*sorted(zip(population, fitness_values), key=lambda x: x[1]))
    return list(sorted_population), list(sorted_fitness)
