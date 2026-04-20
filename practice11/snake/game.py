import pygame, random
from config import *

DIRECTIONS = {"UP":(0,-1),"DOWN":(0,1),"LEFT":(-1,0),"RIGHT":(1,0)}
OPPOSITE   = {"UP":"DOWN","DOWN":"UP","LEFT":"RIGHT","RIGHT":"LEFT"}

FOOD_TYPES = [
    ("normal", FOOD_NORM,   1, 0),
    ("bonus",  FOOD_BONUS,  3, 8),
    ("rare",   FOOD_RARE,   5, 5),
    ("poison", FOOD_POISON, 0, 0),
]

POWERUP_TYPES   = ["speed","slow","shield"]
PU_COLORS       = {"speed":PU_SPEED,"slow":PU_SLOW,"shield":PU_SHIELD}
PU_DURATION_MS  = {"speed":5000,"slow":5000,"shield":0}
PU_FIELD_TTL    = 8000

class SnakeGame:
    def __init__(self, settings, username, personal_best):
        self.settings      = settings
        self.username      = username
        self.personal_best = personal_best
        self.snake_color   = tuple(settings["snake_color"])
        self.grid          = settings["grid_overlay"]

        cx, cy = COLS//2, ROWS//2
        self.body      = [(cx,cy),(cx-1,cy),(cx-2,cy)]
        self.direction = "RIGHT"
        self.next_dir  = "RIGHT"

        self.score = 0; self.level = 1; self.food_eaten = 0
        self.food_per_level = 5
        self.game_over = False; self.game_over_reason = ""
        self.fps = FPS_DEFAULT
        self.speed_boost_end = 0; self.slow_end = 0
        self.shield_active = False; self.active_powerup_label = None
        self.foods=[]; self.powerup=None; self.pu_spawn_time=0
        self.obstacles=set()
        self._place_food()
        self._maybe_place_powerup(force=True)

    def _free_cells(self, extra=None):
        occ = set(self.body)|self.obstacles
        if extra: occ|=set(extra)
        return [(x,y) for x in range(COLS) for y in range(ROWS) if (x,y) not in occ]

    def _place_food(self):
        if len(self.foods)>=2: return
        free = self._free_cells([(f["x"],f["y"]) for f in self.foods])
        if not free: return
        ftype = random.choices(FOOD_TYPES,[4,2,1,1],k=1)[0]
        name,color,pts,ttl = ftype
        pos = random.choice(free)
        self.foods.append({
            "x":pos[0],"y":pos[1],"type":name,"color":color,
            "pts":pts,"expires":pygame.time.get_ticks()+ttl*1000 if ttl>0 else 0,
            "ttl":ttl
        })

    def _maybe_place_powerup(self, force=False):
        if self.powerup: return
        if not force and random.random()>0.25: return
        fc = [(f["x"],f["y"]) for f in self.foods]
        free = self._free_cells(fc)
        if not free: return
        ptype = random.choice(POWERUP_TYPES)
        pos = random.choice(free)
        self.powerup = {"x":pos[0],"y":pos[1],"type":ptype}
        self.pu_spawn_time = pygame.time.get_ticks()

    def _place_obstacles(self):
        if self.level<3: return
        count = 2+(self.level-3)*2
        head = self.body[0]
        safety = {(head[0]+dx,head[1]+dy) for dx in range(-3,4) for dy in range(-3,4)}
        cands = [(x,y) for x in range(COLS) for y in range(ROWS)
                 if (x,y) not in set(self.body) and (x,y) not in self.obstacles
                 and (x,y) not in safety
                 and not any(f["x"]==x and f["y"]==y for f in self.foods)]
        random.shuffle(cands)
        for pos in cands[:count]: self.obstacles.add(pos)

    def _advance_level(self):
        self.level+=1; self.food_eaten=0
        self.fps = min(FPS_DEFAULT+(self.level-1)*2,22)
        self._place_obstacles()

    @property
    def current_fps(self):
        now=pygame.time.get_ticks()
        if now<self.speed_boost_end: return min(self.fps+6,28)
        if now<self.slow_end:        return max(self.fps-4,3)
        return self.fps

    def change_direction(self, d):
        if d!=OPPOSITE[self.direction]: self.next_dir=d

    def update(self):
        if self.game_over: return
        now=pygame.time.get_ticks()
        self.foods=[f for f in self.foods if f["expires"]==0 or now<f["expires"]]
        if not self.foods: self._place_food()
        if self.powerup and (now-self.pu_spawn_time)>PU_FIELD_TTL: self.powerup=None
        if self.active_powerup_label=="speed" and now>=self.speed_boost_end:
            self.active_powerup_label=None
        if self.active_powerup_label=="slow" and now>=self.slow_end:
            self.active_powerup_label=None

        self.direction=self.next_dir
        dx,dy=DIRECTIONS[self.direction]
        hx,hy=self.body[0]
        nh=(hx+dx,hy+dy)
        wall = not(0<=nh[0]<COLS and 0<=nh[1]<ROWS)
        self_= nh in self.body[:-1]
        obs_  = nh in self.obstacles

        if wall or self_ or obs_:
            if self.shield_active:
                self.shield_active=False; self.active_powerup_label=None; return
            self.game_over=True
            self.game_over_reason=("Hit the wall!" if wall else
                                   "Hit an obstacle!" if obs_ else "Bit yourself!")
            return

        self.body.insert(0,nh)
        ate=False
        for food in self.foods[:]:
            if nh==(food["x"],food["y"]):
                if food["type"]=="poison":
                    for _ in range(3):
                        if len(self.body)>1: self.body.pop()
                    if len(self.body)<=1:
                        self.game_over=True; self.game_over_reason="Poisoned!"; return
                    self.score=max(0,self.score-2)
                else:
                    self.score+=food["pts"]; self.food_eaten+=1
                    if self.food_eaten>=self.food_per_level: self._advance_level()
                self.foods.remove(food)
                self._place_food(); self._maybe_place_powerup(); ate=True; break
        if not ate: self.body.pop()

        if self.powerup and nh==(self.powerup["x"],self.powerup["y"]):
            pt=self.powerup["type"]
            if pt=="speed":   self.speed_boost_end=now+5000; self.active_powerup_label="speed"
            elif pt=="slow":  self.slow_end=now+5000;        self.active_powerup_label="slow"
            elif pt=="shield":self.shield_active=True;       self.active_powerup_label="shield"
            self.powerup=None

    def draw(self, surface):
        pygame.draw.rect(surface,BG,(0,80,WIDTH,HEIGHT-80))
        if self.grid:
            for x in range(COLS):
                for y in range(ROWS):
                    pygame.draw.rect(surface,GRID_COLOR,(x*CELL,80+y*CELL,CELL,CELL),1)
        for ox,oy in self.obstacles:
            pygame.draw.rect(surface,OBSTACLE,(ox*CELL+2,80+oy*CELL+2,CELL-4,CELL-4),border_radius=4)
        for food in self.foods:
            r=pygame.Rect(food["x"]*CELL+4,80+food["y"]*CELL+4,CELL-8,CELL-8)
            pygame.draw.ellipse(surface,food["color"],r)
            if food["expires"]>0:
                now=pygame.time.get_ticks()
                ratio=max(0,(food["expires"]-now)/(food["ttl"]*1000))
                bw=int((CELL-8)*ratio)
                pygame.draw.rect(surface,WHITE,(food["x"]*CELL+4,80+food["y"]*CELL+CELL-8,bw,4))
        if self.powerup:
            px,py=self.powerup["x"],self.powerup["y"]
            r=pygame.Rect(px*CELL+3,80+py*CELL+3,CELL-6,CELL-6)
            pygame.draw.rect(surface,PU_COLORS[self.powerup["type"]],r,border_radius=6)
            pygame.draw.rect(surface,WHITE,r,2,border_radius=6)
        for i,(sx,sy) in enumerate(self.body):
            col=PU_SHIELD if self.shield_active else self.snake_color
            r=pygame.Rect(sx*CELL+1,80+sy*CELL+1,CELL-2,CELL-2)
            pygame.draw.rect(surface,col,r,border_radius=5)
            if i==0:
                pygame.draw.circle(surface,BLACK,(sx*CELL+7,80+sy*CELL+7),3)
                pygame.draw.circle(surface,BLACK,(sx*CELL+CELL-7,80+sy*CELL+7),3)
        pygame.draw.rect(surface,WALL,(0,80,WIDTH,HEIGHT-80),4)

    def draw_hud(self, surface, font_med, font_small):
        pygame.draw.rect(surface,HUD_BG,(0,0,WIDTH,80))
        pygame.draw.line(surface,WALL,(0,80),(WIDTH,80),2)
        _t(font_med, f"Score: {self.score}", WHITE, surface, 14,8)
        _t(font_small,f"Level: {self.level}", LIGHT_GRAY, surface, 14,42)
        _t(font_small,f"Best: {self.personal_best}", LIGHT_GRAY, surface, 14,60)
        now=pygame.time.get_ticks()
        if self.active_powerup_label=="speed":
            rem=max(0,(self.speed_boost_end-now)//1000+1)
            _t(font_small,f"SPEED BOOST ({rem}s)",PU_SPEED,surface,WIDTH//2,10,center=True)
        elif self.active_powerup_label=="slow":
            rem=max(0,(self.slow_end-now)//1000+1)
            _t(font_small,f"SLOW MOTION ({rem}s)",PU_SLOW,surface,WIDTH//2,10,center=True)
        elif self.shield_active:
            _t(font_small,"SHIELD ACTIVE",PU_SHIELD,surface,WIDTH//2,10,center=True)
        _t(font_small,self.username, LIGHT_GRAY, surface, WIDTH-14,8,right=True)
        _t(font_small,f"Length: {len(self.body)}", LIGHT_GRAY, surface, WIDTH-14,30,right=True)

def _t(font, text, color, surface, x, y, center=False, right=False):
    img=font.render(str(text),True,color)
    r=img.get_rect()
    if center:   r.midtop=(x,y)
    elif right:  r.topright=(x,y)
    else:        r.topleft=(x,y)
    surface.blit(img,r)