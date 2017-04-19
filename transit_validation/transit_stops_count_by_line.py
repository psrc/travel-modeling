'''
This script is to count transit stops by line. 
transit running time from 5am to 20pm. 
This script is used for transit validation task, could be applied on whichever year's outputs. 
'''

import sys
import os 
import inro.emme.matrix as ematrix
import inro.emme.database.matrix
import inro.emme.database.emmebank as _eb
import numpy as np
import pandas as pd
from collections import defaultdict

banks = 'D:/Angela/soundcast_2040/soundcast/Banks/'
output = 'R:/Angela/soundcast_transit_validation/transit_stop/transit_stop_counts_2040.txt'
fi_name = ['5to6', '6to7', '7to8', '8to9', '9to10', '10to14', '14to15', '15to16', '16to17', '17to18', '18to20']

net_dict_s = defaultdict(dict)

for name in fi_name:
    with _eb.Emmebank(banks + name + '/emmebank') as emmebank:
            current_scenario = emmebank.scenario(1002)
            network = current_scenario.get_network()
    print name
    # create a net dictionary- outer key: transit line, inner keys: count, i_node
    for segment in network.transit_segments(): 
        if segment.line not in net_dict_s:
            net_dict_s[segment.line.id]['count'] = 0 
            net_dict_s[segment.line.id]['i_node'] = []
    # count stop, record i_node
    for segment in network.transit_segments():
        # first stops
        if segment.number == 0: 
            if segment.i_node not in net_dict_s[segment.line.id]['i_node']:
                #print 'got a first stop'
                net_dict_s[segment.line.id]['count'] += 1
                net_dict_s[segment.line.id]['i_node'].append(segment.i_node.id)
        # last stops
        if segment.j_node is None:
            if segment.i_node not in net_dict_s[segment.line.id]['i_node']:
                #print 'got a last stop'
                net_dict_s[segment.line.id]['count'] += 1
                net_dict_s[segment.line.id]['i_node'].append(segment.i_node.id)
        # stops in the middle: 'allow_boarding == True'
        else:
            if segment.allow_boardings == True:
                if segment.i_node not in net_dict_s[segment.line.id]['i_node']:
                    #print 'got a middle stop'
                    net_dict_s[segment.line.id]['count'] += 1
                    net_dict_s[segment.line.id]['i_node'].append(segment.i_node.id)

    print len(net_dict_s.keys())

stop_count_df = pd.DataFrame.from_dict(net_dict_s, orient='index', dtype=None).reset_index()
stop_count_df.columns = ['line', 'count', 'i_node']
stop_count_df.to_csv(output)