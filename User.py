import numpy as np
import math 
from collections import Counter 
from collections import OrderedDict
import sys
import geopy.distance

class User:
    'Common base class for all users'

    def __init__(self, id, posX, posY, scenario, memory):

        # print ("Creating new user...")

        self.id = id
        self.scenario = scenario
        self.total_memory = memory
        self.model_list = []
        self.pending_model_list = []
        self.computing_counter = 0
        self.merging_counter = 0
        self.exchange_list = []
        self.exchange_size = 0
        self.prev_peer = None
        self.busy = False # busy only per slot
        self.ongoing_conn = False
        self.db_exchange = False
        self.x_list = []
        self.y_list = []
        self.x_list.append(posX)
        self.y_list.append(posY)
        self.isPaused = False
        self.flight_length= np.inf
        self.x2 = 0
        self.y2 = 0
        self.xb = []
        self.yb = []
        self.xs = 0
        self.xd = 0
        self.ys = 0
        self.yd = 0
        self.first_move = True
        self.new_point_x = 0
        self.new_point_y = 0
        self.speed = (np.random.uniform(self.scenario.max_speed,self.scenario.min_speed))*self.scenario.delta
        self.N12 = np.inf            # slots to reach target position (x2,y2) 
        self.n = 1                   # current slot within N12 for random waypoint
        self.m = 0                   # current slot for random Direction
        self.rebound_counter = 0
        self.neighbours_list = []
        self.counter_list = []
        self.exchange_counter = 0
        self.used_memory = 0
        self.vx = 0
        self.vy = 0
        self.out = False
        self.x_origin = 0
        self.y_origin = 0
        self.connection_duration = 0
        self.contacts_per_slot_dynamic = OrderedDict()
        self.contacts_per_slot_static = OrderedDict()
        self.myFuture = OrderedDict()
        self.existing1 = True
        self.existing2 = True
        self.existing3 = True
        self.observations = []
        self.calculateZones(1)
        self.list_to_merge = []
        self.freshness = OrderedDict()
        self.observation_to_train = None
        self.start_exchange = 0
        

        # self.displayUser()

    
    def displayUser(self):
        print("ID : ", self.id,  ", Total Memory: ", self.total_memory,  ", Used Memory: ", self.used_memory, ", PosX: ",self.x_list, 
              ", PosY: ", self.y_list, ", Is Paused: ", self.isPaused, ", Slots Paused: ", self.pause_slots, 
              ", Counter Paused: ", self.pause_counter, ", slot n: ", self.n, ", Model list: " , len(self.model_list), ", Coordinates list: " , len(self.x_list))
        for z in self.zones:
            print("ZOI ID: ", z.id)
            print("Zone: ", self.zones[z])
           
    
    def calculateZones(self,c):
        # print("Slot:", c, "node: ", self.id)
        self.zones = OrderedDict()
        for z in self.scenario.zois_list:
            if self.scenario.city =="Paderborn" or self.scenario.city =="Luxembourg" or self.scenario.city == "none" :
                d = np.power(self.x_list[-1]- z.x,2) + np.power(self.y_list[-1]- z.y,2)
            if self.scenario.city !="Paderborn" and self.scenario.city !="Luxembourg" and self.scenario.city != "none" :
                coords_1 = (z.x, z.y)
                coords_2 = (self.x_list[-1], self.y_list[-1])
                d = geopy.distance.distance(coords_1, coords_2).m
            
            if d <= z.scenario.square_radius_of_replication:
                self.out = False
                # print("replication")
                self.zones[z] = "replication"
                self.myFuture[c] = z.id
                # print("calculating in replication", self.id)
            if d < z.scenario.square_radius_of_interest:
                # print("entro en replication", c, self.newObservation)
                self.out = False
                # print("interest")
                self.zones[z] = "interest"
                self.myFuture[c] = z.id
                # print("calculating in interes", self.id)
            if d > z.scenario.square_radius_of_replication:
                self.out = True
                # if c not in self.myFuture:
                self.myFuture[c] = -1
                if c > 1 and self.myFuture[c-1] != -1:
                    self.scenario.exiting_nodes[c] += 1

                    for observation in self.scenario.observations:
                        for model in self.model_list:
                            for key, value in model.contributions.items():
                                if key.id == observation.id:
                                    if observation.id not in self.scenario.nodes_exiting_with_obs.keys():
                                        self.scenario.nodes_exiting_with_obs[observation.id] = OrderedDict()

                                    if c not in self.scenario.nodes_exiting_with_obs[observation.id]:
                                        self.scenario.nodes_exiting_with_obs[observation.id][c] = 0

                                    self.scenario.nodes_exiting_with_obs[observation.id][c] += 1
                        
               
                self.deleteModels(z)
                
          
    # def deleteModels(self,z):
        # We remove the messages belonging to this zone in case the node was previously in the zone (the zone existed before)    \
        # print("My id: ", self.id, " zone: ", z.id)
        # print("Used memory: ", self.used_memory)
        # # print("Exchange list size: ", self.exchange_size)
        # for m in self.model_list:
        #     # print("MESSAGE: ", m.id, " zone: ", m.zoi.id)
        #     if m.zoi == z:
        #         # print("Entro en borrar de mi lista el size: ", m.size, "lista: ", len(self.model_list))
        #         self.used_memory -= m.size
        #         self.model_list.remove(m)
        #         # print("lista: ", len(self.model_list))
        #         if m in self.exchange_list:
        #             # print("Entro en borrar de mi exchange", len(self.exchange_list),self.exchange_size)
        #             self.exchange_size -= m.size
        #             self.exchange_list.remove(m)
        #             # print("despues de borrar exchange", len(self.exchange_list),self.exchange_size)

        # for m in self.pending_model_list:
        #     if m.zoi == z:
        #         self.pending_model_list.remove(m)
        #         self.computing_counter = 0
               
        
        # self.db_exchange = False what to do with this?
        # print("Dropping my DB")
        # print("Used memory: ", self.used_memory)
        # print("Exchange list size: ", self.exchange_size)


    def deleteModels(self,z):
        if self.id == 127:
            print(self.id,"estoy deleteando mis models", len(self.model_list))
        self.model_list = []
        self.pending_model_list = []
        self.computing_counter = 0
        self.merging_counter = 0
        self.list_to_merge = []
        self.observations = []
        self.observation_to_train = None
   
    
    def getNextWayPoint(self):
        self.x2 = np.random.uniform(-self.scenario.max_area,self.scenario.max_area)
        self.y2 = np.random.uniform(-self.scenario.max_area,self.scenario.max_area)

    def randomWaypoint(self,c):
  
            # print ("My id is ", self.id)           
            # if it is the first time that the user is moving from origin (x1,y1), 
            # we need to  calculate target position (x2,y2) and the number of slots to reach target position (only at the beginning)
            if self.n==1:
                self.randomWaypointParameters()
   
            # If we are at the beggining of a path between 2 points, 
            # save source and destination coordinates and N12 as self information for the following slots (It is going to be the same until n = N12)
            if self.n == 1:
                # print("Entering in n == 1 for a new rebound")
                self.xs = self.xb[self.rebound_counter]
                self.ys = self.yb[self.rebound_counter]
                self.xd = self.xb[self.rebound_counter + 1]
                self.yd = self.yb[self.rebound_counter + 1]
                # print(self.xs, self.ys, self.xd, self.yd)
                # Distance between 2 points
                dist = np.sqrt(np.power((self.xb[self.rebound_counter+1]-self.xb[self.rebound_counter]),2) + 
                            np.power((self.yb[self.rebound_counter+1]-self.yb[self.rebound_counter]),2))
                # print('Distancia----> ',dist)
                # Time to move from (xb1,yb1) to (xb2,yb2)
                self.T12 = dist/self.speed
                # print('t12----> ',self.T12)

                # Number of slots to reach (xb2,yb2)
                self.N12 = np.ceil((self.T12))
                # print("Number of slots until target/border position N12 --> %d" % self.N12)

            # we need to find the new intermediate position between n and n-1 regarding user speed
            # Euclidean vector ev = (x2-x1,y2-y1) and next position after one time slot (xi,yi) = (x1,y1) + n/N12 * ev
            xi = self.xs + (self.n/self.N12) * (self.xd - self.xs)   
            yi = self.ys + (self.n/self.N12) * (self.yd - self.ys)
            # print("xi --> " , xi)
            # print("yi --> " , yi)
    

            # Once the intermediate position (xi,yi) is selected, add the coordinates to the lists
            self.x_list.append(xi)
            self.y_list.append(yi)

            self.n = self.n + 1

            # if we have reached a bound position, update the counters to start again with the next
            if self.n == self.N12 + 1:
                self.n = 1
                self.N12 = 0
                self.rebound_counter += 1
                # print("rebound_counter: ",self.rebound_counter)
                # print("Bound position reached, n = 0.")
                    

            if self.rebound_counter == len(self.xb)-1:
                self.rebound_counter = 0
                self.xb = []
                self.yb = []
                # print("Final target position reached, rebound counter = 0.")

        
            # # Check the new point zone and print the info of the user
            # self.calculateZones(c)


        # with this method we create two lists xb and yb at the beggining of the mobility with all the border and targer positions of the user
    def randomWaypointParameters(self):
        self.getNextWayPoint()            
        # print("X2: ",self.x2, ", Y2: ", self.y2)
        # Save current position
        self.xb.append(self.x_list[-1]) 
        self.yb.append(self.y_list[-1])

        # Append target possition to the end of the list 
        # (if the target position is never out of bounds this list will only containg the first position and the targer position)
        # print("Final target position ----> X2: ", self.x2, ", Y2: ", self.y2)
            
        self.xb.append(self.x2)
        self.yb.append(self.y2)


    def randomDirection(self,c):
        # initial position m = 1
        if self.first_move:
            # select an angle
            randNum = np.random.uniform()
            alpha = 360 * randNum *(math.pi/180)

            # vector based on angle
            self.vx = math.cos(alpha)
            self.vy = math.sin(alpha)

            # take my current position
            self.x_origin = self.x_list[-1]
            self.y_origin = self.y_list[-1]

            self.first_move = False


        # flight_length is infinite
        if not self.first_move:
            self.m += 1
            x = (self.vx*self.speed*self.m) + self.x_origin
            y = (self.vy*self.speed*self.m) + self.y_origin  

            if x > self.scenario.max_area:
                x = -self.scenario.max_area + (x-self.scenario.max_area)
                y = y
                self.x_origin = x
                self.y_origin = y
                self.m = 0
            if x < -self.scenario.max_area:
                x = self.scenario.max_area + (x+self.scenario.max_area)
                y = y
                self.x_origin = x
                self.y_origin = y
                self.m = 0
            if y > self.scenario.max_area:
                y = -self.scenario.max_area + (y-self.scenario.max_area)
                x = x
                self.x_origin = x
                self.y_origin = y
                self.m = 0
            if y < -self.scenario.max_area:
                y = self.scenario.max_area + (y+self.scenario.max_area)
                x = x
                self.x_origin = x
                self.y_origin = y
                self.m = 0


            self.x_list.append(x)
            self.y_list.append(y)
           
            # Use only when we don't want to store every position in the list but only the current position. We are now 
            # storing everything in the previous 2 lines of code.
            # self.x_list[-1]=x
            # self.y_list[-1]=y
            
      
    # Method to read from the traces (stored in the scenario) each node's new position
    # This method will make a node move in every new slot to the next point in the list
    def readTraces(self,c):
        if c in self.scenario.tracesDic[self.id]:
            items = self.scenario.tracesDic[self.id][c]
            x = items[0]
            y = items[1]
            # speed = items[2]

            # print("Next point: ", x, y)   
            self.x_list.append(x)
            self.y_list.append(y)

        else:
            self.x_list.append(self.x_list[-1])
            self.y_list.append(self.y_list[-1])

        # self.calculateZones(c)

    def predict(self,nslots):
        for c in range(nslots):
            if c in self.scenario.tracesDic[self.id]:
                items = self.scenario.tracesDic[self.id][c]
                x = items[0]
                y = items[1]
                for z in self.scenario.zois_list:
                    if self.scenario.city =="Paderborn" or self.scenario.city =="Luxembourg" or self.scenario.city =="none":
                        d = np.power(x - z.x,2) + np.power(y - z.y,2)
                    if self.scenario.city !="Paderborn" and self.scenario.city !="Luxembourg" and self.scenario.city != "none":
                        coords_1 = (z.x, z.y)
                        coords_2 = (x, y)
                        d = geopy.distance.distance(coords_1, coords_2).m
                    if d < z.scenario.square_radius_of_replication:
                        self.myFuture[c] = z.id
                    if d < z.scenario.square_radius_of_interest:
                        self.myFuture[c] = z.id
                    if d > z.scenario.square_radius_of_replication:
                        if c not in self.myFuture:
                            self.myFuture[c] = -1 
            else:
                if c == 0:
                    # print(self.id,self.scenario.tracesDic[self.id].keys()[0])
                    first_c = list(self.scenario.tracesDic[self.id].keys())[0]
                    items = self.scenario.tracesDic[self.id][first_c]

                    x = items[0]
                    y = items[1]
                    for z in self.scenario.zois_list:
                        if self.scenario.city =="Paderborn" or self.scenario.city =="Luxembourg" or self.scenario.city =="none":
                            d = np.power(x - z.x,2) + np.power(y - z.y,2)
                        if self.scenario.city !="Paderborn" and self.scenario.city !="Luxembourg" and self.scenario.city != "none":
                            coords_1 = (z.x, z.y)
                            coords_2 = (x, y)
                            d = geopy.distance.distance(coords_1, coords_2).m
                        if d < z.scenario.square_radius_of_replication:
                            self.myFuture[c] = z.id
                        if d < z.scenario.square_radius_of_interest:
                            self.myFuture[c] = z.id
                        if d > z.scenario.square_radius_of_replication:
                            if c not in self.myFuture:
                                self.myFuture[c] = -1 
                else:
                    self.myFuture[c] = self.myFuture[c-1]

    def userContact(self,c):
        # print ("My id is ", self.id, " Am I busy for this slot: ", self.busy)
        my_rep_zones = []
        my_inter_zones = []
        if "replication" in self.zones.values():
            my_rep_zones.append(list(self.zones.keys())[list(self.zones.values()).index("replication")])
        if "interest" in self.zones.values():
            my_inter_zones.append(list(self.zones.keys())[list(self.zones.values()).index("interest")])

        my_rep_zones.extend(my_inter_zones)

        # Include the neighbours found in this slot for contact statistics
        for user in self.scenario.usr_list:
            if user.id != self.id: #and user.myFuture[c] != -1:
                pos_user = np.power(user.x_list[-1]-self.x_list[-1],2) + np.power(user.y_list[-1]-self.y_list[-1],2)
              
                if pos_user < self.scenario.square_radius_of_tx:
                    if user.id in self.scenario.list_of_static_nodes or self.id in self.scenario.list_of_static_nodes:
                        self.contacts_per_slot_static[c].append(user.id)
                    if user.id not in self.scenario.list_of_static_nodes and self.id not in self.scenario.list_of_static_nodes:
                        self.contacts_per_slot_dynamic[c].append(user.id)
               


        if self.busy:
            if c not in self.scenario.whos_transmiting.keys():
                self.scenario.whos_transmiting[c] = 0
            self.scenario.whos_transmiting[c] += 1

        # Check if the node is not BUSY already for this slot and if the it is in the areas where data exchange is allowed
        if not self.busy and len(my_rep_zones)>0:
            self.neighbours_list = []
            # Find neighbours in this user's tx range
            for user in self.scenario.usr_list:
                if user.id != self.id:
                    pos_user = np.power(user.x_list[-1]-self.x_list[-1],2) + np.power(user.y_list[-1]-self.y_list[-1],2)
                    
                    if pos_user < self.scenario.square_radius_of_tx:
                        # Check if the neighbour is in the areas where data exchange is allowed
                        user_rep_zones = []
                        user_inter_zones = []
                        if "replication" in user.zones.values():
                            user_rep_zones.append(list(user.zones.keys())[list(user.zones.values()).index("replication")])
                        if "interest" in user.zones.values():
                            user_inter_zones.append(list(user.zones.keys())[list(user.zones.values()).index("interest")])

                        user_rep_zones.extend(user_inter_zones)
                        p = set(my_rep_zones)&set(user_rep_zones)
                        if len(p) > 0:
                            self.neighbours_list.append(user)
                            # print("This is my neighbour: ", user.id, user.busy)

            # Suffle neighbours list to void connecting always to the same users
            np.random.shuffle(self.neighbours_list)
           
            # Once we have the list of neighbours, first check if there is a previous connection ongoing and the peer is still inside my tx range
            # which is the same as been in the neighbours list since we checked the positions above
            if self.ongoing_conn == True and self.prev_peer in self.neighbours_list:
                # print("I have a prev peer and it is still close. ", self.prev_peer.id)
                self.connection_duration += 1
                self.prev_peer.connection_duration += 1
                # keep exchanging
                self.db_exchange = False
                self.prev_peer.db_exchange = False
                self.exchangeModel(self.prev_peer,c)

            # else exchange data with a probability and within a channel rate per slot
            else:
                # if my prev peer is not in my communication range we don't exchange data anymore
                if self.ongoing_conn == True and self.prev_peer not in self.neighbours_list:
                    # print("I have a prev peer and it is far. ", self.prev_peer.id)
                    if self.connection_duration not in self.scenario.connection_duration_list.keys():
                        self.scenario.connection_duration_list[self.connection_duration] = 1
                    else:
                        self.scenario.connection_duration_list[self.connection_duration] +=1

                    self.connection_duration = 0
                    self.prev_peer.connection_duration = 0
                    # If in previous slot we have exchanged bits from next messages we have to remove them from the used memory because we did't manage to
                    # exchange the whole message so we loose it. Basically --> only reset used_memory because the msg has not been added to the list.
                    reset_used_memory = 0
                    for m in self.model_list:
                        reset_used_memory = reset_used_memory + m.size
                    self.used_memory = reset_used_memory
                    reset_used_memory = 0
                    for m in self.prev_peer.model_list:
                        reset_used_memory = reset_used_memory + m.size
                    self.prev_peer.used_memory = reset_used_memory

                    # reset all parameters to start clean with a new peer
                    self.exchange_list = []
                    self.prev_peer.exchange_list = []
                    self.exchange_size = 0  
                    self.prev_peer.exchange_size = 0
                    self.db_exchange = False
                    self.prev_peer.db_exchange = False
                    self.ongoing_conn = False
                    self.prev_peer.ongoing_conn = False
                    # Set back the used mbs for next data exchange for next slot
                    self.scenario.used_mbs = 0
                
                # Continue looking for neighbours   
                # print("Neighbour list: ", len(self.neighbours_list))
                # In case we want to connect with more than one neighbour we need to run a loop. Now we only select one neighbour from the list.
                neighbour = None
                for neig in self.neighbours_list:
                        if not neig.busy and neig.ongoing_conn == False and (len(neig.model_list)>0 or len(self.model_list)>0):
                            neighbour = neig
                            # print("I found a peer not busy and without ongoing connection. ", neighbour.id)
                            break
                if neighbour != None:
                    if self.id == 127:
                        print("tengo neighbour:", neighbour.id)
                    self.scenario.attempts +=1
                    # print("Attempts--- ", self.scenario.attempts)
                    self.connection_duration += 1
                    neighbour.connection_duration +=  1
                    self.exchange_size = 0
                    neighbour.exchange_size = 0
                    self.exchange_list = []
                    neighbour.exchange_list = []
                    self.exchange_counter = 0
                    neighbour.exchange_counter = 0
                    self.counter_list = []
                    neighbour.counter_list = []
                    self.db_exchange = False
                    neighbour.db_exchange = False
                    self.scenario.used_mbs = 0
                    # First, check the messages missing in the peers devices and add them to the exchange list 
                    # of messages of every peer
                    
                    if len(self.model_list) > 0:
                        for m1 in self.model_list:
                            self.existing1 = False
                            self.existing2 = False
                            self.existing3 = False
                            if len(m1.contributions) > 0:
                                for pickCont1 in m1.contributions.keys():
                                    if len(neighbour.pending_model_list) > 0:
                                        for nm1 in neighbour.pending_model_list: 
                                            if nm1.id == m1.id:
                                                if pickCont1 in nm1.contributions.keys():
                                                    self.existing1 = True 
                                                                                            
                                                
                                    if len(neighbour.model_list) > 0:
                                        for nm2 in neighbour.model_list:
                                            if nm2.id == m1.id:
                                                if pickCont1 in nm2.contributions.keys():
                                                    self.existing2 = True                 
                                            

                                    if len(neighbour.list_to_merge) > 0:
                                        for nm5 in neighbour.list_to_merge:
                                            if nm5.id == m1.id:
                                                if pickCont1 in nm5.contributions.keys():
                                                    self.existing3 = True                                                             
                                        
                                    if not self.existing1 and not self.existing2 and not self.existing3:
                                        meter = True
                                        for modelcomp in self.exchange_list:
                                            if modelcomp.id == m1.id:
                                                meter = False

                                        if meter:
                                            self.exchange_list.append(m1.copy()) 
                                            if str(m1.id) not in self.scenario.exchanges_of_models.keys():
                                                self.scenario.exchanges_of_models[str(m1.id)] = 0
                                            self.scenario.exchanges_of_models[str(m1.id)] +=1
                                            
                                            if self.id == 127:
                                                print("meto en exchange para mi neighbour:", len(self.exchange_list)) 
                                            self.exchange_size = self.exchange_size + m1.size
                                            if len(self.counter_list) == 0:
                                                self.counter_list.append(m1.size)
                                            else:
                                                self.counter_list.append(self.counter_list[-1]+m1.size)


                        # np.random.shuffle(self.exchange_list)
                    
                    if len(neighbour.model_list) > 0:
                        for m2 in neighbour.model_list:
                            neighbour.existing1 = False
                            neighbour.existing2 = False
                            neighbour.existing3 = False
                            if len(m2.contributions) > 0:
                                for pickCont2 in m2.contributions.keys():
                                    if len(self.pending_model_list) > 0:
                                        for nm3 in self.pending_model_list:  
                                            if nm3.id == m2.id:  
                                                if pickCont2 in nm3.contributions.keys():
                                                    neighbour.existing1 = True
                                            
                                    if len(self.model_list) > 0:
                                        for nm4 in self.model_list:  
                                            if nm4.id == m2.id:
                                                if pickCont2 in nm4.contributions.keys():
                                                    neighbour.existing2 = True
                                            
                                                
                                    if len(self.list_to_merge) > 0:
                                        for nm6 in self.list_to_merge:
                                            if nm6.id == m2.id:
                                                if pickCont2 in nm6.contributions.keys():
                                                    neighbour.existing3 = True
                                                
                                            
                                    
                                    if not neighbour.existing1 and not neighbour.existing2 and not neighbour.existing3:
                                        meter = True
                                        for modelcomp in neighbour.exchange_list:
                                            if modelcomp.id == m2.id:
                                                meter = False
                                        if meter:
                                            neighbour.exchange_list.append(m2.copy())
                                            if str(m2.id) not in self.scenario.exchanges_of_models.keys():
                                                self.scenario.exchanges_of_models[str(m2.id)] = 0
                                            self.scenario.exchanges_of_models[str(m2.id)] +=1

                                            if self.id == 127:
                                                print("meto en exchange  de mi neigubhour para mi:", len(neighbour.exchange_list))
                                            neighbour.exchange_size = neighbour.exchange_size + m2.size
                                            if len(neighbour.counter_list) == 0:
                                                neighbour.counter_list.append(m2.size)
                                            else:
                                                neighbour.counter_list.append(neighbour.counter_list[-1]+m2.size)

                                    

                        # After choosing the messages that are missing in the peer, we need to shuffle the list
                        # np.random.shuffle(neighbour.exchange_list)


                    # Second, exchange the data with peer!!
                    # Count in advance if the connection is going to be useful or not, it means if they have something to exchange.
                    # In case we have nothing to exchange we use the last slot for the checking
                    self.scenario.total_num_exchanges += 1

                    # if self.exchange_size == 0 and neighbour.exchange_size == 0:
                    #     self.scenario.count_non_useful +=1
                    # if self.exchange_size != 0 or neighbour.exchange_size != 0:
                    #     self.scenario.count_useful +=1
                    # if self.exchange_size != 0 and neighbour.exchange_size != 0:
                    #     self.scenario.num_bidirectional +=1


                    if len(self.exchange_list) == 0 and len(neighbour.exchange_list) == 0:
                        self.scenario.count_non_useful +=1
                    if len(self.exchange_list) != 0 or len(neighbour.exchange_list) != 0:
                        self.scenario.count_useful +=1
                    if len(self.exchange_list) != 0 and len(neighbour.exchange_list) != 0:
                        self.scenario.num_bidirectional +=1

                    self.start_exchange = c
                    neighbour.start_exchange = c

                    self.exchangeModel(neighbour,c)

        
                        
                    
    # Method to check which DB is smaller and start exchanging it. 
    # At this point We have the messages to be exchange (exchange_list) and the total list sizes (exchange_size).

    def exchangeModel(self,neighbour,c):

        
        self.busy = True
        neighbour.busy = True
        self.ongoing_conn = True
        neighbour.ongoing_conn = True

        if self.exchange_size == 0 and neighbour.exchange_size == 0:
            self.db_exchange = True
            neighbour.db_exchange= True

        if self.exchange_size <= neighbour.exchange_size and self.db_exchange is False:
            howMany = 0
            howMany1 = 0
            howMany2 = 0

            # print("My db is smaller than neighbours ", self.exchange_size)
            if self.exchange_size == 0:
                self.db_exchange = True
            else: 
                #########################################################################################################
                if (self.exchange_counter < self.exchange_size):
                    howMany = self.exchange_size - self.exchange_counter
                    howMany1 = self.exchange_size - self.exchange_counter
                    howMany2 = self.exchange_size - self.exchange_counter

                    # Check if the amount of bits to transfer (self.exchange_size) fits in the available channel rate
                    if (howMany > ((self.scenario.mbs/2) - self.scenario.used_mbs)):
                        howMany1 = (self.scenario.mbs/2) - self.scenario.used_mbs
                    if (neighbour.used_memory + howMany > neighbour.total_memory):
                        howMany2 = neighbour.total_memory - neighbour.used_memory

                    howMany = min(howMany1,howMany2)
                    
                    self.exchange_counter += howMany
                    self.scenario.used_mbs += howMany
                    neighbour.used_memory += howMany

                    self.db_exchange = True 
                   
            self.scenario.used_mbs_per_slot.append(self.scenario.used_mbs)   
            #########################################################################################################
            # print("Now we continue with Neigbours db", neighbour.exchange_size)
            if neighbour.exchange_size == 0:
                neighbour.db_exchange = True
            else:
                if (neighbour.exchange_counter < neighbour.exchange_size):
                    howMany = neighbour.exchange_size - neighbour.exchange_counter
                    howMany1 = neighbour.exchange_size - neighbour.exchange_counter
                    howMany2 = neighbour.exchange_size - neighbour.exchange_counter

                    # Check if the amount of bits to transfer (neighbour.exchange_size) fits in the available channel rate
                    if(howMany > (self.scenario.mbs - self.scenario.used_mbs)):
                        howMany1 = self.scenario.mbs - self.scenario.used_mbs
                    if (self.used_memory + howMany > self.total_memory):
                        howMany2 = self.total_memory - self.used_memory
        

                    howMany = min(howMany1,howMany2)
                
                    neighbour.exchange_counter += howMany
                    neighbour.scenario.used_mbs += howMany
                    self.used_memory += howMany
                    
                    neighbour.db_exchange = True  
                   
            neighbour.scenario.used_mbs_per_slot.append(howMany)
        #########################################################################################################
        if neighbour.exchange_size < self.exchange_size and neighbour.db_exchange is False:
            howMany = 0
            howMany1 = 0
            howMany2 = 0
            # print("Neighbour db is smaller than mine", neighbour.exchange_size)
            if neighbour.exchange_size == 0:
                neighbour.db_exchange = True
            else:
                if (neighbour.exchange_counter < neighbour.exchange_size):
                    howMany = neighbour.exchange_size - neighbour.exchange_counter
                    howMany1 = neighbour.exchange_size - neighbour.exchange_counter
                    howMany2 = neighbour.exchange_size - neighbour.exchange_counter

                    if(howMany > ((self.scenario.mbs/2) - self.scenario.used_mbs)):
                        howMany1 = (self.scenario.mbs/2) - self.scenario.used_mbs
                    if(self.used_memory + howMany > self.total_memory):
                        howMany2 = self.total_memory - self.used_memory
                
                    
                    howMany = min(howMany1,howMany2)
                        
                    neighbour.exchange_counter += howMany
                    neighbour.scenario.used_mbs += howMany
                    self.used_memory += howMany

                    neighbour.db_exchange = True  
                  
            neighbour.scenario.used_mbs_per_slot.append(self.scenario.used_mbs)
            #########################################################################################################
            # print("Now we continue with my db", self.exchange_size)
            if self.exchange_size == 0:
                self.db_exchange = True
            else:
                if (self.exchange_counter < self.exchange_size):
                    howMany = self.exchange_size - self.exchange_counter
                    howMany1 = self.exchange_size - self.exchange_counter
                    howMany2 = self.exchange_size - self.exchange_counter
                    
                    if(howMany > (self.scenario.mbs - self.scenario.used_mbs)):
                        howMany1 = self.scenario.mbs - self.scenario.used_mbs
                        
                    if(neighbour.used_memory + self.exchange_size > neighbour.total_memory):
                        howMany2 = neighbour.total_memory - neighbour.used_memory
                    
                    howMany = min(howMany1,howMany2)
                    
                    self.exchange_counter += howMany
                    neighbour.used_memory += howMany
                    self.scenario.used_mbs += howMany

                    self.db_exchange = True  
                    
            self.scenario.used_mbs_per_slot.append(howMany)
            #########################################################################################################

        # Now we exchange the db based on the already exchanged bytes of messages
      
        if len(self.exchange_list) > 0:
            print("que tengo antes", len(neighbour.pending_model_list))
            for m in neighbour.pending_model_list:
                print(m.id)

            for i in range(0,len(self.counter_list)): 
                if (self.counter_list[i] <= self.exchange_counter):
                    print("i------------>",i)
                    print("checking exchange counters-->", self.counter_list[i], self.exchange_counter)

                    alreadythere = False
                    for mp in neighbour.pending_model_list:
                        if mp.id == self.exchange_list[i].contributions:
                            alreadythere = True

                    if not alreadythere:
                        neighbour.pending_model_list.append(self.exchange_list[i].copy())


                        if str(self.exchange_list[i].id) not in self.scenario.exchanges_succesful_of_models.keys():
                            self.scenario.exchanges_succesful_of_models[str(self.exchange_list[i].id)] = 0
                        self.scenario.exchanges_succesful_of_models[str(self.exchange_list[i].id)] += 1

                        self.scenario.length_content_exchange.append(c-neighbour.start_exchange)
                        neighbour.start_exchange = c

                if(self.counter_list[i] == self.exchange_counter):
                    break

            print(self.id,neighbour.id,"que he metido al final", len(neighbour.pending_model_list))
            for m in neighbour.pending_model_list:
                print(m.id)
                    
        if len(neighbour.exchange_list) > 0:
            for j in range(0,len(neighbour.counter_list)):
                if (neighbour.counter_list[j] <= neighbour.exchange_counter): 
                    
                    alreadythere = False
                    for sp in self.pending_model_list:
                        if sp.contributions == neighbour.exchange_list[j].contributions:
                            alreadythere = True

                    if not alreadythere:

                        self.pending_model_list.append(neighbour.exchange_list[j].copy())

                        if str(neighbour.exchange_list[j].id) not in self.scenario.exchanges_succesful_of_models.keys():
                            self.scenario.exchanges_succesful_of_models[str(neighbour.exchange_list[j].id)] = 0
                        self.scenario.exchanges_succesful_of_models[str(neighbour.exchange_list[j].id)] += 1



                        if self.id == 127:
                            print("me han pasado un modelo a mis pendings-->", len(self.pending_model_list))
                        self.scenario.length_content_exchange.append(c-self.start_exchange)
                        self.start_exchange = c

                    # if self.id == 2:
                    #     print(neighbour.id,self.id,"adding model", neighbour.exchange_list[j].id)
                    #     for contrib in neighbour.exchange_list[j].contributions.keys():
                    #         print(contrib.id)

                if(neighbour.counter_list[j] == neighbour.exchange_counter):
                    break

     

            

        # After exchanging both peers part of the db, set back the booleans for next slot
        self.db_exchange = False
        neighbour.db_exchange = False
        # Set back the used mbs for next data exchange for next slot
        self.scenario.used_mbs = 0

        # If any of the peers DB has not been totally exchanged we have to store the peer device to keep the connection for next slot
        # print("COMPROBAR---------> ",self.exchange_counter, self.exchange_size, neighbour.exchange_counter, neighbour.exchange_size,len(self.model_list),len(neighbour.model_list))
        if self.exchange_counter < self.exchange_size or neighbour.exchange_counter < neighbour.exchange_size:
            self.prev_peer = neighbour
            # print(" PASSING NEIGHBOUR TO PREV DB", neighbour.id, self.prev_peer.id, neighbour == self.prev_peer)
            self.ongoing_conn = True
            self.prev_peer.ongoing_conn = True
            self.prev_peer.prev_peer = self
            
        # If everything has been exchanged, reset parameters
        if (self.exchange_counter == self.exchange_size and neighbour.exchange_counter == neighbour.exchange_size) or (self.total_memory == self.used_memory and neighbour.total_memory == neighbour.used_memory):
            # print("EVERYTHING HAS BEEN EXCHANGED WITH: ", self.exchange_counter,self.exchange_size)
            # print("ENTRO AQUI", self.exchange_counter, self.exchange_size,neighbour.exchange_counter, neighbour.exchange_size, self.used_memory, self.used_memory)
            if self.connection_duration not in self.scenario.connection_duration_list.keys():
                self.scenario.connection_duration_list[self.connection_duration] = 1
            else:
                self.scenario.connection_duration_list[self.connection_duration] +=1
            # print("CONNEC DURATION normal--> ", self.connection_duration)

    
            self.connection_duration = 0
            neighbour.connection_duration = 0
            self.ongoing_conn = False
            neighbour.ongoing_conn = False
            self.exchange_list = []
            neighbour.exchange_list = []
            self.db_exchange = False
            neighbour.db_exchange = False
            self.counter_list = []
            neighbour.counter_list = []
            self.exchange_counter = 0
            neighbour.exchange_counter = 0
            self.exchange_size = 0
            neighbour.exchange_size = 0
            self.scenario.used_mbs = 0
            self.hand_shake_counter = 0
            neighbour.hand_shake_counter = 0
            # If they don't have anything to exchange from the beginning they will not be set as busy for this slot.
            # They will remain busy just in case that during this slot they finished exchanging their DB.
            if neighbour.exchange_size == 0 and self.exchange_size == 0:
                self.busy = False
                neighbour.busy = False

   
    def computeTask(self,c):
        # print(self.id)
        if self.out:
            self.computing_counter = 0
            self.merging_counter = 0
            self.list_to_merge = []
           
        if not self.out:
            # no he empezado a ejecutar ninguna tarea pero tengo pendings
            if self.computing_counter == 0 and len(self.pending_model_list) > 0 and self.merging_counter == 0:
                if self.id == 127:
                    print(self.id,"entro aqui por primera vez porque tengo pendings", len(self.pending_model_list))

                # si tengo observations primero meto todos los pendings con el mismo id que una de las observations en list to merge 
                # selecciono la observation para el training
                if len(self.observations)>0:
                    if self.id == 127:
                        print("si tengo observations")
                    for obs in self.observations:
                        if self.id == 127:
                            print("observation model id", obs.model.id)
                        exists_belonging_model1 = False
                        exists_belonging_model2 = False
                        existing_obs1 = False
                        existing_obs2 = False

                        for mod in self.model_list:
                            if mod.id == obs.model.id:
                                exists_belonging_model1 = True
                                for o in mod.contributions.keys():
                                    if o.id == obs.id:
                                        existing_obs1 = True
                                
                       
                        for pend_model in self.pending_model_list:
                            if pend_model.id == obs.model.id:
                                exists_belonging_model2 = True
                                for o in pend_model.contributions.keys():
                                    if o.id == obs.id:
                                        existing_obs2 = True
                                        
                        
                        # if (exists_belonging_model1 == True or exists_belonging_model2 == True) and existing_obs1 == False and existing_obs2 == False:
                        if exists_belonging_model2 == True and existing_obs1 == False and existing_obs2 == False:

                            if self.id == 127:
                                print("cuantos pending models tengo para meter en list to merge:", len(self.pending_model_list))
                            for pend_model in self.pending_model_list:
                                if self.id == 127:
                                    print(pend_model.id)
                                if pend_model.id == obs.model.id:
                                    self.list_to_merge.append(pend_model)

                            self.observation_to_train = obs.copy()
                            if self.id == 127:
                                print("esta es mi observation to train ahora-->",self.observation_to_train.id)
                                print("y este es su modelo-->", self.observation_to_train.model.id)
                            self.merging_counter = self.merging_counter + 1
                            if self.id == 127:
                                print("merging counter 2:", self.merging_counter, len(self.list_to_merge))

                            break       

                # si no tengo observations para hacer un training o las observations que tengo no coinciden con ningun pending,
                # meto en list to merge lo que tenga en pending
                if len(self.list_to_merge)==0:
                    if self.id == 127:
                        print("o no tengo observations 1 o las que tengo no coinciden 2", len(self.observations),len(self.pending_model_list))

                if len(self.observations)==0 or len(self.list_to_merge)==0:
                    for pend_model in self.pending_model_list:
                        if pend_model.id == self.pending_model_list[0].id:
                            self.list_to_merge.append(pend_model)
                            
                    self.merging_counter = self.merging_counter + 1
                    if self.id == 127:
                        print("merging conunter con los pendings solos metidos en el merge", self.merging_counter, len(self.list_to_merge))



                # borro todos los pendings con el mismo id porque ya los he metido en merge
                if len(self.list_to_merge)>0:

                    first_id = self.pending_model_list[0].id
                    pending_model_list2 = []
                    for i in range(len(self.pending_model_list)):
                        if self.pending_model_list[i].id != first_id: 
                            pending_model_list2.append(self.pending_model_list[i])
                    

                    self.pending_model_list = []
                    self.pending_model_list = pending_model_list2[:]
                    
                    # segundo hago un merge de los pendings
                    np.random.shuffle(self.list_to_merge)
                    if self.id == 127:
                        print("EL MODELO MERGED---->", len(self.list_to_merge),self.list_to_merge[0].id)
                    for pm in self.list_to_merge:
                        if pm != self.list_to_merge[0]:
                            if self.id == 127:
                                print(pm.id,"estoy haciendo merge de mis pending", len(pm.contributions))
                                for contri in pm.contributions.keys():
                                    print(contri.id)
                            self.list_to_merge[0].contributions.update(pm.contributions)
                            if self.id == 127:
                                print("----->", len(self.list_to_merge[0].contributions))
                                for contri in self.list_to_merge[0].contributions.keys():
                                    print(contri.id)

                    # borro todos los merge menos el primero
                    # if self.id == 31:
                    #     print(self.id,"pendings:",len(self.pending_model_list),"models:", len(self.model_list), "merges",len(self.list_to_merge))
                    merged_model = self.list_to_merge[0].copy()
                    self.list_to_merge = []
                    self.list_to_merge.append(merged_model)
                    if self.id == 127:
                        print("que tengo en merged 1: ", len(self.list_to_merge))



            # Nothing to do, just checking
            if self.computing_counter == 0 and len(self.pending_model_list) == 0 and self.merging_counter == 0:
                if self.id == 127:
                    print(self.id,"si entro aqui es que no tengo nada que hacer")

        
            # Increase the merging counter
            if self.merging_counter > 0 and self.merging_counter < self.scenario.merging_time:
                self.merging_counter = self.merging_counter + 1
                if self.id == 127:
                    print("merging counter 3:",self.merging_counter, len(self.list_to_merge))

            # start training here
            if self.merging_counter == self.scenario.merging_time and self.computing_counter == 0: 
                self.merging_counter = 0
         
                if self.observation_to_train != None:
                    self.computing_counter = self.computing_counter + 1
                    if c not in self.scenario.whos_training.keys():
                        self.scenario.whos_training[c] = 0
                    self.scenario.whos_training[c] += 1
                    if self.id == 127:
                        print("es que SI tengo observation to train")

                if self.observation_to_train == None:
                    self.computing_counter = self.scenario.computing_time
                    if self.id == 127:
                        print("es que NO tengo observation to train")


            #  continue training here
            if self.computing_counter > 0 and self.computing_counter < self.scenario.computing_time:
                self.computing_counter += 1
                if c not in self.scenario.whos_training.keys():
                    self.scenario.whos_training[c] = 0
                self.scenario.whos_training[c] += 1
                if self.id == 127:
                    print(self.id,"training + 1")

                

            # when we are done training
            if self.computing_counter == self.scenario.computing_time:
                if self.id == 127:
                    print(self.id,"training done")

                self.computing_counter = 0
                if len(self.list_to_merge) > 0:
                    if self.id == 127:
                        print(self.id,"tengo merge")

                    if len(self.model_list)> 0:
                        if self.id == 127:
                            print(self.id,"tengo model")

                        for i in range(len(self.model_list)):
                            if self.model_list[i].id == self.list_to_merge[0].id:
                                self.list_to_merge[0].contributions.update(self.model_list[i].contributions)


                        if self.id == 127:
                            print("comprobando estas contributions 1:",self.list_to_merge[0].contributions)
                        

                        for m in self.model_list:
                            if m.id == self.list_to_merge[0].id:     
                                self.model_list.remove(m)

                    # add also new observation to merged model in case there is any
                    # print(self.id)

                    if self.observation_to_train != None:
                        self.list_to_merge[0].contributions[self.observation_to_train.copy()] = c
                        for o in self.observations:
                            if o.id == self.observation_to_train.id:
                                if self.id == 127:
                                    print("despues de entrenar la elimino--->", o)
                                self.observations.remove(o)

                        self.observation_to_train = None
                        if self.id == 127:
                            print("comprobando estas contributions 2:",self.list_to_merge[0].contributions)

                    if self.id == 127:
                        print("meto el merge en el model list con las observations:", len(self.list_to_merge[0].contributions))
                    self.model_list.append(self.list_to_merge[0].copy())
                    self.list_to_merge = []
                    
                    if self.id == 127:
                        print(self.id,"Adding model to the user: ", self.model_list[-1].id)


                
                    
            
                