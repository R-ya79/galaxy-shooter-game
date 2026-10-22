import random
import sys
import pygame

# Galaxy Shooter – Steuerung: WASD/Pfeile = bewegen, Leertaste = schießen, R = Neustart
pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Galaxy Shooter")
clock = pygame.time.Clock()

WHITE = (245, 245, 255)
CYAN = (60, 220, 255)
PURPLE = (170, 90, 255)
RED = (255, 80, 100)
YELLOW = (255, 225, 100)
DARK = (5, 8, 28)

font = pygame.font.SysFont("consolas", 24)
big_font = pygame.font.SysFont("consolas", 52, bold=True)

# Sternenfeld
stars = [
    [random.randrange(WIDTH), random.randrange(HEIGHT), random.choice([1, 1, 2, 3])]
    for _ in range(100)
]


def reset_game():
    player = pygame.Rect(WIDTH // 2 - 22, HEIGHT - 85, 44, 38)
    bullets = []
    enemies = []
    particles = []
    score = 0
    lives = 3
    spawn_timer = 0
    shoot_cooldown = 0
    game_over = False
    return player, bullets, enemies, particles, score, lives, spawn_timer, shoot_cooldown, game_over


def draw_ship(rect):
    # Einfaches Raumschiff aus Polygonen
    pygame.draw.polygon(
        screen, CYAN,
        [(rect.centerx, rect.top), (rect.left, rect.bottom), (rect.centerx, rect.bottom - 10),
         (rect.right, rect.bottom)]
    )
    pygame.draw.polygon(
        screen, WHITE,
        [(rect.centerx, rect.top + 10), (rect.centerx - 7, rect.bottom - 12),
         (rect.centerx + 7, rect.bottom - 12)]
    )
    pygame.draw.ellipse(screen, PURPLE, (rect.centerx - 5, rect.bottom - 2, 10, 9))


def draw_enemy(enemy):
    rect = enemy["rect"]
    kind = enemy["kind"]

    if kind == "small":
        # Kleine, flinke Gegner in Lila
        pygame.draw.polygon(
            screen, PURPLE,
            [(rect.centerx, rect.bottom), (rect.left, rect.centery),
             (rect.left + 5, rect.top), (rect.centerx, rect.top + 6),
             (rect.right - 5, rect.top), (rect.right, rect.centery)]
        )
        eye_y = rect.centery
        pygame.draw.circle(screen, WHITE, (rect.centerx - 5, eye_y), 2)
        pygame.draw.circle(screen, WHITE, (rect.centerx + 5, eye_y), 2)

    elif kind == "large":
        # Große, gepanzerte Gegner mit drei Lebenspunkten
        pygame.draw.ellipse(screen, (105, 45, 65), rect)
        pygame.draw.ellipse(screen, RED, rect.inflate(-10, -10))
        pygame.draw.rect(screen, YELLOW, (rect.left + 8, rect.centery - 4, rect.width - 16, 8), border_radius=4)
        pygame.draw.circle(screen, WHITE, (rect.left + rect.width // 3, rect.centery - 7), 4)
        pygame.draw.circle(screen, WHITE, (rect.right - rect.width // 3, rect.centery - 7), 4)
        # Kleine Panzerplatten zeigen die Robustheit des Gegners
        pygame.draw.arc(screen, (255, 170, 180), rect.inflate(-8, -8), 0, 3.14, 3)

    else:
        # Normaler Gegner
        pygame.draw.ellipse(screen, RED, rect)
        pygame.draw.arc(screen, YELLOW, rect.inflate(-8, -8), 0, 3.14, 3)
        pygame.draw.circle(screen, WHITE, (rect.left + 10, rect.centery - 2), 3)
        pygame.draw.circle(screen, WHITE, (rect.right - 10, rect.centery - 2), 3)


def draw_text(text, font_obj, color, x, y, center=False):
    image = font_obj.render(text, True, color)
    rect = image.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(image, rect)


def main():
    player, bullets, enemies, particles, score, lives, spawn_timer, shoot_cooldown, game_over = reset_game()
    running = True

    while running:
        dt = clock.tick(60) / 1000
        screen.fill(DARK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if game_over and event.key == pygame.K_r:
                    player, bullets, enemies, particles, score, lives, spawn_timer, shoot_cooldown, game_over = reset_game()

        # Sterne bewegen sich leicht nach unten
        for star in stars:
            star[1] += star[2] * 35 * dt
            if star[1] > HEIGHT:
                star[0] = random.randrange(WIDTH)
                star[1] = 0
            pygame.draw.circle(screen, WHITE, (star[0], int(star[1])), star[2] // 2 + 1)

        if not game_over:
            keys = pygame.key.get_pressed()
            speed = 330 * dt
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            player.x += int(dx * speed)
            player.y += int(dy * speed)
            player.clamp_ip(screen.get_rect())

            # Schießen mit kurzer Abklingzeit
            shoot_cooldown = max(0, shoot_cooldown - dt)
            if keys[pygame.K_SPACE] and shoot_cooldown <= 0:
                bullets.append({"rect": pygame.Rect(player.centerx - 4, player.top - 14, 8, 20), "damage": 2})
                shoot_cooldown = 0.10

            # Gegner erzeugen; das Spiel wird mit dem Punktestand etwas schwieriger
            spawn_timer += dt
            spawn_delay = max(0.35, 0.95 - score * 0.008)
            if spawn_timer >= spawn_delay:
                spawn_timer = 0
                # Drei Gegnertypen: kleine/schnelle, normale und große/langsame Gegner.
                kind = random.choices(
                    ["small", "normal", "large"],
                    weights=[4, 5, 2],
                    k=1
                )[0]

                if kind == "small":
                    size = random.randint(20, 27)
                    enemy = {
                        "rect": pygame.Rect(random.randint(5, WIDTH - size - 5), -size, size, size),
                        "speed": random.randint(200, 280) + score * 0.7,
                        "hp": 1,
                        "kind": kind,
                        "points": 15
                    }
                elif kind == "large":
                    size = random.randint(52, 66)
                    enemy = {
                        "rect": pygame.Rect(random.randint(5, WIDTH - size - 5), -size, size, size),
                        "speed": random.randint(55, 90) + score * 0.35,
                        "hp": 3,
                        "kind": kind,
                        "points": 40
                    }
                else:
                    size = random.randint(32, 42)
                    enemy = {
                        "rect": pygame.Rect(random.randint(5, WIDTH - size - 5), -size, size, size),
                        "speed": random.randint(110, 165) + score * 0.8,
                        "hp": 1,
                        "kind": kind,
                        "points": 10
                    }
                enemies.append(enemy)

            # Projektile bewegen
            for bullet in bullets[:]:
                bullet["rect"].y -= int(760 * dt)
                if bullet["rect"].bottom < 0:
                    bullets.remove(bullet)

            # Gegner bewegen
            for enemy in enemies[:]:
                enemy["rect"].y += int(enemy["speed"] * dt)
                if enemy["rect"].top > HEIGHT:
                    enemies.remove(enemy)
                    lives -= 1
                elif enemy["rect"].colliderect(player):
                    enemies.remove(enemy)
                    lives -= 1

            # Treffer prüfen
            for bullet in bullets[:]:
                hit = None
                for enemy in enemies:
                    if bullet["rect"].colliderect(enemy["rect"]):
                        hit = enemy
                        break
                if hit:
                    if bullet in bullets:
                        bullets.remove(bullet)
                    if hit in enemies:
                        hit["hp"] -= bullet["damage"]
                        # Nur wenn alle Lebenspunkte weg sind, wird der Gegner besiegt.
                        if hit["hp"] <= 0:
                            enemies.remove(hit)
                            score += hit["points"]
                            for _ in range(8 if hit["kind"] != "large" else 16):
                                particles.append([
                                    hit["rect"].centerx, hit["rect"].centery,
                                    random.uniform(-130, 130), random.uniform(-130, 130), 0.35
                                ])

            # Kleine Treffer-Partikel
            for p in particles[:]:
                p[0] += p[2] * dt
                p[1] += p[3] * dt
                p[4] -= dt
                if p[4] <= 0:
                    particles.remove(p)
                else:
                    pygame.draw.circle(screen, YELLOW, (int(p[0]), int(p[1])), 3)

            if lives <= 0:
                game_over = True

        # Zeichnen
        for bullet in bullets:
            rect = bullet["rect"]
            pygame.draw.rect(screen, CYAN, rect, border_radius=3)
            pygame.draw.circle(screen, WHITE, rect.midtop, 4)
        for enemy in enemies:
            draw_enemy(enemy)
        if not game_over:
            draw_ship(player)

        draw_text(f"PUNKTE: {score}", font, WHITE, 18, 16)
        draw_text(f"LEBEN: {max(0, lives)}", font, RED, WIDTH - 150, 16)
        draw_text("MOVE: WASD/PFEILE   SHOOT: LEERTASTE   ESC: BEENDEN", pygame.font.SysFont("consolas", 15),
                  (165, 180, 215), 18, HEIGHT - 28)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 15, 190))
            screen.blit(overlay, (0, 0))
            draw_text("GAME OVER", big_font, RED, WIDTH // 2, HEIGHT // 2 - 55, center=True)
            draw_text(f"Dein Punktestand: {score}", font, WHITE, WIDTH // 2, HEIGHT // 2 + 5, center=True)
            draw_text("Drücke R zum Neustarten", font, CYAN, WIDTH // 2, HEIGHT // 2 + 48, center=True)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
