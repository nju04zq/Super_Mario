import sys
try:
    import pygame_sdl2
    pygame_sdl2.import_as_pygame()
except:
    pass
import pygame
import argparse
from pygame.locals import *

TRANSPARENT_COLOR = (0, 0, 0, 0)

SCREEN_SIZE = (800, 600)

def quit():
    pygame.quit()
    sys.exit()

class Palette(object):
    MAX_PNG_SIZE = 32
    MARGIN_SIZE = 8
    LABEL_SIZE = 24
    COLOR_CNT_PER_LINE = 4
    PADDING_WIDTH = 8
    COLOR_SIZE = 24
    COLOR_START = MARGIN_SIZE + LABEL_SIZE + PADDING_WIDTH
    SELECTOR_THICK = PADDING_WIDTH/2

    def __init__(self, pos, src_file, palette_file):
        self.pos = pos
        self.color_list = [TRANSPARENT_COLOR]
        self.import_colors(src_file)
        self.import_colors(palette_file)
        self.color_list.sort(self.cmp_color)

        self.selector_idx = 0
        self.selector_locked = False
        self.selector_last_visit = 0

        self.label_font = pygame.font.SysFont("Arial", 24)
        self.label_num = "0123456789abcdef"

        (self.w, self.h) = self.calc_size()
        self.basic_surface = self.make_basic_surface()

    @staticmethod
    def cmp_color(value1, value2):
        for i in xrange(0, len(value1)):
            if value1[i] < value2[i]:
                return -1
            else:
                return 1

    def import_colors(self, file_name):
        if file_name is None:
            return

        img = pygame.image.load(file_name).convert_alpha()
        w, h = img.get_size()

        if w > self.MAX_PNG_SIZE or w > self.MAX_PNG_SIZE:
            raise Exception("Img size should not exceed %dx%d"%\
                            (self.MAX_PNG_SIZE, self.MAX_PNG_SIZE))

        for i in xrange(0, w):
            for j in xrange(0, h):
                color = img.get_at((i, j))
                if color not in self.color_list:
                    self.color_list.append(color)

    def calc_size(self):
        color_cnt = len(self.color_list)
        rows = color_cnt/self.COLOR_CNT_PER_LINE + 1

        w = self.COLOR_START
        h = w
        w += self.COLOR_CNT_PER_LINE * (self.COLOR_SIZE + self.PADDING_WIDTH)
        h += rows * (self.COLOR_SIZE + self.PADDING_WIDTH)
        
        return (w,h)

    def get_size(self):
        return (self.w, self.h)
    
    def calc_color_pos(self, row, column):
        x = self.COLOR_START
        y = x
        x += column * (self.COLOR_SIZE + self.PADDING_WIDTH)
        y += row * (self.COLOR_SIZE + self.PADDING_WIDTH)

        return (x, y)

    def split_idx(self, idx):
        row = idx/self.COLOR_CNT_PER_LINE
        column = idx%self.COLOR_CNT_PER_LINE
        return (row, column)
    

    def render_colors(self, surface):
        for idx in xrange(0, len(self.color_list)):
            (row, column) = self.split_idx(idx)
            x, y = self.calc_color_pos(row, column)
            rect = pygame.Rect((x, y), (self.COLOR_SIZE, self.COLOR_SIZE))
            color = self.color_list[idx]
            pygame.draw.rect(surface, color, rect)

    def make_label_text(self, i):
        return self.label_font.render(i, True, (0, 0, 0))

    def render_label_x(self, surface):
        x = self.MARGIN_SIZE
        y = self.MARGIN_SIZE
        x += (self.LABEL_SIZE + self.PADDING_WIDTH)
        
        for i in xrange(0, self.COLOR_CNT_PER_LINE):
            text = self.make_label_text(self.label_num[i])
            surface.blit(text, (x, y))
            x += (self.COLOR_SIZE + self.PADDING_WIDTH)

    def render_label_y(self, surface):
        x = self.MARGIN_SIZE
        y = self.MARGIN_SIZE
        y += (self.LABEL_SIZE + self.PADDING_WIDTH)
        (row, column) = self.split_idx(len(self.color_list)-1)
        row += 1

        for i in xrange(0, row):
            text = self.make_label_text(self.label_num[i])
            surface.blit(text, (x, y))
            y += (self.COLOR_SIZE + self.PADDING_WIDTH)

    def render_label(self, surface):
        self.render_label_x(surface)
        self.render_label_y(surface)

    def make_basic_surface(self):
        surface = pygame.Surface((self.w, self.h), SRCALPHA, 32)

        surface.fill((TRANSPARENT_COLOR))
        self.render_colors(surface)
        self.render_label(surface)
        self.render_right_border(surface)

        return surface
    
    def render(self, surface):
        surface.blit(self.basic_surface, self.pos)
        self.render_selector(surface)
        self.render_right_border(surface)

    def render_right_border(self, surface):
        start_x = self.pos[0]
        start_x += self.w
        start_y = self.pos[1]
        end_x = start_x
        end_y = SCREEN_SIZE[1]-1
        pygame.draw.line(surface, (255, 255, 255),
                         (start_x, start_y), (end_x, end_y), 4)

    def render_selector(self, surface):
        (row, column) = self.split_idx(self.selector_idx)
        x, y = self.calc_color_pos(row, column)
        size = self.COLOR_SIZE
        x -= self.SELECTOR_THICK
        y -= self.SELECTOR_THICK
        size += (self.SELECTOR_THICK*2)
        rect = pygame.Rect((x, y), (size, size))
        if self.selector_locked:
            color = (255, 255, 255, 255)
        else:
            color = (0, 0, 0, 255)
        pygame.draw.rect(surface, color, rect, self.SELECTOR_THICK)

    def move_selector_up(self):
        if self.selector_locked:
            return
        idx = self.selector_idx
        idx -= self.COLOR_CNT_PER_LINE
        if idx >= 0:
            self.selector_idx = idx

    def move_selector_down(self):
        if self.selector_locked:
            return
        max_idx = len(self.color_list)
        idx = self.selector_idx
        idx += self.COLOR_CNT_PER_LINE
        if idx < max_idx:
            self.selector_idx = idx

    def move_selector_left(self):
        if self.selector_locked:
            return
        if self.selector_idx > 0:
            self.selector_idx -= 1

    def move_selector_right(self):
        if self.selector_locked:
            return
        max_idx = len(self.color_list) - 1
        if self.selector_idx < max_idx:
            self.selector_idx += 1

    def get_selector_color(self):
        return self.color_list[self.selector_idx]
    
    def get_color_idx(self, color):
        try:
            index = self.color_list.index(color)
        except:
            index = "not exist"
        else:
            index = str(self.split_idx(index))

        return index

    def set_selector_color(self, color):
        if self.selector_locked:
            return
        try:
            index = self.color_list.index(color)
        except:
            index = 0

        self.selector_idx = index

    def lock_selector(self, idx):
        old_ts = self.selector_last_visit
        new_ts = pygame.time.get_ticks()
        self.selector_last_visit = new_ts

        if idx != self.selector_idx:
            return

        if (new_ts - old_ts) > 500:
            return

        self.selector_locked = not self.selector_locked

    def process_keyup(self, key):
        if key == K_w:
            self.move_selector_up()
        elif key == K_s:
            self.move_selector_down()
        elif key == K_a:
            self.move_selector_left()
        elif key == K_d:
            self.move_selector_right()

    def is_pos_in_palette(self, pos):
        rect = pygame.Rect(self.pos, (self.w, self.h))
        return rect.collidepoint(pos)

    def calc_selector_idx_from_pos(self, pos):
        color_area_size = self.COLOR_SIZE+self.PADDING_WIDTH

        dx = pos[0] - self.COLOR_START
        dy = pos[1] - self.COLOR_START
        if dx < 0 or dy < 0:
            return -1

        row = dy/color_area_size
        column = dx/color_area_size
        idx = row * self.COLOR_CNT_PER_LINE + column
        if idx >= len(self.color_list):
            return -1

        dx %= color_area_size
        dy %= color_area_size
        if dx > self.COLOR_SIZE or dy > self.COLOR_SIZE:
            return -1

        return idx

    def process_mousebuttondown(self, pos):
        if self.is_pos_in_palette(pos) == False:
            return
        
        idx = self.calc_selector_idx_from_pos(pos)
        if idx == -1:
            return

        self.lock_selector(idx)
        if self.selector_locked == False:
            self.selector_idx = idx

class ViewChange(object):
    def __init__(self, pos, old_color, new_color):
        self.pos = tuple(pos) #copy out the pos
        self.old_color = old_color
        self.new_color = new_color

class View(object):
    MIN_SCALE_LEVEL = 12
    MAX_SCALE_LEVEL = 24
    SCALE_LEVEL_PACE = 4
    SELECTOR_THICK = 2

    def __init__(self, painter, pos, size, src_file, tgt_file):
        self.painter = painter
        self.pos = pos
        self.size = size
        self.img = pygame.image.load(src_file).convert_alpha()
        self.img_size = self.img.get_size()
        self.tgt_file = tgt_file
        self.is_dirty = False
        self.change_list = []

        self.selector = [0, 0]
        self.update_selector()

        self.init_scale_level()
        self.img_pos = self.calc_img_pos()

    def is_scale_level_qualified(self, level):
        scaled_w = level * self.img_size[0]
        scaled_h = level * self.img_size[1]
        if scaled_w < self.size[0] and scaled_h < self.size[1]:
            return True
        else:
            return False

    def init_scale_level(self):
        min_level = self.MIN_SCALE_LEVEL
        max_level = self.MAX_SCALE_LEVEL
        level_pace = self.SCALE_LEVEL_PACE
        self.scale_levels = range(min_level, max_level+1, level_pace)

        self.scale_level_max_idx  = 0
        for level in self.scale_levels[1:]:
            if self.is_scale_level_qualified(level):
                self.scale_level_max_idx += 1

        self.scale_level_idx = self.scale_level_max_idx
        self.update_scale_level()

    def calc_img_pos(self):
        scaled_w = self.img_size[0] * self.scale_level
        scaled_h = self.img_size[1] * self.scale_level

        dx, dy = 0, 0
        if scaled_w < self.size[0]:
            dx = (self.size[0] - scaled_w)/2
        if scaled_h < self.size[1]:
            dy = (self.size[1] - scaled_h)/2

        return (self.pos[0]+dx, self.pos[1]+dy)

    def render(self, surface):
        self.render_img(surface)
        self.render_border(surface)
        self.render_selector(surface)

    def render_border(self, surface):
        scaled_w = self.img_size[0] * self.scale_level
        scaled_h = self.img_size[1] * self.scale_level

        w = scaled_w + 2
        h = scaled_h + 2
        x = self.img_pos[0]-1
        y = self.img_pos[1]-1
        rect = pygame.Rect((x, y), (w-1, h-1))
        pygame.draw.rect(surface, (0, 0, 0, 255), rect, 1)

    def render_img(self, surface):
        scaled_w = self.img_size[0] * self.scale_level
        scaled_h = self.img_size[1] * self.scale_level
        scaled_img = pygame.transform.scale(self.img, (scaled_w, scaled_h))
        surface.blit(scaled_img, self.img_pos)

    def calc_selector_color(self, img_color):
        dist1 = img_color[0] + img_color[1] + img_color[2]
        dist2 = 255*3 - dist1
        if dist1 > dist2:
            return (0, 0, 0, 255)
        else:
            return (255, 255, 255, 255)

    def render_selector(self, surface):
        dx = self.selector[0] * self.scale_level
        dy = self.selector[1] * self.scale_level
        x = self.img_pos[0] + dx
        y = self.img_pos[1] + dy

        rect = pygame.Rect((x, y), (self.scale_level, self.scale_level))
        img_color = self.img.get_at(self.selector)
        color = self.calc_selector_color(img_color)
        pygame.draw.rect(surface, color, rect, self.SELECTOR_THICK)

    def update_selector(self):
        color = self.get_selector_color()
        self.painter.palette.set_selector_color(color)

    def move_selector_left(self):
        if self.selector[0] > 0:
            self.selector[0] -= 1
            self.update_selector()

    def move_selector_right(self):
        if self.selector[0] < (self.img_size[0]-1):
            self.selector[0] += 1
            self.update_selector()

    def move_selector_up(self):
        if self.selector[1] > 0:
            self.selector[1] -= 1
            self.update_selector()

    def move_selector_down(self):
        if self.selector[1] < (self.img_size[1]-1):
            self.selector[1] += 1
            self.update_selector()
    
    def get_selector_color(self):
        return self.img.get_at(self.selector)

    def get_img_status(self):
        if self.is_dirty:
            cnt = min(5, len(self.change_list))
            is_dirty = "+"*cnt
        else:
            is_dirty = ""
        return tgt_file + is_dirty

    def adopt_palette_selected_color(self):
        new_color = self.painter.palette.get_selector_color()
        old_color = self.img.get_at(self.selector)

        if old_color == new_color:
            return

        self.img.set_at(self.selector, new_color)
        self.is_dirty = True

        view_change = ViewChange(self.selector, old_color, new_color)
        self.add_view_change(view_change)

    def save_img(self):
        pygame.image.save(self.img, self.tgt_file)
        self.is_dirty = False
        self.change_list = []

    def revert_change(self):
        self.revert_view_change()
        if len(self.change_list) == 0:
            self.is_dirty = False

    def add_view_change(self, view_change):
        self.change_list.append(view_change)

    def revert_view_change(self):
        if len(self.change_list) == 0:
            return

        view_change = self.change_list.pop()
        self.img.set_at(view_change.pos, view_change.old_color)

    def update_scale_level(self):
        self.scale_level = self.scale_levels[self.scale_level_idx]
        self.img_pos = self.calc_img_pos()

    def inc_scale_level(self):
        if self.scale_level_idx < self.scale_level_max_idx:
            self.scale_level_idx += 1
        self.update_scale_level()

    def dec_scale_level(self):
        if self.scale_level_idx > 0:
            self.scale_level_idx -= 1
        self.update_scale_level()

    def process_keyup(self, key):
        if key == K_UP:
            self.move_selector_up()
        elif key == K_DOWN:
            self.move_selector_down()
        elif key == K_LEFT:
            self.move_selector_left()
        elif key == K_RIGHT:
            self.move_selector_right()
        elif key == K_RETURN:
            self.adopt_palette_selected_color()
        elif key == K_SPACE:
            self.save_img()
        elif key == K_ESCAPE:
            self.revert_change()
        elif key == K_EQUALS:
            self.inc_scale_level()
        elif key == K_MINUS:
            self.dec_scale_level()

    def process_mousebuttondown(self, pos):
        rect = pygame.Rect(self.pos, self.size)
        if rect.collidepoint(pos) == False:
            return

        dx = pos[0]-self.img_pos[0]
        dy = pos[1]-self.img_pos[1]
        if dx < 0 or dy < 0:
            return

        row = dy/self.scale_level
        column = dx/self.scale_level
        if row >= self.img_size[1] or column >= self.img_size[0]:
            return

        self.selector = [column, row]
        self.update_selector()

class Status(object):
    MARGIN = 16
    FONT_HEIGHT = 48

    def __init__(self, painter, x):
        width = SCREEN_SIZE[0] - x
        height = self.MARGIN*3 + self.FONT_HEIGHT*2
        self.size = (width, height)
        self.pos = (x, SCREEN_SIZE[1]-height)
        self.painter = painter
        self.font = pygame.font.SysFont("Arial", 28)

    def get_size(self):
        return self.size

    def render(self, surface):
        self.render_img_selector_and_color(surface)
        self.render_img_status(surface)
        self.render_top_border(surface)

    def render_img_selector_and_color(self, surface):
        x, y = self.pos
        x += self.MARGIN
        y += self.MARGIN

        render_str = ("size" + str(self.painter.view.img_size)+" ")

        img_selector = self.painter.view.selector
        render_str += ("pos" + str(img_selector) + " ")

        color = self.painter.view.get_selector_color()
        index = self.painter.palette.get_color_idx(color)
        render_str += ("color" + index + "#"+str(color))

        text = self.font.render(render_str, True, (0, 0, 0))
        surface.blit(text, (x, y))

    def render_img_status(self, surface):
        x, y = self.pos
        x += self.MARGIN
        y += (self.MARGIN + self.FONT_HEIGHT)

        img_status = self.painter.view.get_img_status()
        text = self.font.render(img_status, True, (0, 0, 0)).convert_alpha()

        if img_status.endswith("+"):
            w, h = text.get_size()
            bk_color = pygame.Surface((w, h), SRCALPHA)
            bk_color.fill((255, 0, 0, 64))
            surface.blit(bk_color, (x, y))

        surface.blit(text, (x, y))

    def render_top_border(self, surface):
        start_x = self.pos[0]
        start_y = self.pos[1]
        end_x = SCREEN_SIZE[0]-1
        end_y = start_y
        pygame.draw.line(surface, (255, 255, 255),
                         (start_x, start_y), (end_x, end_y), 4)

class Painter(object):
    def __init__(self, src_file, tgt_file, palette_file):
        self.img = pygame.image.load(src_file).convert_alpha()
        self.tgt_file = tgt_file

        x, y = 0, 0
        self.palette = Palette((0, 0), src_file, palette_file)

        w, h = self.palette.get_size()
        x += w
        self.status = Status(self, x)

        w, h = self.status.get_size()
        h = SCREEN_SIZE[1] - h
        self.view = View(self, (x, y), (w, h), src_file, tgt_file)

    def render(self, surface):
        surface.fill((128, 128, 128, 255))
        self.palette.render(surface)
        self.view.render(surface)
        self.status.render(surface)

    def process_keyup(self, key):
        self.palette.process_keyup(key)
        self.view.process_keyup(key)

    def process_mousebuttondown(self):
        pressed = pygame.mouse.get_pressed()
        if pressed[0] == False:
            return

        pos = pygame.mouse.get_pos()
        self.palette.process_mousebuttondown(pos)
        self.view.process_mousebuttondown(pos)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--source",
                        metavar="SOURCE_PNG",
                        help="the source png file")
    parser.add_argument("-t", "--target",
                        metavar="TARGET_PNG",
                        help="save to this file")
    parser.add_argument("-p", "--palette",
                        metavar="PALETTE_PNG",
                        help="png file as palette")

    args = parser.parse_args()

    if args.source == None:
        print "Should specify source file"
        raise Exception("No source file")

    if args.target == None:
        print "Should specify target file"
        raise Exception("No target file")

    return (args.source, args.target, args.palette)


pygame.init()
screen = pygame.display.set_mode(SCREEN_SIZE, SRCALPHA, 32)
pygame.display.set_caption("Super painter")

src_file, tgt_file, palette_file = parse_args()

painter = Painter(src_file, tgt_file, palette_file)
painter.render(screen)

clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            quit()
        if event.type == KEYUP:
            painter.process_keyup(event.key)
        if event.type == MOUSEBUTTONDOWN:
            painter.process_mousebuttondown()

    clock.tick(20)

    painter.render(screen)

    pygame.display.flip()
