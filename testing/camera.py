import pygame as pg
from pygame.math import Vector2


class Player(pg.sprite.Sprite):

    def __init__(self, pos, walls, *groups):
        super().__init__(*groups)
        self.image = pg.Surface((30, 50))
        self.image.fill(pg.Color('dodgerblue'))
        self.rect = self.image.get_rect(center=pos)
        self.vel = Vector2(0, 0)
        self.pos = Vector2(pos)
        self.walls = walls
        self.camera = Vector2(0, 0)

    def update(self):
        self.camera -= self.vel  # Change the camera pos if we're moving.
        # Horizontal movement.
        self.pos.x += self.vel.x
        self.rect.centerx = self.pos.x
        # Change the rect and self.pos coords if we touched a wall.
        for wall in pg.sprite.spritecollide(self, self.walls, False):
            if self.vel.x > 0:
                self.rect.right = wall.rect.left
            elif self.vel.x < 0:
                self.rect.left = wall.rect.right
            self.pos.x = self.rect.centerx
            self.camera.x += self.vel.x  # Also move the camera back.

        # Vertical movement.
        self.pos.y += self.vel.y
        self.rect.centery = self.pos.y
        for wall in pg.sprite.spritecollide(self, self.walls, False):
            if self.vel.y > 0:
                self.rect.bottom = wall.rect.top
            elif self.vel.y < 0:
                self.rect.top = wall.rect.bottom
            self.pos.y = self.rect.centery
            self.camera.y += self.vel.y


class Wall(pg.sprite.Sprite):

    def __init__(self, x, y, w, h, *groups):
        super().__init__(*groups)
        self.image = pg.Surface((w, h))
        self.image.fill(pg.Color('sienna2'))
        self.rect = self.image.get_rect(topleft=(x, y))


def main():
    screen = pg.display.set_mode((640, 480))
    clock = pg.time.Clock()
    all_sprites = pg.sprite.Group()
    walls = pg.sprite.Group()
    for rect in ((100, 170, 90, 20), (200, 100, 20, 140),
                 (400, 60, 150, 100), (300, 470, 150, 100)):
        walls.add(Wall(*rect))
    all_sprites.add(walls)
    player = Player((320, 240), walls, all_sprites)

    done = False

    while not done:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                done = True
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_d:
                    player.vel.x = 5
                elif event.key == pg.K_a:
                    player.vel.x = -5
                elif event.key == pg.K_w:
                    player.vel.y = -5
                elif event.key == pg.K_s:
                    player.vel.y = 5
            elif event.type == pg.KEYUP:
                if event.key == pg.K_d and player.vel.x > 0:
                    player.vel.x = 0
                elif event.key == pg.K_a and player.vel.x < 0:
                    player.vel.x = 0
                elif event.key == pg.K_w and player.vel.y < 0:
                    player.vel.y = 0
                elif event.key == pg.K_s and player.vel.y > 0:
                    player.vel.y = 0

        all_sprites.update()

        screen.fill((30, 30, 30))
        for sprite in all_sprites:
            # Add the player's camera offset to the coords of all sprites.
            screen.blit(sprite.image, sprite.rect.topleft+player.camera)

        pg.display.flip()
        clock.tick(30)


if __name__ == '__main__':
    pg.init()
    main()
    pg.quit()
