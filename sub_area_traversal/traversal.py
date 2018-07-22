import inro.emme.database.emmebank as _eb
import pandas as pd
import numpy as np
import os
from EmmeProject import *
import json 
import multiprocessing as mp
import subprocess
from multiprocessing import Pool


parallel_instances = 3
max_gate_id = 15
get_gate_mode_splits = False
use_warm_starts = True

gates_df = pd.read_csv(r'inputs\gates.csv')
tod_list = ['6to7', '7to8','8to9']

bank_list = [r'D:\stefan\Seattle_voc\code\banks\6to7', r'D:\stefan\Seattle_voc\code\banks\7to8', r'D:\stefan\Seattle_voc\code\banks\8to9'] 

project_list = ['projects/6to7/6to7.emp', 'projects/7to8/7to8.emp', 'projects/8to9/8to9.emp']

skim_dict = {"sov" : ["svtl1", "svtl2", "svtl3"], "hov2" : ["h2tl1", "h2tl2", "h2tl3"], "hov3" : ["h3tl1","h3tl2", "h3tl3"], "trucks" : ["hvtrk", "metrk", "lttrk"], "transit" : ['litrat', 'trnst']}

skim_list = [item for sublist in skim_dict.values() for item in sublist]


def start_pool(project_list):
    pool = Pool(processes=parallel_instances)
    pool.map(run_traversal_parallel,project_list[0:parallel_instances])
    pool.close()

def run_traversal_parallel(project_name):
    my_project = EmmeProject(project_name)

    # auto assignment/traversal:
    with open(r'inputs\traffic_assignment.ems') as f:
        spec = json.load(f)
    assign_traffic = my_project.m.tool("inro.emme.traffic_assignment.path_based_traffic_assignment")
    report = assign_traffic(spec, warm_start = use_warm_starts)

    print 'finished assignment'

    with open(r'inputs\auto_taversal.ems') as f:
        spec = json.load(f)
    NAMESPACE = "inro.emme.traffic_assignment.path_based_traffic_analysis"
    analyze_paths = my_project.m.tool(NAMESPACE)
    report = analyze_paths(spec)

    # bus transit assignment/traversal
    with open(r'inputs\bus_transit_assignment.ems') as f:
        spec = json.load(f)
    assign_transit = my_project.m.tool("inro.emme.transit_assignment.extended_transit_assignment")
    report = assign_transit(spec, save_strategies=True, class_name='Bus', add_volumes=False)

    print 'finished assignment'

    with open(r'inputs\transit_traversal_analysis.ems') as f:
        spec = json.load(f)
    NAMESPACE = "inro.emme.transit_assignment.extended.traversal_analysis"
    analyze_transit_paths = my_project.m.tool(NAMESPACE)
    report = analyze_transit_paths(spec, append_to_output_file=False, class_name='Bus', output_file= 'outputs/bus_traversal_' + my_project.tod, num_processors = 8)

    # rail transit assignment/traversal
    with open(r'inputs\rail_transit_assignment.ems') as f:
        spec = json.load(f)
    assign_transit = my_project.m.tool("inro.emme.transit_assignment.extended_transit_assignment")
    report = assign_transit(spec, save_strategies=True, class_name='Rail', add_volumes=True)

    print 'finished assignment'

    with open(r'inputs\transit_traversal_analysis.ems') as f:
        spec = json.load(f)
    NAMESPACE = "inro.emme.transit_assignment.extended.traversal_analysis"
    analyze_transit_paths = my_project.m.tool(NAMESPACE)
    report = analyze_transit_paths(spec, append_to_output_file=False, class_name='Rail', output_file= 'outputs/rail_traversal_' + my_project.tod, num_processors = 8)
    
    my_project.bank.dispose()

def update_network_attribute(bank_path, att_name):
    bank = _eb.Emmebank(os.path.join(bank_path, 'emmebank'))
    scenario = bank.scenario('1002')
    if att_name in scenario.attributes('LINK'):
        scenario.delete_extra_attribute(att_name)
    scenario.create_extra_attribute('LINK', att_name)
    network = scenario.get_network()
    for row in gates_df.iterrows():
        link = network.link(row[1].INODE, row[1].JNODE)
        link[att_name] = row[1].TAZ
    scenario._publish_network(network)
    bank.dispose()

def gate_volumes_by_class(bank):
    scenario = bank.scenario('1002')
    network = scenario.get_network()
    gate_dict = {}
  
    for link in network.links():
        if abs(link['@gate']) > 0 and abs(link['@gate']) < max_gate_id:
            if link['@gate'] not in gate_dict.keys():
                gate_dict[link['@gate']] = {}
            for key, value in skim_dict.iteritems():
                if not key == 'transit':
                    vol = 0
                    
                    for user_class in value:
                        vol = vol + link['@' + user_class]
                    if not key in gate_dict[link['@gate']].keys():
                        gate_dict[link['@gate']][key] = vol
                    else:
                        gate_dict[link['@gate']][key] = gate_dict[link['@gate']][key] + vol
            transit_vol = 0
            for seg in link.segments():
                transit_vol = seg.transit_volume + transit_vol
            if not 'transit' in gate_dict[link['@gate']].keys():
                gate_dict[link['@gate']]['transit'] = transit_vol
            else:
                gate_dict[link['@gate']]['transit'] = gate_dict[link['@gate']]['transit'] + transit_vol


    return gate_dict




def main():
    gates_df = pd.read_csv(r'inputs\gates.csv')
    districts_df = gates_df[gates_df['TAZ'] >0]
    districts_df = districts_df.groupby('TAZ').first()
    districts_df.reset_index(inplace = True)
    

    
    # update the gate attribute
    for path in bank_list:
        update_network_attribute(path, '@gate')

    # create matrices for traversal results
    for bank_path in bank_list:
        bank = _eb.Emmebank(os.path.join(bank_path, 'emmebank'))
        for matrix in bank.matrices():
            if matrix.name not in skim_list:
                bank.delete_matrix(matrix.id)
        for matrix_name in skim_list:
            matrix = bank.create_matrix(bank.available_matrix_identifier('FULL'))
            matrix.name = matrix_name + 'v'
        bank.dispose()

    # run assingments/traversal analysis
    for i in range (0, parallel_instances, parallel_instances):
            l = project_list[i:i+parallel_instances]
            start_pool(l)
 
    np_matrices = {}
    for key in skim_dict.keys():
        print key 
        np_matrices[key] = np.zeros((3700,3700), np.float16)

    for tod in tod_list:
        bank = _eb.Emmebank(os.path.join('banks', tod, 'emmebank'))

        if get_gate_mode_splits:
            gate_volumes = gate_volumes_by_class(bank)
            gate_vol_df = pd.DataFrame(gate_volumes).transpose()
            gate_vol_df['TAZ'] = abs(gate_vol_df.index)
            gate_vol_df['direction'] = np.where(gate_vol_df.index < 0, 'outbound', 'inbound')
            gate_vol_df = gate_vol_df.merge(districts_df, how = 'left', on = 'TAZ')
            gate_vol_df.to_csv(os.path.join('outputs', 'gate_vols_' + tod + '.csv')) 

        for key in np_matrices.keys():
            for skim_name in skim_dict[key]:
                #print skim_name
                np_matrix = bank.matrix(skim_name + 'v').get_numpy_data()[0:3700, 0:3700]
                if skim_name == 'hvtrk':
                    np_matrix = np_matrix / 2
                elif skim_name == 'metrk':
                    np_matrix = np_matrix / 1.5
                np_matrices[key] = np_matrices[key] + np_matrix
    
    df_list = []

    for key in np_matrices.keys():
        if key <> 'transit':
            df = pd.DataFrame(np_matrices[key])
            df['from'] = df.index 
            df = pd.melt(df, id_vars= 'from', value_vars=list(df.columns[0:3700]), var_name = 'to', value_name=key)
            df['from'] = df['from'] + 1
            df['to'] = df['to'] + 1
            df = df.loc[df['from'].isin(districts_df['TAZ']) & df['to'].isin(districts_df['TAZ'])]
            df_list.append(df)

    df_final = reduce(lambda left,right: pd.merge(left,right,on=['from', 'to']), df_list)

    # transit
    # TO DO: walk and bike here as well
    df_final['transit_vol'] = 0
    df_final['bike_vol'] = 0
    df_final['walk_vol'] = 0
     
    for tod in tod_list:
        rail_df = pd.read_csv(r'outputs\rail_traversal_' + tod, skiprows=17, delim_whitespace = True, header =  None)
        rail_df.columns = ['from', 'to', 'tvol']
        df_final = df_final.merge(rail_df, how='left', on = ['from', 'to'])
        df_final['tvol'] = df_final['tvol'].convert_objects(convert_numeric=True)
        df_final.tvol.fillna(0, inplace=True)
        df_final['transit_vol'] = df_final['transit_vol'] + df_final['tvol']
        df_final.drop('tvol', axis= 1, inplace=True)

        bus_df = pd.read_csv(r'outputs\bus_traversal_' + tod, skiprows=17, delim_whitespace = True, header =  None)
        bus_df.columns = ['from', 'to', 'tvol']
        df_final = df_final.merge(bus_df, how='left', on = ['from', 'to'])
        df_final['tvol'] = df_final['tvol'].convert_objects(convert_numeric=True)
        df_final.tvol.fillna(0, inplace=True)
        df_final['transit_vol'] = df_final['transit_vol'] + df_final['tvol'].astype(float)
        df_final.drop('tvol', axis= 1, inplace=True)

    districts_df = districts_df[['TAZ', 'district_2', 'district_2_name', 'aggregate_district_name2']]
    df_final = df_final.merge(districts_df, how= 'left', left_on = 'from', right_on = 'TAZ')
    df_final = df_final.rename(columns={'district_2_name' : 'from_district'})
    df_final.drop(['aggregate_district_name2', 'district_2'], axis = 1, inplace = True)
    df_final = df_final.merge(districts_df, how = 'left', left_on = 'to', right_on = 'TAZ')
    df_final = df_final.rename(columns={'aggregate_district_name2' : 'to_district'})
    df_final.drop(['district_2'], axis = 1, inplace = True)
    test = df_final.groupby(['from_district', 'to_district'])['hov2', 'sov', 'hov3', 'trucks', 'transit_vol', 'walk_vol', 'bike_vol'].sum()
    test.reset_index(inplace = True)
    test.to_csv('outputs/seattle_flows.csv')

    print 'done'



if __name__ == "__main__":

    main()



