import numpy as np
from random import random

class Partition:

    max_concentration = 3

    def __init__(self, width, height) -> None:
        self.local_concentration = self.max_concentration
        #mu, sigma = 3, 1
        #s = np.random.normal(mu, sigma, 1)
        #self.local_concentration = s[0]
        self.max_concentration = self.local_concentration
        self.consumption = 0
        self.width = width
        self.height = height
        
    def growth_consumption(self, consumption) -> float:
        growth_yield = 1
        self.local_concentration = max(0, (self.local_concentration * self.width * self.height - growth_yield * consumption) / (self.width * self.height))
        return growth_yield * consumption

    def total_substrate_consumed(self) -> float:
        '''
        total_substrate_consumed() returns the total amount of substrate that has been consumed thus far
        '''
        return (self.max_concentration - self.local_concentration) * self.width * self.height

    def consume(self) -> float:
        initial = self.local_concentration
        self.local_concentration = max(0, self.local_concentration*self.width*self.height - self.consumption)/(self.width*self.height)
        return initial - self.local_concentration
