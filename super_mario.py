import sys
import logging
import pygame_sdl2
pygame_sdl2.import_as_pygame()
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
            entity.update()

    def process_key(self, event):
        self.mario.process_key(event)

    def render_with_etype(self, surface, etype):
        for entity in self.entities.itervalues():
            if entity.etype == etype:
                entity.render(surface)

    def render(self, surface):
        surface.fill(self.bg_color)
        self.render_with_etype(surface, EntityType.GROUND)
        self.render_with_etype(surface, EntityType.BACKGROUND)
        self.render_with_etype(surface, EntityType.STILL)
        self.render_with_etype(surface, EntityType.MARIO)

    def exceed_border(self, mario):
        w, h = mario.img.get_size()
        ul_x = mario.pos[0]
        ul_y = mario.pos[1] - h + 1
        br_x = mario.pos[0] + w - 1
        br_y = mario.pos[1]
        left_border = 1
        if ul_x <= left_border:
            mario.pos[0] = left_border
            return True
        right_border = ORIGINAL_SIZE[0]-2
        if br_x >= right_border:
            mario.pos[0] = right_border - w + 1
            return True
        return False

class GameEntity(object):
    def __init__(self, world, pos, name, etype, img):
        self.world = world
        self.name = name
        self.etype = etype
        self.img = img
        self.pos = Vector2(pos)
        self.eid = 0

    def render(self, surface):
        h = self.img.get_height()
        pos = (self.pos[0], self.pos[1]-h+1)
        surface.blit(self.img, pos)

    def update(self):
        pass

class EntityName(object):
    GROUND = "ground"
    WOOD = "wood"
    MARIO = "mario"
    PIPE = "pipe"

class EntityType(object):
    GROUND = "ground"
    BACKGROUND = "bg"
    MARIO = "mario"
    STILL = "still"

class GameRc(object):
    ground_block_png = "ground_block_16x16.png"
    wood_png = "wood_48x16.png"
    pipe1_png = "pipe1_32x15.png"
    pipe2_png = "pipe2_32x1.png"
    pipe3_png = "pipe3_32x2.png"
    mario1_png = "mario1_12x16.png"
    mario2_png = "mario2_13x15.png"
    mario3_png = "mario3_15x16.png"
    mario4_png = "mario4_13_16.png"
    mario5_png = "mario5_13x16.png"
    mario6_png = "mario6_16x16.png"

    def __init__(self):
        self.ground_block_img = get_img(self.ground_block_png)
        self.wood_img = get_img(self.wood_png)
        self.pipe1_img = get_img(self.pipe1_png)
        self.pipe2_img = get_img(self.pipe2_png)
        self.pipe3_img = get_img(self.pipe3_png)
        self.mario1_img = get_img(self.mario1_png)
        self.mario2_img = get_img(self.mario2_png)
        self.mario3_img = get_img(self.mario3_png)
        self.mario4_img = get_img(self.mario4_png)
        self.mario5_img = get_img(self.mario5_png)
        self.mario6_img = get_img(self.mario6_png)

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

    def __init__(self, world, pos, level):
        img = self.make_img(level)
        GameEntity.__init__(self, world, pos, EntityName.PIPE,
                            EntityType.STILL, img)

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
            self.set_mario_img()
        else:
            offset = self.calc_move_offset()

        return offset

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

class MarioBrakeState(MarioState):
    def __init__(self, state_machine):
        state_name = state_machine.brake_state_name
        img_set = [game_rc.mario5_img]
        transform_rate = 1
        transform_offset = [0]
        move_offset = 2
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)

class MarioHitWallState(MarioState):
    def __init__(self, state_machine):
        state_name = state_machine.hit_wall_state_name
        img_set = [game_rc.mario2_img, game_rc.mario3_img, game_rc.mario4_img]
        transform_rate = 7
        transform_offset = [-2, 2, 0]
        move_offset = 0
        MarioState.__init__(self, state_machine, state_name, img_set,
                            transform_rate, transform_offset, move_offset)

class MarioFlyState(MarioState):
    POWER_MIN = 2
    POWER_MAX = 14
    FULL_POWER_FRAMES = 7
    POWER_MOVE_OFFSET = 4

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
        self.power_full_up_data = [(7, 2, 1), (3, 1, 3), (6, 0, 1)]
        self.power_down_data = [(2, 1, 1), (8, 3, 1), (0, 5, 1)]

        self.power_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.offset_x = 0
        self.offset_y = 0

    def entry_action_init_offset(self):
        self.offset_y = self.POWER_MOVE_OFFSET
        mario = self.state_machine.mario
        speed_x = abs(mario.get_speed_x())
        if speed_x > mario.SPEED_RUN_SLOW_MAX:
            self.offset_x = 2
        elif speed_x > mario.SPEED_WALK_MAX:
            self.offset_x = 1
        else:
            self.offset_x = 0

    def entry_action(self, img_idx):
        MarioState.entry_action(self, img_idx)
        self.power = 0
        self.power_data = []
        self.power_data_idx = 0
        self.total_frames = 0
        self.cur_cycle = 0
        self.cur_frame = 0
        self.entry_action_init_offset()

    def set_power_data(self):
        self.power = max(self.POWER_MIN, self.power)
        self.power = min(self.POWER_MAX, self.power)
        f = (float(self.power)/self.POWER_MAX)**2
        up_data = map(lambda x:(max(int(x[0]*f), 1), x[1], x[2]),
                      self.power_full_up_data)
        self.power_data += up_data
        self.power_data += self.power_down_data

    def set_offset_y(self):
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

    def set_mario_speed_y(self):
        mario = self.state_machine.mario
        if self.power_data_idx < len(self.power_full_up_data):
            mario.set_speed_y_up()
        else:
            mario.set_speed_y_down()

    def power_inc_end(self):
        mario = self.state_machine.mario
        if self.power > self.POWER_MAX:
            return True
        if mario.get_ctrl_y() == Mario.DIRECTION_NONE:
            return True
        return False

    def update(self):
        self.set_mario_speed_y()
        if self.power == self.FULL_POWER_FRAMES:
            self.offset_y -= 1
        self.power += 1
        if self.power_inc_end() == False:
            return;
        if len(self.power_data) == 0:
            self.set_power_data()
        self.set_offset_y()
        self.run_cycle()

    def calc_move_offset(self):
        return (self.offset_x, self.offset_y)

    def exit_action(self):
        self.state_machine.mario.zero_speed_y()

class MarioStateMachine(object):
    stand_state_name = "stand_state"
    walk_state_name = "walk_state"
    brake_state_name = "brake_state"
    hit_wall_state_name = "hit_wall_state"
    fly_state_name = "fly_state"

    def __init__(self, mario):
        self.mario = mario
        self.states = {}
        self.add_state(MarioStandState(self))
        self.add_state(MarioWalkState(self))
        self.add_state(MarioBrakeState(self))
        self.add_state(MarioHitWallState(self))
        self.add_state(MarioFlyState(self))

        self.active_state = None
        self.think()

    def add_state(self, state):
        self.states[state.state_name] = state

    def decide_cur_state(self):
        mario = self.mario
        if mario.speed_y != 0:
            return self.states[self.fly_state_name]
        elif mario.speed_x == 0:
            return self.states[self.stand_state_name]
        elif mario.world.exceed_border(mario):
            return self.states[self.hit_wall_state_name]
        elif abs(mario.acce_x) == mario.ACCE_DEC_FAST:
            return self.states[self.brake_state_name]
        elif abs(mario.speed_x) > 0:
            return self.states[self.walk_state_name]

        # should not arrive here, but to be safe
        return self.states[self.stand_state_name]

    def switch_state(self, state):
        img_idx = 0
        if self.active_state is not None:
            self.active_state.exit_action()
            img_idx = self.active_state.img_idx;
        state.entry_action(img_idx)
        self.active_state = state

    def choose_state(self):
        cur_state = self.decide_cur_state()
        if cur_state is not self.active_state:
            self.switch_state(cur_state)

    def apply_state(self):
        state = self.active_state
        state.update()
        offset = state.calc_offset()
        self.update_mario_pos(offset)

    def think(self):
        self.choose_state()
        self.apply_state()

    def update_mario_pos(self, offset):
        mario = self.mario
        mario.set_heading()
        heading = mario.get_heading()
        #print "offset:", offset, "heading:", heading
        mario.pos += Vector2(offset[0]*heading[0], offset[1]*heading[1])
        #TODO TEMP FIX
        if mario.pos[1] > GROUND_Y:
            mario.pos[1] = GROUND_Y
            mario.zero_speed_y()

class Mario(GameEntity):
    IMG_UPDATE_RATE = 3
    SPEED_WALK_MAX = 10
    SPEED_RUN_SLOW_MAX = 20
    SPEED_RUN_FAST_MAX = 30

    ACCE_INC = 1.
    ACCE_DEC_SLOW = 1.
    ACCE_DEC_FAST = 2.5
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
        self.ctry_y = 0
        self.heading = Vector2(1, 0)
        self.pos = Vector2(MARIO_START_X, GROUND_Y)

        self.state_machine = MarioStateMachine(self)

        GameEntity.__init__(self, world, self.pos, EntityName.MARIO,
                            EntityType.MARIO, self.img)

    def set_img(self, img):
        self.img = img
        if self.heading[0] == self.DIRECTION_LEFT:
            self.img = pygame.transform.flip(img, True, False)

    def get_speedx_direction(self):
        if self.speed_x < 0:
            return self.DIRECTION_LEFT
        elif self.speed_x > 0:
            return self.DIRECTION_RIGHT
        else:
            return self.DIRECTION_NONE

    def get_speedy_direction(self):
        if self.speed_y < 0:
            return self.DIRECTION_UP
        elif self.speed_y > 0:
            return self.DIRECTION_DOWN
        else:
            return self.DIRECTION_NONE

    def set_acce_x(self):
        if self.speed_x == 0 and self.ctrl_x == 0:
            self.acce_x = 0
            return
        speed_direction = self.get_speedx_direction()
        if self.ctrl_x != 0:
            if self.speed_x == 0 or self.ctrl_x == speed_direction:
                self.acce_x = self.ctrl_x * self.ACCE_INC
            else:
                self.acce_x = -1 * speed_direction * self.ACCE_DEC_FAST
        else:
            self.acce_x = -1 * speed_direction * self.ACCE_DEC_SLOW
        return

    def set_speed_x(self):
        speed_max = self.SPEED_RUN_FAST_MAX
        speed_direction = self.get_speedx_direction()
        if self.speed_x == 0 or self.acce_x == 0:
            self.speed_x += self.acce_x
            return
        if self.acce_x * speed_direction > 0:
            self.speed_x += self.acce_x
            self.speed_x = min(abs(self.speed_x), speed_max)
            self.speed_x *= speed_direction
        else:
            if abs(self.acce_x) > abs(self.speed_x):
                self.speed_x = 0
            else:
                self.speed_x += self.acce_x
        return

    def get_speed_x(self):
        return self.speed_x

    def zero_speed_y(self):
        self.speed_y = 0

    def set_speed_y_up(self):
        self.speed_y = self.DIRECTION_UP

    def set_speed_y_down(self):
        self.speed_y = self.DIRECTION_DOWN

    def get_ctrl_y(self):
        return self.ctrl_y

    def set_heading_x(self):
        if self.speed_x == 0:
            self.heading[0] = 0
            return
        else:
            speedx_direction = self.get_speedx_direction()
            self.heading[0] = speedx_direction

    def set_heading_y(self):
        if self.speed_y == 0:
            self.heading[1] = 0
            return
        else:
            speedy_direction = self.get_speedy_direction()
            self.heading[1] = speedy_direction

    def set_heading(self):
        self.set_heading_x()
        self.set_heading_y()

    def get_heading(self):
        return self.heading

    def debug(self, surface):
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
        self.set_acce_x()
        self.set_speed_x()
        self.state_machine.think()

    def process_key(self, event):
        if event.type == KEYDOWN:
            self.process_keydown(event)
        if event.type == KEYUP:
            self.process_keyup(event)

    def process_keydown(self, event):
        if event.key == K_LEFT:
            self.ctrl_x += self.DIRECTION_LEFT
            self.ctrl_x = max(self.ctrl_x, self.DIRECTION_LEFT)
        elif event.key == K_RIGHT:
            self.ctrl_x += self.DIRECTION_RIGHT
            self.ctrl_x = min(self.ctrl_x, self.DIRECTION_RIGHT)
        elif event.key == K_f:
            self.ctrl_y = self.DIRECTION_UP
            self.set_speed_y_up()

    def process_keyup(self, event):
        if event.key == K_LEFT:
            self.ctrl_x -= self.DIRECTION_LEFT
            self.ctrl_x = min(self.ctrl_x, self.DIRECTION_RIGHT)
        elif event.key == K_RIGHT:
            self.ctrl_x -= self.DIRECTION_RIGHT
            self.ctrl_x = max(self.ctrl_x, self.DIRECTION_LEFT)
        elif event.key == K_f:
            self.ctrl_y = self.DIRECTION_NONE

def construct_world():
    world = World()

    ground = Ground(world, (0, ORIGINAL_SIZE[1]-1), GROUND_BLOCK_ROWS, 16)
    world.add_entity(ground)

    world.mario = Mario(world)
    world.add_entity(world.mario)

    wood = Wood(world, (0, GROUND_Y), game_rc.wood_img)
    world.add_entity(wood)

    pipe = Pipe(world, (MARIO_START_X+16, GROUND_Y), level=24)
    world.add_entity(pipe)

    return world

def get_img(path):
    return pygame.image.load(path).convert_alpha()

SCREEN_BK_COLOR = (148, 148, 255, 255)

ORIGINAL_SIZE = (256, 240)
ENARGE_SCALE = 3
FRAME_RATE = 60
SCREEN_SIZE = (ORIGINAL_SIZE[0]*ENARGE_SCALE, ORIGINAL_SIZE[1]*ENARGE_SCALE)

GROUND_BLOCK_ROWS = 2
GROUND_BLOCK_H = 16
GROUND_Y = ORIGINAL_SIZE[1] - GROUND_BLOCK_ROWS*GROUND_BLOCK_H

MARIO_START_X = ORIGINAL_SIZE[0]/4

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

        world.render(sscreen)
        pygame.transform.smoothscale(sscreen.convert(), SCREEN_SIZE, screen)

        #print "fps:", clock.get_fps()

        #pygame.display.update()
        pygame.display.flip()

if __name__ == "__main__":
    run()
    #import profile
    #profile.run("run()")
