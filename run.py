import random
from ga.genetic_algorithm import generate_random_population
from visualization.tsp import run_visualization  # caso você crie uma função main em tsp.py


def main():
    # Inicializa cidades e população
    N_CITIES = 15
    POPULATION_SIZE = 100
    cities_locations = [(random.randint(0, 800), random.randint(0, 400)) for _ in range(N_CITIES)]
    start_city = cities_locations[0]
    population = generate_random_population(cities_locations, POPULATION_SIZE, start_city_location=start_city)

    # Chama visualização
    run_visualization(population, start_city)

if __name__ == "__main__":
    main()
