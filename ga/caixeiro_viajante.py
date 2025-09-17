import random
import math
import copy
from typing import List, Tuple, Dict

# --- Parâmetros do problema ---
N_CITIES = 20               # Número de cidades
POPULATION_SIZE = 50
N_GENERATIONS = 50
MUTATION_PROBABILITY = 0.3
MAX_CAPACITY = 120            # Capacidade máxima do caixeiro
CITY_COORD_MIN = 0           # coordenadas mínimas
CITY_COORD_MAX = 1000        # coordenadas máximas
MIN_DEMAND = 1
MAX_DEMAND = 10

# --- Funções utilitárias ---
def calculate_distance(p1: Tuple[int,int], p2: Tuple[int,int]) -> float:
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def calculate_fitness(individual: Dict) -> float:
    route = individual["route"]
    total_load = individual["total_load"]
    if total_load > MAX_CAPACITY:
        return float('inf')  # rota inviável
    distance = sum(calculate_distance(route[i], route[i+1]) for i in range(len(route)-1))
    distance += calculate_distance(route[-1], route[0])
    return distance

# --- Gera população inicial com cidades e demandas aleatórias ---
def generate_population(pop_size: int, n_cities: int) -> List[Dict]:
    # Gera cidades aleatórias
    cities_locations = [(random.randint(CITY_COORD_MIN, CITY_COORD_MAX),
                         random.randint(CITY_COORD_MIN, CITY_COORD_MAX))
                        for _ in range(n_cities)]
    start_city = cities_locations[0]
    
    population = []
    for _ in range(pop_size):
        # Gera demandas aleatórias para cada cidade
        city_demand = {city: random.randint(MIN_DEMAND, MAX_DEMAND) for city in cities_locations}
        remaining_cities = [c for c in cities_locations if c != start_city]
        shuffled = random.sample(remaining_cities, len(remaining_cities))
        route = [start_city] + shuffled
        total_load = sum(city_demand[city] for city in route)
        population.append({"route": route, "total_load": total_load, "city_demand": city_demand})
    
    return population, start_city

# --- Crossover OX preservando cidade inicial ---
def order_crossover(parent1: Dict, parent2: Dict, start_city: Tuple[int,int]) -> Dict:
    p1 = parent1["route"]
    p2 = parent2["route"]
    length = len(p1)
    
    start_index = random.randint(1, length-2)
    end_index = random.randint(start_index+1, length-1)
    
    child_route = p1[start_index:end_index]
    remaining_genes = [gene for gene in p2[1:] if gene not in child_route]
    
    pos = 1
    for gene in remaining_genes:
        if pos == start_index:
            pos = end_index
        child_route.insert(pos - start_index, gene)
        pos += 1
    
    child_route = [start_city] + child_route

    # Combina demandas dos pais
    child_city_demand = {}
    for city in child_route:
        d1 = parent1["city_demand"][city]
        d2 = parent2["city_demand"][city]
        child_city_demand[city] = random.choice([d1, d2])
    
    total_load = sum(child_city_demand[city] for city in child_route)
    return {"route": child_route, "total_load": total_load, "city_demand": child_city_demand}

# --- Mutação preservando cidade inicial ---
def mutate(individual: Dict, mutation_probability: float, start_city: Tuple[int,int]) -> Dict:
    mutated_route = copy.deepcopy(individual["route"])
    if random.random() < mutation_probability and len(mutated_route) > 2:
        index = random.randint(1, len(mutated_route)-2)
        mutated_route[index], mutated_route[index+1] = mutated_route[index+1], mutated_route[index]
    total_load = sum(individual["city_demand"][city] for city in mutated_route)
    return {"route": mutated_route, "total_load": total_load, "city_demand": individual["city_demand"]}

# --- Ordena população pelo fitness ---
def sort_population(population: List[Dict]) -> List[Dict]:
    return sorted(population, key=lambda ind: calculate_fitness(ind))

# --- Execução do GA ---
population, start_city = generate_population(POPULATION_SIZE, N_CITIES)

best_solutions = []
best_fitness_values = []

for generation in range(N_GENERATIONS):
    population = sort_population(population)
    
    best_solutions.append(population[0])
    best_fitness_values.append(calculate_fitness(population[0]))
    
    print(f"Generation {generation}: Best fitness = {calculate_fitness(population[0])}")
    
    new_population = [population[0]]  # elitismo
    
    while len(new_population) < POPULATION_SIZE:
        parent1, parent2 = random.choices(population[:10], k=2)
        child = order_crossover(parent1, parent2, start_city)
        child = mutate(child, MUTATION_PROBABILITY, start_city)
        new_population.append(child)
    
    population = new_population

# --- Resultado final ---
print("\nMelhor solução encontrada:")
print("Rota:", best_solutions[-1]["route"])
print("Carga total:", best_solutions[-1]["total_load"])
print("Fitness (distância total):", best_fitness_values[-1])
print("Demandas das cidades:", best_solutions[-1]["city_demand"])
