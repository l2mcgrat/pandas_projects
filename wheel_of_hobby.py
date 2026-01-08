
import pygame
import math
import random
import sys
import pandas as pd
import os

pygame.init()

# -----------------------------
# BASE HOBBY NAMES
# -----------------------------
HOBBY_NAMES = [
    "Leetcode",
    "Coursera",
    "Gaming",
    "Learning",
    "Music",
    "Career Prep",
    "Media",
    "Manga",
    "Reading"
]

HOBBIES = []  # rebuilt dynamically from CSV

WIDTH, HEIGHT = 600, 600
CENTER = (WIDTH // 2, HEIGHT // 2)
RADIUS = 250

SPIN_SPEED = 0
DECELERATION = 0.05

CSV_PATH = "hobby_counts.csv"

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dynamic Hobby Wheel")

font = pygame.font.SysFont(None, 32)
clock = pygame.time.Clock()

angle = 0
spinning = False


# -----------------------------
# CSV INIT
# -----------------------------
if os.path.exists(CSV_PATH):
    df = pd.read_csv(CSV_PATH)
    if "count" not in df.columns:
        df["count"] = 0
    if "points" not in df.columns:
        df["points"] = 0.0
else:
    df = pd.DataFrame({
        "category": HOBBY_NAMES,
        "count": [0] * len(HOBBY_NAMES),
        "points": [0.0] * len(HOBBY_NAMES)
    })
    df.to_csv(CSV_PATH, index=False)


# -----------------------------
# REBUILD HOBBIES AS TUPLES WITH WEIGHTS
# -----------------------------
def rebuild_hobbies_from_csv():
    global df, HOBBIES

    df = pd.read_csv(CSV_PATH)  # always load fresh

    points = df["points"].values
    total_points = points.sum()

    if total_points == 0:
        weights = [1] * len(points)
    else:
        shares = points / total_points
        weights = 1/shares  # your formula

    HOBBIES = [
        (category, weight)
        for category, weight in zip(df["category"], weights)
    ]


# -----------------------------
# DRAW ARROW
# -----------------------------
def draw_arrow(surface):
    pygame.draw.polygon(surface, (255, 0, 0), [
        (CENTER[0], CENTER[1] - RADIUS + 20),
        (CENTER[0] - 20, CENTER[1] - RADIUS - 20),
        (CENTER[0] + 20, CENTER[1] - RADIUS - 20)
    ])


# -----------------------------
# DRAW WHEEL
# -----------------------------
def draw_wheel(surface, angle):
    total_weight = sum(w for _, w in HOBBIES)
    current_angle = angle

    for i, (hobby, weight) in enumerate(HOBBIES):
        span = (weight / total_weight) * 360

        start_rad = math.radians(current_angle)
        end_rad = math.radians(current_angle + span)

        color = (100 + (i * 20) % 155, 100 + (i * 20) % 155, 150)

        pts = [CENTER]
        for s in range(41):
            t = start_rad + (end_rad - start_rad) * (s / 40)
            x = CENTER[0] + math.cos(t) * RADIUS
            y = CENTER[1] + math.sin(t) * RADIUS
            pts.append((x, y))

        pygame.draw.polygon(surface, color, pts)

        mid_angle = math.radians(current_angle + span / 2)
        tx = CENTER[0] + math.cos(mid_angle) * (RADIUS * 0.6)
        ty = CENTER[1] + math.sin(mid_angle) * (RADIUS * 0.6)

        text = font.render(hobby, True, (0, 0, 0))
        surface.blit(text, text.get_rect(center=(tx, ty)))

        current_angle += span


# -----------------------------
# GET SELECTED HOBBY
# -----------------------------
def get_selected_hobby(angle):
    total_weight = sum(w for _, w in HOBBIES)

    arrow_angle = 90
    corrected = (-angle + arrow_angle + 180) % 360

    current_angle = 0
    for hobby, weight in HOBBIES:
        span = (weight / total_weight) * 360
        if current_angle <= corrected < current_angle + span:
            return hobby
        current_angle += span

    return None

# ------------------------------------
# NORMALIZE POINTS EVERY 10 SPINS
# ------------------------------------
def normalize_points_if_needed():
    global df

    total_points = df["points"].sum()
    df["points"] = 100*(df["points"] / total_points)

    df.to_csv(CSV_PATH, index=False)
    print("Points normalized.")

# -----------------------------
# MAIN LOOP
# -----------------------------
rebuild_hobbies_from_csv()  # load weights ONCE at startup

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Start a new spin on mouse click
        if event.type == pygame.MOUSEBUTTONDOWN and not spinning:
            rebuild_hobbies_from_csv()  # update weights BEFORE spin
            SPIN_SPEED = random.uniform(20, 30)
            spinning = True

    screen.fill((255, 255, 255))

    if spinning:
        angle += SPIN_SPEED
        SPIN_SPEED = max(0, SPIN_SPEED - DECELERATION)

        if SPIN_SPEED == 0:
            spinning = False
            selected = get_selected_hobby(angle)
            print("Selected:", selected)

            if selected is not None:
                df.loc[df["category"] == selected, "count"] += 1
            
                # inverse slice fraction scoring
                weights = [w for _, w in HOBBIES]
                total_weight = sum(weights)
                selected_weight = next(w for h, w in HOBBIES if h == selected)
            
                if selected_weight == 0:
                    inverse_fraction = 1
                else:
                    inverse_fraction = total_weight / selected_weight
            
                df.loc[df["category"] == selected, "points"] += inverse_fraction
            

                if df["count"].sum() % 10 == 0:
                    normalize_points_if_needed()
                else:
                    df.to_csv(CSV_PATH, index=False)

    draw_wheel(screen, angle)
    draw_arrow(screen)

    pygame.display.flip()
    clock.tick(60)










