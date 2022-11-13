class Pixel:

    def __init__(self, scale, temperature) -> None:
        self.ptype = ''
        self.scale = scale
        self.temp = temperature
    
    def air(self) -> None:
        '''
        air() sets the current pixel to an air block. 
        '''
        self.ptype = 'air'
        self.sub_conc = 0

        '''
        We need to find the area of a pixel in cm^2.
        Convert 1 Pixel squared to cm^2.
        '''
        pixel_area = 1.0/(float(self.scale)**3)
        



    def substrate(self) -> None:
        '''
        substrate() sets the current pixel to a substrate b
        '''
        self.ptype = 'substrate'
        self.sub_conc = 1.0

    

    # Run function when space is turned into mycelium
    def mycelium(self) -> None:
        self.ptype = 'mycelium'



            

        
    

