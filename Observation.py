import numpy as np
from collections import OrderedDict

class Observation:
    'Common base class for all observations'

    def __init__(self, id, generation_time, zoi,model):
        # print ("Creating new observation...")
        self.id = id
        self.generation_time = generation_time
        self.zoi = zoi
        self.model = model
        
    def displayObservation(self):
        print("ID : ", self.id, ", Generation time: ", self.generation_time,  ", Zoi: ", self.zoi)

    def copy(self):
        copied_observation = Observation(self.id, self.generation_time, self.zoi, self.model)
        return copied_observation
