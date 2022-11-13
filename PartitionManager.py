import math
import sys
from Partition import Partition
from Tip import Tip
from PIL import Image

class PartitionManager:


    def __init__(self, grid, partition_width=15) -> None:
        '''
        x_start: Starting x position of the partition grid
        e_end: end index

        [x_start, x_end] = [0, 10] ==> results in single partition of width 10 (0 to 9 including)
        '''
        self.partition_width = partition_width
        self.grid = grid
        self.partition_grid: list[list[Partition]] = []

        num_of_partitions = 20
        self.partition_width = int(len(grid[0]) / num_of_partitions)
        self.partition_width = 15

        for y in range(math.ceil(len(grid)/self.partition_width)):
            row: list[Partition] = []
            for x in range(math.ceil(len(grid[0])/self.partition_width)):
                width = min(self.partition_width, len(grid[0])-x*self.partition_width)
                height = min(self.partition_width, len(grid)-y*self.partition_width)
                row.append(Partition(width, height))
            self.partition_grid.append(row)
        self.total_consumption = 0

    def initial_substrate(self) -> None:
        total = 0
        for row in self.partition_grid:
            for partition in row:
                total += partition

    def get_partition_at(self, tip: Tip) -> Partition:
        return self.partition_grid[int(tip.y//self.partition_width)][int(tip.x//self.partition_width)]

    def consume_all(self):
        for row in self.partition_grid:
            for partition in row:
                consumption_amount = partition.consume()
                self.total_consumption += consumption_amount
                #if partition.consumption>0: print(f"consumption: {partition.consumption}, left: {partition.local_concentration*partition.width*partition.height}")

    def color_map(self, fraction) -> tuple:
        '''
        color_map() takes a percentage (substrate consumed) and converts it to an RGB value in a color map from white to black through red
        '''
        
        if fraction > 0.75:
            # White to yellow, (255, 255, 255) -> (255, 255, 0)
            return (255, 255, int(255 * (fraction - 0.75)/0.25))
        if fraction > 0.5:
            # Yellow to orange: (255, 255, 0) -> (255, 160, 0)
            return (255, int(160 + ((fraction - 0.5)/0.25)*(255-160)), 0)
        if fraction > 0.25:
            # Orange to Dark Red: (255, 160, 0) -> (165, 0, 0)
            return (int(fraction * 360 + 70), int(640 * fraction - 160), 0)
        else:
            # Dark Red to Black: (165, 0, 0) -> (0, 0, 0)
            return ( int(660 * fraction), 0, 0)


    def paint_grid(self, iteration: int) -> Image:
        '''
        paint_grid() loops through each partition, finds a color based on the concentration and then saves to an image for the entire grid
        '''
        bg_color = (0,0,0)
        image = Image.new('RGB', (len(self.grid[0]), len(self.grid)), bg_color)
        
        # Need to change iteration to the form 0010, 0020, 0030, etc

        if iteration < 10:
            file_name = '00' + str(iteration * 10)
        elif iteration < 100:
            file_name = '0' + str(iteration * 10)
        else:
            file_name = str(iteration*10)

        count1 = 0
        count2 = 0
        for row in self.partition_grid:

            for partition in row:
                fraction = partition.local_concentration / partition.max_concentration
                im = Image.new('RGB', (partition.width, partition.height), self.color_map(fraction))
                image.paste(im, (count1*self.partition_width, count2 * self.partition_width))
                count1 += 1
            count1 = 0
            count2 += 1
        fungi = sys.argv[0].split('/')[0]
        image.save('Substrate Frames'+ '/' + file_name + '.png')
        return image

    def total_substrate_consumed(self, height) -> float:
        '''
        total_substrate_consumed() returns the total amount of substrate that has been consumed in the substrate area
        height: position to start at 
        '''
        start_height = height // self.partition_width
        total = 0
        for row in self.partition_grid[start_height:]:
            for partition in row:
                total += partition.total_substrate_consumed()
        return total

    def average_concentrations(self, height) -> None:
        '''
        average_concentrations() takes a starting height and sets the local_concentration for each partition below that
        starting height to an average local concentration and sets this as the concentration for each partition.
        
        Function is meant to emulate the mixing of the substrate prior to aerial growth
        '''
        total = 0
        num = 0
        for row in self.partition_grid[int(height//self.partition_width):]:
            for partition in row:
                total += partition.local_concentration
                num += 1
        average_concentration = total / num
        for row in self.partition_grid[int(height//self.partition_width):]:
            for partition in row:
                partition.local_concentration = average_concentration
                partition.consumption = 0
        
    def add_nutrients(self, concentration, stop_height):
        '''
        add_nutrients() increases the local_concentration of the partitions above the substrate. 
        Function needs to find the first layer not containing mycelium (consumers) and affect the concentration at that level.
        '''
        end = stop_height//self.partition_width
        for row in self.partition_grid[:end]:
            row_has_mycelium = False
            for partition in row:
                if partition.consumption > 0:
                    row_has_mycelium = True
            if row_has_mycelium or row == self.partition_grid[end-1]:
                for partition in row:
                    partition.local_concentration += 3
                return
