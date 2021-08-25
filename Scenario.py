from Zoi import Zoi
from Observation import Observation
import numpy as np
from collections import OrderedDict
import re
import os
from datetime import datetime, timedelta
from User import User
import json

class Scenario:
    'Common base class for all scenarios'

    def __init__(self, radius_of_interest, radius_of_replication, max_area,min_speed,max_speed,delta,
    radius_of_tx,channel_rate,num_users,num_zois,traces_folder,num_slots,list_of_static_nodes,computing_time,merging_time,num_models,max_generation_time):
        # print ("Creating new scenario...")
        self.num_slots = num_slots
        self.square_radius_of_interest = radius_of_interest*radius_of_interest
        self.square_radius_of_replication = radius_of_replication*radius_of_replication
        self.radius_of_interest = radius_of_interest
        self.radius_of_replication = radius_of_replication
        self.max_area = max_area
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.delta = delta         # slot time
        self.radius_of_tx = radius_of_tx
        self.square_radius_of_tx = radius_of_tx*radius_of_tx
        self.usr_list = []
        self.channel_rate =  channel_rate
        self.mbs = self.delta*self.channel_rate
        self.used_mbs = 0
        self.num_users= num_users
        self.used_mbs_per_slot = []
        self.zois_list = []
        self.observations_counter = 0
        self.num_zois = num_zois
        self.observations_mean_rate = []
        self.merging_mean_rate = []
        self.tracesDic = OrderedDict()
        self.tracesDic2 = OrderedDict()
        self.attempts = 0
        self.whos_training= OrderedDict()
        self.whos_transmiting = OrderedDict()
        self.count_0_exchange_conn = 0
        self.count_non_useful = 0
        self.count_useful = 0
        self.connection_duration_list = OrderedDict()
        self.list_of_static_nodes = list_of_static_nodes
        self.exiting_nodes = [0]*self.num_slots
        self.computing_time = computing_time + 3
        self.merging_time = merging_time + 1
        self.max_memory = 0
        self.transmitting_1 = OrderedDict()
        self.transmitting_2 = OrderedDict()
        self.nodes_exiting_with_obs = OrderedDict()
        self.obs_tracking_case_1 = OrderedDict()
        self.obs_tracking_case_2 = OrderedDict()
        self.observations = []
        self.observations_to_track = []
        self.max_generation_time = max_generation_time

        self.obs_found_1 = OrderedDict()
        self.obs_found_2 = OrderedDict()
        self.num_models = num_models

        self.num_no_exchanges = 0
        self.total_num_exchanges = 0
        self.num_bidirectional = 0
        self.length_content_exchange = []
        self.exchanges_of_models = OrderedDict()
        self.exchanges_succesful_of_models = OrderedDict()
         # In case we are running simulations based on maps points
        if traces_folder == "Rome":
            self.city = "Rome"
        if traces_folder == "SanFrancisco":
            self.city = "SanFrancisco"
        if traces_folder == "Luxembourg":
            self.city = "Luxembourg"
        if traces_folder == "Paderborn":
            self.city="Paderborn"
        if traces_folder == "none":
            self.city = "none"
           
        if self.num_zois == 1:
            if self.city == "Luxembourg":
                zoi = Zoi(0, 7000,7000,self)
            if self.city != "Luxembourg":
                zoi = Zoi(0,0,0,self)
            self.zois_list.append(zoi)

        if self.num_zois > 1:
            for i in range(0,self.num_zois):
                zoi = Zoi(i, np.random.uniform(-self.max_area + self.radius_of_replication, self.max_area - self.radius_of_replication),
                np.random.uniform(-self.max_area + self.radius_of_replication, self.max_area - self.radius_of_replication),self)
                self.zois_list.append(zoi)

        # self.displayScenario()

    def displayScenario(self):
        print("Radius of interest : ", self.radius_of_interest,  ", Radius of replication: ", self.radius_of_replication, 
              ", Max area: ", self.max_area, ", Min speed: ", self.min_speed, 
              ", Max speed: ", self.max_speed, ", Max pause: ", self.max_pause, ", Min pause: ", self.max_pause, ", Delta: ", self.delta, 
              ", Radious of tx: ", self.radius_of_tx, ", Mbs: ", self.mbs, ", Used Mbs: ", self.used_mbs, 
              ", Channel rate: ", self.channel_rate, ", ZOIS: ", self.num_zois)


     # Traces parser for each scenario, we parse the traces after the scenario creation, depending on which folder (map) and file (specific traces for a given seed in that map)
    def parsePaderbornTraces(self, folder, file):
        f=open('traces/' + folder + '/'+ file +'_MovementNs2Report.txt',"r")
        lines=f.readlines()
        count = 0
        for line in lines:
            lp = line.split()
            if "at" not in line: 
                node = line[line.find("(")+1:line.find(")")]
                if "X_" in line:
                    x = float(lp[3])
                if "Y_" in line:
                    y = float(lp[3])
                time = float(0)
                speed = float(0)
                count += 1
            else:
                count = 2
                node = int(line[line.find("(")+1:line.find(")")])
                time = float(lp[2])
                x = float(lp[5])
                y = float(lp[6])
                speed = float(lp[7][:-1])

            # We add the line info to each node dictionary
            if count == 2:
                count = 0
                if node not in self.tracesDic:
                    self.tracesDic[node] = OrderedDict()
                    
                # Stop storing positions if we already have 10000 slots     
                # if len(self.tracesDic[node]) <= 10000:
                self.tracesDic[node][time] = [x,y,speed]
            # print("node ", node , "time", time , "x", x, "y",y, "speed", speed)


           
    # Traces parser for each scenario, we parse the traces after the scenario creation, depending on which folder (map) and file (specific traces for a given seed in that map)
    def parseRomaTraces(self, folder, file):
        replacementDicc= OrderedDict()
        f=open('traces/' + folder + '/'+ file +'_Rome.txt',"r")
        lines=f.readlines()
        for line in lines:
            lp = line.split(';')
            node = lp[0]
            time = lp[1].split('-')
            time = time[2].split(':')
            daysHours = time[0].split(' ')
            days = ((int(daysHours[0])-1)*24)*3600
            hours = int(daysHours[1])*3600
            minutes = int(time[1])*60
            if "." in time[2]:
                seconds = int(time[2].split('.')[0])
            else:
                seconds = int(time[2].split('+')[0])

            totalSeconds = days+hours+minutes+seconds
            time = int(totalSeconds)
            coordinates = re.findall("\d+\.\d+", lp[2])
            x = float(coordinates[0])
            y = float(coordinates[1])

            # We add the line info to each node dictionary
            if node not in replacementDicc:
                replacementDicc[node] = OrderedDict()
        
            replacementDicc[node][time] = [x,y]
            # print("node ", node , "time", time , "x", x, "y",y)

        nodes_counter=0
        for key,value in replacementDicc.items():
            self.tracesDic[nodes_counter] = OrderedDict()
            self.tracesDic[nodes_counter] = value
            nodes_counter +=1 

        print("Cuantos nodos hay---> ", nodes_counter)
        self.num_users = nodes_counter

    def parseSanFranciscoTraces(self, folder):
        counter_users = 0
        folder = 'traces/' + folder
        for filename in os.listdir(folder):
            f=open(folder + '/'+ filename,"r")
            lines=f.readlines()
            for line in lines:
                node = counter_users
                lp = line.split(' ')
                x = float(lp[0])
                y = float(lp[1])
                time = int(lp[3])

                given_date_format = datetime.fromtimestamp(time).strftime('%d-%m-%Y %H:%M:%S')
                given_date = datetime.strptime(given_date_format, '%d-%m-%Y %H:%M:%S')

                fix_starting_date_format = datetime.fromtimestamp(1210975200).strftime('%d-%m-%Y %H:%M:%S')
                fix_starting_date = datetime.strptime(fix_starting_date_format, '%d-%m-%Y %H:%M:%S')

                time = given_date-fix_starting_date
                time = time.total_seconds()

                 # We add the line info to each node dictionary
                if node not in self.tracesDic:
                    self.tracesDic[node] = OrderedDict()

                self.tracesDic[node][time] = [x,y]


            counter_users += 1
            # if counter_users == self.num_users:
            #     break
        self.num_users = counter_users


    def parseLuxembourgTraces2(self, folder,file):
        replacementDicc= OrderedDict()
        f=open('traces/' + folder + '/1_Luxembourg.txt',"r")
        lines=f.readlines()
        for line in lines:
            lp = line.split(' ')
            node= int(lp[0])
            time = float(lp[2])
            time = int(time)
            x = float(lp[4])
            y=float(lp[5])

            if node not in replacementDicc:
                replacementDicc[node] = OrderedDict()
            replacementDicc[node][time] = [x,y]

        nodes_counter=0
        for key,value in replacementDicc.items():
            self.tracesDic2[nodes_counter] = OrderedDict()
            self.tracesDic2[nodes_counter] = value
            nodes_counter +=1 
        
        print("Cuantos nodos hay---> ", nodes_counter)
        self.num_users = nodes_counter

    def parseLuxembourgTraces(self, folder,file):
        with open('traces/' + folder + '/tracesLux-'+file+'.json', 'r') as fp:
                data = json.load(fp, object_pairs_hook=OrderedDict)
            
        for k,v in data.items():
            self.tracesDic[int(k)] = OrderedDict()
            for key,value in v.items():
                self.tracesDic[int(k)][int(key)]=[]
                for coord in value:
                    self.tracesDic[int(k)][int(key)].append(float(coord))
       
        print("Cuantos nodos hay---> ", len(self.tracesDic))
        self.num_users = len(self.tracesDic)
        print("son iguales???", self.tracesDic == self.tracesDic2)


    def addRemoveNodes(self,c):
        # print("entrando en add remove",c)
        for k,v in self.tracesDic.items():
            if self.tracesDic[k].keys()[0] == c:
                x = self.tracesDic[k].items()[0][1][0]
                y = self.tracesDic[k].items()[0][1][1] 
                # print("El nodo", k, " entra en", c)
                user = User(k,x,y, self,self.max_memory)
                self.usr_list.append(user)
                user.predict(self.num_slots)


            if self.tracesDic[k].keys()[-1] == c:
                # print("El nodo", k, " sale en", c)
                for u in self.usr_list:
                    if k == u.id:
                        self.usr_list.remove(u)     


    def getObservationsFromScenario(self,c,amount,multiseeding,model):
        generated = 0
        while generated < amount:
            if len(self.observations)>0:
                observation_generated = Observation(self.observations[-1].id+1, c, self.zois_list[0],model)

            else:
                observation_generated = Observation(1, c, self.zois_list[0],model)
                
            self.observations.append(observation_generated)
            self.observations_mean_rate.append(c)
            
            if c>200:
                self.observations_to_track.append(observation_generated)

            generated = generated + 1

            if multiseeding:
                seeds_amount = np.random.randint(2)
                for i in range(seeds_amount):
                    u = np.random.randint(self.num_users)
                    for user in self.usr_list:
                        if user.id == u and user.myFuture[c] != -1:
                            # if the node does not have the model, we give it the model to start training
                            if (observation_generated.model not in user.model_list) and (observation_generated.model not in user.pending_model_list):
                                user.pending_model_list.append(model.copy())

                            user.observations.append(observation_generated)
                            # print("user con observation:", user.id)


                            break

            if not multiseeding:
                valid = False
                while not valid:
                    u = np.random.randint(self.num_users)
                    for user in self.usr_list:
                        yalotiene = False
                        if user.id == u and user.myFuture[c] != -1:
                            for upendmod in user.pending_model_list:
                                if upendmod.id == observation_generated.model.id:
                                    yalotiene = True
                            
                            # print("Nueva observation para:", user.id, "observation id:", observation_generated.id, "para modelo:",observation_generated.model.id)
                            user.observations.append(observation_generated.copy())
                            if not yalotiene:
                                user.pending_model_list.append(model.copy())
                                valid = True   




