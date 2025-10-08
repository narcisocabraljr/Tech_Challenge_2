# vrptw_pygame.py
import random
import math
import copy
import pygame
from typing import List, Tuple, Dict
import matplotlib.pyplot as plt

# -----------------------
# Configurações principais
# -----------------------
N_CITIES = 20              # inclui depósito como cidade 0
POPULATION_SIZE = 60
N_GENERATIONS = 120
MUTATION_PROBABILITY = 0.35

# Demanda / capacidades
MIN_DEMAND = 1
MAX_DEMAND = 20

# Veículos (3 veículos com capacidades diferentes)
VEHICLE_COUNT = 3
VEHICLE_CAPACITIES = [60, 80, 70]  # ajuste aqui se quiser outros valores

# Movimento / tempo
SPEED = 50.0            # unidades de distância por unidade de tempo
SERVICE_TIME = 10.0     # tempo de atendimento por hospital
TIME_WINDOW_PENALTY_FACTOR = 5000.0

# Pausa para almoço
LUNCH_BREAK_THRESHOLD = 250.0
LUNCH_BREAK_DURATION = 60.0

# Prioridades
PRIORITY_LEVELS = [1, 2, 3]
PRIORITY_PENALTY_FACTORS = {1: 1.0, 2: 5.0, 3: 10.0}

# Coordenadas
CITY_COORD_MIN = 0
CITY_COORD_MAX = 1000

# -----------------------
# Pygame (visual)
# -----------------------
SCREEN_WIDTH = 1500
SCREEN_HEIGHT = 1000
MARGIN_X = 50
MARGIN_Y = 50
SCALE_X = (SCREEN_WIDTH - 2 * MARGIN_X) / CITY_COORD_MAX
SCALE_Y = (SCREEN_HEIGHT - 2 * MARGIN_Y) / CITY_COORD_MAX
FPS = 5

# Colors for vehicles (distinct)
VEHICLE_COLORS = [
    (80, 180, 255),   # veículo 0 - azul
    (120, 255, 120),  # veículo 1 - verde
    (255, 165, 0),   # veículo 2 - laranja
    (255, 120, 180),  # extras se necessário
]

# -----------------------
# Utilitários
# -----------------------
def calculate_distance(p1: Tuple[int,int], p2: Tuple[int,int]) -> float:
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

def generate_time_windows(cities_locations: List[Tuple[int,int]]) -> Dict[Tuple[int,int], Tuple[float,float]]:
    time_windows = {}
    for city in cities_locations:
        start = random.uniform(100, 800)
        end = start + 120
        time_windows[city] = (start, end)
    if cities_locations:
        time_windows[cities_locations[0]] = (0.0, 10000.0)
    return time_windows

# -----------------------
# Geração da população (VRP)
# -----------------------
def generate_vrp_population(pop_size: int, n_cities: int, n_vehicles: int, vehicle_capacities: List[int]):
    # gera cidades
    cities_locations = [
        (random.randint(CITY_COORD_MIN, CITY_COORD_MAX),
         random.randint(CITY_COORD_MIN, CITY_COORD_MAX))
        for _ in range(n_cities)
    ]
    # demandas e prioridades por cidade (fixas para toda a população)
    city_demand = {city: random.randint(MIN_DEMAND, MAX_DEMAND) for city in cities_locations}
    city_priority = {city: random.choice(PRIORITY_LEVELS) for city in cities_locations}

    # janelas de tempo
    city_time_windows = generate_time_windows(cities_locations)
    start_city = cities_locations[0]
    city_priority[start_city] = PRIORITY_LEVELS[0]

    population = []
    for _ in range(pop_size):
        # distribuição aleatória das cidades entre veículos
        remaining = [c for c in cities_locations if c != start_city]
        random.shuffle(remaining)

        # distribuição balanceada entre veículos
        routes_assigned = [[] for _ in range(n_vehicles)]
        loads = [0 for _ in range(n_vehicles)]
        for i, city in enumerate(remaining):
            vid = i % n_vehicles  # round-robin
            routes_assigned[vid].append(city)
            loads[vid] += city_demand[city]


        individual_routes = []
        for vid in range(n_vehicles):
            route = [start_city] + routes_assigned[vid]  # não duplicamos depósito no final
            total_load = sum(city_demand[c] for c in route)
            individual_routes.append({
                "vehicle_id": vid,
                "route": route,
                "total_load": total_load,
                "capacity": vehicle_capacities[vid]
            })

        population.append({
            "routes": individual_routes,
            "city_demand": city_demand,
            "city_priority": city_priority
        })

    return population, start_city, city_time_windows, city_priority

# -----------------------
# Fitness (soma de todas as rotas)
# -----------------------
def calculate_vrp_fitness(individual: Dict, city_time_windows: Dict) -> float:
    total_distance = 0.0
    total_penalty = 0.0

    # percorre cada veículo separadamente (inclui pausas de almoço)
    for route_info in individual["routes"]:
        route = route_info["route"]
        capacity = route_info["capacity"]
        load = route_info["total_load"]

        # penalidade por ultrapassar capacidade
        if load > capacity:
            total_penalty += 1e6 + (load - capacity) * 1e3

        current_time = 0.0
        work_since_last_break = 0.0

        n = len(route)
        for i in range(n):
            city = route[i]

            # pausa de almoço (não no depósito)
            if work_since_last_break >= LUNCH_BREAK_THRESHOLD and i > 0:
                current_time += LUNCH_BREAK_DURATION
                work_since_last_break = 0.0

            # prioridade do hospital
            priority_level = individual["city_priority"].get(city, 1)
            priority_factor = PRIORITY_PENALTY_FACTORS.get(priority_level, 1.0)

            # janelas de tempo
            if city in city_time_windows:
                start_w, end_w = city_time_windows[city]

                # espera se chegou cedo
                if current_time < start_w:
                    wait = start_w - current_time
                    current_time += wait
                    work_since_last_break += wait

                # atraso -> penalidade proporcional à prioridade
                if current_time > end_w:
                    delay = current_time - end_w
                    total_penalty += delay * TIME_WINDOW_PENALTY_FACTOR * priority_factor

                # tempo de serviço
                current_time += SERVICE_TIME
                work_since_last_break += SERVICE_TIME

            # deslocamento para próxima cidade (fecha o ciclo de rota)
            next_city = route[(i + 1) % n]
            seg_dist = calculate_distance(city, next_city)
            total_distance += seg_dist
            travel_time = seg_dist / SPEED
            current_time += travel_time
            work_since_last_break += travel_time

    # ----------------------------------------------------------------------
    # Penalidades e ajustes globais (aplicados após processar todos os veículos)
    # ----------------------------------------------------------------------

    # Penaliza veículos ociosos (não usados)
    used_vehicles = sum(1 for r in individual["routes"] if len(r["route"]) > 1)
    idle_vehicles = len(individual["routes"]) - used_vehicles
    total_penalty += idle_vehicles * 50000  # incentivo a usar todos

    # Penalidade de balanceamento de carga (incentiva dividir entregas)
    loads = [r["total_load"] for r in individual["routes"]]
    mean_load = sum(loads) / len(loads)
    imbalance = sum(abs(l - mean_load) for l in loads)
    total_penalty += imbalance * 100  # 100 = peso ajustável do balanceamento

    # Penaliza veículos com pouca carga (menos de 20% da capacidade)
    for r in individual["routes"]:
        if r["total_load"] < 0.2 * r["capacity"]:
            total_penalty += 30000  # custo fixo para evitar veículos quase vazios

    # Aumenta levemente o peso da distância total (para influenciar o equilíbrio)
    total_distance *= 1.2

    # Fitness final
    return total_distance + total_penalty


# -----------------------
# Função para integração com LLM
# -----------------------
def gerar_instrucoes_motorista(best_solution: Dict, distancia_total: float) -> Dict[int, str]:
    """
    Recebe a melhor solução e retorna instruções detalhadas por veículo.
    Retorna um dicionário: {vehicle_id: texto_instrucoes}
    """
    instrucoes = {}
    for rinfo in best_solution["routes"]:
        vid = rinfo["vehicle_id"]
        route = rinfo["route"]
        texto = f"Veículo {vid} deve seguir a rota com {len(route)-1} entregas (distância total aproximada: {distancia_total:.1f}).\n"
        for i, city in enumerate(route):
            if i == 0:
                texto += f"  - Início no depósito {city}.\n"
            else:
                texto += f"  - Visitar cidade {city}, prioridade {best_solution['city_priority'].get(city, 1)}.\n"
        texto += "Seguir janelas de tempo e pausas conforme necessário.\n"
        instrucoes[vid] = texto
    return instrucoes

# -----------------------
# Crossover para VRP
# Strategy: flatten all non-depot cities (in vehicle order),
# apply OX between two parents to get an ordering, then split it among vehicles
# trying to respect capacities (greedy split).
# -----------------------
def flatten_parent_routes(parent: Dict) -> List[Tuple[int,int]]:
    seq = []
    for r in parent["routes"]:
        # append cities excluding depot
        seq.extend([c for c in r["route"] if c != parent["routes"][0]["route"][0]])
    return seq

def ox_on_sequence(seq1: List[Tuple[int,int]], seq2: List[Tuple[int,int]]) -> List[Tuple[int,int]]:
    size = len(seq1)
    if size == 0:
        return []
    a, b = sorted(random.sample(range(size), 2))
    child = [None] * size
    child[a:b+1] = seq1[a:b+1]
    pos = (b + 1) % size
    for g in seq2:
        if g not in child:
            child[pos] = g
            pos = (pos + 1) % size
    return child

def split_sequence_among_vehicles(sequence: List[Tuple[int,int]], start_city: Tuple[int,int],
                                   vehicle_capacities: List[int], city_demand: Dict) -> List[List[Tuple[int,int]]]:
    n = len(vehicle_capacities)
    assigned = [[] for _ in range(n)]
    loads = [0 for _ in range(n)]
    vid = 0
    for city in sequence:
        demand = city_demand[city]
        placed = False
        # try current vehicle then nexts
        for trial in range(n):
            idx = (vid + trial) % n
            if loads[idx] + demand <= vehicle_capacities[idx]:
                assigned[idx].append(city)
                loads[idx] += demand
                vid = idx
                placed = True
                break
        if not placed:
            # put into vehicle with smallest load (will be penalized)
            idx = min(range(n), key=lambda x: loads[x])
            assigned[idx].append(city)
            loads[idx] += demand
            vid = idx
    # final route list with depot prefix
    final_routes = [[start_city] + a for a in assigned]
    return final_routes

def crossover_vrp(parent1: Dict, parent2: Dict, start_city: Tuple[int,int], vehicle_capacities: List[int]) -> Dict:
    seq1 = flatten_parent_routes(parent1)
    seq2 = flatten_parent_routes(parent2)
    child_seq = ox_on_sequence(seq1, seq2)
    city_demand = parent1["city_demand"]  # same for parents
    splitted = split_sequence_among_vehicles(child_seq, start_city, vehicle_capacities, city_demand)
    routes = []
    for vid, r in enumerate(splitted):
        total_load = sum(city_demand[c] for c in r)
        routes.append({
            "vehicle_id": vid,
            "route": r,
            "total_load": total_load,
            "capacity": vehicle_capacities[vid]
        })
    return {
        "routes": routes,
        "city_demand": city_demand,
        "city_priority": parent1["city_priority"]
    }

# -----------------------
# Mutação VRP: troca entre rotas ou dentro de rota
# -----------------------
def mutate_vrp(ind: Dict, prob: float) -> Dict:
    ind = copy.deepcopy(ind)
    if random.random() < prob:
        # escolha aleatória entre trocar entre veículos ou swap interno
        if random.random() < 0.5 and len(ind["routes"]) >= 2:
            # swap entre veículos: escolhe dois veículos e troca uma cidade entre eles
            v1, v2 = random.sample(range(len(ind["routes"])), 2)
            r1 = ind["routes"][v1]["route"]
            r2 = ind["routes"][v2]["route"]
            # se ambos têm cidades além do depósito
            if len(r1) > 1 and len(r2) > 1:
                i = random.randint(1, len(r1)-1)
                j = random.randint(1, len(r2)-1)
                r1[i], r2[j] = r2[j], r1[i]
        else:
            # swap interno em uma rota
            v = random.randrange(len(ind["routes"]))
            r = ind["routes"][v]["route"]
            if len(r) > 2:
                i, j = random.sample(range(1, len(r)), 2)
                r[i], r[j] = r[j], r[i]

    # atualiza cargas
    for rinfo in ind["routes"]:
        rinfo["total_load"] = sum(ind["city_demand"][c] for c in rinfo["route"])
    return ind

# -----------------------
# Ordena população
# -----------------------
def sort_population(pop: List[Dict], city_time_windows: Dict) -> List[Dict]:
    return sorted(pop, key=lambda ind: calculate_vrp_fitness(ind, city_time_windows))

# -----------------------
# Desenho (cada rota com cor distinta)
# -----------------------
def draw_vrp(screen, best_ind: Dict, gen: int, fitness: float, city_time_windows: Dict):
    screen.fill((18, 18, 18))
    font = pygame.font.SysFont("Arial", 18)
    small = pygame.font.SysFont("Arial", 14)

    # desenha cada veículo
    for rinfo in best_ind["routes"]:
        vid = rinfo["vehicle_id"]
        color = VEHICLE_COLORS[vid % len(VEHICLE_COLORS)]
        route = rinfo["route"]
        n = len(route)
        for i in range(n):
            c1 = route[i]
            c2 = route[(i+1) % n]
            p1 = (int(c1[0] * SCALE_X) + MARGIN_X, int(c1[1] * SCALE_Y) + MARGIN_Y)
            p2 = (int(c2[0] * SCALE_X) + MARGIN_X, int(c2[1] * SCALE_Y) + MARGIN_Y)
            pygame.draw.line(screen, color, p1, p2, 3)

        # desenha pontos do veículo (colore de acordo com prioridade)
        for idx, city in enumerate(route):
            pos = (int(city[0] * SCALE_X) + MARGIN_X, int(city[1] * SCALE_Y) + MARGIN_Y)
            priority = best_ind["city_priority"].get(city, 1)
            if idx == 0:
                # depósito: desenha em vermelho grande (apenas no primeiro veículo)
                pygame.draw.circle(screen, (255, 80, 80), pos, 9)
                label = small.render("Depósito", True, (255, 255, 255))
                screen.blit(label, (pos[0] + 10, pos[1] - 10))
            else:
                # cor base do veículo com um contorno
                pygame.draw.circle(screen, color, pos, 7)
            # desenha janela de tempo como anel pequeno
            tw = city_time_windows.get(city, (0,0))
            window_size = max(8, min(26, (tw[1] - tw[0]) / 50)) if tw != (0,0) else 8
            pygame.draw.circle(screen, (0, 140, 0), pos, int(window_size), 1)
            txt = f"P{priority} [{int(tw[0])}-{int(tw[1])}]"
            lbl = pygame.font.SysFont("Arial", 12).render(txt, True, (200, 255, 200))
            screen.blit(lbl, (pos[0] + 8, pos[1] - 8))

    fitness_text = "inf" if math.isinf(fitness) else f"{fitness:.2f}"
    screen.blit(font.render(f"Geração: {gen+1}/{N_GENERATIONS}", True, (255,255,255)), (20, 20))
    screen.blit(font.render(f"Melhor fitness: {fitness_text}", True, (255,255,255)), (20, 45))
    # legenda veículos
    for vid in range(len(best_ind["routes"])):
        color = VEHICLE_COLORS[vid % len(VEHICLE_COLORS)]
        lbl = pygame.font.SysFont("Arial", 14).render(f"Veículo {vid} (cap {best_ind['routes'][vid]['capacity']})", True, color)
        screen.blit(lbl, (20, 80 + 20*vid))

    pygame.display.flip()

# -----------------------
# Cálculo de tempos de chegada e pausas por veículo
# retorna dict por veículo: arrival_times[vid] = {city: time,...}, lunch_breaks[vid] = [t1,t2...]
# -----------------------
def compute_vrp_arrival_times_and_breaks(best_solution: Dict, city_time_windows: Dict):
    vehicle_arrivals = {}
    vehicle_breaks = {}

    for route_info in best_solution["routes"]:
        vid = route_info["vehicle_id"]
        route = route_info["route"]

        arrival_times = {}
        lunch_breaks = []
        current_time = 0.0
        work_since_last_break = 0.0

        for i, city in enumerate(route):
            # pausa
            if work_since_last_break >= LUNCH_BREAK_THRESHOLD and i > 0:
                current_time += LUNCH_BREAK_DURATION
                work_since_last_break = 0.0
                lunch_breaks.append((current_time - LUNCH_BREAK_DURATION, current_time))  # (start,end)

            if city in city_time_windows:
                start_w, end_w = city_time_windows[city]
                wait = max(0, start_w - current_time)
                current_time += wait
                work_since_last_break += wait
                arrival_times[city] = current_time
                current_time += SERVICE_TIME
                work_since_last_break += SERVICE_TIME

            if i < len(route) - 1:
                next_city = route[i+1]
                d = calculate_distance(city, next_city)
                travel_time = d / SPEED
                current_time += travel_time
                work_since_last_break += travel_time

        vehicle_arrivals[vid] = arrival_times
        vehicle_breaks[vid] = lunch_breaks

    return vehicle_arrivals, vehicle_breaks

# -----------------------
# Plota o resultado do VRPTW de forma detalhada, integrando prioridades, janelas de tempo e atrasos.
# -----------------------
def plot_vrp_solution_detailed(solution: dict, arrivals: dict, breaks: dict, vehicle_colors=None):
    """
    Plota o resultado do VRPTW de forma detalhada, integrando prioridades, janelas de tempo e atrasos.
    
    solution: dict retornado pelo algoritmo (melhor solução)
    arrivals: dict retornado por compute_vrp_arrival_times_and_breaks
    breaks: dict retornado por compute_vrp_arrival_times_and_breaks
    vehicle_colors: lista de cores para os veículos
    """
    if vehicle_colors is None:
        vehicle_colors = ["#50B4FF", "#78FF78", "#FFA500", "#FF78B4"]

    plt.figure(figsize=(14,10))

    for route_info in solution["routes"]:
        vid = route_info["vehicle_id"]
        route = route_info["route"]
        color = vehicle_colors[vid % len(vehicle_colors)]
        
        # Trajeto
        xs = [c[0] for c in route]
        ys = [c[1] for c in route]
        plt.plot(xs, ys, color=color, linewidth=2, marker='o', markersize=6, label=f"Veículo {vid}")

        # Distância aproximada da rota
        total_dist = sum(math.hypot(xs[i]-xs[i+1], ys[i]-ys[i+1]) for i in range(len(xs)-1))
        plt.text(xs[-1], ys[-1], f"{total_dist:.1f}", fontsize=10, color=color)

        # Depósito em destaque
        plt.scatter(xs[0], ys[0], color='red', s=120, marker='s', zorder=5)
        plt.text(xs[0]+5, ys[0]+5, "Depósito", fontsize=9, color='red')

        # Pausas (indicativo aproximado no depósito)
        for b_start, b_end in breaks.get(vid, []):
            plt.scatter(xs[0], ys[0], color='yellow', s=200, alpha=0.3, zorder=4)

        # Prioridades e atrasos
        for city in route[1:]:
            arrival = arrivals[vid].get(city,0)
            priority = solution["city_priority"].get(city, 1)
            plt.scatter(city[0], city[1], s=20*priority, edgecolor='black', facecolor='none', linewidth=1, zorder=5)
            plt.text(city[0]+5, city[1]+5, f"P{priority}", fontsize=8)

            # janela de tempo
            if "city_time_windows" in solution:
                start, end = solution["city_time_windows"].get(city, (0,0))
                plt.plot([city[0]-5, city[0]+5], [start, start], color='green', linewidth=1)  # início janela
                plt.plot([city[0]-5, city[0]+5], [end, end], color='green', linewidth=1)      # fim janela

                # atraso
                if arrival > end:
                    plt.scatter(city[0], city[1], color='red', s=50, marker='x', zorder=6)
    
    plt.title("Rotas dos Veículos - VRPTW (Detalhado)")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.legend()
    plt.show()

# -----------------------
# Loop principal
# -----------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("VRPTW - múltiplos veículos (pausa, janelas, prioridade)")
    clock = pygame.time.Clock()

    population, start_city, city_time_windows, city_priority = generate_vrp_population(
        POPULATION_SIZE, N_CITIES, VEHICLE_COUNT, VEHICLE_CAPACITIES
    )

    best_solution = None
    best_fitness = float("inf")

    for generation in range(N_GENERATIONS):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        population = sort_population(population, city_time_windows)
        current_best = population[0]
        current_fitness = calculate_vrp_fitness(current_best, city_time_windows)

        if current_fitness < best_fitness:
            best_solution, best_fitness = current_best, current_fitness

        draw_vrp(screen, current_best, generation, current_fitness, city_time_windows)
        print(f"Geração {generation+1}: melhor fitness = {current_fitness:.2f}")

        # criação nova população (elitismo + crossover + mutação)
        new_population = [population[0]]
        while len(new_population) < POPULATION_SIZE:
            p1, p2 = random.choices(population[:12], k=2)
            child = crossover_vrp(p1, p2, start_city, VEHICLE_CAPACITIES)
            child = mutate_vrp(child, MUTATION_PROBABILITY)
            new_population.append(child)

        population = new_population
        clock.tick(FPS)

    pygame.quit()

    # resultado final: print por veículo
    print("\n=== Melhor solução final (por veículo) ===")
    if best_solution:
        arrivals, breaks = compute_vrp_arrival_times_and_breaks(best_solution, city_time_windows)
        for route_info in best_solution["routes"]:
            vid = route_info["vehicle_id"]
            route = route_info["route"]
            load = route_info["total_load"]
            cap = route_info["capacity"]

            print(f"\nVeículo {vid} (capacidade {cap}) - carga: {load}")
            print("Rota:")
            for i, city in enumerate(route):
                tw = city_time_windows.get(city, (0,0))
                arr = arrivals[vid].get(city, 0.0)
                priority = best_solution["city_priority"].get(city, 1)
                if i == 0:
                    status = "depósito"
                elif arr < tw[0]:
                    status = f"cedo (espera {tw[0]-arr:.1f})"
                elif arr > tw[1]:
                    atraso = arr - tw[1]
                    mult = PRIORITY_PENALTY_FACTORS.get(priority, 1.0)
                    status = f"ATRASADO ({atraso:.1f}) - penalidade x{mult:.1f}"
                else:
                    status = "dentro"
                print(f"  {i+1:02d} - {city} | P{priority} | Chegada: {arr:.1f} | Janela: [{tw[0]:.1f},{tw[1]:.1f}] | {status}")

            # pausas do veículo
            vb = breaks.get(vid, [])
            if vb:
                print("Pausas (início -> fim):")
                for idx, (s,e) in enumerate(vb, start=1):
                    print(f"   - Pausa {idx}: {s:.1f} -> {e:.1f}")
            else:
                print("Nenhuma pausa para este veículo.")
        print(f"\nFitness final (soma tudo): {best_fitness:.2f}")

        # -----------------------
        # Gera instruções detalhadas por veículo via LLM
        # -----------------------
        # calcula distância total aproximada para a LLM
        distancia_total = sum(
            calculate_distance(route[i], route[(i+1) % len(route)])
            for rinfo in best_solution["routes"]
            for route in [rinfo["route"]]
            for i in range(len(route))
        )
        instrucoes = gerar_instrucoes_motorista(best_solution, distancia_total)
        for vid, texto in instrucoes.items():
            print(f"\nInstruções para veículo {vid}:\n{texto}\n")
    else:
        print("Nenhuma solução encontrada.")

    best_solution["city_time_windows"] = city_time_windows  # necessário para o gráfico
    plot_vrp_solution_detailed(best_solution, arrivals, breaks)


if __name__ == "__main__":
    main()
