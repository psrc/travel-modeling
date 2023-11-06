########################################
# General Configuration Settings
########################################

# Project Output Directory
output_dir = r'R:\e2projects_two\2018_base_year\survey\daysim_format\revised'

######################################
# Locate Parcels Config
######################################
# Load Survey Data from Elmer or use CSV
use_elmer = False
survey_year = '(2017, 2019)'

# If not using Elmer, specify CSV location
survey_input_dir = r'R:\e2projects_two\2023_base_year\2017_2019_survey\elmer'

# Spatial join trip lat/lng values to shapefile of parcels
lat_lng_crs = 'epsg:4326'

# Set parcel file location
parcel_file_dir = r'R:\e2projects_two\SoundCast\Inputs\dev\landuse\2018\rtp_2018\parcels_urbansim.txt'

######################################
# Daysim Conversion Config
######################################

# Geolocated directory
input_dir = r'R:\e2projects_two\2023_base_year\2017_2019_survey'

debug_tours = False
write_debug_files = True

# Flexible column names, given that these may change in future surveys
hhno = 'household_id'
hownrent = 'rent_own'
hrestype = 'res_type'
hhincome = 'hhincome_detailed'
hhtaz = 'final_home_taz'
hhparcel = 'final_home_parcel'
hhexpfac = 'hh_wt_revised'
hhwkrs = 'numworkers'
hhvehs = 'vehicle_count'
pno = 'pernum'

# Heirarchy order for tour mode, per DaySim docs: https://www.psrc.org/sites/default/files/2015psrc-modechoiceautomodels.pdf
# Drive to Transit > Walk to Transit > School Bus > HOV3+ > HOV2 > SOV > Bike > Walk > Other
drive_transit_i = 0
walk_transit_i = 0
mode_heirarchy = [6,8,9,5,4,3,2,1,10]

# Weights
person_weight_col = 'hh_weight_2017_2019'
hh_weight_col = 'hh_weight_2017_2019'
trip_weight_col = 'trip_weight_2017_2019'

# Employment
employment_full_time = "Employed full time (35+ hours/week, paid)"
employment_part_time = "Employed part time (fewer than 35 hours/week, paid)"
employment_retired = 'Retired'
employment_selfemployed = 'Self-employed'
employment_homemaker = 'Homemaker'
employment_volunteer = 'Unpaid volunteer or intern'
not_employed = 'Not currently employed'

# Hours worked
full_time_hours_list = ['31-40 hours','41–50 hours','More than 50 hours',
                        'More than 50 hours', '31-34 hours']

# Worker
is_worker = "1+ job(s) (including part-time)"

# Age
age_under_5 = 'Under 5 years old'
age_5_11 = '5-11 years'
age_12_15 = '12-15 years'
age_16_17 = '16-17 years'
age_18_24 = '18-24 years'
age_25_34 = '25-34 years'
age_35_44 = '35-44 years'
age_45_54 = '45-54 years'
age_55_64 = '55-64 years'
age_65_74 = '65-74 years'
age_75_84 = '75-84 years'
age_85_plus = '85 or years older'

# student
student_full_time = 'Full-time student'
student_part_time = 'Part-time student'
not_student = 'No, not a student'

# schooltype
schooltype_daycare = 'Daycare'
schooltype_homeschool = 'K-12 home school (full-time or part-time)'
schooltype_public_k12 = 'K-12 public school'
schooltype_private_k12 = 'K-12 private school'
schooltype_vocational = 'Vocational/technical school'
schooltype_college = 'College, graduate, or professional school'

# Transit Pass
transit_pass_yes_all_paid = 'Yes, school pays all of value'
transit_pass_yes_part_paid = 'Yes, school pays part of value'
transit_pass_no_self_paid = 'No, participant/household pays all of value',
transit_pass_no_other_paid = 'No, someone else pays all of value'

# Transit Benefits
transit_benefits_offered_used = 'Offered, and I use'
transit_benefits_not_offered = 'Not offered'
transit_benefits_offered_not_used = "Offered, but I don't use"

# Work Parking Pass
work_parking_employer_pays_all = 'Yes, employer pays/reimburses for all or part of daily parking costs'
work_parking_employer_pays_some = 'Yes, employer pays/reimburses for all or part of parking pass'
work_parking_worker_pays_all_pass = 'Yes, personally pay for parking pass at work'
work_parking_worker_pays_all_daily = 'Yes, personally pay daily with cash/tickets'
work_parking_free = 'No, parking is usually/always free'
work_parking_na = 'N/A (e.g. dropped off)'

# Take median age
age_map = {
    'Under 5 years old': 2,
    '5-11 years': 8,
    '12-15 years': 14,
    '16-17 years': 17,
    '18-24 years': 21,
    '25-34 years': 30,
    '35-44 years': 40,
    '45-54 years': 50,
    '55-64 years': 60,
    '65-74 years': 70,
    '75-84 years': 80,
    '85 or years older': 85
}

gender_map = {
    "Male": 1,    
    "Female": 2,
    "Another": 9,
    "Prefer not to answer": 9
}

pstyp_map = {
    'No, not a student': 0,
    'Full-time student': 1,
    'Part-time student': 2
}

mode_dict = {
    'Walk': 1,
    'Bike': 2,
    'SOV': 3,
    'HOV2': 4,
    'HOV3+': 5,
    'Transit': 6,
    'School_Bus': 8,
    'TNC': 9,   # Note that 9 was other in older Daysim records
    'Other': 10
    }

# FIXME: usual commute mode should consider occupancy from observed work trips
# FIXME: usual commute transit mode should include drive to transit (assuming all walk to transit currently)
commute_mode_dict = {
    'null': 0,
    'Bus (public transit)': 6, 
    'Private bus or shuttle': 6,
    'Drive alone': 3, 
    'Vanpool': 5, # assume hov3
    'Walk, jog, or wheelchair': 1,
    'Bicycle or e-bike': 2, 
    'Commuter rail (Sounder, Amtrak)': 6,
    'Airplane or helicopter': 0,
    'Carpool with other people not in household (may also include household members)': 5,  # assume hov3
    'Urban rail (Link light rail, monorail)': 6,
    'Carpool ONLY with other household members': 4,   # assume HH carpool is hov2
    'Other hired service (Uber, Lyft, or other smartphone-app car service)': 0,
    'Motorcycle/moped/scooter':3, 
    'Ferry or water taxi': 6, 
    'Streetcar': 6,
    'Taxi (e.g., Yellow Cab)': 0, 
    'Paratransit': 6,
    'Other (e.g. skateboard)': 0, 
    'Missing: Skip Logic': 0,
    'Scooter or e-scooter (e.g., Lime, Bird, Razor)': 0,
    'Motorcycle/moped': 3
    }

day_map = {
    'Monday': 1,
    'Tuesday': 2,
    'Wednesday': 3,
    'Thursday': 4
}

purpose_map = {
    'Went home': 0, # home
    'Went to school/daycare (e.g., daycare, K-12, college)': 2, # school
    "Dropped off/picked up someone (e.g., son at a friend's house, spouse at bus stop)": 3, # escort
    'Went to primary workplace': 1, # work
    'Went to work-related place (e.g., meeting, second job, delivery)': 1, # work-related
    'Went to other work-related activity': 1, # work-related
    'Went grocery shopping': 5, # grocery -> shop
    'Went to other shopping (e.g., mall, pet store)': 5, # other shopping -> shop
    'Other social/leisure (rMove only)': 7, # personal business
    'Went to medical appointment (e.g., doctor, dentist)': 4, # medical is combined with personal business (4)
    'Went to restaurant to eat/get take-out': 6, # restaurant -> meal
    'Attended recreational event (e.g., movies, sporting event)': 7, # recreational is combined with social (7)
    'Other purpose': 7, # social
    "Went to a family activity (e.g., child's softball game)": 7, # recreational is combined with social (7)
    'Went to religious/community/volunteer activity': 7, # religious/community/volunteer -> social
    'Attended social event (e.g., visit with friends, family, co-workers)': 7, # family activity -> social
    'Transferred to another mode of transportation (e.g., change from ferry to bus)': 10, # change mode
    'Conducted personal business (e.g., bank, post office)': 4, # personal business
    'Went to exercise (e.g., gym, walk, jog, bike ride)': 7, # other social
    'Other appointment/errands (rMove only)': 4 # other, setting as personal business for now (4) ?
}

dorp_map = {
    'Driver': 1,
    'Passenger': 2,
}

##############################
# Household
##############################
hownrent_map = {
    'Own/paying mortgage': 1,
    'Rent': 2,
    'Provided by job or military': 3,
    'Prefer not to answer': 3,
    'Other': 3
}
hhrestype_map = {
    'Single-family house (detached house)': 1, # SFH: SFH
    'Townhouse (attached house)': 2, # Townhouse (attached house): duplex/triplex/rowhouse
    'Building with 3 or fewer apartments/condos': 2, # Building with 3 or fewer apartments/condos: duplex/triplex/rowhouse
    'Building with 4 or more apartments/condos': 3, # Building with 4 or more apartments/condos: apartment/condo
    'Mobile home/trailer': 4, # Mobile home/trailer: Mobile home/trailer
    'Dorm or institutional housing': 5, # Dorm or institutional housing: Dorm room/rented room
    'Other (including boat, RV, van, etc.)': 6, # other: other
}

# Use the midpoint of the ranges provided since DaySim uses actual values
income_map = {
    'Under $10,000': 5000,
    '$10,000-$24,999': 17500,
    '$25,000-$34,999': 30000,
    '$35,000-$49,999': 42500,
    '$50,000-$74,999': 62500,
    '$75,000-$99,999': 87500,
    '$100,000-$149,999': 125000,
    '$150,000-$199,999': 175000,
    '$200,000-$249,999': 225000,
    '$250,000 or more': 250000,
   'Prefer not to answer': -1
}

hhsize_map = {
    '1 person': 1, 
    '2 people': 2, 
    '3 people': 3, 
    '4 people': 4, 
    '5 people': 5, 
    '6 people': 6,
    '7 people': 7,
    '8 people': 8, 
    '9 people': 9
}

hhvehs_map = {
    '0 (no vehicles)': 0,
    '1 vehicle': 1, 
    '2 vehicles': 2, 
    '3 vehicles': 3,
    '4 vehicles': 4, 
    '5 vehicles': 5, 
    '6 vehicles': 6, 
    '7 vehicles': 7,
    '8+ vehicles': 8
}

transit_mode_list = ['Ferry or water taxi',
                     'Commuter rail (Sounder, Amtrak)',
                     'Urban Rail (e.g., Link light rail, monorail)',
                     'Bus (public transit)',
                     'Other rail (e.g., streetcar)']

######################################
# Attach Skims Config
######################################

h5output = 'survey2021.h5'
version_tag = 'P21'

bike_speed = 10 # miles per hour
walk_speed = 3 # miles per hour

# lookup for departure time to skim times
tod_dict = {
	0: '20to5',
	1: '20to5',
	2: '20to5',
	3: '20to5',
	4: '20to5',
	5: '5to6',
	6: '6to7',
	7: '7to8',
	8: '8to9',
	9: '9to10',
	10: '10to14',
	11: '10to14',
	12: '10to14',
	13: '10to14',
	14: '14to15',
	15: '15to16',
	16: '16to17',
	17: '17to18',
	18: '18to20',
	19: '18to20',
	20: '20to5',
	21: '20to5',
	22: '20to5',
	23: '20to5',
	24: '20to5'
}

# Create an ID to match skim naming method
skim_mode_dict = {
	1: 'walk',
	2: 'bike',
	3: 'sov',
	4: 'hov2',
	5: 'hov3',
	6: 'ivtwa',	# transit in-vehicle time
	7: 'sov',
	8: 'sov',   # assign school bus as sov
	9: 'sov',	# assign other as sov
	10: 'sov',	# assign other as sov
	-99: 'sv'
}