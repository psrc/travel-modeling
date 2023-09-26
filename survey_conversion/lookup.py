# Weights
person_weight_col = 'hh_weight_2017_2019'
hh_weight_col = 'hh_weight_2017_2019'
trip_weight_col = 'trip_weight_2017_2019'

# Employment
employment_full_time = "Employed full time (35+ hours/week, paid)"
employment_part_time = "Employed part time (fewer than 35 hours/week, paid)"
employment_retired = 'Retired'
employment_homemaker = 'Homemaker'
employment_volunteer = 'Unpaid volunteer or intern'
not_employed = 'Not currently employed'

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
    "Male": 1,    # male: male
    "Female": 2,    # female: female
    "Another": 9,    # another: missing
    "Prefer not to answer": 9     # prefer not to answer: missing
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

commute_mode_dict = {
    1: 3, # SOV
    2: 4, # HOV (2 or 3)
    3: 4, # HOV (2 or 3)
    4: 3, # Motorcycle, assume drive alone 
    5: 5, # vanpool, assume HOV3+
    6: 2, # bike
    7: 1, # walk
    8: 6, # bus -> transit
    9: 10, # private bus -> other
    10: 10, # paratransit -> other
    11: 6, # commuter rail
    12: 6, # urban rail
    13: 6, # streetcar
    14: 6, # ferry
    15: 10, # taxi -> other
    16: 9, # TNC
    17: 10, # plane -> other
    97: 10 # other
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

transit_mode_list = ['Ferry or water taxi',
                     'Commuter rail (Sounder, Amtrak)',
                     'Urban Rail (e.g., Link light rail, monorail)',
                     'Bus (public transit)',
                     'Other rail (e.g., streetcar)']