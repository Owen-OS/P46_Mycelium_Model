from cmath import sqrt
import time
import pygame
from random import random, randint
import math
import numpy as np



class Tip:
    substrate_col = (115, 68, 32)
    stalk_col = (255,255,230)
    # Position of the tip
    x, y = 0,0
    conc_radius = 5

    # Width and height of tip
    thickness = 1
    w, h = thickness, thickness

    '''
    Gravity, from a scale of 0-1. A direction of 0 is downwards. Multiply the direction by (1-gravity) which will multiply by 0 if
    gravity is 1
    '''
    gravity = 0.0
    max_speed = 0.017
    speed = 0.017                   # (cm/h), Speed of the tip
    speed_scale = 1

    direction = math.pi

    wander_speed = math.pi/30

    lastX, lastY = 0, 0

    color = (153, 102, 51)
    grid_points = lambda x, y: (int(round(x, 0), int(round(y, 0))))


    # Initiate without a direction
    def __init__(self, x, y, grid, screen, direction, speed_scale, level: str) -> None:
        self.level = level
        self.direction = direction
        self.speed_scale = speed_scale
        self.grid = grid
        self.age = 0

        self.lastX = x
        self.lastY = y

        self.lateral_distance = 0

        self.x = x
        self.y = y
        self.screen = screen

        self.find_min_distance()


    def find_min_distance(self) -> None:
        self.length = 0
        shape, scale = 1.32,0.022  # mean=4, std=2*sqrt(2)
        s = np.random.gamma(shape, scale, 1)
        real_min_branching_distance = s[0]
        self.min_branching_distance = 5 * self.speed_scale * real_min_branching_distance # distance now in pixels
        

    # Function returns the position of the tip, rounded to the nearest integers
    def grid_points(self, x, y):
        grid_x = int(round(x, 0))
        grid_y = int(round(y, 0))
        return [grid_x, grid_y]


    def inBounds(self, x, y) -> bool:
        '''
        inBounds returns true if the given coordinates are within the bounds of self.grid.
        returns false otherwise
        '''
        y_len = len(self.grid)
        x_len = len(self.grid[0])

        #print('x_len: ' + str(x_len))
        #print('y_len: ' + str(y_len))

        if x < x_len-1 and x >= 0 and y < y_len-1 and y >= 0:
            return True
        return False

    def myc_line(self, x1, y1, x2, y2) -> None:
        '''
        myc_line() takes two sets of coordinates and sets the grid values to mycelium between those points        
        '''

        # Move from left to right
        if x1 > x2:
            x_temp = x1
            y_temp = y1

            x1 = x2
            y1 = y2
            x2 = x_temp
            y2 = y_temp
        
        # (x1, y1) is now the left-most point
        width = len(self.grid[1])

        height = len(self.grid)
        #print('Width: ' + str(width) + '\nHeight: ' + str(height))
        x2 = min(x2, width-1)
        y2 = min(y2, height-1)

        moving_point = [x1+0.5, y1+0.5]
        dx = x2 - x1
        dy = y2 - y1

        #print('Painting from (' + str(x1) + ';' + str(y1) + ') to (' + str(x2) + ";" + str(y2) + ')')


        if x1 == x2:
            moving_point[1] = min(y1, y2)
            while moving_point[1] < max(y1,y2) and self.inBounds(moving_point[0], moving_point[1]):
                #print('myc_line, 145\nx: ' + str(moving_point[0]) + ' y: ' + str(moving_point[1]))
                self.grid[int(moving_point[1])][int(moving_point[0])].mycelium()
                self.consume_substrate(int(moving_point[0]), int(moving_point[1]))
                moving_point[1] += 1
            return

        if abs(dx) > abs(dy):
            # Slope is more flat than steep. Move in increments of 1 in the x direction
            while moving_point[0] < x2 + 0.5 and self.inBounds(moving_point[0], moving_point[1]):
                #print('x: ' + str(int(moving_point[0])) + ' y: ' + str(int(moving_point[1])))
                #print(str(len(self.grid)) + 'x' + str(len(self.grid[0])))
                self.grid[int(moving_point[1])][int(moving_point[0])].mycelium()
                self.consume_substrate(int(moving_point[0]), int(moving_point[1]))
                moving_point[0] += 1
                moving_point[1] += dy/dx
            
        else:
        # Slope is more steep. Move in increments of 1 in the y direction
            if y1 < y2:
                # Line moves down, need to decrease y in increments of 1
                while moving_point[1] < y2 + 0.5 and self.inBounds(moving_point[0], moving_point[1]):
                    #print('x: ' + str(int(moving_point[0])) + ' y: ' + str(int(moving_point[1])))
                    self.grid[int(moving_point[1])][int(moving_point[0])].mycelium()
                    self.consume_substrate(int(moving_point[0]), int(moving_point[1]))
                    moving_point[1] += 1
                    moving_point[0] += dx/dy
            else:
                # Line is moving up
                while moving_point[1] > y2 - 0.5 and self.inBounds(moving_point[0], moving_point[1]):
                    #print('x: ' + str(moving_point[0]) + ' y: ' + str(moving_point[1]))
                    self.grid[int(moving_point[1])][int(moving_point[0])].mycelium()
                    self.consume_substrate(int(moving_point[0]), int(moving_point[1]))
                    moving_point[1] -= 1
                    moving_point[0] -= dx/dy      

    def consume_substrate(self, x, y) -> None:
        '''
        consume_substrate() sets the sub_conc values in the area surrounding mycelium. Implements a gradient:
            Mycelium -> 0
            ...
            Edge -> 1
        '''
        Yxs = 0.5
        max_width = len(self.grid[0])-1
        max_height = len(self.grid)-1

        concentration_curve = lambda i, j: 0.01 * (i+j)**2 - 0.2 * (i+j) + 1

        left = max(0, x-self.conc_radius)
        right = min(max_width, x + self.conc_radius)

        top = max(0, y - self.conc_radius)
        bottom = min(max_height, y + self.conc_radius)

        for i in range(left, right):
            for j in range(top, bottom):
                pass
                '''
                DO THIS LATER
                '''



    def grow(self, local_concentration) -> float:
        '''
        grow() finds the next point for a tip and paints a line between the current point and next point. Returns the consumption.
        '''

        #stalk = Stalk(self.lastX, self.lastY, self.screen)
        #stalk.draw()

        # Create a new surface with width and height
        surface = pygame.Surface((self.w, self.h)).convert()
        self.surface = surface
        
        # Fill the surface with RGB color
        surface.fill(self.color)
        # Print the surface to the screen
        pygame.draw.line(self.screen, self.stalk_col, (self.lastX, self.lastY), (self.x, self.y), self.thickness)
        
        
        self.screen.blit(surface, (self.x, self.y))

        # Set the last position to draw the stalk
        self.lastX = self.x
        self.lastY = self.y

        # Generate a random number between -wander_speed to wander_speed to change direction
        random_wander = random()*self.wander_speed*2 - self.wander_speed
        self.direction += random_wander
        self.direction = self.direction * (1 - self.gravity)
        speed = self.calculate_speed(local_concentration)
        #print('jump: ' + str(self.speed_scale * speed))

        self.x += self.speed_scale * speed * math.sin(self.direction)
        self.y += self.speed_scale * speed * math.cos(self.direction)

        if self.x < 0 or self.y < 0 or self.x >= len(self.grid[0]) or self.y >= len(self.grid):
            self.x -= self.speed_scale * speed * math.sin(self.direction)
            self.y -= self.speed_scale * speed * math.cos(self.direction)
        
        else:
            self.length += self.speed_scale * speed

        self.age += 1

        [x1, y1] = self.grid_points(self.lastX, self.lastY)
        [x2, y2] = self.grid_points(self.x, self.y)

        self.myc_line(x1, y1, x2, y2)

        # wait for some amount of time dependent on food
        # then call grow()
        # await time.sleep(2.5) <- wait for some amount of time proportional to food
        
        self.lateral_distance += self.length

        return self.speed_scale * speed

    def calculate_speed(self, local_concentration) -> float:
        mu_max = 0.0288         # Maximum growth rate in cm/h
        Ks = 0.0144                 
        mean = mu_max * local_concentration / (Ks + local_concentration)
        if mean <= 0:
            return 0
        sd = 0.0005
        s = np.random.normal(mean, sd, 1)
        speed = s[0]
        return max(0, speed)

    
    
        
