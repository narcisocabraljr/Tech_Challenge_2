import random
import math
import copy
import pygame
from typing import List, Tuple, Dict

# --- Parâmetros do problema ---
N_CITIES = 20
POPULATION_SIZE = 50
N_GENERATIONS = 100
MUTATION_PROBABILITY = 0.3
MAX_CAPACITY = 120
CITY_COORD_MIN = 0
CITY_COORD_MAX = 1000
MIN_DEMAND = 1
MAX_DEMAND = 10
SPEED = 50.0
SERVICE_TIME = 10.0
TIME_WINDOW_PENALTY_FACTOR = 5000.0

# --- Parâmetros da pausa para almoço ---
LUNCH_BREAK_THRESHOLD = 250.0  # Tempo de trabalho antes da pausa
LUNCH_BREAK_DURATION = 60.0    # Duração da pausa
# --------------------------------------

# --- Parâmetros de prioridade ---
PRIORITY_LEVELS = [1, 2, 3]  # 1: Baixa, 2: Média, 3: Alta
PRIORITY_PENALTY_FACTORS = {
    1: 1.0,
    2: 5.0,
    3: 10.0
}
# --------------------------------

# --- Pygame Config ---
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
MARGIN_X = 50
MARGIN_Y = 50
SCALE_X = (SCREEN_WIDTH - 2 * MARGIN_X) / CITY_COORD_MAX
SCALE_Y = (SCREEN_HEIGHT - 2 * MARGIN_Y) / CITY_COORD_MAX
FPS = 5


# --- Funções auxiliares ---
def generate_time_windows(cities_locations: List[Tuple[int, int]]) -> Dict[Tuple[int, int], Tuple[float, float]]:
    time_windows = {}
    for city in cities_locations:
        start = random.uniform(100, 800)
        end = start + 120
        time_windows[city] = (start, end)
    if cities_locations:
        time_windows[cities_locations[0]] = (0.0, 10000.0)
    return time_windows


def calculate_distance(p1: Tuple[int, int], p2: Tuple[int, int]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


# --- Função de fitness com pausa de almoço ---
def calculate_fitness(individual: Dict, city_time_windows: Dict) -> float:
    route = individual["route"]
    total_load = individual["total_load"]
    city_priority = individual["city_priority"]

    distance = 0.0
    time_penalty = 0.0
    current_time = 0.0
    work_since_last_break = 0.0

    if total_load > MAX_CAPACITY:
        return float("inf")

    n = len(route)
    for i in range(n):
        city = route[i]

        # --- Pausa de almoço ---
        if work_since_last_break >= LUNCH_BREAK_THRESHOLD and i > 0:
            current_time += LUNCH_BREAK_DURATION
            work_since_last_break = 0.0  # zera o contador
            # print(f"Pausa para almoço em t={current_time:.1f}")

        # --- Prioridade ---
        priority_level = city_priority.get(city, 1)
        priority_factor = PRIORITY_PENALTY_FACTORS.get(priority_level, 1.0)

        if city in city_time_windows:
            start_w, end_w = city_time_windows[city]

            # Espera se chegou cedo
            if current_time < start_w:
                wait_time = start_w - current_time
                current_time += wait_time
                work_since_last_break += wait_time

            # Penalidade se atrasou
            if current_time > end_w:
                delay = current_time - end_w
                time_penalty += delay * TIME_WINDOW_PENALTY_FACTOR * priority_factor

            # Tempo de serviço
            current_time += SERVICE_TIME
            work_since_last_break += SERVICE_TIME

        # Próxima cidade
        next_city = route[(i + 1) % n]
        segment_distance = calculate_distance(city, next_city)
        distance += segment_distance
        travel_time = segment_distance / SPEED
        current_time += travel_time
        work_since_last_break += travel_time

    return distance + time_penalty


# --- População inicial ---
def generate_population(pop_size: int, n_cities: int):
    cities_locations = [
        (random.randint(CITY_COORD_MIN, CITY_COORD_MAX),
         random.randint(CITY_COORD_MIN, CITY_COORD_MAX))
        for _ in range(n_cities)
    ]

    city_demand = {city: random.randint(MIN_DEMAND, MAX_DEMAND) for city in cities_locations}
    city_priority = {city: random.choice(PRIORITY_LEVELS) for city in cities_locations}

    city_time_windows = generate_time_windows(cities_locations)
    start_city = cities_locations[0]
    city_priority[start_city] = PRIORITY_LEVELS[0]  # depósito com prioridade baixa

    population = []
    for _ in range(pop_size):
        remaining = [c for c in cities_locations if c != start_city]
        random.shuffle(remaining)
        route = [start_city] + remaining
        total_load = sum(city_demand[c] for c in route)

        population.append({
            "route": route,
            "total_load": total_load,
            "city_demand": city_demand,
            "city_priority": city_priority
        })

    return population, start_city, city_time_windows, city_priority


# --- Crossover e mutação ---
def order_crossover(parent1: Dict, parent2: Dict, start_city: Tuple[int, int]) -> Dict:
    p1 = parent1["route"]
    p2 = parent2["route"]
    genes1, genes2 = p1[1:], p2[1:]
    size = len(genes1)
    a, b = sorted(random.sample(range(size), 2))
    child_genes = [None] * size
    child_genes[a:b + 1] = genes1[a:b + 1]
    pos = (b + 1) % size
    for gene in genes2:
        if gene not in child_genes:
            child_genes[pos] = gene
            pos = (pos + 1) % size
    child_route = [start_city] + child_genes
    child_city_priority = parent1["city_priority"]
    child_city_demand = {
        city: random.choice([parent1["city_demand"][city], parent2["city_demand"][city]])
        for city in child_route
    }
    total_load = sum(child_city_demand[c] for c in child_route)

    return {
        "route": child_route,
        "total_load": total_load,
        "city_demand": child_city_demand,
        "city_priority": child_city_priority
    }


def mutate(ind: Dict, prob: float, start_city: Tuple[int, int]) -> Dict:
    route = copy.deepcopy(ind["route"])
    if random.random() < prob and len(route) > 2:
        i, j = random.sample(range(1, len(route)), 2)
        route[i], route[j] = route[j], route[i]
    total_load = sum(ind["city_demand"][c] for c in route)
    return {
        "route": route,
        "total_load": total_load,
        "city_demand": ind["city_demand"],
        "city_priority": ind["city_priority"]
    }


def sort_population(pop: List[Dict], city_time_windows: Dict) -> List[Dict]:
    return sorted(pop, key=lambda i: calculate_fitness(i, city_time_windows))


# --- Desenho ---
def draw_route(screen, best, gen, fitness, city_time_windows):
    screen.fill((25, 25, 25))
    font = pygame.font.SysFont("Arial", 18)
    small_font = pygame.font.SysFont("Arial", 14)
    route = best["route"]
    n = len(route)
    city_priority = best["city_priority"]

    for i in range(n):
        c1, c2 = route[i], route[(i + 1) % n]
        p1 = (int(c1[0] * SCALE_X) + MARGIN_X, int(c1[1] * SCALE_Y) + MARGIN_Y)
        p2 = (int(c2[0] * SCALE_X) + MARGIN_X, int(c2[1] * SCALE_Y) + MARGIN_Y)
        pygame.draw.line(screen, (100, 200, 255), p1, p2, 2)

    for idx, city in enumerate(route):
        pos = (int(city[0] * SCALE_X) + MARGIN_X, int(city[1] * SCALE_Y) + MARGIN_Y)
        start, end = city_time_windows.get(city, (0, 0))
        window_size = max(10, min(40, (end - start) / 50))

        pygame.draw.circle(screen, (0, 150, 0), pos, int(window_size), 1)
        priority = city_priority.get(city, 1)
        if idx == 0:
            color = (255, 50, 50)
        elif priority == 3:
            color = (255, 100, 100)
        elif priority == 2:
            color = (255, 255, 100)
        else:
            color = (50, 150, 255)
        pygame.draw.circle(screen, color, pos, 6)

        text = f"P{priority} [{int(start)}–{int(end)}]"
        label = small_font.render(text, True, (180, 255, 180))
        screen.blit(label, (pos[0] + 8, pos[1] - 10))

    fitness_text = "inf" if math.isinf(fitness) else f"{fitness:.2f}"
    screen.blit(font.render(f"Geração: {gen + 1}/{N_GENERATIONS}", True, (255, 255, 255)), (20, 20))
    screen.blit(font.render(f"Melhor fitness: {fitness_text}", True, (255, 255, 255)), (20, 45))
    pygame.display.flip()


# --- Cálculo de tempos de chegada (com pausa incluída) ---
def compute_arrival_times(best_solution, city_time_windows):
    route = best_solution["route"]
    arrival_times = {}
    current_time = 0.0
    work_since_last_break = 0.0

    for i, city in enumerate(route):
        if work_since_last_break >= LUNCH_BREAK_THRESHOLD and i > 0:
            current_time += LUNCH_BREAK_DURATION
            work_since_last_break = 0.0

        if city in city_time_windows:
            start_w, end_w = city_time_windows[city]
            wait_time = max(0, start_w - current_time)
            current_time += wait_time
            work_since_last_break += wait_time
            arrival_times[city] = current_time
            current_time += SERVICE_TIME
            work_since_last_break += SERVICE_TIME

        if i < len(route) - 1:
            next_city = route[i + 1]
            dist = calculate_distance(city, next_city)
            travel_time = dist / SPEED
            current_time += travel_time
            work_since_last_break += travel_time

    return arrival_times


# --- Execução principal ---
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Algoritmo Genético - Caixeiro Viajante (c/ Janelas, Prioridade e Pausa de Almoço)")
    clock = pygame.time.Clock()

    population, start_city, city_time_windows, city_priority = generate_population(POPULATION_SIZE, N_CITIES)
    best_solution = None
    best_fitness = float("inf")

    for generation in range(N_GENERATIONS):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        population = sort_population(population, city_time_windows)
        current_best = population[0]
        current_fitness = calculate_fitness(current_best, city_time_windows)

        if current_fitness < best_fitness:
            best_solution, best_fitness = current_best, current_fitness

        draw_route(screen, current_best, generation, current_fitness, city_time_windows)
        print(f"Geração {generation + 1}: melhor fitness = {current_fitness:.2f}")

        new_population = [population[0]]
        while len(new_population) < POPULATION_SIZE:
            p1, p2 = random.choices(population[:10], k=2)
            child = order_crossover(p1, p2, start_city)
            child = mutate(child, MUTATION_PROBABILITY, start_city)
            new_population.append(child)

        population = new_population
        clock.tick(FPS)

    pygame.quit()

    # --- Resultado final ---
    print("\nMelhor solução final:")
    if best_solution:
        arrival_times = compute_arrival_times(best_solution, city_time_windows)
        print("Rota, prioridade e horários:")
        for i, city in enumerate(best_solution["route"]):
            tw = city_time_windows.get(city, (0, 0))
            arrival = arrival_times.get(city, 0.0)
            priority = best_solution["city_priority"].get(city, 1)

            if i == 0:
                status = "depósito"
            elif arrival < tw[0]:
                status = f"cedo (espera {tw[0] - arrival:.1f})"
            elif arrival > tw[1]:
                atraso = arrival - tw[1]
                mult = PRIORITY_PENALTY_FACTORS.get(priority, 1.0)
                status = f"ATRASADO ({atraso:.1f}) - penalidade x{mult:.1f}"
            else:
                status = "dentro"

            print(
                f"  {i + 1:02d} - Cidade {city} | P{priority} | Chegada: {arrival:.1f} | "
                f"Janela: [{tw[0]:.1f}, {tw[1]:.1f}] | {status}"
            )

        print("\nCarga total:", best_solution["total_load"])
        print("Fitness final:", best_fitness)
    else:
        print("Nenhuma solução viável encontrada.")


if __name__ == "__main__":
    main()
