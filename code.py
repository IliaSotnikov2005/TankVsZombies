import pygame, sys, math, random


pygame.init()
pygame.key.set_repeat(20, 70)

FPS = 30
SIZE = WIDTH, HEIGHT = 1920, 1080

screen = pygame.display.set_mode(SIZE)
clock = pygame.time.Clock()
frameCount = 0
speed = 27
rotate_speed = 4
tile_width = 350

# создание переменных, необходимых для работы классов
all_sprites = None
player_group = None
tower_group = None
bullet_group = None
enemy_group = None
guns_group = None
tracks_group = None
baff_group = None
target_group = None
angrytiles_group = None
goodtiles_group = None

up = False
down = False
left = False
right = False

fire = False
ratata_playing = False
driving_playing = False
tower_image = '0.png'
cooldown = 0
baff_cooldown0 = 0
baff_cooldown1 = 0
freeze_cooldown = 0
ratata_cooldown = 0
kills = 0
level = None
player = None
tower = None
tr = None
tr1 = None
camera = None
target = None
mouse = None
keys = None

medium_shot = pygame.mixer.Sound('data/medium.wav')
ratata_shot = pygame.mixer.Sound('data/ratata.wav')
plasma_shot = pygame.mixer.Sound('data/plasma.wav')
driving = pygame.mixer.Sound('data/driving.wav')
killed = pygame.mixer.Sound('data/killed.wav')
new_gun = pygame.mixer.Sound('data/newgun.wav')
new_baff = pygame.mixer.Sound('data/baff.wav')
death_sound = pygame.mixer.Sound('data/deathsound.wav')
medium_shot.set_volume(0.2)
ratata_shot.set_volume(0.2)
plasma_shot.set_volume(0.2)
driving.set_volume(0.2)


# загрузка изображения
def load_image(name):
    name = 'data/' + name
    return pygame.image.load(name)


track_animation = [load_image('Track0.png'), load_image('Track1.png')]


# загрузка уровня
def load_level():
    with open('data/level.txt', 'r') as mapFile:
        return [line.strip() for line in mapFile]


# создание плиток уровня и игрока
def generate_level():
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('.', x, y)
            elif level[y][x] == '#':
                Tile('#', x, y)
            elif level[y][x] == '@':
                Tile('.', x, y)
                player = Player(x, y)
    return player


def terminate():
    pygame.quit()
    sys.exit()


# начальный экран
def start_screen():
    fon = load_image('start.png')
    screen.blit(fon, (0, 0))
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        clock.tick(FPS)


# экран завершения игры
def death_screen():
    global cooldown, baff_cooldown0, baff_cooldown1, freeze_cooldown, ratata_cooldown
    driving.stop()
    ratata_shot.stop()
    cooldown = 0
    baff_cooldown0 = 0
    baff_cooldown1 = 0
    freeze_cooldown = 0
    ratata_cooldown = 0
    pygame.mouse.set_visible(True)
    with open('data/bestscore.TXT', 'r') as bs:
        last = int(bs.read())
    if last < kills:
        with open('data/bestscore.TXT', 'w') as bs:
            bs.write(str(kills))
            last = kills
    fon = load_image('death.png')
    screen.blit(fon, (0, 0))

    font = pygame.font.Font('data/Pixel.ttf', 30)
    string_rendered = font.render(f'Ваш счёт {kills}' + ' ' * 32 + f'Лучший счет {last}', 1, pygame.Color('white'))
    screen.blit(string_rendered, (WIDTH // 2 - 420, HEIGHT // 2 - 100))

    btn = pygame.sprite.Sprite()
    btn.image = pygame.Surface((600, 60))
    btn.image.fill((154, 154, 154))
    btn.rect = btn.image.get_rect()
    btn.rect = btn.rect.move(WIDTH // 2 - 300, HEIGHT // 2 + 300)
    string_rendered = font.render(f'НАЧАТЬ СНАЧАЛА', 1, pygame.Color('white'))
    btn.image.blit(string_rendered, (200, 20))
    screen.blit(btn.image, (WIDTH // 2 - 300, HEIGHT // 2 + 300))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if btn.rect.collidepoint(pygame.mouse.get_pos()):
                        game_loop()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    terminate()
        pygame.display.flip()
        clock.tick(FPS)


# функция для отрисовывания спрайтов
def drawScreen():
    global frameCount, bg
    clock.tick(FPS)
    screen.fill('black')
    for i in goodtiles_group:
        if -500 < i.rect.x < 1920 and -500 < i.rect.y < 1080:
            i.draw(screen)
    angrytiles_group.draw(screen)
    guns_group.draw(screen)
    baff_group.draw(screen)
    tracks_group.update()
    tracks_group.draw(screen)
    player_group.update()
    player_group.draw(screen)
    bullet_group.update()
    bullet_group.draw(screen)
    tower_group.update()
    tower_group.draw(screen)
    enemy_group.update()
    enemy_group.draw(screen)
    target_group.update()
    target_group.draw(screen)
    pygame.display.flip()


# плитка
class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y):
        super().__init__(all_sprites)
        self.image = TILES[tile_type]
        if tile_type == '#':
            self.add(angrytiles_group)
        else:
            self.add(goodtiles_group)
        self.rect = self.image.get_rect().move(pos_x * tile_width, pos_y * tile_width)
        self.mask = pygame.mask.from_surface(self.image)

    def draw(self, screen):
        screen.blit(self.image, self.rect)


# камера
class Camera:
    def __init__(self):
        self.dx = 0
        self.dy = 0

    def apply(self, obj):
        if obj == player:
            obj.pos.x += self.dx
            obj.pos.y += self.dy
            return
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -round(target.pos.x - WIDTH // 2)
        self.dy = -round(target.pos.y - HEIGHT // 2)


# танк
class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.image = load_image('tank.png')
        pos_x = pos_x * tile_width
        pos_y = pos_y * tile_width
        self.rect = self.image.get_rect(center=(pos_x, pos_y))
        self.orig_image = load_image('tank.png')
        self.angle = 0
        self.gun = 0
        self.map_pos = [pos_x, pos_y]
        self.pos = pygame.math.Vector2((pos_x, pos_y))
        self.mask = pygame.mask.from_surface(self.image)

    # обновление башни и проверка на пересечение с бонусами и противниками
    def update(self):
        global tower_image, rotate_speed, speed, baff_cooldown0, baff_cooldown1
        for i in tower_group:
            i.kill()
        tower = TankTower()
        for i in guns_group:
            if pygame.sprite.collide_mask(self, i):
                self.gun = i.gun
                tower_image = f'{str(i.gun)}.png'
                i.kill()
                new_gun.play()
                Gun()
        for i in baff_group:
            if pygame.sprite.collide_mask(self, i):
                if i.baff == 0:
                    rotate_speed = 9
                    baff_cooldown0 = 300
                else:
                    speed = 40
                    baff_cooldown1 = 300
                new_baff.play()
                i.kill()
                Baff()
        for i in enemy_group:
            if pygame.sprite.collide_mask(self, i):
                death_sound.play()
                death_screen()

    # движение танка по полю
    def move(self):
        dirvec = pygame.math.Vector2(0, speed).rotate(self.angle)
        if keys[pygame.K_w]:
            self.map_pos -= dirvec
            self.map_pos = list(map(lambda x: round(x), self.map_pos))
            x = self.map_pos[0]
            y = self.map_pos[1]
            top = level[(y - 100) // 350][(x - 100) // 350] == '#'
            bottom = level[(y + 100) // 350][(x + 100) // 350] == '#'
            levay = level[y // 350][(x - 120) // 350] == '#'
            pravay = level[y // 350][(x + 120) // 350] == '#'
            if top or bottom or levay or pravay:
                self.map_pos += dirvec
                return
            self.pos = self.pos - dirvec

        if keys[pygame.K_s]:
            self.map_pos += dirvec
            self.map_pos = list(map(lambda x: round(x), self.map_pos))
            x = self.map_pos[0]
            y = self.map_pos[1]
            top = level[(y - 100) // 350][(x - 100) // 350] == '#'
            bottom = level[(y + 100) // 350][(x + 100) // 350] == '#'
            levay = level[y // 350][(x - 120) // 350] == '#'
            pravay = level[y // 350][(x + 120) // 350] == '#'
            if top or bottom or levay or pravay:
                self.map_pos -= dirvec
                return
            self.pos = self.pos + dirvec
        if keys[pygame.K_a]:
            self.angle -= rotate_speed
        if keys[pygame.K_d]:
            self.angle += rotate_speed
        self.image = pygame.transform.rotate(self.orig_image, -self.angle)
        self.mask = pygame.mask.from_surface(self.image)
        camera.update(player)
        for i in all_sprites:
            camera.apply(i)
        self.rect = self.image.get_rect(center=(round(self.pos.x), round(self.pos.y)))


# башня танка
class TankTower(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, tower_group)
        self.image = load_image(tower_image)
        self.orig_image = self.image
        self.rect = self.image.get_rect(center=player.rect.center)
        self.pos = pygame.math.Vector2(self.rect.center)
        self.offset = pygame.math.Vector2(0, -40)
        self.x, self.y = self.rect.x, self.rect.y
        self.angle = 0

    # поворот башни
    def update(self):
        mouse_x, mouse_y = mouse
        rel_x, rel_y = -(mouse_x - self.rect.center[0]), -(mouse_y - self.rect.center[1])
        self.angle = (180 / math.pi) * math.atan2(rel_y, rel_x) - 90
        self.image = pygame.transform.rotozoom(self.orig_image, -self.angle, 1)
        offset_rotated = self.offset.rotate(self.angle)
        self.rect = self.image.get_rect(center=self.pos + offset_rotated)


BULLETS = [load_image('Medium.png'), load_image('Light.png'), load_image('Plasma.png')]
BAFFS = ['rotate_speed = 2', 'speed = 15']
TILES = {'#': pygame.transform.scale(load_image('desk.png'), (350, 350)),
         '.': pygame.transform.scale(load_image('grass.jpg'), (350, 350))}


# оружия для танка
class Gun(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, guns_group)
        self.gun = random.randint(0, 2)
        self.image = load_image(f'gun{self.gun}.png')
        finding = True
        self.mask = pygame.mask.from_surface(self.image)
        self.rect = self.image.get_rect()
        while finding:
            self.rect.x = random.randint(400, 40 * tile_width - 400)
            self.rect.y = random.randint(400, 40 * tile_width - 400)
            if not (pygame.sprite.spritecollideany(self, baff_group) and
                    pygame.sprite.spritecollideany(self, guns_group) and
                    level[self.rect.y // 350][self.rect.x // 350] == '#'):
                self.add(all_sprites, guns_group)
                finding = False


# улучшения для танка
class Baff(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.baff = random.randint(0, 1)
        self.image = load_image(f'baff{self.baff}.png')
        self.mask = pygame.mask.from_surface(self.image)
        finding = True
        self.rect = self.image.get_rect()
        while finding:
            self.rect.x = random.randint(400, 40 * tile_width - 400)
            self.rect.y = random.randint(400, 40 * tile_width - 400)
            if not (pygame.sprite.spritecollideany(self, baff_group) and
                    pygame.sprite.spritecollideany(self, guns_group) and
                    level[self.rect.y // 350][self.rect.x // 350] == '#'):
                self.add(all_sprites, baff_group)
                finding = False


# снаряды для оружия
class Bullet(pygame.sprite.Sprite):
    def __init__(self, bullet, second=False):
        super().__init__(all_sprites, bullet_group)
        self.image = BULLETS[bullet]
        self.orig_image = BULLETS[bullet]
        self.type = bullet
        self.rect = self.image.get_rect(center=(player.rect.x + player.rect.width // 2,
                                                player.rect.y + player.rect.height // 2))
        self.pos = pygame.math.Vector2(self.rect.center)
        if player.gun == 1:
            if second:
                self.offset = pygame.math.Vector2(10, -100)
            else:
                self.offset = pygame.math.Vector2(-10, -100)
        else:
            self.offset = pygame.math.Vector2(0, -150)
        self.mouse_x, self.mouse_y = mouse
        self.player_pos = player.rect.center
        rel_x, rel_y = -(self.mouse_x - self.rect.center[0]), -(self.mouse_y - self.rect.center[1])
        self.angle = (180 / math.pi) * math.atan2(rel_y, rel_x) - 90
        self.image = pygame.transform.rotozoom(self.orig_image, -self.angle, 1)
        offset_rotated = self.offset.rotate(self.angle)
        self.rect = self.image.get_rect(center=self.pos + offset_rotated)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self):
        speed = 50
        distance = [self.mouse_x - self.player_pos[0], self.mouse_y - self.player_pos[1]]
        norm = math.sqrt(distance[0] ** 2 + distance[1] ** 2)
        direction = [distance[0] / norm, distance[1] / norm]
        bullet_vector = [-direction[0] * speed, -direction[1] * speed]
        self.rect.x -= bullet_vector[0]
        self.rect.y -= bullet_vector[1]
        for i in angrytiles_group:
            if pygame.sprite.collide_mask(self, i):
                self.kill()
                break
        if self.rect.x < -100 or self.rect.x > 1920 or self.rect.y < -100 or self.rect.y > 1080:
            self.kill()


# зомби
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites, enemy_group)
        self.image = load_image('enemy.png')
        self.original_image = self.image
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(400, 40 * tile_width - 400)
        self.rect.y = random.randint(400, 40 * tile_width - 400)
        self.speedx = -10
        self.speedy = -10
        self.health = 100

    def update(self):
        global freeze_cooldown, kills

        dx = self.rect.x - player.rect.center[0]
        dy = self.rect.y - player.rect.center[1]
        dist = math.hypot(dx, dy)
        dx = dx / dist
        dy = dy / dist
        self.rect.x += dx * self.speedx
        self.rect.y += dy * self.speedy
        # проверка на попадание снаряда
        for i in bullet_group:
            if pygame.sprite.collide_mask(self, i):
                if i.type == 0:
                    self.health -= 50
                if i.type == 1:
                    self.health -= 20
                if i.type == 2:
                    # урон по площади и временное замедление
                    for j in enemy_group:
                        if (self.rect.center[0] - 80 < j.rect.center[0] < self.rect.center[0] + 80 and
                                self.rect.center[1] - 80 < j.rect.center[1] < self.rect.center[1] + 80):
                            j.speedx = -5
                            j.speedy = -5
                            self.health -= 30
                            j.image = load_image('freezeenemy.png')
                            j.original_image = self.image
                    freeze_cooldown = 30
                i.kill()
        if not freeze_cooldown and self.speedx == -5:
            self.speedx = -10
            self.speedy = -10
            self.image = load_image('enemy.png')
            self.original_image = self.image
        if self.health < 0:
            killed.play()
            self.kill()
            kills += 1
            Enemy()
        self.rotate()

    def rotate(self):
        x, y = player.rect.center
        rel_x, rel_y = x - self.rect.x, y - self.rect.y
        angle = (180 / math.pi) * -math.atan2(rel_y, rel_x) - 90
        self.image = pygame.transform.rotate(self.original_image, int(angle))
        self.rect = self.image.get_rect(center=self.rect.center)


# гусеница танка левая или правая
class Track(pygame.sprite.Sprite):
    def __init__(self, left=True):
        super().__init__(all_sprites, tracks_group)
        self.step = 0
        self.image = track_animation[0]
        self.orig_image = track_animation[self.step]
        self.left = left
        self.rect = self.image.get_rect()

    def update(self):
        # анимация гусениц
        if left or right or up or down:
            self.step = (self.step + 1) % 2
            self.image = track_animation[self.step]
            self.orig_image = track_animation[self.step]
        self.rect = self.image.get_rect(center=player.rect.center)
        self.pos = pygame.math.Vector2(self.rect.center)
        # движение гусениц
        if self.left:
            self.offset = pygame.math.Vector2(68, 0)
        else:
            self.offset = pygame.math.Vector2(-68, 0)
        self.rotate(player.angle)

    def rotate(self, angle):
        self.image = pygame.transform.rotozoom(self.orig_image, -angle, 1)
        offset_rotated = self.offset.rotate(angle)
        self.rect = self.image.get_rect(center=self.pos + offset_rotated)


# прицел
class Target(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(target_group)
        self.image = pygame.transform.scale(load_image('target.png'), (50, 50))
        self.rect = self.image.get_rect()

    def update(self):
        self.rect.x = mouse[0] - 25
        self.rect.y = mouse[1] - 25


# функция игрового цикла
def game_loop():
    global cooldown, freeze_cooldown, baff_cooldown1, baff_cooldown0, fire, left, right, up, down,\
        driving_playing, rotate_speed, speed, ratata_playing, level, player, tower, tr, tr1,\
    camera, target, mouse, keys, kills, all_sprites, player_group, tracks_group, tower_group,\
    bullet_group, enemy_group, guns_group, baff_group, target_group, angrytiles_group,\
        goodtiles_group, ratata_cooldown

    pygame.mouse.set_visible(False)
    all_sprites = pygame.sprite.Group()
    player_group = pygame.sprite.Group()
    tower_group = pygame.sprite.Group()
    bullet_group = pygame.sprite.Group()
    enemy_group = pygame.sprite.Group()
    guns_group = pygame.sprite.Group()
    tracks_group = pygame.sprite.Group()
    baff_group = pygame.sprite.Group()
    target_group = pygame.sprite.Group()
    angrytiles_group = pygame.sprite.Group()
    goodtiles_group = pygame.sprite.Group()

    kills = 0
    level = load_level()
    player = generate_level()
    tower = TankTower()
    tr = Track()
    tr1 = Track(False)
    camera = Camera()
    target = Target()

    for i in range(10):
        Enemy()
    for i in range(30):
        Gun()
    for i in range(30):
        Baff()

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            keys = pygame.key.get_pressed()
            buttons = pygame.mouse.get_pressed()
            mouse = pygame.mouse.get_pos()
            if keys[pygame.K_ESCAPE]:
                terminate()
            if keys[pygame.K_d]:
                right = True
            else:
                right = False
            if keys[pygame.K_w]:
                up = True
            else:
                up = False
            if keys[pygame.K_a]:
                left = True
            else:
                left = False
            if keys[pygame.K_s]:
                down = True
            else:
                down = False
            if buttons[0]:
                if player.gun == 1:
                    fire = True
                if not cooldown:
                    if player.gun in (0, 2):
                        cooldown = 50
                        if not fire:
                            if player.gun == 0:
                                medium_shot.play()
                            else:
                                plasma_shot.play()
                            Bullet(player.gun)
                        fire = True
            else:
                fire = False
        player.move()
        if up or down or left or right:
            if not driving_playing:
                driving_playing = True
                driving.play(40)
        else:
            driving_playing = False
            driving.stop()
        if cooldown:
            cooldown -= 1
        if baff_cooldown0:
            baff_cooldown0 -= 1
        else:
            rotate_speed = 4
        if baff_cooldown1:
            baff_cooldown1 -= 1
        else:
            speed = 27
        if freeze_cooldown:
            freeze_cooldown -= 1
        if ratata_cooldown:
            ratata_cooldown -= 1
        if fire and player.gun == 1:
            if not ratata_playing:
                ratata_shot.play(40)
                ratata_playing = True
            if not ratata_cooldown:
                ratata_cooldown = 5
                Bullet(1)
                Bullet(1, True)
        else:
            ratata_shot.stop()
            ratata_playing = False
        drawScreen()


start_screen()
game_loop()
terminate()
