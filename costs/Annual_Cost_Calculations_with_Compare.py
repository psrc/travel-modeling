
# coding: utf-8

# In[2]:

import pandas as pd
import numpy as np



# In[3]:

# 2014 
df = pd.read_csv(r'I:\T2040\soundcast_2014\outputs\daysim\_trip.tsv', sep='\t')
hh = pd.read_csv(r'I:\T2040\soundcast_2014\outputs\daysim\_household.tsv', sep='\t')
df_2040 =pd.read_csv(r'I:\T2040\soundcast_2040_constrained\outputs\daysim\_trip.tsv', sep='\t')
hh_2040 = pd.read_csv(r'I:\T2040\soundcast_2040_constrained\outputs\daysim\_household.tsv', sep='\t')
parcels = pd.read_csv(r'I:\T2040\soundcast_2014\inputs\accessibility\parcels_urbansim.txt', sep = ' ')
parcels_2040 = pd.read_csv(r'I:\T2040\soundcast_2040_constrained\inputs\accessibility\parcels_urbansim.txt', sep = ' ')
#zone_tract = pd.read_csv(r'R:\SoundCastDocuments\metrics\housing_transport_costs\tract_zone.csv')
#housing_cost_tract = pd.read_excel(r'R:\SoundCastDocuments\metrics\housing_transport_costs\MedianHousingCost_Tract.xlsx')
#tractids = pd.read_csv(r'R:\SoundCastDocuments\metrics\housing_transport_costs\tract2010_nowater.csv')
rgc_taz = pd.read_csv(r'I:\T2040\soundcast_2014\scripts\summarize\inputs\rgc_taz.csv')
equity_taz = pd.read_csv(r'I:\T2040\soundcast_2014\scripts\summarize\inputs\special_needs_taz.csv')
# In[ ]:

# AAA Calculations availavble for small, medium, large Sedans (and average of these), SUV, Minivan

# Analysis of survey could be used to allocate vehicle type distributions?

# http://publicaffairsresources.aaa.biz/wp-content/uploads/2016/03/2016-YDC-Brochure.pdf
# results are averages for sedans

# Annualalize costs as 262
annual_factor = 262

# Costs by miles
# Operating costs total (gas + maintenance + tires) using model estimates for this in the travcost field
depreciation_per_mile = 3759.0/15000    # depreciation by mile

# Annual costs
insurance = 1222    #(full-coverage insurance, license, registration, taxes, depreciation @ 15,000 miles per year), finance charge
taxes = 687    # license, registration, taxes
finance = 683    # load financing

annual_fixed_costs = insurance+taxes+finance


# In[ ]:

# to calculate activity durations for parking cost:
day_minutes = 1440
minutes_hr = 60.0
cents_dollar = 100


# In[ ]:

# get total travel cost (based on vmt) for household records
hh_mile_costs = df.groupby('hhno').sum()[['travcost']]
hh_mile_costs = hh_mile_costs.reset_index()

hh = pd.merge(hh, hh_mile_costs, on='hhno', how='left')

# Some households have 0 travel cost
hh['travcost'] = hh['travcost'].fillna(0)


# In[ ]:

# Total vehicle miles traveled per household to calculate mile-based costs
driver_trips = df[df['dorp'] == 1]


# In[ ]:

# Get total travel distance 
hh_travdist = df.groupby('hhno').sum()[['travdist']]
hh_travdist = hh_travdist.reset_index()

hh = pd.merge(hh, hh_travdist, on='hhno', how='left')


# In[ ]:

# annual operating costs
driver_trips['operating_cost_drivers'] = driver_trips['travcost']*annual_factor
driver_trips['travdist'] = driver_trips['travdist'].fillna(0)
driver_trips['depreciation'] = driver_trips['travdist']*depreciation_per_mile*annual_factor

#calculating parking costs based on activity duration
# the results look weird - add in parking cost later
driver_trips = pd.merge(driver_trips, parcels[['PARCELID','PPRICHRP']], left_on='dpcl', right_on = 'PARCELID')
# if a trip spans midnight you need to adjust across the day - like this:
driver_trips['duration'] = np.where(driver_trips['endacttm']<driver_trips['arrtm'], day_minutes-driver_trips['arrtm'] +driver_trips['endacttm'], driver_trips['endacttm']-driver_trips['arrtm'])/minutes_hr
driver_trips['parking_cost_per_hr'] = driver_trips['PPRICHRP']/cents_dollar
driver_trips['parking_cost'] = driver_trips['parking_cost_per_hr'] *driver_trips['duration']


driver_trips_hh = driver_trips.groupby('hhno').sum()[['operating_cost_drivers','depreciation','parking_cost']].reset_index()
hh = pd.merge(hh, driver_trips_hh, on = 'hhno')


# In[ ]:

# fixed costs as function of number of vehicles owned
hh['veh_insurance'] = hh['hhvehs']*insurance
hh['veh_taxes'] = hh['hhvehs']*taxes
hh['veh_finance'] = hh['hhvehs']*finance

hh['annual_auto_costs'] = hh['operating_cost_drivers']+hh['depreciation']+hh['veh_insurance']+hh['veh_taxes']+hh['veh_finance']
hh['annual_auto_costs']=hh['annual_auto_costs'].fillna(0)
# Need to add per mile depreciation costs


# In[ ]:

# Calculate transit cost
transit_trips = df[df['mode'] == 6]

hh_travdist_transit_cost = transit_trips.groupby('hhno').sum()[['travcost']]
hh_travdist_transit_cost['transit_cost'] = hh_travdist_transit_cost['travcost']
hh_travdist_transit_cost = hh_travdist_transit_cost.reset_index()
hh_travdist_transit_cost['annual_transit_cost'] = hh_travdist_transit_cost['transit_cost']*annual_factor


# In[ ]:

hh = pd.merge(hh, hh_travdist_transit_cost[['hhno','annual_transit_cost']], on='hhno', how='left')
hh['annual_transit_cost'] = hh['annual_transit_cost'].fillna(0)


# In[ ]:

hh['total_cost']= hh['annual_transit_cost']+hh['annual_auto_costs']
hh = hh.loc[hh['hhincome']!=0]
hh['percent_transport_cost'] = hh['total_cost']/hh['hhincome']
hh['percent_transport_cost'] =hh['percent_transport_cost'].fillna(0)


# In[15]:

print hh['total_cost'].mean()
print hh['veh_insurance'].mean()
print hh['veh_taxes'].mean()
print hh['operating_cost_drivers'].mean()
print hh['depreciation'].mean()
print hh['annual_transit_cost'].mean()
print hh['percent_transport_cost'].median()


# get total travel cost (based on vmt) for household records
hh_2040_mile_costs = df.groupby('hhno').sum()[['travcost']]
hh_2040_mile_costs = hh_2040_mile_costs.reset_index()

hh_2040 = pd.merge(hh_2040, hh_2040_mile_costs, on='hhno', how='left')

# Some households have 0 travel cost
hh_2040['travcost'] = hh_2040['travcost'].fillna(0)


# In[ ]:

# Total vehicle miles traveled per household to calculate mile-based costs
driver_trips = df_2040[df_2040['dorp'] == 1]


hh_2040_travdist = df_2040.groupby('hhno').sum()[['travdist']]
hh_2040_travdist = hh_2040_travdist.reset_index()

hh_2040 = pd.merge(hh_2040, hh_2040_travdist, on='hhno', how='left')


# In[ ]:

# annual operating costs
driver_trips['operating_cost_drivers'] = driver_trips['travcost']*annual_factor
driver_trips['travdist'] = driver_trips['travdist'].fillna(0)
driver_trips['depreciation'] = driver_trips['travdist']*depreciation_per_mile*annual_factor

#calculating parking costs based on activity duration
# the results look weird - add in parking cost later
driver_trips = pd.merge(driver_trips, parcels_2040[['PARCELID','PPRICHRP']], left_on='dpcl', right_on = 'PARCELID')
# if a trip spans midnight you need to adjust across the day - like this:
driver_trips['duration'] = np.where(driver_trips['endacttm']<driver_trips['arrtm'], day_minutes-driver_trips['arrtm'] +driver_trips['endacttm'], driver_trips['endacttm']-driver_trips['arrtm'])/minutes_hr
driver_trips['parking_cost_per_hr'] = driver_trips['PPRICHRP']/cents_dollar
driver_trips['parking_cost_daily'] = driver_trips['parking_cost_per_hr'] *driver_trips['duration']
driver_trips['parking_cost'] = driver_trips['parking_cost_daily']*annual_factor


driver_trips_hh_2040 = driver_trips.groupby('hhno').sum()[['operating_cost_drivers','depreciation','parking_cost']].reset_index()
hh_2040 = pd.merge(hh_2040, driver_trips_hh_2040, on = 'hhno')


# In[ ]:

# fixed costs as function of number of vehicles owned
hh_2040['veh_insurance'] = hh_2040['hhvehs']*insurance
hh_2040['veh_taxes'] = hh_2040['hhvehs']*taxes
hh_2040['veh_finance'] = hh_2040['hhvehs']*finance

hh_2040['annual_auto_costs'] = hh_2040['operating_cost_drivers']+hh_2040['depreciation']+hh_2040['veh_insurance']+hh_2040['veh_taxes']+hh_2040['veh_finance']
hh_2040['annual_auto_costs']=hh_2040['annual_auto_costs'].fillna(0)
# Need to add per mile depreciation costs


# In[ ]:

# Calculate transit cost
transit_trips = df_2040[df_2040['mode'] == 6]

hh_2040_travdist_transit_cost = transit_trips.groupby('hhno').sum()[['travcost']]
hh_2040_travdist_transit_cost['transit_cost'] = hh_2040_travdist_transit_cost['travcost']
hh_2040_travdist_transit_cost = hh_2040_travdist_transit_cost.reset_index()
hh_2040_travdist_transit_cost['annual_transit_cost'] = hh_2040_travdist_transit_cost['transit_cost']*annual_factor


# In[ ]:

hh_2040 = pd.merge(hh_2040, hh_2040_travdist_transit_cost[['hhno','annual_transit_cost']], on='hhno', how='left')
hh_2040['annual_transit_cost'] = hh_2040['annual_transit_cost'].fillna(0)


# In[ ]:

hh_2040['total_cost']= hh_2040['annual_transit_cost']+hh_2040['annual_auto_costs']
hh_2040 = hh_2040.loc[hh_2040['hhincome']!=0]
hh_2040['percent_transport_cost'] = hh_2040['total_cost']/hh_2040['hhincome']
hh_2040['percent_transport_cost'] =hh_2040['percent_transport_cost'].fillna(0)


# In[15]:

print hh_2040['total_cost'].mean()
print hh_2040['veh_insurance'].mean()
print hh_2040['veh_taxes'].mean()
print hh_2040['operating_cost_drivers'].mean()
print hh_2040['depreciation'].mean()
print hh_2040['annual_transit_cost'].mean()
print hh_2040['percent_transport_cost'].median()

### join the two scenarios and summarize by geographies
hh_rgc = pd.merge(hh, rgc_taz, left_on = 'hhtaz', right_on = 'taz', how = 'outer')
hh_equity = pd.merge(hh_rgc, equity_taz, left_on = 'hhtaz', right_on = 'TAZ', how = 'outer')


hh_equity_rgc = hh_equity.groupby('geog_name').mean()
hh_equity_rgc['year'] = '2014'
#hh_equity['In Center']=np.where(pd.notnull(hh_equity['geog_name']), 'In Center', 'Not In Center')
#hh_equity = hh_equity.groupby('In Center').mean()
#hh_equity['year'] = 'Today'

hh_2040_rgc = pd.merge(hh_2040, rgc_taz, left_on = 'hhtaz', right_on = 'taz', how = 'outer')
hh_2040_equity = pd.merge(hh_2040_rgc, equity_taz, left_on = 'hhtaz', right_on = 'TAZ', how = 'outer')


hh_equity_rgc_2040 = hh_2040_equity.groupby('geog_name').mean()
hh_equity_rgc_2040['year'] = '2040'

#hh_2040_equity['In Center']=np.where(pd.notnull(hh_2040_equity['geog_name']), 'In Center', 'Not In Center')
#hh_2040_equity=hh_2040_equity.groupby('In Center').mean()
#hh_2040_equity['year'] = '2040'

hh_equity_compare = hh_equity_rgc.append(hh_equity_rgc_2040)

hh_equity_compare.to_csv(r'R:\SoundCastDocuments\metrics\housing_transport_costs\transport_costs_compare_all_rgc.csv')


