###################################################################################
# Reads: PSRC_TAZlist.csv, External_Work_Trips.csv, External_NonWork_Trips.csv
# Writes: SOV, HOV2, HOV3 trip matrices for work and non-work trips
####################################################################################
import pandas as pd
#Read PSRC TAZ list
TAZlist = pd.read_csv('PSRC_TAZlist.csv')['TAZ']
#Read External work and non-work trips
work = pd.read_csv('External_Work_Trips.csv')
nonwork = pd.read_csv('External_NonWork_Trips.csv')
#Calculate HOV2 and HOV3 trips respectively as 2/3 and and 1/3 of HOV trips
work['HOV2_IE'] = (0.67)*work['HOV_IE']; nonwork['HOV2_IE'] = (0.67)*nonwork['HOV_IE']
work['HOV3_IE'] = (0.33)*work['HOV_IE']; nonwork['HOV3_IE'] = (0.33)*nonwork['HOV_IE']
work['HOV2_EI'] = (0.67)*work['HOV_EI']; nonwork['HOV2_EI'] = (0.67)*nonwork['HOV_EI']
work['HOV3_EI'] = (0.33)*work['HOV_EI']; nonwork['HOV3_EI'] = (0.33)*nonwork['HOV_EI']
#Keep only the needed columns
work    =    work [['PSRC_TAZ','External_Station','SOV_IE','SOV_EI','HOV2_IE','HOV2_EI','HOV3_IE','HOV3_EI']]
nonwork = nonwork [['PSRC_TAZ','External_Station','SOV_IE','SOV_EI','HOV2_IE','HOV2_EI','HOV3_IE','HOV3_EI']]
#Group trips by O-D TAZ's
w_grp = work.groupby(['PSRC_TAZ','External_Station']).sum()
nw_grp = work.groupby(['PSRC_TAZ','External_Station']).sum()
#Create empty matrices for SOV, HOV2 and HOV3 with rows and columns being set to PSRC TAZ's
w_SOV = pd.DataFrame(None, columns=TAZlist, index=TAZlist)
w_HOV2 = pd.DataFrame(None, columns=TAZlist, index=TAZlist)
w_HOV3 = pd.DataFrame(None, columns=TAZlist, index=TAZlist)
nw_SOV = pd.DataFrame(None, columns=TAZlist, index=TAZlist)
nw_HOV2 = pd.DataFrame(None, columns=TAZlist, index=TAZlist)
nw_HOV3 = pd.DataFrame(None, columns=TAZlist, index=TAZlist)

#Populate the matrices accordingly:
#work trips
for i in work['PSRC_TAZ'].value_counts().keys():
    for j in work.groupby('PSRC_TAZ').get_group(i)['External_Station'].value_counts().keys():
        #SOV
        w_SOV[i][j] = w_grp.loc[(i,j),'SOV_IE']
        w_SOV[j][i] = w_grp.loc[(i,j),'SOV_EI']
        #HOV2
        w_HOV2[i][j] = w_grp.loc[(i,j),'HOV2_IE']
        w_HOV2[j][i] = w_grp.loc[(i,j),'HOV2_EI']
        #HOV3
        w_HOV3[i][j] = w_grp.loc[(i,j),'HOV3_IE']
        w_HOV3[j][i] = w_grp.loc[(i,j),'HOV3_EI']
#non_work trips
for i in nonwork['PSRC_TAZ'].value_counts().keys():
    for j in nonwork.groupby('PSRC_TAZ').get_group(i)['External_Station'].value_counts().keys():
        #SOV
        nw_SOV[i][j] = nw_grp.loc[(i,j),'SOV_IE']
        nw_SOV[j][i] = nw_grp.loc[(i,j),'SOV_EI']
        #HOV2
        nw_HOV2[i][j] = nw_grp.loc[(i,j),'HOV2_IE']
        nw_HOV2[j][i] = nw_grp.loc[(i,j),'HOV2_EI']
        #HOV3
        nw_HOV3[i][j] = nw_grp.loc[(i,j),'HOV3_IE']
        nw_HOV3[j][i] = nw_grp.loc[(i,j),'HOV3_EI']

#Write the outputs
w_SOV.to_csv('w_SOV.csv'); w_HOV2.to_csv('w_HOV2.csv'); w_HOV3.to_csv('w_HOV3.csv')
nw_SOV.to_csv('nw_SOV.csv'); nw_HOV2.to_csv('nw_HOV2.csv'); nw_HOV3.to_csv('nw_HOV3.csv')