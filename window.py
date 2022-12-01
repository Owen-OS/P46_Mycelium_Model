import pygame
import math
import sys
import os
import moviepy.video.io.ImageSequenceClip
from time import time as ttime
from threading import Thread
from PIL import Image
import multiprocessing
from sys import exit
from random import random, randint
import matplotlib.pyplot as plt
import random as rd
from PartitionManager import PartitionManager
from Pixel import Pixel
import xlsxwriter
import numpy as np
from Tip import Tip    


start_time = ttime() # Start time to determine runtime

# Arguments given as: [file_name, spore_num, innoculation_at_surface, random_inocculation]

'''VARIABLE DECLARATION START'''

    # Model Conditions
inocculation_at_surface = True
random_innoculation = False
shuffle_time = 3 * 24       # Time at which the bed is shuffled, currently set to 3 days
stop_time = 10 * 24          # Time the model is stopped, currently set to 10 days

    # Images Variables
lateral_branching = False
draw_images = True
image_iteration = 5

    # Screen Dimension Variables
bed_width = 4               # (cm), Actual width of the bed
bed_height = 4              # (cm), actual height of the bed
sub_height = 0.7            # Fraction of screen occupied by substrate

    # Hyphae Behaviour Variables
initial_branches = 5        # Number of branches formed by starting spores
spore_num = 3               # Number of starting spores, evenly spaced

std_offset = math.pi/50     # Hyphae branching offset
min_length = 0.40           # Minimum tip age before branching can occur
min_lateral_length = 10     # Minimum distance a branch must grow before a lateral branch can occur
branch_chance = 0.1         # Chance of a branch happening
ab_mean = 44.5              # Apical Branching angle mean, (°)
ab_sd = 0.625               # Apical Branching standard deviation (°)



    # Clock Variables
tick_speed = 1000             # Frames per second, running speed

    # Colour Variables
substrate_col = (115, 68, 32)
stalk_col = (255,255,230)
air_color = (124, 169, 242)

    # Lists to store information for Excel sheet
total_biomass = [0]
substrate_time = [0]
substrate_consumed = [0]
aerial_mycelium = [0]
aerial_time = [0]
'''VARIABLE DECLARATION END'''


'''FILE INITIATION START'''
# Clear out old items from current directory
fungi = sys.argv[0].split('/')[0]
substrate_folder = 'Substrate Frames'
frames_folder = 'Mycelium Frames'
composite_folder = 'Composite Frames'

if substrate_folder not in os.listdir():
    os.mkdir(substrate_folder)
if frames_folder not in os.listdir():
    os.mkdir(frames_folder)
if composite_folder not in os.listdir():
    os.mkdir(composite_folder)

for item in os.listdir(substrate_folder):
    os.remove(substrate_folder + '/' + item)
for item in os.listdir(frames_folder):
    os.remove(frames_folder + '/' + item)
for item in os.listdir(composite_folder):
    os.remove(composite_folder + '/' + item)
for item in os.listdir():
    if item.endswith('.mp4'):
        os.remove(item)
'''FILE INITIATION END'''

pygame.init()

n = multiprocessing.cpu_count()


'''
Function determines the window width and height in pixels for a given real bed height and diameter
This function ensures that the bed diameters in the window are to scale. The window width and height are
returned as integers and the scale is returned as a double indicating pixels to cm
'''
def scale(bed_width, bed_height, air_fraction) -> list:
    max_width = 1400        # Maximum allowable window width in pixels
    max_height = 800        # Maximum allowable window height in pixels
    
    total_height = bed_height/(1-air_fraction) # Height of the bed plus the air above in cm
    '''
    If the ratio of the input width to input height is greater than the width of the maximum width to maximum height
    then the width of the window should be set to the maximum width and the height should be scaled down. Otherwise
    the window height is set as the maximum height and the width is scaled down.

    Scale given as Pixels/cm
    '''
    # Return Width, Height, Screen Width/Actual Width
    if bed_width/total_height >= max_width / max_height:
        return [max_width, int(max_width*total_height/bed_width), max_width/bed_width]
    else:
        return [int(max_height*bed_width/total_height), max_height, int(max_height*bed_width/total_height)/bed_width]

 
[width, height, speed_scale] = scale(bed_width, bed_height, 1-sub_height)

substrate_start_height = int(height * (1-sub_height))

print(f'Width: {width}\nHeight: {height}')
print(f'Pixel Scale: {speed_scale} Pixels/cm')
# Grid to contain information about CO2, O2, Temp, H2O etc...
grid = []
for i in range(height):
    line = []
    for j in range(width):
        line.append(Pixel(speed_scale, 303.15))
    grid.append(line)

for i in range(height):
    for j in range(width):
        if i < height*(1-sub_height):
            grid[i][j].air()
        else:
            grid[i][j].substrate()

partitions = PartitionManager(grid)

# We need to set the local_concentration of each partition above the substrate to 0
air_height = int(height * (1-sub_height)) # Number of pixels for air section

air_partitions = air_height // partitions.partition_width
for i in range(air_partitions):
    for partition in partitions.partition_grid[i]:
        partition.local_concentration = 0

screen = pygame.display.set_mode((width, height))
screen.fill(air_color)
pygame.display.set_caption('Mycelium')
clock = pygame.time.Clock()

tips: list[Tip] = []
inactive_tips: list[Tip] = []       # inactive_tips will store the tips that are in areas of low concentration but have not undergone anastamosis


substrate = pygame.Surface((width, height*sub_height)).convert()
substrate.fill(substrate_col)
screen.blit(substrate, (0,height*(1-sub_height)))


'''START OF SUBSTRATE INNOCULATION'''
for i in range(spore_num):
    if not inocculation_at_surface:
        culture_x = randint(0, width)
        culture_y = randint(int(height * (1-sub_height)), height)
        starting_direction = random() * 2 * math.pi
    # Direction to be uniformly distributed between -pi/2 and pi/2
    for j in range(initial_branches):
        if inocculation_at_surface:
            cur_direction = -math.pi / 2 + (j+1) * (math.pi / (initial_branches + 1))
            tips.append(Tip((width - 1) // (spore_num + 1) * (i+1), height*(1-sub_height), grid, screen, cur_direction, speed_scale, 'secondary'))
        elif random_innoculation:
            cur_direction = starting_direction - math.pi / 2 + (j+1) * (2 * math.pi / (initial_branches))
            tips.append(Tip(culture_x, culture_y, grid, screen, cur_direction, speed_scale, 'secondary'))
        else:
            # need to rotate points in a 360• angle
            cur_direction = starting_direction - math.pi / 2 + (j+1) * (2 * math.pi / (initial_branches))
            tips.append(Tip((width - 1) // (spore_num + 1) * (i+1), substrate_start_height + height*(sub_height)/2, grid, screen, cur_direction, speed_scale, 'secondary'))
'''END OF SUBSTRATE INNOCULATION'''


# 0 means no stalk, 1 means a stalk is present
stalks = [[0]*width for _ in range(height)]

def count_mycelium(grid:list[list[Pixel]]) -> int:
    '''
    count_mycelium() loops through the grid and counts every Pixel with the pixel type 'mycelium'
    '''
    total_mycelium = 0
    for row in grid:
        for pixel in row:
            if pixel.ptype == 'mycelium':
                total_mycelium += 1
    return total_mycelium

def count_aerial_mycelium(grid: list[list[Pixel]]) -> int:
    total_mycelium = 0
    for row in grid[:substrate_start_height]:
        for pixel in row:
            if pixel.ptype == 'mycelium':
                total_mycelium += 1
    return total_mycelium

def draw_days(hours) -> None:
    '''
    draw_days() prints the current day and hour at the top of the screen
    '''
    days_passed = hours // 24
    hours_passed = hours - days_passed * 24

    string = "Days: " + str(days_passed) + " Hours: " + str(hours_passed) + "  "
    text = pygame.font.Font(None, 30).render(string, True, 'White')
    text_bg = text.get_rect(topleft = (25,50))
    
    pygame.draw.rect(screen, air_color, text_bg)
    screen.blit(text, (25, 50))


def paintGrid(iteration:int) -> Image:
    '''
    paintGrid() moves through the grid object and paints each pixel as a visual representation
    '''
    if iteration < 10:
        file_name = '00' + str(iteration * 10)
    elif iteration < 100:
        file_name = '0' + str(iteration * 10)
    else:
        file_name = str(iteration*10)
    
    image = Image.new(mode='RGB', size=(width, height), color=(12,25,245))

    # Create dictionary for color values of pixels
    colors = {'air':air_color, 'mycelium': stalk_col, 'substrate':substrate_col}

    for i in range(width):
        for j in range(height):
            image.putpixel((i,j), colors[grid[j][i].ptype])
    image.save(frames_folder + '/' + file_name + '.png')
    return image


def paint_composite(iteration:int, im1:Image, im2:Image):
    '''
    paint_composite() takes two images and overlays one image ontop of the other and then saves this image to a folder.
    '''
    if iteration < 10:
        file_name = '00' + str(iteration * 10)
    elif iteration < 100:
        file_name = '0' + str(iteration * 10)
    else:
        file_name = str(iteration*10)
    
    image = Image.blend(im1, im2, 0.3)
    image.save('Composite Frames/' + file_name + '.png')



def toVideo(folder: str, video_name: str) -> None:
    '''
    toVideo() takes a directory and video name and combines the images in the folder to an mp4 file with the title of the given string
    '''
    # Video should have a minimum length of 10 s?
    fps=10      # Preffered frame rate
    min_video_length = 10
    min_video_frames = min_video_length * fps
    # Video length given by Frames / fps
    # fps given as Frames / Vid_length
    
    
    image_files = [os.path.join(folder,img)
                for img in os.listdir(folder)
                if img.endswith(".png")]

    if len(image_files) < min_video_frames:
        # fps needs to be decreased so that video length minimum is upheld
        fps = max(1,round(len(image_files) / min_video_length))
    
    # Need to sort files, files are named 
    image_files.sort()

    clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    clip.write_videofile(video_name + '.mp4')

def exit_actions():
    '''
    exit_actions() contains a number of operations to complete once the visualisation tool is exited
    '''
    # Count each pixel in the substrate layer and see if it is substrate or mycelium
    sub_count = 0
    tip_count = 0

    for i in range(int(height*sub_height)-1):
        for j in range(width-1):
            if screen.get_at((j, int(i+height*(1-sub_height)))) == substrate_col:
                sub_count += 1
            else:
                tip_count += 1
    
    if draw_images:
        toVideo(composite_folder, 'composite_map')
    

    path = 'Data/' + fungi + '.xlsx'
    if 'Data' not in os.listdir():
        os.mkdir('Data')
    excel_book = xlsxwriter.Workbook(path)
    sheet = excel_book.add_worksheet()

    row = 0
    column = 0

    for i in range(len(substrate_time)):
        if row == 0:
            sheet.write(row, column, 'Time (h)')
            sheet.write(row, column+1, 'Substrate Consumed')
            sheet.write(row, column+2, 'Total Biomass')
        sheet.write(row+1, column, substrate_time[i])
        sheet.write(row+1, column+1, substrate_consumed[i])
        sheet.write(row+1, column+2, total_biomass[i])
        row += 1
    row = 0
    for i in range(len(aerial_mycelium)):
        if i == 0:
            sheet.write(row, column + 5, 'Time (h)')
            sheet.write(row, column + 6, 'Aerial Biomass')
        sheet.write(row+1, column + 5, aerial_time[i])
        sheet.write(row+1, column + 6, aerial_mycelium[i])
        row += 1
    
    excel_book.close()
    pygame.quit()
    end_time = ttime()
    runtime = end_time - start_time
    with open('runtime.txt', 'w') as f:
        f.write(f'Runtime: {runtime} s')
    print(f'\nRuntime: {end_time-start_time} s')
    exit()




hours = 0       # Counts the current hour. Used for drawing the hours and days
time = [0]      # Array of time passed. Used to plot biomass over time

'''
Total Mycelium body will have a growth potential. This is the number of movements (??) that can be taken 
'''
growth_potential = 5.0

aerial_growth = False
randomised = False
data_count = 1
count = 0
pic_num = 1
running = True  
while running:

    if hours == stop_time:
        exit_actions()
    
    
    '''DATA COLLECTION START'''
    if data_count == 2:
        #substrate_consumed.append(partitions.total_substrate_consumed(int(height * (1-sub_height))))
        substrate_consumed.append(partitions.total_consumption)
        substrate_time.append(time[-1])
        total_biomass.append(count_mycelium(grid))
        
        if aerial_growth:
            aerial_mycelium.append(count_aerial_mycelium(grid))
            aerial_time.append(time[-1])
        data_count = 0
    data_count += 1
    '''DATA COLLECTION END'''


    '''IMAGE DRAWING START'''
    count+=1
    if count == image_iteration and draw_images:
        #paintGrid(pic_num)
        substrate_map = paintGrid(pic_num)
        concentration_map = partitions.paint_grid(pic_num)
        paint_composite(pic_num, substrate_map, concentration_map)
        pic_num += 1
        count = 0
    '''IMAGE DRAWING END'''



    '''SHUFFLE CONDITION START'''
    if hours == shuffle_time and not randomised:
        aerial_growth = True
        randomised = True
        # Need to randomise the substrate and add nutrients to air. Allow for aerial mycelium growth
        partitions.average_concentrations(int(height * (1-sub_height)))

        # Now we need to randomly distribute mycelium, inactive tips and substrate in the bed
        mycelium_amount = count_mycelium(grid) - len(inactive_tips)
    
        new_grid = []
        for i in range(height):
            line = []
            for j in range(width):
                line.append(Pixel(speed_scale, 303.15))
            new_grid.append(line)

        for i in range(height):
            for j in range(width):
                if i < height*(1-sub_height):
                    new_grid[i][j].air()
                else:
                    new_grid[i][j].substrate()
        
        while mycelium_amount > 0:
            # randomly generate two numbers for width and height. Try and place a mycelium at this point
            y = randint(int(height * (1-sub_height)), height-1) 
            x = randint(0,  width - 1)
            if new_grid[y][x].ptype != 'mycelium':
                new_grid[y][x].mycelium()
                mycelium_amount -= 1
            
        grid = new_grid
        new_tips = []
        tip_amount = len(tips) + len(inactive_tips)
        while tip_amount > 0:
            y = randint(int(height * (1-sub_height)), height-1) 
            x = randint(0,  width - 1)
            if new_grid[y][x].ptype != 'mycelium':
                new_grid[y][x].mycelium()
                new_tips.append(Tip(x, y, grid, screen, random() * 2 * math.pi, speed_scale, 'secondary'))
                tip_amount -= 1
        
        tips = new_tips

        # now we need to add substrate to air section
        partitions.add_nutrients(3, int(height * (1-sub_height)))
    '''SHUFFLE CONDITION END'''



    '''USER INPUT DETECTION START'''
    # Check for Window being closed
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit_actions()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not randomised:
            print('R Pressed')
            aerial_growth = True
            randomised = True
            # Need to randomise the substrate and add nutrients to air. Allow for aerial mycelium growth
            partitions.average_concentrations(int(height * (1-sub_height)))

            # Now we need to randomly distribute mycelium, inactive tips and substrate in the bed
            mycelium_amount = count_mycelium(grid) - len(inactive_tips)
        
            new_grid = []
            for i in range(height):
                line = []
                for j in range(width):
                    line.append(Pixel(speed_scale, 303.15))
                new_grid.append(line)

            for i in range(height):
                for j in range(width):
                    if i < height*(1-sub_height):
                        new_grid[i][j].air()
                    else:
                        new_grid[i][j].substrate()
            
            while mycelium_amount > 0:
                # randomly generate two numbers for width and height. Try and place a mycelium at this point
                y = randint(int(height * (1-sub_height)), height-1) 
                x = randint(0,  width - 1)
                if new_grid[y][x].ptype != 'mycelium':
                    new_grid[y][x].mycelium()
                    mycelium_amount -= 1
                
            grid = new_grid
            new_tips = []
            tip_amount = len(tips) + len(inactive_tips)
            while tip_amount > 0:
                y = randint(int(height * (1-sub_height)), height-1) 
                x = randint(0,  width - 1)
                if new_grid[y][x].ptype != 'mycelium':
                    new_grid[y][x].mycelium()
                    new_tips.append(Tip(x, y, grid, screen, random() * 2 * math.pi, speed_scale, 'secondary'))
                    tip_amount -= 1

            tips = new_tips

            # now we need to add substrate to air section
            partitions.add_nutrients(3, int(height * (1-sub_height)))
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_t and aerial_growth:
            print('T Pressed')
            partitions.add_nutrients(3, int(height * (1-sub_height)))
    '''USER INPUT DETECTION END'''


    '''COLLISION DETECTION START'''
    # Remove tips that leave the bounds of the screen
    for t in tips:
        # if the tip reaches the top of the substrate, it should be redirected towards the edges
        if t.y < height * (1 - sub_height) and not aerial_growth:
            # if the tip has a leftward direction and is moving above the substrate, it should be moved to the left
            if t.direction > 0 and t.direction <= math.pi:
                t.direction = math.pi/2 - math.pi/25
            else:
                t.direction = -math.pi/2 + math.pi/25
        if t.speed <= 0.0:
            tips.remove(t)
            inactive_tips.append(t)
        # Out of bounds, remove the tip
        elif t.x <= t.speed or t.x >= width - t.speed or t.y >= height - t.speed:
            tips.remove(t)
    '''COLLISION DETECTION END'''


    '''RANDOM SPLITTING START'''
    # Determines random hyphae splitting
    for i in range(len(tips)):
        # Generate a psuedorandom number.
        split_chance = random()
        branch_chance = partitions.get_partition_at(t).local_concentration*3
        branch_chance = 0.05
        if partitions.get_partition_at(t).consumption != 0:
            branch_chance = 1 / partitions.get_partition_at(t).consumption

        if tips[i].length > tips[i].min_branching_distance:
            direc = tips[i].direction
            new_x = tips[i].x
            new_y = tips[i].y
            age = tips[i].age

            if tips[i].level == 'primary' and lateral_branching and tips[i].lateral_distance > min_lateral_length:
                # Lateral branch
                # Append a secondary branch to tips.
                # Angle to fall on a normal distribution around 80°
                tips[i].lateral_distance = 0
                mu, sigma = 80, 10
                s = np.random.normal(mu, sigma, 1)
                offset = s[0] * (math.pi / 180) # Convert angle to radians
                if random() < 0.5:
                    tips.append(Tip(new_x, new_y, grid, screen, direc - offset, speed_scale, 'secondary'))
                else:
                    tips.append(Tip(new_x, new_y, grid, screen, direc + offset, speed_scale, 'secondary'))

            else:
                # Apical branching
                tips.remove(tips[i])

                # Branching angle on a normal distribution between 42° and 47°
                mu, sigma = 44.5, 0.625
                s = np.random.normal(mu, sigma, 1)
                offset = s[0]/2 * (math.pi / 180) # Convert angle to radians

                tips.append(Tip(new_x, new_y, grid, screen, direc - offset, speed_scale, 'secondary'))
                tips[-1].find_min_distance()
                tips.append(Tip(new_x, new_y, grid, screen, direc + offset, speed_scale, 'secondary'))
                tips[-1].find_min_distance()

            #tips[-1].age = age
    '''RANDOM SPLITTING END'''


    '''CONSUMPTION START'''
    for t in tips:
        local_concentration = partitions.get_partition_at(t).local_concentration
        consumption = t.grow(local_concentration)
        gc = partitions.get_partition_at(t).growth_consumption(consumption)
        partitions.total_consumption += gc
        partitions.get_partition_at(t).consumption += consumption
    partitions.consume_all()
    '''CONSUMPTION END'''
    
    hours += 1
    time.append(hours)
    if tips:
        draw_days(hours)
    else:
        pass
        #exit_actions()

    
    
    pygame.display.update()
    clock.tick(tick_speed)
