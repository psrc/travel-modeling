library(psrccensus)
library(tidyverse)

# get PUMS data
pums_2023 <-  get_psrc_pums(span = 5,    
                            dyear = 2023,
                            level = "p", 
                            vars = c("JWTRNS",   # Means of transportation to work
                                     "JWRIP"     # Vehicle occupancy for worker whose means of transportation to work is "car, truck, or van"
                                     )) 

# ---- commute mode ----
# data dictionary: https://www2.census.gov/programs-surveys/acs/tech_docs/pums/data_dict/PUMS_Data_Dictionary_2019-2023.pdf
# page 38
modes <- data.frame(JWTRNS = c(1,2,3,4,5,6,7,8,9,10,11,12),
                    # labels from data dictionary
                    label = c("Car, truck, or van", 
                              "Bus", 
                              "Subway or elevated rail", 
                              "Long-distance train or commuter rail", 
                              "Light rail, streetcar, or trolley", 
                              "Ferryboat", 
                              "Taxicab", 
                              "Motorcycle", 
                              "Bicycle",
                              "Walked",
                              "Worked from home",
                              "Other method"),
                    # mode groupings matching model results
                    group = c("Drive",    
                              "Transit", 
                              "Transit", 
                              "Transit", 
                              "Transit", 
                              "Transit", 
                              "TNC", 
                              "Drive", 
                              "Bike",
                              "Walk",
                              NA,  # assign NA to exclude "Worked from home" and "Other method"
                              NA))

data <- pums_2023 
data$variables <- data$variables %>% 
  # add mode labels
  left_join(modes, by = "JWTRNS") %>%
  # add SOV & HOV
  mutate(mode = case_when(group=="Drive" & JWRIP==1 ~ "SOV",
                          group=="Drive" & JWRIP==2 ~ "HOV2",
                          group=="Drive" ~ "HOV3+",
                          TRUE~group))

# commute mode by home county
commute_2023_county <- psrc_pums_count(data, group_vars=c("COUNTY","mode"), incl_na = FALSE) 
# commute mode in region
commute_2023_region <- psrc_pums_count(data, group_vars=c("mode"), incl_na = FALSE) 

commute_2023 <- commute_2023_county %>% 
  add_row(commute_2023_region) %>%
  filter(mode != "Total") %>%
  select(DATA_YEAR,COUNTY,mode,share) %>%
  rename(county = COUNTY,
         year = DATA_YEAR)

write_csv(commute_2023,'R:/e2projects_two/SoundCast/Inputs/db_inputs/acs_commute_mode_by_home_county.csv')
