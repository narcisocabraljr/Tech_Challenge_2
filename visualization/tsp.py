import pygame
from ga.ga_utils import evaluate_population, sort_population_with_fitness
from visualization.draw_functions import draw_paths, draw_plot, draw_cities
from ga.genetic_algorithm import mutate, order_crossover, generate_random_population, calculate_fitness, sort_population, default_problems
from ga.caixeiro_viajante import generate_population, calculate_fitness as fitness_caixeiro

import itertools
import random
import numpy as np

WIDTH, HEIGHT = 800, 400
FPS = 30
NODE_RADIUS = 10

def run_visualization(initial_population, start_city):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("TSP Solver using Pygame")
    clock = pygame.time.Clock()
    generation_counter = itertools.count(start=1)

    population = initial_population
    best_fitness_values = []
    best_solutions = []

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        generation = next(generation_counter)
        screen.fill((255, 255, 255))

        # Avalia e ordena
        population_fitness = evaluate_population(population)
        population, population_fitness = sort_population_with_fitness(population)

        best_fitness = population_fitness[0]
        best_solution = population[0]
        best_fitness_values.append(best_fitness)
        best_solutions.append(best_solution)

        # Desenhos
        draw_plot(screen, list(range(len(best_fitness_values))), best_fitness_values, y_label="Fitness - Distance (pxls)")
        draw_cities(screen, [city for city in best_solution], (255, 0, 0), NODE_RADIUS)
        draw_paths(screen, best_solution, (0, 0, 255), width=3)

        # Criação da nova população
        new_population = [population[0]]  # elitismo
        while len(new_population) < len(population):
            probability = 1 / np.array(population_fitness)
            parent1, parent2 = random.choices(population, weights=probability, k=2)
            child = order_crossover(parent1, parent2, start_city)
            child = mutate(child, 0.5, start_city)
            new_population.append(child)

        population = new_population
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
