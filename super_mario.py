import sys
import logging
try:
    import pygame_sdl2
    pygame_sdl2.import_as_pygame()
except:
    pass
import pygame
from pygame.locals import *
from gameobjects.vector2 import Vector2

class World(object):
    def __init__(self):
        self.bg_color = SCREEN_BK_COLOR
        self.next_eid = 1000
        self.entities = {}
        self.mario = None

    def add_entity(self, entity):
        entity.eid = self.next_eid
        self.entities[entity.eid] = entity
        self.next_eid += 1

    def remove_entity(self, entity):
        del self.entities[entity.eid]

    def get(self, entity_id):
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def update(self):
        for entity in self.entities.values():
            if entity.eid != self.mario.eid:
                entity.update()
        self.mario.update()

    def process_key(self, event):
        #only supported on pygame_sdl2
        try:
            if event.repeat:
                return
        except:
            pass
        self.mario.process_key(event)

    def render_with_etype(self, surface, etype):
        for entity in self.entities.itervalues():
            if entity.etype == etype:
                entity.render(surface)

    def render(self, surface):
        surface.fill(self.bg_color)
        render_etypes = [EntityType.GROUND, EntityType.BACKGROUND,
                         EntityType.STILL, EntityType.FOREGROUND,
                         EntityType.BODY, EntityType.ENEMY,
                         EntityType.MARIO]
        for etype in render_etypes:
            self.render_with_etype(surface, etype)

    def exceed_border(self, entity):
        w, h = entity.img.get_size()
        ul_x = entity.pos[0]
        ul_y = entity.pos[1] - h + 1
        br_x = entity.pos[0] + w - 1
        br_y = entity.pos[1]
        left_border = 1
        if ul_x <= left_border:
            entity.pos[0] = left_border
            return True
        right_border = ORIGINAL_SIZE[0]-2
        if br_x >= right_border:
            entity.pos[0] = right_border - w + 1
            return True
        return False

    def make_collision_entity_list(self, entity_in, target_etypes):
        entity_list = []

        for entity in self.entities.itervalues():
            if entity.etype not in target_etypes:
                continue
            if entity_in.eid == entity.eid:
                continue
            if pygame.Rect.colliderect(entity_in.rect, entity.rect):
                entity_list.append(entity)

        return entity_list

    def is_not_on_ground(self, entity):
        entity.rect.move_ip((0, 1))
        etypes = [EntityType.GROUND, EntityType.STILL, EntityType.ENEMY,\
                  EntityType.MARIO] #TODO remove mario
        collision_list = self.make_collision_entity_list(entity, etypes)
        entity.rect.move_ip((0, -1))

        if len(collision_list) == 0:
            return True
        else:
            return False

    def check_collision_x(self, entity, collision_list):
        for entity1 in collision_list:
            if entity.rect.left < entity1.rect.left < entity.rect.right:
                return (entity1, GameDef.DIRECTION_LEFT)
            if entity.rect.left < entity1.rect.right < entity.rect.right:
                return (entity1, GameDef.DIRECTION_RIGHT)
        return (None, None)

    def is_on_ground(self, entity, collision_list):
        for entity1 in collision_list:
            if entity.rect.top < entity1.rect.top < entity.rect.bottom:
                return entity1 
        else:
            return None

    def is_pushing_on(self, entity, collision_list):
        entity_list = []
        for entity1 in collision_list:
            if entity.rect.top < entity1.rect.bottom < entity.rect.bottom:
                entity_list.append(entity1)

        return entity_list

    def fix_collision_x(self, entity, entity1, direction):
        if direction == GameDef.DIRECTION_LEFT:
            offset_x = entity1.rect.left - entity.rect.right
        else:
            offset_x = entity1.rect.right - entity.rect.left
        entity.update_pos((offset_x, 0), with_direction=True)

    def fix_collision_y(self, entity, entity1, direction):
        if direction == GameDef.DIRECTION_UP:
            offset_y = entity1.rect.top - entity.rect.bottom
        else:
            offset_y = entity1.rect.bottom - entity.rect.top
        entity.update_pos((0, offset_y), with_direction=True)

    def calc_collision_align_x(self, entity, direction):
        collision_align = 0

        if direction == GameDef.DIRECTION_LEFT:
            collision_align = entity.rect.left
        elif direction == GameDef.DIRECTION_RIGHT:
            collision_align = entity.rect.right

        return collision_align

    def calc_collision_align_y(self, entity, direction):
        collision_align = 0

        if direction == GameDef.DIRECTION_UP:
            collision_align = entity.rect.top
        elif direction == GameDef.DIRECTION_DOWN:
            collision_align = entity.rect.bottom

        return collision_align

    def is_out_of_screen(self, entity):
        #do not conisder out of top
        rect = entity.rect
        if rect.right < 0 or rect.left > ORIGINAL_SIZE[0] or \
           rect.bottom < 0 or rect.top > ORIGINAL_SIZE[1]:
            return True
        else:
            return False

    def push_on_top_entity(self, entity):
        entity.rect.move_ip((0, -1))

        etypes = [EntityType.ENEMY]
        collision_list = self.make_collision_entity_list(entity, etypes)
        
        for entity1 in collision_list:
            if entity1.rect.top < entity.rect.top < entity1.rect.bottom:
                entity1.handle_push()
        
        entity.rect.move_ip((0, 1))

class GameEntity(object):
    def __init__(self, world, pos, name, etype, img):
        w, h = img.get_size()
        self.world = world
        self.name = name
        self.etype = etype
        self.img = img
        self.pos = Vector2(pos)
        self.heading = Vector2(1, 0)
        self.rect = build_rect_from_pos(pos, w, h)
        self.eid = 0

    def set_img(self, img):
        self.img = img
        #del self.rect
        w, h = self.img.get_size()
        self.rect = build_rect_from_pos(self.pos, w, h)

    def render(self, surface):
        h = self.img.get_height()
        pos = (self.pos[0], self.pos[1]-h+1)
        surface.blit(self.img, pos)

    def update(self):
        pass
    
    def get_pos(self):
        return self.pos

    def update_heading(self):
        pass

    def exceed_left_border_fix(self, offset):
        offset_x = offset[0]
        offset_y = offset[1]
        if (self.rect.left + offset[0]*self.heading[0]) < 0:
            offset_x = self.rect.left
        return (offset_x, offset_y)

    def exceed_right_border_fix(self, offset):
        offset_x = offset[0]
        offset_y = offset[1]
        right_border = ORIGINAL_SIZE[0] - 1
        if (self.rect.right + offset[0]*self.heading[0]) >= right_border:
            offset_x = right_border - self.rect.right
        return (offset_x, offset_y)

    def update_pos(self, offset, with_direction=False):
        self.update_heading()
        offset = self.exceed_left_border_fix(offset)
        offset = self.exceed_right_border_fix(offset)
        if with_direction == False:
            heading = self.heading
        else:
            heading = (1, 1)
        offset_vector = Vector2(offset[0]*heading[0], offset[1]*heading[1])
        self.pos += offset_vector
        self.rect.move_ip(offset_vector)

    def handle_push(self):
        pass

    def handle_stamp(self):
        pass

class EntityName(object):
    GROUND = "ground"
    WOOD = "wood"
    MARIO = "mario"
    PIPE = "pipe"
    BRICK = "brick"
    PLATE = "plate"
    ROCK = "rock"
    CLOUD = "cloud"
    GOOMBA = "goomba"

class EntityType(object):
    GROUND = "ground"
    BACKGROUND = "bg"
    FOREGROUND = "fg"
    MARIO = "mario"
    STILL = "still"
    ENEMY = "enemy"
    BODY = "body"

class GameRc(object):
    rock_png = "rock_16x16.png"
    brick_png = "brick_16x16.png"
    plate1_png = "plate1_16x16.png"
    plate2_png = "plate2_16x16.png"
    plate3_png = "plate3_16x16.png"
    plate4_png = "plate4_16x16.png"
    ground_block_png = "ground_block_16x16.png"
    wood1_png = "wood1_48x16.png"
    wood2_png = "wood2_80x35.png"
    cloud1_png = "cloud1_8x24.png"
    cloud2_png = "cloud2_16x24.png"
    cloud3_png = "cloud3_8x24.png"
    pipe1_png = "pipe1_32x15.png"
    pipe2_png = "pipe2_32x1.png"
    pipe3_png = "pipe3_32x2.png"
    mario1_png = "mario1_12x16.png"
    mario2_png = "mario2_13x15.png"
    mario3_png = "mario3_15x16.png"
    mario4_png = "mario4_13_16.png"
    mario5_png = "mario5_13x16.png"
    mario6_png = "mario6_16x16.png"
    goomba1_png = "goomba1_16x16.png"
    goomba2_png = "goomba2_16x7.png"
    koopa1_png = "koopa1_16x23.png"
    koopa2_png = "koopa2_16x24.png"
    koopa3_png = "koopa3_16x14.png"
    koopa4_png = "koopa4_16x14.png"

    def __init__(self):
        self.rock_img = get_img(self.rock_png)
        self.brick_img = get_img(self.brick_png)
        self.ground_block_img = get_img(self.ground_block_png)
        self.wood1_img = get_img(self.wood1_png)
        self.wood2_img = get_img(self.wood2_png)
        self.plate1_img = get_img(self.plate1_png)
        self.plate2_img = get_img(self.plate2_png)
        self.plate3_img = get_img(self.plate3_png)
        self.plate4_img = get_img(self.plate4_png)
        self.cloud1_img = get_img(self.cloud1_png)
        self.cloud2_img = get_img(self.cloud2_png)
        self.cloud3_img = get_img(self.cloud3_png)
        self.pipe1_img = get_img(self.pipe1_png)
        self.pipe2_img = get_img(self.pipe2_png)
        self.pipe3_img = get_img(self.pipe3_png)
        self.mario1_img = get_img(self.mario1_png)
        self.mario2_img = get_img(self.mario2_png)
        self.mario3_img = get_img(self.mario3_png)
        self.mario4_img = get_img(self.mario4_png)
        self.mario5_img = get_img(self.mario5_png)
        self.mario6_img = get_img(self.mario6_png)
        self.goomba1_img = get_img(self.goomba1_png)
        self.goomba2_img = get_img(self.goomba2_png)
        self.koopa1_img = get_img(self.koopa1_png)
        self.koopa2_img = get_img(self.koopa2_png)
        self.koopa3_img = get_img(self.koopa3_png)
        self.koopa4_img = get_img(self.koopa4_png)

class GameDef(object):
    DIRECTION_LEFT = -1
    DIRECTION_RIGHT = 1
    DIRECTION_UP = -1
    DIRECTION_DOWN = 1
    DIRECTION_NONE = 0

class Ground(GameEntity):
    def make_img(self, rows, columns):
        block_img = game_rc.ground_block_img
        block_w, block_h = block_img.get_size()
        w = block_w*columns
        h = block_h*rows
        img = pygame.Surface((w, h))
        for i in xrange(0, self.columns):
            for j in xrange(0, self.rows):
                img.blit(block_img, (block_w*i, block_h*j))
        return img

    def __init__(self, world, pos, rows, columns):
        self.rows = rows
        self.columns = columns
        img = self.make_img(rows, columns)
        GameEntity.__init__(self, world, pos, EntityName.GROUND,
                            EntityType.GROUND, img)

class Wood(GameEntity):
    def __init__(self, world, pos, img):
        GameEntity.__init__(self, world, pos, EntityName.WOOD,
                            EntityType.BACKGROUND, img)

class Cloud(GameEntity):
    def make_img(self, level):
        w1,h = game_rc.cloud1_img.get_size()
        w2 = game_rc.cloud2_img.get_width()
        w3 = game_rc.cloud3_img.get_width()

        w = w1 + w2 * level + w3
        img = pygame.Surface((w, h), SRCALPHA)

        x = 0
        img.blit(game_rc.cloud1_img, (x, 0))
        x += w1
        for i in xrange(0, level):
            img.blit(game_rc.cloud2_img, (x, 0))
            x += w2
        img.blit(game_rc.cloud3_img, (x, 0))

        return img

    def __init__(self, world, pos, level=1):
        img = self.make_img(level)
        GameEntity.__init__(self, world, pos, EntityName.CLOUD,
                            EntityType.BACKGROUND, img)

class Pipe(GameEntity):
    def make_img(self, level):
        w, h1 = game_rc.pipe1_img.get_size()
        h2 = game_rc.pipe2_img.get_height()
        h3 = game_rc.pipe3_img.get_height()
        h = h1 + h2 + h3*level

        img = pygame.Surface((w, h), SRCALPHA)
        y = 0
        img.blit(game_rc.pipe1_img, (0, y))
        y += h1
        img.blit(game_rc.pipe2_img, (0, y))
        y += h2
        for i in xrange(0, level):
            img.blit(game_rc.pipe3_img, (0, y))
            y += h3
        return img

    def __init__(self, world, pos, level=1):
        img = self.make_img(level)
        GameEntity.__init__(self, world, pos, EntityName.PIPE,
                            EntityType.STILL, img)
        w, h = img.get_size()
        self.reinit_rect(pos, w, h)

    def reinit_rect(self, pos, w, h):
        w2 = game_rc.pipe2_img.get_width()
        w_offset = (w2 - w) / 2
        left, bottom = pos
        left += w_offset
        self.rect = build_rect_from_pos((left, bottom), w2, h)

class Rock(GameEntity):
    def __init__(self, world, pos):
        img = game_rc.rock_img
        GameEntity.__init__(self, world, pos, EntityName.ROCK,
                            EntityType.STILL, img)

class StillBounceCtrl(object):
    def __init__(self, entity):
        self.entity = entity
        self.bounce_offset = [(5, -1), (4, 0), (4, 1), (1, 2), (1, -1)]
        self.bounce_offset_idx = 0
        self.bounce_cur_frame = 0
        self.started = False

    def start(self):
        if self.started == True:
            return

        self.bounce_offset_idx = 0
        self.bounce_cur_frame = 0
        self.started = True

    def update(self):
        if self.started == False:
            return

        offset_data = self.bounce_offset[self.bounce_offset_idx]
        offset_y = offset_data[1]
        self.entity.update_pos((0, offset_y), with_direction=True)

        self.bounce_cur_frame += 1
        if self.bounce_cur_frame < offset_data[0]:
            return

        self.bounce_cur_frame = 0
        self.bounce_offset_idx += 1
        if self.bounce_offset_idx >= len(self.bounce_offset):
            self.started = False
            return

class Brick(GameEntity):
    def __init__(self, world, pos):
        img = game_rc.brick_img
        GameEntity.__init__(self, world, pos, EntityName.BRICK,
                            EntityType.STILL, img)

        self.bounce_ctrl = StillBounceCtrl(self)
    
    def handle_push(self):
        self.bounce_ctrl.start()
        self.world.push_on_top_entity(self)

    def update(self):
        self.bounce_ctrl.update()

class Plate(GameEntity):
    def __init__(self, world, pos):
        self.img_set = [game_rc.plate1_img, game_rc.plate2_img,\
                        game_rc.plate3_img]
        img = self.img_set[0]
        GameEntity.__init__(self, world, pos, EntityName.PLATE,
                            EntityType.STILL, img)

        self.is_dead = False
        self.shine_frames = [24, 8, 8]
        self.shine_idx = 0
        self.shine_idx_min = 0
        self.shine_idx_max = len(self.shine_frames)-1
        self.shine_idx_inc = 1
        self.shine_cur_frame = 0
        self.bounce_ctrl = StillBounceCtrl(self)

    def handle_push(self):
        if self.is_dead == True:
            return
        self.bounce_ctrl.start()
        self.is_dead = True
        self.img = game_rc.plate4_img
        self.world.push_on_top_entity(self)

    def shine(self):
        self.img = self.img_set[self.shine_idx]

        self.shine_cur_frame += 1
        if self.shine_cur_frame < self.shine_frames[self.shine_idx]:
            return

        self.shine_cur_frame = 0

        if self.shine_idx == self.shine_idx_max:
            self.shine_idx_inc = -1
        elif self.shine_idx == self.shine_idx_min:
            self.shine_idx_inc = 1

        self.shine_idx += self.shine_idx_inc

    def update(self):
        if self.is_dead == True:
            self.bounce_ctrl.update()
        else:
            self.shine()

class GoombaState(object):
    def __init__(self, state_machine, state_name):
        self.state_machine = state_machine
        self.goomba = state_machine.goomba
        self.state_name = state_name

        self.img_set = []
        self.img_idx = 0

    def run(self):
        pass

    def set_goomba_img(self):
        self.goomba.set_img(self.img_set[self.img_idx])

    def entry_action(self):
        self.set_goomba_img()

    def handle_stamp(self):
        return None

    def handle_push(self):
        return None

class GoombaNormalState(GoombaState):
    MOVE_DOWN_MAX = 5

    def __init__(self, state_machine):
        GoombaState.__init__(self, state_machine,
                             state_machine.normal_state_name)
        
        img_flipped = pygame.transform.flip(game_rc.goomba1_img, True, False)
        self.img_set = [img_flipped, game_rc.goomba1_img]
        self.img_idx = 0
        self.img_cnt = len(self.img_set)

        self.offset_x = 1
        self.move_counter = 0
        self.move_rate = 2

        self.flip_counter = 0
        self.flip_rate = 8

        self.fall_data = [(2, 1), (8, 3), (0, 5)]
        self.fall_cycle = 0
        self.fall_cur_frame = 0

    def calc_offset_x(self):
        self.move_counter += 1
        self.move_counter %= self.move_rate
        if self.move_counter == 0:
            return self.offset_x
        else:
            return 0

    def calc_offset_y(self):
        if self.goomba.speed_y == 0:
            return 0

        cur_fall_data = self.fall_data[self.fall_cycle]
        offset_y = cur_fall_data[1]

        self.fall_cur_frame += 1
        if self.fall_cur_frame < cur_fall_data[0]:
            return offset_y
        
        self.fall_cur_frame = 0
        if cur_fall_data[0] > 0:
            self.fall_cycle += 1

        return offset_y

    def move_goomba(self):
        offset_x = self.calc_offset_x() * self.goomba.heading_x
        offset_y = self.calc_offset_y()
        self.goomba.update_pos((offset_x, offset_y), with_direction=True)

    def flip_img(self):
        self.flip_counter += 1
        self.flip_counter %= self.flip_rate

        if self.flip_counter == 0:
            self.img_idx += 1
        self.img_idx %= self.img_cnt

        self.set_goomba_img()

    def run(self):
        self.move_goomba()
        self.flip_img()
        self.check_collision()
        self.check_on_ground()
        self.check_exceed_border()

    def check_exceed_border(self):
        goomba = self.goomba
        world = goomba.world

        if world.exceed_border(goomba) == False:
            return

        if goomba.rect.left == 1:
            goomba.heading_x = 1
        else:
            goomba.heading_x = -1

    def check_on_ground(self):
        goomba = self.goomba
        world = goomba.world
        if world.is_not_on_ground(goomba):
            goomba.speed_y = 1

    def check_collision(self):
        world = self.goomba.world

        etypes = [EntityType.GROUND, EntityType.STILL, EntityType.ENEMY,\
                  EntityType.MARIO, EntityType.BODY] #TODO remove mario
        collision_list = world.make_collision_entity_list(self.goomba, \
                                                          etypes)
        if len(collision_list) == 0:
            return

        self.check_collision_y(collision_list)
        self.check_collision_x(collision_list)

    def check_collision_y(self, collision_list):
        goomba = self.goomba
        if goomba.speed_y == 0:
            return
        
        world = goomba.world
        entity = world.is_on_ground(goomba, collision_list)
        if entity is None:
            return

        offset_y = entity.rect.top - goomba.rect.bottom
        if abs(offset_y) > self.MOVE_DOWN_MAX:
            return

        goomba.speed_y = 0
        world.fix_collision_y(goomba, entity, GameDef.DIRECTION_UP)

    def check_collision_x(self, collision_list):
        goomba = self.goomba
        world = goomba.world

        (entity, direction) = world.check_collision_x(goomba, collision_list)
        if entity is None:
            return

        if pygame.Rect.colliderect(goomba.rect, entity.rect) == False:
            return

        world.fix_collision_x(goomba, entity, direction)
        goomba.heading_x = -goomba.heading_x

    def handle_stamp(self):
        state_machine = self.state_machine
        return state_machine.states[state_machine.body_state_name]

    def handle_push(self):
        state_machine = self.state_machine
        return state_machine.states[state_machine.dead_state_name]

class GoombaDeadState(GoombaState):
    def __init__(self, state_machine):
        GoombaState.__init__(self, state_machine,
                             state_machine.dead_state_name)

        img = pygame.transform.flip(game_rc.goomba1_img, False, True)
        self.img_set = [img]
        self.img_idx = 0

        self.offset_x = 0
        self.offset_y = 0

        self.offset_y_data = [(6, -2), (3, -1), (3, 0), (2, 1), (8, 3), (0, 5)]
        self.offset_y_idx = 0
        self.offset_y_frame = 0
    
    def entry_action(self):
        GoombaState.entry_action(self)
        
        goomba = self.goomba
        mario = goomba.world.mario

        if mario.rect.center[0] > goomba.rect.center[0]:
            self.offset_x = -1
        else:
            self.offset_x = 1

    def calc_offset_y(self):
        offset_data = self.offset_y_data[self.offset_y_idx]
        self.offset_y = offset_data[1]

        self.offset_y_frame += 1
        if self.offset_y_frame < offset_data[0]:
            return

        self.offset_y_frame = 0
        if offset_data[0] > 0:
            self.offset_y_idx += 1

    def run(self):
        goomba = self.goomba
        world = goomba.world

        self.calc_offset_y()
        goomba.update_pos((self.offset_x, self.offset_y), with_direction=True)
        if world.is_out_of_screen(goomba):
            world.remove_entity(goomba)

class GoombaBodyState(GoombaState):
    def __init__(self, state_machine):
        GoombaState.__init__(self, state_machine,
                             state_machine.body_state_name)

        self.img_set = [game_rc.goomba2_img]
        self.img_idx = 0

        self.live_frames = 32

    def run(self):
        goomba = self.goomba
        world = goomba.world

        self.live_frames -= 1
        if self.live_frames == 0:
            world.remove_entity(goomba)

class GoombaStateMachine(object):
    normal_state_name = "normal_state"
    dead_state_name = "dead_state"
    body_state_name = "body_state"

    def __init__(self, goomba):
        self.goomba = goomba
        self.states = {}

        self.add_state(GoombaNormalState(self))
        self.add_state(GoombaDeadState(self))
        self.add_state(GoombaBodyState(self))

        self.active_state = None
        self.switch_to(self.states[self.normal_state_name])

    def add_state(self, state):
        self.states[state.state_name] = state

    def switch_to(self, state):
        self.active_state = state
        self.active_state.entry_action()

    def think(self):
        self.active_state.run()

    def handle_stamp(self):
        new_state = self.active_state.handle_stamp()
        if new_state is not None:
            self.goomba.etype = EntityType.BODY
            self.switch_to(new_state)

    def handle_push(self):
        new_state = self.active_state.handle_push()
        if new_state is not None:
            self.goomba.etype = EntityType.FOREGROUND
            self.switch_to(new_state)

class Goomba(GameEntity):
    def __init__(self, world, pos):
        GameEntity.__init__(self, world, pos, EntityName.GOOMBA,
                            EntityType.ENEMY, game_rc.goomba1_img)

        self.heading_x = -1
        self.speed_x = 1 #no use, just x/y pair
        self.speed_y = 0 #0/1, indicate move on y
        self.state_machine = GoombaStateMachine(self)
    
    def set_img(self, img):
        self.img = img

    def update(self):
        self.state_machine.think()

    def handle_stamp(self):
        self.state_machine.handle_stamp()

    def handle_push(self):
        self.state_machine.handle_push()

class MarioState(object):
    def __init__(self, state_machine, state_name, img_set,
                 transform_rate, transform_offset, move_offset):
        self.state_machine = state_machine
        self.state_name = state_name
        self.img_idx = 0
        self.img_set = img_set
        self.transform_counter = 0
        self.transform_rate = transform_rate
        self.transform_offset = transform_offset
        self.move_offset = move_offset
        self.state_detail = "normal"

    def set_mario_img(self):
        self.state_machine.mario.set_img(self.img_set[self.img_idx])

    def entry_action(self, img_idx):
        self.transform_counter = 0
        img_idx %= len(self.img_set)
        self.img_idx = img_idx
        self.set_mario_img()
        self.state_machine.apply_collision_align()

    def update(self):
        pass

    def calc_transform_offset(self):
        mario = self.state_machine.mario
        if mario.speed_x >= 0: #moving right or not moving
            offset = self.transform_offset[self.img_idx]
        else:
            next_img_idx = (self.img_idx+1) % len(self.img_set)
            next_img_w = self.img_set[next_img_idx].get_width()
            w = self.img_set[self.img_idx].get_width()
            offset = self.transform_offset[self.img_idx]
            offset += (next_img_w - w)
        return (offset, 0)

    def calc_move_offset(self):
        return (self.move_offset, 0)

    def calc_offset(self):
        self.transform_counter += 1
        self.transform_counter %= self.transform_rate
        if self.transform_rate != 1 and self.transform_counter == 0:
            offset = self.calc_transform_offset()
            self.img_idx += 1
            self.img_idx %= len(self.img_set)
        else:
            offset = self.calc_move_offset()

        self.set_mario_img()
        return offset

    def move_state_transform(self):
        return None

    def collision_state_transform(self, collision_list):
        return None

    def calc_mario_acce_x(self, mario, ctrl_x, speed_x):
        acce_x = 0
        if speed_x == 0 and ctrl_x == 0:
            return 0
        speed_direction = mario.get_speedx_direction()
        if ctrl_x != 0:
            if speed_x == 0 or ctrl_x == speed_direction:
                acce_x = ctrl_x * mario.ACCE_INC
            else:
                acce_x = -1 * speed_direction * mario.ACCE_DEC_FAST
        else:
            acce_x = -1 * speed_direction * mario.ACCE_DEC_SLOW
        return acce_x

    def calc_mario_speed_x(self, mario, acce_x, speed_x):
        speed_max = mario.SPEED_RUN_FAST_MAX
        speed_direction = mario.get_speedx_direction()
        if speed_x == 0 or acce_x == 0:
            speed_x += acce_x
            return speed_x
        if acce_x * speed_direction > 0:
            speed_x += acce_x
            speed_x = min(abs(speed_x), speed_max)
            speed_x *= speed_direction
        else:
            if abs(acce_x) > abs(speed_x):
                speed_x = 0
            else:
                speed_x += acce_x
        return speed_x

    def update_mario_due_ctrl_x(self):
        mario = self.state_machine.mario
        ctrl_x = mario.get_ctrl_x()
        speed_x = mario.get_speed_x()
        acce_x = self.calc_mario_acce_x(mario, ctrl_x, speed_x)
        speed_x = self.calc_mario_speed_x(mario, acce_x, speed_x)
        mario.set_acce_x(acce_x)
        mario.set_speed_x(speed_x)

    def update_mario_due_ctrl_y(self):
        mario = self.state_machine.mario
        ctrl_y = mario.get_ctrl_y()
        if ctrl_y == GameDef.DIRECTION_UP:
            mario.set_speed_y_up()

    def exit_action(self):
        pass

class MarioStandState(MarioState):
    def __init__(self, state_machine):
        state_name = state_machine.stand_state_name
        img_set = [game_rc.mario1_img]
        transform_rate = 1
        transform_offset = [0]
        move_offset = 0
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)

    def move_state_transform(self):
        state_machine = self.state_machine
        mario = state_machine.mario
        speed_x, speed_y = mario.get_speed()

        states = state_machine.states
        if speed_y != 0:
            return states[state_machine.fly_state_name]
        elif speed_x != 0:
            return states[state_machine.walk_state_name]
        else:
            return None

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world
        states = state_machine.states

        if world.is_not_on_ground(mario):
            return states[state_machine.fall_state_name]
        else:
            return None

class MarioWalkState(MarioState):
    state_detail_walk = "normal"
    state_detail_slow_run = "slow_run"
    state_detail_fast_run = "fast_run"

    transform_offset = [0, 5, 1]
    walk_transform_rate = 4
    walk_move_offset = 1
    slow_run_transform_rate = 3
    slow_run_move_offset = 1
    fast_run_tranform_rate = 2
    fast_run_move_offset = 2

    def __init__(self, state_machine):
        state_name = state_machine.walk_state_name
        img_set = [game_rc.mario2_img, game_rc.mario3_img, game_rc.mario4_img]
        transform_rate = self.walk_transform_rate
        transform_offset = self.transform_offset
        move_offset = self.walk_move_offset
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)
        self.state_detail = self.state_detail_walk

    def set_to_normal_walk(self):
        self.state_detail = self.state_detail_walk
        self.move_offset = self.walk_move_offset
        self.transform_rate = self.walk_transform_rate

    def set_to_slow_run(self):
        self.state_detail = self.state_detail_slow_run
        self.move_offset = self.slow_run_move_offset
        self.transform_rate = self.slow_run_transform_rate

    def set_to_fast_run(self):
        self.state_detail = self.state_detail_fast_run
        self.move_offset = self.fast_run_move_offset
        self.transform_rate = self.fast_run_tranform_rate

    def update(self):
        mario = self.state_machine.mario
        if abs(mario.speed_x) <= mario.SPEED_WALK_MAX:
            self.set_to_normal_walk()
        elif abs(mario.speed_x) <= mario.SPEED_RUN_SLOW_MAX:
            self.set_to_slow_run()
        elif abs(mario.speed_x) <= mario.SPEED_RUN_FAST_MAX:
            self.set_to_fast_run()

    def move_state_transform(self):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world
        speed_x, speed_y = mario.get_speed()
        acce_x = mario.get_acce_x()
        states = state_machine.states

        if world.is_not_on_ground(mario):
            return states[state_machine.fall_state_name]

        if speed_y != 0:
            return states[state_machine.fly_state_name]
        elif speed_x == 0:
            return states[state_machine.stand_state_name]
        elif abs(acce_x) == mario.ACCE_DEC_FAST:
            return states[state_machine.brake_state_name]
        else:
            return None

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        (entity, direction) = world.check_collision_x(mario, collision_list)
        if entity is None:
            return None

        collision_align = world.calc_collision_align_x(entity, direction)
        state_machine.add_collision_align_x(collision_align, direction)

        return state_machine.states[state_machine.hit_wall_state_name]

class MarioBrakeState(MarioState):
    def __init__(self, state_machine):
        state_name = state_machine.brake_state_name
        img_set = [game_rc.mario5_img]
        transform_rate = 1
        transform_offset = [0]
        move_offset = 2
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)

        self.end_frames = 12

    def entry_action(self, img_idx):
        MarioState.entry_action(self, img_idx)
        self.end_frames = 12

    def move_state_transform(self):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world
        speed_x, speed_y = mario.get_speed()
        acce_x = mario.get_acce_x()
        states = state_machine.states

        if world.is_not_on_ground(mario):
            return states[state_machine.fall_state_name]

        if speed_x == 0:
            self.end_frames -= 1

        if speed_y != 0:
            return states[state_machine.fly_state_name]
        elif speed_x == 0 and self.end_frames <= 0:
            return states[state_machine.stand_state_name]
        elif abs(acce_x) != mario.ACCE_DEC_FAST:
            return states[state_machine.walk_state_name]
        else:
            return None

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        (entity, direction) = world.check_collision_x(mario, collision_list)
        if entity is None:
            return None

        collision_align = world.calc_collision_align_x(entity, direction)
        state_machine.add_collision_align_x(collision_align, direction)

        return state_machine.states[state_machine.stand_state_name]

class MarioHitWallState(MarioState):
    def __init__(self, state_machine):
        state_name = state_machine.hit_wall_state_name
        img_set = [game_rc.mario2_img, game_rc.mario3_img, game_rc.mario4_img]
        transform_rate = 7
        transform_offset = [-2, 2, 0]
        move_offset = 0
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)

    def limit_mario_speed(self):
        mario = self.state_machine.mario
        if mario.speed_x < -mario.SPEED_WALK_MAX:
            mario.set_speed_x(-mario.SPEED_WALK_MAX)
        elif mario.speed_x > mario.SPEED_WALK_MAX:
            mario.set_speed_x(mario.SPEED_WALK_MAX)

    def entry_action(self, img_idx):
        MarioState.entry_action(self, img_idx)
        mario = self.state_machine.mario
        self.limit_mario_speed()

    def update_mario_due_ctrl_x(self):
        MarioState.update_mario_due_ctrl_x(self)
        self.limit_mario_speed()

    def move_state_transform(self):
        state_machine = self.state_machine
        mario = state_machine.mario
        speed_x, speed_y = mario.get_speed()
        acce_x = mario.get_acce_x()

        states = state_machine.states
        if speed_y != 0:
            return states[state_machine.fly_state_name]
        elif speed_x == 0:
            return states[state_machine.stand_state_name]
        else:
            return None

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        (entity, direction) = world.check_collision_x(mario, collision_list)
        if entity is not None:
            world.fix_collision_x(mario, entity, direction)

        return None

class MarioFlyState(MarioState):
    POWER_MIN = 2
    POWER_MAX = 14
    FULL_POWER_FRAMES = 7
    POWER_MOVE_OFFSET = 4
    MOVE_DOWN_MAX_OFFSET = 5
    MOVE_UP_MAX_OFFSET = 5

    def __init__(self, state_machine):
        state_name = state_machine.fly_state_name
        img_set = [game_rc.mario6_img]
        transform_rate = 1
        transform_offset = [0]
        move_offset = 0
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)
        self.power = 0
        self.power_data = []
        # total_cycles/each_cycle_move_pixel/each_cycle_has_frames
        #self.power_full_up_data = [(7, 3, 1), (7, 2, 1), (3, 1, 3), (6, 0, 1)]
        self.power_up_data_speed = [(7, 2, 1), (3, 1, 1), (3, 0, 1)]
        self.power_up_data_no_speed = [(7, 2, 1), (3, 1, 3), (6, 0, 1)]
        self.power_up_data_len = len(self.power_up_data_speed)
        self.power_down_data = [(2, 1, 1), (8, 3, 1), (0, 5, 1)]

        self.power_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.offset_x = 0
        self.offset_y = 0

        self.speed_x_counter = 0

    def entry_action(self, img_idx):
        MarioState.entry_action(self, img_idx)
        self.power = 0
        self.power_data = []
        self.power_up_data = []
        self.power_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.speed_x_counter = 0
        self.offset_y = self.POWER_MOVE_OFFSET

    def set_power_data(self):
        mario = self.state_machine.mario
        speed_x = mario.get_speed_x()
        if abs(speed_x) <= mario.SPEED_WALK_MAX:
            power_up_data = self.power_up_data_no_speed
        else:
            power_up_data = self.power_up_data_speed

        self.power = max(self.POWER_MIN, self.power)
        self.power = min(self.POWER_MAX, self.power)
        f = (float(self.power)/self.POWER_MAX)**2
        up_data = map(lambda x:(max(int(x[0]*f), 1), x[1], x[2]),
                      power_up_data)
        self.power_data += up_data
        self.power_data += self.power_down_data

    def set_offset_y_on_cycle(self):
        cur_data = self.power_data[self.power_data_idx]
        if cur_data[2] > 1 and self.cur_frame != 0:
            self.offset_y = 0
        else:
            self.offset_y = cur_data[1]

    def run_cycle(self):
        cur_data = self.power_data[self.power_data_idx]
        self.total_frames += 1
        self.cur_frame += 1
        self.state_detail = "%d, %d, %d, %d"%(self.total_frames,
                                              self.power_data_idx,
                                              self.cur_cycle, self.cur_frame)

        target_frames = cur_data[2]
        if target_frames > 1 and self.cur_frame < target_frames:
            return

        self.cur_frame = 0
        self.cur_cycle += 1

        target_cycle = cur_data[0]
        if target_cycle == 0 or self.cur_cycle < target_cycle:
            return

        self.cur_cycle = 0
        self.power_data_idx += 1

    def power_inc_end(self):
        mario = self.state_machine.mario
        if self.power > self.POWER_MAX:
            return True
        if mario.get_ctrl_y() == Mario.DIRECTION_NONE:
            return True
        return False

    def update_y(self):
        if self.power == self.FULL_POWER_FRAMES:
            self.offset_y -= 1
        self.power += 1
        if self.power_inc_end() == False:
            return;
        if len(self.power_data) == 0:
            self.set_power_data()
        self.set_offset_y_on_cycle()
        self.run_cycle()

    def update_x(self):
        mario = self.state_machine.mario
        speed_x = abs(mario.get_speed_x())
        if speed_x == 0:
            self.offset_x = 0
        elif speed_x <= mario.SPEED_WALK_MAX:
            self.speed_x_counter %= 2
            self.speed_x_counter += 1
            if self.speed_x_counter == 0:
                self.offset_x = 1
            else:
                self.offset_x = 0
        elif speed_x <= mario.SPEED_RUN_SLOW_MAX:
            self.offset_x = 1
        elif speed_x <= mario.SPEED_RUN_FAST_MAX:
            self.offset_x = 2

    def update(self):
        self.update_x()
        self.update_y()

    def calc_move_offset(self):
        return (self.offset_x, self.offset_y)

    def move_state_transform(self):
        return None

    def stamp_collision_list(self, collision_list):
        mario = self.state_machine.mario

        stamp_enemy = False
        for entity in collision_list:
            offset_y = entity.rect.top - mario.rect.bottom
            if abs(offset_y) > self.MOVE_DOWN_MAX_OFFSET:
                continue
            if mario.rect.top < entity.rect.top < mario.rect.bottom:
                if entity.etype == EntityType.ENEMY:
                    stamp_enemy = True
                entity.handle_stamp()

        if stamp_enemy:
            mario.set_speed_y_up()
            direction = mario.get_speedx_direction()
            mario.set_speed_x(mario.SPEED_RUN_FAST_MAX*direction)

    def collision_state_transform_y(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        entity = world.is_on_ground(mario, collision_list)
        if entity == None:
            return None

        self.stamp_collision_list(collision_list)

        direction = GameDef.DIRECTION_UP
        collision_align = world.calc_collision_align_y(entity, direction)

        offset_y = collision_align - mario.rect.bottom
        if abs(offset_y) > self.MOVE_DOWN_MAX_OFFSET:
            return None

        state_machine.add_collision_align_y(collision_align, direction)
        return state_machine.states[state_machine.stand_state_name]

    def push_collision_entities(self, entity_list):
        mario = self.state_machine.mario
        for entity in entity_list:
            dist = abs(mario.rect.center[0]-entity.rect.center[0])
            if dist <= 8:
                entity.handle_push()

    def check_collision_push(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        pushed_entity_list = world.is_pushing_on(mario, collision_list)
        if len(pushed_entity_list) == 0:
            return False

        pushed_entity0 = pushed_entity_list[0]
        offset_y = mario.rect.top - pushed_entity0.rect.bottom
        if abs(offset_y) > self.MOVE_UP_MAX_OFFSET:
            return False

        world.fix_collision_y(mario, pushed_entity_list[0],
                              GameDef.DIRECTION_DOWN)

        self.power_data_idx = self.power_up_data_len
        self.cur_cycle = 0
        self.cur_frame = 0

        self.push_collision_entities(pushed_entity_list)
        return True

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        transform_state = None
        collision_push = False
        if mario.get_speedy_direction() == GameDef.DIRECTION_DOWN:
            transform_state = self.collision_state_transform_y(collision_list)
        else:
            collision_push = self.check_collision_push(collision_list)

        if collision_push:
            return None

        (entity, direction) = world.check_collision_x(mario, collision_list)
        if entity is not None and transform_state is None:
            world.fix_collision_x(mario, entity, direction)
            return None

        return transform_state

    def calc_mario_acce_x(self, mario, ctrl_x, speed_x):
        acce_x = 0
        if speed_x == 0 and ctrl_x == 0:
            return 0
        speed_direction = mario.get_speedx_direction()
        if ctrl_x != 0:
            if speed_x == 0 or ctrl_x == speed_direction:
                acce_x = ctrl_x * mario.ACCE_INC
            elif ctrl_x == -speed_direction:
                acce_x = -1 * speed_direction * mario.ACCE_DEC_SLOW
        return acce_x

    def calc_mario_speed_x(self, mario, acce_x, speed_x):
        speed_max = mario.SPEED_RUN_FAST_MAX
        speed_direction = mario.get_speedx_direction()
        if speed_x == 0 or acce_x == 0:
            speed_x += acce_x
            return speed_x
        if acce_x * speed_direction > 0:
            speed_x += acce_x
            speed_x = min(abs(speed_x), speed_max)
            speed_x *= speed_direction
        else:
            if abs(acce_x) > abs(speed_x):
                speed_x = 0
            else:
                speed_x += acce_x
        return speed_x

    def update_mario_due_ctrl_x(self):
        mario = self.state_machine.mario
        ctrl_x = mario.get_ctrl_x()
        speed_x = mario.get_speed_x()
        acce_x = self.calc_mario_acce_x(mario, ctrl_x, speed_x)
        speed_x = self.calc_mario_speed_x(mario, acce_x, speed_x)
        mario.set_acce_x(acce_x)
        mario.set_speed_x(speed_x)

    def update_mario_due_ctrl_y(self):
        mario = self.state_machine.mario
        if self.power_data_idx < self.power_up_data_len:
            mario.set_speed_y_up()
        else:
            mario.set_speed_y_down()

    def exit_action(self):
        mario = self.state_machine.mario
        if mario.speed_y == GameDef.DIRECTION_DOWN:
            mario.zero_speed_y() #if up, it's bounce case
            speed_x = mario.get_speed_x()/2
            mario.set_speed_x(speed_x)

class MarioFallState(MarioState):
    MOVE_DOWN_MAX_OFFSET = 5

    def __init__(self, state_machine):
        state_name = state_machine.fall_state_name
        img_set = [game_rc.mario2_img, game_rc.mario3_img, game_rc.mario4_img]
        transform_rate = 1
        transform_offset = [0, 0, 0]
        move_offset = 0
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)
        self.fall_data = [(2, 1, 1), (8, 3, 1), (0, 5, 1)]

        self.fall_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.offset_x = 0
        self.offset_y = 0

    def entry_action(self, img_idx):
        MarioState.entry_action(self, img_idx)
        self.fall_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.speed_x_counter = 0
        self.offset_y = 0
        self.state_machine.mario.set_speed_y_down()

    def set_offset_y_on_cycle(self):
        cur_data = self.fall_data[self.fall_data_idx]
        if cur_data[2] > 1 and self.cur_frame != 0:
            self.offset_y = 0
        else:
            self.offset_y = cur_data[1]

    def run_cycle(self):
        cur_data = self.fall_data[self.fall_data_idx]
        self.total_frames += 1
        self.cur_frame += 1
        self.state_detail = "%d, %d, %d, %d"%(self.total_frames,
                                              self.fall_data_idx,
                                              self.cur_cycle, self.cur_frame)

        target_frames = cur_data[2]
        if target_frames > 1 and self.cur_frame < target_frames:
            return

        self.cur_frame = 0
        self.cur_cycle += 1

        target_cycle = cur_data[0]
        if target_cycle == 0 or self.cur_cycle < target_cycle:
            return

        self.cur_cycle = 0
        self.fall_data_idx += 1

    def update_y(self):
        self.set_offset_y_on_cycle()
        self.run_cycle()

    def update_x(self):
        mario = self.state_machine.mario
        speed_x = abs(mario.get_speed_x())
        if speed_x == 0:
            self.offset_x = 0
        elif speed_x <= mario.SPEED_WALK_MAX:
            self.speed_x_counter %= 2
            self.speed_x_counter += 1
            if self.speed_x_counter == 0:
                self.offset_x = 1
            else:
                self.offset_x = 0
        elif speed_x <= mario.SPEED_RUN_SLOW_MAX:
            self.offset_x = 1
        elif speed_x <= mario.SPEED_RUN_FAST_MAX:
            self.offset_x = 2

    def update(self):
        self.update_x()
        self.update_y()

    def calc_move_offset(self):
        return (self.offset_x, self.offset_y)

    def move_state_transform(self):
        return None

    def stamp_collision_list(self, collision_list):
        mario = self.state_machine.mario

        stamp_enemy = False
        for entity in collision_list:
            offset_y = entity.rect.top - mario.rect.bottom
            if abs(offset_y) > self.MOVE_DOWN_MAX_OFFSET:
                continue
            if mario.rect.top < entity.rect.top < mario.rect.bottom:
                if entity.etype == EntityType.ENEMY:
                    stamp_enemy = True
                entity.handle_stamp()

        if stamp_enemy:
            direction = mario.get_speedx_direction()
            mario.set_speed_x(mario.SPEED_RUN_SLOW_MAX*direction)
            mario.set_speed_y_up()

    def collision_state_transform_y(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        entity = world.is_on_ground(mario, collision_list)
        if entity == None:
            return None

        self.stamp_collision_list(collision_list)

        direction = GameDef.DIRECTION_UP
        collision_align = world.calc_collision_align_y(entity, direction)

        offset_y = collision_align - mario.rect.bottom
        if abs(offset_y) > self.MOVE_DOWN_MAX_OFFSET:
            return None

        state_machine.add_collision_align_y(collision_align, direction)
        return state_machine.states[state_machine.stand_state_name]

    def collision_state_transform(self, collision_list):
        state_machine = self.state_machine
        mario = state_machine.mario
        world = mario.world

        transform_state = self.collision_state_transform_y(collision_list)

        (entity, direction) = world.check_collision_x(mario, collision_list)
        if entity is not None and transform_state is None:
            world.fix_collision_x(mario, entity, direction)
            return None

        return transform_state

    def calc_mario_acce_x(self, mario, ctrl_x, speed_x):
        acce_x = 0
        if speed_x == 0 and ctrl_x == 0:
            return 0
        speed_direction = mario.get_speedx_direction()
        if ctrl_x != 0:
            if speed_x == 0 or ctrl_x == speed_direction:
                acce_x = ctrl_x * mario.ACCE_INC
            elif ctrl_x == -speed_direction:
                acce_x = -1 * speed_direction * mario.ACCE_DEC_SLOW
        return acce_x

    def calc_mario_speed_x(self, mario, acce_x, speed_x):
        speed_max = mario.SPEED_RUN_FAST_MAX
        speed_direction = mario.get_speedx_direction()
        if speed_x == 0 or acce_x == 0:
            speed_x += acce_x
            return speed_x
        if acce_x * speed_direction > 0:
            speed_x += acce_x
            speed_x = min(abs(speed_x), speed_max)
            speed_x *= speed_direction
        else:
            if abs(acce_x) > abs(speed_x):
                speed_x = 0
            else:
                speed_x += acce_x
        return speed_x

    def update_mario_due_ctrl_x(self):
        mario = self.state_machine.mario
        ctrl_x = mario.get_ctrl_x()
        speed_x = mario.get_speed_x()
        acce_x = self.calc_mario_acce_x(mario, ctrl_x, speed_x)
        speed_x = self.calc_mario_speed_x(mario, acce_x, speed_x)
        mario.set_acce_x(acce_x)
        mario.set_speed_x(speed_x)

    def update_mario_due_ctrl_y(self):
        pass

    def exit_action(self):
        mario = self.state_machine.mario
        if mario.speed_y == GameDef.DIRECTION_DOWN:
            mario.zero_speed_y() #if up, it's bounce case
            speed_x = mario.get_speed_x()/2
            mario.set_speed_x(speed_x)

class MarioStateMachine(object):
    stand_state_name = "stand_state"
    walk_state_name = "walk_state"
    brake_state_name = "brake_state"
    hit_wall_state_name = "hit_wall_state"
    fly_state_name = "fly_state"
    fall_state_name = "fall_state"

    def __init__(self, mario):
        self.mario = mario
        self.world = mario.world
        self.states = {}
        self.add_state(MarioStandState(self))
        self.add_state(MarioWalkState(self))
        self.add_state(MarioBrakeState(self))
        self.add_state(MarioHitWallState(self))
        self.add_state(MarioFlyState(self))
        self.add_state(MarioFallState(self))

        self.collision_align_x_list = []
        self.collision_align_y_list = []

        self.active_state = self.states[self.stand_state_name]
        self.switch_state(self.active_state)
        #self.think()

    def add_state(self, state):
        self.states[state.state_name] = state

    def decide_next_state(self):
        mario = self.mario
        cur_state = self.active_state
        if cur_state == None:
            return self.states[self.stand_state_name]

        return cur_state.move_state_transform()

    def switch_state(self, state):
        img_idx = 0
        if self.active_state is not None:
            self.active_state.exit_action()
            img_idx = self.active_state.img_idx;
        state.entry_action(img_idx)
        self.active_state = state

    def transform_state(self):
        next_state = self.decide_next_state()
        if next_state is not None:
            self.switch_state(next_state)

    def make_collision_entity_list(self):
        etypes = [EntityType.GROUND, EntityType.STILL, EntityType.ENEMY]
        collision_list = self.world.make_collision_entity_list(self.mario,\
                                                               etypes)
        return collision_list

    def think(self):
        self.active_state.update_mario_due_ctrl_x()
        self.active_state.update_mario_due_ctrl_y()
        self.transform_state()

        self.active_state.update()
        self.update_mario_pos()

        collision_list = self.make_collision_entity_list()
        new_state = self.active_state.collision_state_transform(collision_list)
        if new_state != None:
            self.switch_state(new_state)

    def update_mario_pos(self):
        offset = self.active_state.calc_offset()
        self.mario.update_pos(offset, with_direction=False)

    def add_collision_align_x(self, collision_align, direction):
        if collision_align == 0 or direction == GameDef.DIRECTION_NONE:
            return
        self.collision_align_x_list.append([collision_align, direction])

    def add_collision_align_y(self, collision_align, direction):
        if collision_align == 0 or direction == GameDef.DIRECTION_NONE:
            return
        self.collision_align_y_list.append([collision_align, direction])

    def apply_collision_align_x(self):
        for (collision_align, direction) in self.collision_align_x_list:
            if direction == GameDef.DIRECTION_LEFT:
                offset_x = collision_align - self.mario.rect.right
            elif direction == GameDef.DIRECTION_RIGHT:
                offset_x = collision_align - self.mario.rect.left

            self.mario.update_pos((offset_x, 0), with_direction=True)

    def apply_collision_align_y(self):
        for (collision_align, direction) in self.collision_align_y_list:
            if direction == GameDef.DIRECTION_UP:
                offset_y = collision_align - self.mario.rect.bottom
            elif direction == GameDef.DIRECTION_DOWN:
                offset_y = collision_align - self.mario.rect.up

            self.mario.update_pos((0, offset_y), with_direction=True)

    def apply_collision_align(self):
        self.apply_collision_align_x()
        self.apply_collision_align_y()
        self.collision_align_x_list = []
        self.collision_align_y_list = []

class Mario(GameEntity):
    IMG_UPDATE_RATE = 3
    SPEED_WALK_MAX = 10
    SPEED_RUN_SLOW_MAX = 20
    SPEED_RUN_FAST_MAX = 30

    ACCE_INC = 1.
    ACCE_DEC_SLOW = 1.
    ACCE_DEC_FAST = 2
    DIRECTION_LEFT = -1
    DIRECTION_RIGHT = 1
    DIRECTION_UP = -1
    DIRECTION_DOWN = 1
    DIRECTION_NONE = 0

    ACCE_X_NORMAL = 1
    ACCE_X_LARGE = 5

    def __init__(self, world):
        self.speed_x = 0
        self.speed_y = 0
        self.acce_x = 0
        self.acce_y = 0
        self.ctrl_x = 0
        self.ctrl_y = 0
        self.heading = Vector2(GameDef.DIRECTION_RIGHT, 0)
        self.pos = Vector2(MARIO_START_X, GROUND_Y)

        self.world = world
        self.state_machine = MarioStateMachine(self)

        GameEntity.__init__(self, world, self.pos, EntityName.MARIO,
                            EntityType.MARIO, self.img)

    def set_img(self, img):
        if self.heading[0] == GameDef.DIRECTION_LEFT:
            img = pygame.transform.flip(img, True, False)
        GameEntity.set_img(self, img)

    def get_speedx_direction(self):
        if self.speed_x < 0:
            return GameDef.DIRECTION_LEFT
        elif self.speed_x > 0:
            return GameDef.DIRECTION_RIGHT
        else:
            return GameDef.DIRECTION_NONE

    def get_speedy_direction(self):
        if self.speed_y < 0:
            return GameDef.DIRECTION_UP
        elif self.speed_y > 0:
            return GameDef.DIRECTION_DOWN
        else:
            return GameDef.DIRECTION_NONE
    
    def set_acce_x(self, acce_x):
        self.acce_x = acce_x

    def get_acce_x(self):
        return self.acce_x

    def get_speed(self):
        return (self.speed_x, self.speed_y)

    def set_speed_x(self, speed_x):
        self.speed_x = speed_x
        return

    def get_speed_x(self):
        return self.speed_x

    def zero_speed_y(self):
        self.speed_y = 0

    def set_speed_y_up(self):
        self.speed_y = GameDef.DIRECTION_UP

    def set_speed_y_down(self):
        self.speed_y = GameDef.DIRECTION_DOWN

    def get_ctrl_x(self):
        return self.ctrl_x

    def get_ctrl_y(self):
        return self.ctrl_y

    def update_heading_x(self):
        if self.speed_x != 0:
            speedx_direction = self.get_speedx_direction()
            self.heading[0] = speedx_direction

    def update_heading_y(self):
        if self.speed_y == 0:
            self.heading[1] = 0
            return
        else:
            speedy_direction = self.get_speedy_direction()
            self.heading[1] = speedy_direction

    def update_heading(self):
        self.update_heading_x()
        self.update_heading_y()

    def get_heading(self):
        return self.heading

    def debug(self, surface):
        state = self.state_machine.active_state
        y = 40
        status = "{}, {}, {}".format(self.acce_x, self.ctrl_x, self.speed_x)
        text = sys_font.render(status, True, (0, 0, 0))
        surface.blit(text, (16,y))
        h = text.get_height()
        y += h
        state = self.state_machine.active_state
        text = sys_font.render("%s, %s"%(state.state_name, state.state_detail),
                               True, (0, 0, 0))
        surface.blit(text, (16,y))
        h = text.get_height()
        y += h
        text = sys_font.render("%d"%time_passed, True, (0, 0, 0))
        surface.blit(text, (16,y))
        #print "mario state:", state.state_name, "pos:", self.pos

    def render(self, surface):
        GameEntity.render(self, surface)
        #self.debug(surface)

    def update(self):
        self.state_machine.think()

    def process_key(self, event):
        if event.type == KEYDOWN:
            self.process_keydown(event)
        if event.type == KEYUP:
            self.process_keyup(event)

    def process_keydown(self, event):
        if event.key == K_LEFT:
            self.ctrl_x += GameDef.DIRECTION_LEFT
            self.ctrl_x = max(self.ctrl_x, GameDef.DIRECTION_LEFT)
        elif event.key == K_RIGHT:
            self.ctrl_x += GameDef.DIRECTION_RIGHT
            self.ctrl_x = min(self.ctrl_x, GameDef.DIRECTION_RIGHT)
        elif event.key == K_f:
            self.ctrl_y = GameDef.DIRECTION_UP

    def process_keyup(self, event):
        if event.key == K_LEFT:
            self.ctrl_x -= GameDef.DIRECTION_LEFT
            self.ctrl_x = min(self.ctrl_x, GameDef.DIRECTION_RIGHT)
        elif event.key == K_RIGHT:
            self.ctrl_x -= GameDef.DIRECTION_RIGHT
            self.ctrl_x = max(self.ctrl_x, GameDef.DIRECTION_LEFT)
        elif event.key == K_f:
            self.ctrl_y = GameDef.DIRECTION_NONE

def construct_world():
    world = World()

    ground = Ground(world, (0, ORIGINAL_SIZE[1]-1), GROUND_BLOCK_ROWS, 16)
    world.add_entity(ground)

    world.mario = Mario(world)
    world.add_entity(world.mario)

    wood = Wood(world, (0, GROUND_Y), game_rc.wood1_img)
    world.add_entity(wood)

    wood = Wood(world, (176, GROUND_Y), game_rc.wood2_img)
    world.add_entity(wood)

    cloud = Cloud(world, (80, 80), level=1)
    world.add_entity(cloud)

    cloud = Cloud(world, (ORIGINAL_SIZE[0]-64, 64), level=2)
    world.add_entity(cloud)

    x = MARIO_START_X + 32
    pipe = Pipe(world, (x, GROUND_Y), level=8)
    world.add_entity(pipe)

#####bottom plate + brick#####
    x += (32+16)
    plate = Plate(world, (x, GROUND_Y-20))
    world.add_entity(plate)

    rock = Rock(world, (x, GROUND_Y-20-16))
    world.add_entity(rock)

    x += 16
#    goomba = Goomba(world, (x, GROUND_Y))
#    world.add_entity(goomba)

    brick_cnt = 3
    for i in xrange(brick_cnt):
        if i == 1:
            brick = Plate(world, (x, GROUND_Y-20))
        else:
            brick = Brick(world, (x, GROUND_Y-20))
        world.add_entity(brick)
        x += 16
    
    x -= 2
    pipe = Pipe(world, (x, GROUND_Y), level=24)
    world.add_entity(pipe)

#####right side rock#####
    x -= 32
    rock = Rock(world, (x, 100-16))
    world.add_entity(rock)

    rock_cnt = 6
    for i in xrange(rock_cnt):
        rock = Rock(world, (x, 100))
        world.add_entity(rock)
        x += 16

    rock = Rock(world, (x-16, 100-16))
    world.add_entity(rock)

    goomba = Goomba(world, (x-16, 100-16+1-20))
    world.add_entity(goomba)

#####left side rock#####
    x = 0
    rock_cnt = 6
    for i in xrange(rock_cnt):
        rock = Rock(world, (x, 120))
        world.add_entity(rock)
        x += 16

#####left side brick#####
    x = 32
    brick_cnt = 3
    for i in xrange(brick_cnt):
        brick = Brick(world, (x, 64))
        world.add_entity(brick)
        x += 16

    ##Below add row across top of the screen##
    x = 0
    rock_cnt = ORIGINAL_SIZE[0]/16
    for i in xrange(rock_cnt):
        rock = Rock(world, (x, 16))
        world.add_entity(rock)
        x += 16

    return world

def get_img(path):
    return pygame.image.load(path).convert_alpha()

def build_rect_from_pos(pos, w, h):
    w -= 1
    h -= 1
    left = pos[0]
    top = pos[1] - h
    return pygame.Rect((left, top), (w, h))

counter = 0
def generate_enemy(world):
    goomba_max_cnt = 2
    goomba_cnt = 0

    global counter
    counter += 1
    counter %= 60
    if counter != 0:
        return

    for entity in world.entities.itervalues():
        if entity.name == EntityName.GOOMBA:
            goomba_cnt += 1

    if goomba_cnt < goomba_max_cnt: 
        #goomba = Goomba(world, (230, 60))
        goomba = Goomba(world, (144, 160))
        world.add_entity(goomba)

SCREEN_BK_COLOR = (148, 148, 255, 255)

ORIGINAL_SIZE = (256, 240)
ENARGE_SCALE = 3
FRAME_RATE = 60
SCREEN_SIZE = (ORIGINAL_SIZE[0]*ENARGE_SCALE, ORIGINAL_SIZE[1]*ENARGE_SCALE)

GROUND_BLOCK_ROWS = 2
GROUND_BLOCK_H = 16
GROUND_Y = ORIGINAL_SIZE[1] - GROUND_BLOCK_ROWS*GROUND_BLOCK_H

MARIO_START_X = 16

game_rc = None
sys_font = None
time_passed = 0

def run():
    logging.basicConfig(level=logging.DEBUG, filename="dbg.log",\
                        format="%(asctime)s %(levelname)s - %(message)s")

    global time_passed
    time_passed = 0

    pygame.init()
    #flags = pygame.DOUBLEBUF | pygame.HWSURFACE | pygame.FULLSCREEN
    flags = 0
    screen = pygame.display.set_mode(SCREEN_SIZE, flags, 24)
    sscreen = pygame.Surface(ORIGINAL_SIZE, 0, 32)

    global sys_font
    #sys_font = pygame.font.SysFont("Arial", 24)

    global game_rc
    game_rc = GameRc()

    mario = None
    world = construct_world()

    world.render(sscreen)
    pygame.transform.smoothscale(sscreen.convert(), SCREEN_SIZE, screen)

    pygame.display.flip()

    clock = pygame.time.Clock()

    do_save_screen = False
    save_screen_idx = 0

    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN or event.type == KEYUP:
                world.process_key(event)

        #scalex1, tick 60, scalex2, tick 40
        time_passed = clock.tick(FRAME_RATE)
        world.update()

        generate_enemy(world)

        world.render(sscreen)
        pygame.transform.smoothscale(sscreen.convert(), SCREEN_SIZE, screen)

        #print "fps:", clock.get_fps()

        #pygame.display.update()
        pygame.display.flip()

if __name__ == "__main__":
    run()
    #import profile
    #profile.run("run()")
