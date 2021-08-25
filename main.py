from __future__ import division
from User import User
from Dump import Dump
from Model import Model
from Scenario import Scenario
import numpy as np
import json
from collections import OrderedDict
import sys, os
import uuid
import progressbar
from time import sleep
import time
import uuid
import os
import base64
import hashlib
from  shutil import copyfile
from collections import Counter

file_name = str(sys.argv[1])
traces_file = str(sys.argv[2])
print('input-'+ file_name + '.json')
print('traces file number: ' + traces_file)

t0 = time.time()
uid = base64.urlsafe_b64encode(hashlib.md5(os.urandom(128)).digest())[:8]

with open('input-'+ file_name + '.json') as f:
    data = json.load(f)

density_users = data["num_users"]
num_users_distribution = data["num_users_distribution"]
num_static_nodes = data["num_static_nodes"]
radius_of_tx = data["radius_of_tx"]                     # area to look for neigbors (dependent on contact range)
max_area = data["max_area_squared"]                     # outer zone - max area size
radius_of_interest = data["radius_of_interest"]         # inner zone - interest
radius_of_replication = data["radius_of_replication"]   # second zone - replication
density_zois = data["num_zois"]
min_speed = data["min_speed"]
max_speed = data["max_speed"]
delta = data["delta"]                                   # time per slot
channel_rate = data["channel_rate"]
max_model_size = data["max_model_size"]
min_model_size = data["min_model_size"]
model_size = np.random.uniform(max_model_size, min_model_size)
num_models_node = data["num_models_node"]
num_models = data["num_models"]
traces_folder = data["traces_folder"]
max_generation_time = data["max_generation_time"]
num_slots = data["num_slots"] 
computing_time= data["computing_time"] 
merging_time = data["merging_time"]
multiseeding = data["multiseeding"]
if multiseeding == "True":
    multiseeding= True
else:
    multiseeding = False
seed_list = [15482669,15482681,15482683,15482711,15482729,15482941,15482947,15482977,15482993,15483023,15483029,15483067,15483077,15483079,15483089,15483101,15483103,15482743,15482771,15482773,15482783,15482807,15482809,15482827,15482851,15482861,15482893,15482911,15482917,15482923]
uid =  str(file_name) + "-"+ str(uid) 
os.mkdir(uid)
print(uid)
copyfile('input-'+ file_name + '.json', str(uid)+'/input-'+ file_name + '.json') # Copy the corresponding input file into the folder

################## Loop per simulation
# seed = int(seed)
np.random.seed(seed_list[6])
print("Model size ", model_size)
print("Num models in a node ", num_models_node)     
print("Traces Folder ", traces_folder)


# This creates N objects of User class
if num_users_distribution == "poisson":
    num_users = np.random.poisson(density_users)
else:
    num_users=density_users

# Select the nodes id that are going to be static nodes
# list_of_static_nodes = np.random.choice(range(num_users), num_static_nodes, replace=False)
list_of_static_nodes = []
contacts_per_slot_per_user_dynamic= OrderedDict()
contacts_per_slot_per_user_static= OrderedDict()
num_zois=density_zois
usr_list = []        # list of users in the entire scenario
availabilities_list_per_slot = []
nodes_in_zoi = OrderedDict()
attempts = []
a_per_model = OrderedDict()
a_per_obs = OrderedDict()
absolute_number_obs = OrderedDict()
absolute_number_count = OrderedDict()
models_contributions = OrderedDict()
models_freshness = OrderedDict()
nodes_num_observations = OrderedDict()
nodes_num_observations_per_model = OrderedDict()

nodes_future = OrderedDict()
obs_number_slot = OrderedDict()
nodes_without_obs = OrderedDict()

c = 1

# CREATION OF SCENARIO
scenario = Scenario(radius_of_interest, radius_of_replication,max_area,min_speed,max_speed,delta,
radius_of_tx,channel_rate,num_users,num_zois,traces_folder,num_slots,list_of_static_nodes,computing_time,merging_time,num_models,max_generation_time)
scenario.max_memory = num_models*model_size

################## Parse traces in case we are using them
if traces_folder == "Rome":
    scenario.parseRomaTraces(traces_folder,traces_file)
if traces_folder == "Luxembourg":
    scenario.parseLuxembourgTraces(traces_folder,traces_file)
if traces_folder == "none":
    for i in range(0,scenario.num_users):
        user = User(i,np.random.uniform(-max_area, max_area),np.random.uniform(-max_area, max_area), scenario,num_models_node*model_size)
        scenario.usr_list.append(user)
        user.calculateZones(c)

# Creating models in each zoi
for z in scenario.zois_list: 
    for m in range(0,num_models):
        model = Model(uuid.uuid4(),model_size,z,scenario)
        z.model_list.append(model)
        print("Creo un model",len(z.model_list))

# Start users counter in every zoi to 0
for z in scenario.zois_list:
    nodes_in_zoi[z.id] = OrderedDict()
    nodes_in_zoi[z.id][0] = 0

# Adding the nodes to the scenario when reading traces
if traces_folder != "none":
    scenario.addRemoveNodes(1)
    
# Computing availability per ZOI and per model
for z in scenario.zois_list:
    if nodes_in_zoi[z.id][0] == 0:
        for m in z.model_list:
            a_per_model[str(m.id)] = OrderedDict()
            a_per_model[str(m.id)][z.id] = []
            a_per_model[str(m.id)][z.id].append(0)
    else:
        for m in z.model_list:
            a_per_model[str(m.id)] = OrderedDict()
            a_per_model[str(m.id)][z.id] = []
            a_per_model[str(m.id)][z.id].append(m.counter/nodes_in_zoi[z.id][0])

        
print(list_of_static_nodes)
print("number of models: ", num_models)
print("Number of zois ", num_zois)


orig_stdout = sys.stdout
# f = open(os.devnull, 'w')
f = open(str(uid)+'/out.txt', 'w')
sys.stdout = f 

# progress bar
bar = progressbar.ProgressBar(maxval=num_slots, \
widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
bar.start()

################## Loop per slot into a simulation
while c < num_slots:
    bar.update(c)
    print("SLOT NUMBER: ", c)
    # clear data structures
    for z in scenario.zois_list:
         # Restart the counter for nodes in each zoi
        nodes_in_zoi[z.id][c] = 0
        # Restart the counter for model availability
        for m in z.model_list:
            m.counter  = 0

   
    # shuffle users lists
    np.random.shuffle(scenario.usr_list)

    # add models only at  this slot to all users in the zoi
    # if c == 1:
    #     # add the model  to each user according to the ZOIs that they belong to
    #     for user in scenario.usr_list:
    #         if user.myFuture[c] != -1:
    #             nodes_in_zoi[user.myFuture[c]][c] = +1
    #             np.random.shuffle(z.model_list)
    #             for model in z.model_list:
    #                 user.pending_model_list.append(m.copy())
    #                 if user.id == 63:
    #                     print("se lo doy por primera vez", len(user.pending_model_list))
                                 

    # Run mobility for every slot           
    # Nobody should be BUSY at the beggining of a slot (busy means that the node has had a connection already in the current slot, so it cannot have another one)
    # Move every pedestrians once
    for j in scenario.usr_list:
        j.busy = False
        if traces_folder == "none":
            # if j.id not in list_of_static_nodes:
            # j.randomWaypoint(c)
            j.randomDirection(c)
            
        if traces_folder != "none":
            j.readTraces(c)

        j.calculateZones(c)


    # print("number of current alive observations",len(scenario.observations))
    # print("number of total observations to track", len(scenario.observations_to_track))

    for mo in scenario.zois_list[0].model_list:
        # print("modelo------>",mo.id)
        counter = 0
        for observ in scenario.observations:
            if mo.id == observ.model.id:
                counter = counter + 1
            
        # print("observations counter--->", counter)

    # if np.random.uniform() < 0.09:
    for z in scenario.zois_list:
        for m in z.model_list:
            number_observations = np.random.poisson(0.025)
            scenario.getObservationsFromScenario(c,number_observations,multiseeding,m)
            if c in obs_number_slot:
                obs_number_slot[c] = obs_number_slot[c] + number_observations
            else:
                obs_number_slot[c] = number_observations
            

    # Run contacts for every slot after mobility.
    for k in scenario.usr_list:
        # run users 
        k.contacts_per_slot_dynamic[c] = []
        k.contacts_per_slot_static[c] = []
        k.userContact(c)

    for k in scenario.usr_list: 
        k.computeTask(c)

    
    attempts.append(scenario.attempts)
    if traces_folder != "none":
        scenario.addRemoveNodes(c)
    
    # After moving the node and exchanging models, check to which zone it belongs to increase the right counter
    
    for j in scenario.usr_list:
        # if j.myFuture[c] != -1 and len(j.model_list)>0:
        if j.myFuture[c] != -1:
            nodes_in_zoi[j.myFuture[c]][c] += 1
        # Increment the model counter after moving and exchanging
        if len(j.model_list) > 0:
            for z in scenario.zois_list:
                for m in z.model_list:
                    for model in j.model_list:
                        if model.id == m.id:
                            m.counter+= 1

       

    # ################################## Dump data per slot in a file ############################################

    # Compute freshness per user
    for user in scenario.usr_list:
        # print(user.id,"cuantos modelos tengo--->",len(user.model_list))
        if user.myFuture[c] != -1:
            # print("SOY USER-------------------->", user.id)
            have_obs = False
            if len(user.model_list)>0:
                for model in user.model_list:
                    # print("cuantas observations tiene este modelo",len(model.contributions))
                    if len(model.contributions) > 0:
                        have_obs = True
                        if c not in user.freshness.keys():
                            user.freshness[c]=OrderedDict()
                        if str(model.id) not in user.freshness[c].keys():
                            user.freshness[c][str(model.id)] = 0

                        min_fresh = np.Inf

                        for o,p in model.contributions.items():
                            if (c-o.generation_time) < min_fresh:
                                min_fresh = c-o.generation_time


                        if c not in nodes_num_observations.keys():
                            nodes_num_observations[c]=OrderedDict()
                            # nodes_num_observations_per_model[c]= OrderedDict()
                        if user.id not in nodes_num_observations[c].keys():
                            nodes_num_observations[c][user.id] = 0
                            # nodes_num_observations_per_model[c][user.id] = OrderedDict()
                        
                        
                        
                        user.freshness[c][str(model.id)] = min_fresh
                        nodes_num_observations[c][user.id] = nodes_num_observations[c][user.id] + len(model.contributions)
                        # nodes_num_observations_per_model[c][user.id][str(model.id)] = len(model.contributions)
                        

            if have_obs == False:
                if c not in nodes_without_obs.keys():
                    nodes_without_obs[c] = 0
                nodes_without_obs[c] = nodes_without_obs[c] + 1


    for user in scenario.usr_list:
        models_freshness[user.id] = user.freshness

        

    # # we add the current slot availability to the list
    for z in scenario.zois_list:
        if nodes_in_zoi[z.id][c] == 0:
            for m in z.model_list:
                if str(m.id) not in a_per_model:
                    a_per_model[str(m.id)] = OrderedDict()
                if z.id not in a_per_model[str(m.id)]:
                    a_per_model[str(m.id)][z.id] = []
                a_per_model[str(m.id)][z.id].append(0)

        else:
            for m in z.model_list:
                if str(m.id) not in a_per_model:
                    a_per_model[str(m.id)] = OrderedDict()
                if z.id not in a_per_model[str(m.id)]:
                    a_per_model[str(m.id)][z.id] = []
                    # fill the availability list with 0 to match the slot in which the model was created
                    a_per_model[str(m.id)][z.id][:c] = [0] * c
                a_per_model[str(m.id)][z.id].append(m.counter/(nodes_in_zoi[z.id][c]))


    ## remove old observations

   
    for user in scenario.usr_list:
        for model in user.model_list:
            # if user.id == 63:
            #     print(model.id,"contributions antes--->",len(model.contributions.items()))
            #     for k,v in model.contributions.items():
            #         print(k.id,"-->",c-k.generation_time)

            for k,v in model.contributions.items():
                if (c- k.generation_time) >= scenario.max_generation_time:
                    del model.contributions[k]


        model_temp = []
        for model in user.model_list:
            if len(model.contributions) != 0:
                model_temp.append(model)

        user.model_list = []
        user.model_list = model_temp[:]

        # if user.id == 63:
        #     print("contributions despues--->",len(model.contributions.items()))

        
        for pen_model in user.pending_model_list:
            for k, v in pen_model.contributions.items():
                if (c- k.generation_time) >= scenario.max_generation_time:
                    del pen_model.contributions[k]



        # pend_model_temp = []
        # for pen_model in user.pending_model_list:
        #     if len(pen_model.contributions) != 0:
        #         pend_model_temp.append(pen_model)

        # user.pending_model_list = []
        # user.pending_model_list = pend_model_temp[:]
        

        temp_node_observations = []
        for obs_in_node in user.observations:
            if (c- obs_in_node.generation_time) < scenario.max_generation_time:
                temp_node_observations.append(obs_in_node)
        
        user.observations = []
        user.observations = temp_node_observations[:]


    temp_observations = []
    for obs in scenario.observations:
        if (c - obs.generation_time) < scenario.max_generation_time:
            temp_observations.append(obs)

    scenario.observations = []
    scenario.observations = temp_observations[:]



    ################################## Dump data per slot in a file ###########################################

    # we add the current slot observation availability to the list

    # print("time to check",c)
    for observation in scenario.observations_to_track:
        if observation in scenario.observations:
            suma = 0
            count = 0
            if observation.id not in a_per_obs.keys():
                a_per_obs[observation.id] = []
                absolute_number_obs[observation.id] = []
                absolute_number_count[observation.id] = []
            for usu in scenario.usr_list:
                if usu.myFuture[c] != -1:
                    for model in usu.model_list:
                        if model.id == observation.model.id:
                            count = count + 1
                            for key,value in model.contributions.items():
                                if key.id == observation.id:
                                    suma = suma + 1
                                   

            
            if count > 0:
                a_per_obs[observation.id].append(suma/count)
                absolute_number_obs[observation.id].append(suma)
                absolute_number_count[observation.id].append(count)
            if count == 0:
                a_per_obs[observation.id].append(0)
                absolute_number_obs[observation.id].append(suma)
                absolute_number_count[observation.id].append(count)

    c += 1


# At the end of every simulation we need to close connections and add it to the list of connection durations
for k in scenario.usr_list:
    if k.ongoing_conn == True:
        if k.connection_duration not in scenario.connection_duration_list.keys():
            scenario.connection_duration_list[k.connection_duration] = 1
        else:
            scenario.connection_duration_list[k.connection_duration] +=1

        k.ongoing_conn = False
        k.prev_peer.ongoing_conn = False
        # print("CONNEC DURATION out--> ", k.connection_duration)

   
i = 0   
for u in scenario.usr_list:
    contacts_per_slot_per_user_dynamic[u.id] = u.contacts_per_slot_dynamic
    contacts_per_slot_per_user_static[u.id] = u.contacts_per_slot_static
    # models_freshness[u.id] = u.freshness
    nodes_future[u.id] = u.myFuture
    if len(u.model_list) > 0:
        new_model = OrderedDict()
        for m in range(len(u.model_list)):
            for key,value in u.model_list[m].contributions.items():
                new_model[key.id] = value
                
            models_contributions[i] = new_model
            i += 1




###################### Functions to dump data per simulation #########################
dump = Dump(scenario,uid)
dump.userLastPosition(list_of_static_nodes)
dump.connectionDurationAndMore(contacts_per_slot_per_user_dynamic,contacts_per_slot_per_user_static,scenario.exiting_nodes)
# dump.availabilityPerSimulation(np.average(availabilities_list_per_slot))
# dump.listOfAveragesPerSlot(availabilities_list_per_slot)
dump.con0exchange()
dump.availabilityPerModel(a_per_model)
dump.availabilityPerObservation(a_per_obs)
dump.absolutePerObservation(absolute_number_obs)
dump.absolutePerObservationCount(absolute_number_count)
dump.nodesZoiPerSlot(nodes_in_zoi)
# dump.nodesPath()
dump.modelContributions(models_contributions)
dump.modelFreshness(models_freshness)
# dump.nodesFuture(nodes_future)
# dump.mergingMeanRate(scenario.merging_mean_rate)
dump.observationsMeanRate(scenario.observations_mean_rate)
dump.whosTraining(scenario.whos_training,scenario.whos_transmiting)
# dump.transmissionsOneway()
# dump.transmissionsDoubleway()
dump.nodesExitingWithObs()
dump.obsTracked()
dump.obsNumberSlot(obs_number_slot)
dump.nodesWithoutObs(nodes_without_obs)
dump.nodesNumObservations(nodes_num_observations)
dump.nodesNumObservationsPerModel(nodes_num_observations_per_model)
dump.exchangeLength()
dump.numBidirectionalExchanges()
dump.numTotalExchanges()
dump.exchangesOfModels()

########################## End of printing in simulation ##############################
sys.stdout = orig_stdout
f.close()
bar.finish()
t1 = time.time()
print ("Total time running: %s minutes \n" % str((t1-t0)/60))
print("Total Number of observations: ", len(scenario.observations))
print("Number of tracked observations: ", len(scenario.observations_to_track))