####################
# Resource Related #
####################

resource_names = ["Energy",
                  "Mineral",
                  "Crystal",
                  "Ectrolium",
                  "Time",
                  "Population"]

energy_decay_factor = 0.005
crystal_decay_factor = 0.02

####################
# Research Related #
####################
researchNames = [
    "research_points_military",
    "research_points_construction",
    "research_points_tech",
    "research_points_energy",
    "research_points_population",
    "research_points_culture",
    "research_points_operations",
    "research_points_portals"]

####################
# Building Related #
####################

# One option I could do is switch from using a list to using a dict, like building_names.solar or something, which might make the code a little more readable

#            energy, mineral, crystal, endurium, time
building_costs = [[120, 10, 0, 1, 4],
                  [450, 20, 12, 8, 14],
                  [200, 0, 0, 2, 8],
                  [350, 8, 0, 12, 6],
                  [400, 36, 4, 0, 12],
                  [300, 30, 0, 2, 10],
                  [100, 5, 5, 5, 8],
                  [400, 35, 20, 40, 16],
                  [2000, 10, 60, 30, 24],
                  [8000, 200, 500, 400, 128]]  # portal

required_building_tech = [0, 100, 0, 0, 0, 0, 0, 110, 140, 0]

upkeep_solar_collectors = 0.0
upkeep_fission_reactors = 20.0
upkeep_mineral_plants = 2.0
upkeep_crystal_labs = 2.0
upkeep_refinement_stations = 2.0
upkeep_cities = 4.0
upkeep_research_centers = 1.0
upkeep_defense_sats = 4.0
upkeep_shield_networks = 16.0

networth_per_building = 8  # can always break it out into separate buildings later, but it was all 8's in the current C code

building_production_solar = 12
building_production_fission = 40
building_production_mineral = 1
building_production_crystal = 1
building_production_ectrolium = 1
building_production_cities = 1000
building_production_research = 6

population_size_factor = 20  # determines max pop
population_base_factor = 2  # determines starting pop

building_info_list = {
    "Solar Collectors": {
        "Income": "12 Energy",
        "Upkeep": 0},
    "Fission Reactors": {
        "Income": "40 Energy",
        "Upkeep": 20},
    "Mineral Plants": {
        "Income": "1 Mineral",
        "Upkeep": 2},
    "Crystal Laboratories": {
        "Income": "1 Crystal",
        "Upkeep": 2},
    "Refinement Stations": {
        "Income": "1 Ectrolium",
        "Upkeep": 2},
    "Cities": {
        "Effect": "10000 Pop",
        "Upkeep": 4},
    "Research Centers": {
        "Income": "6 RC Points",
        "Upkeep": 1},
    "Defense Satellites": {
        "Effect": "Attack 110 Defence 450",
        "Upkeep": 4},
    "Shield Network": {
        "Effect": "1300 Defence",
        "Upkeep": 16},
    "Portal": {
        "Effect": "Allows faster travel",
        "Upkeep": 10000}}

################
# Unit Related #
################

#           energy, mineral, crystal, endurium, time
unit_costs = [[250, 15, 0, 5, 6],  # bombers
              [150, 10, 0, 3, 5],  # fighters
              [600, 35, 10, 10, 8],  # transports
              [1600, 90, 0, 45, 12],  # cruisers
              [2000, 160, 15, 20, 12],  # carriers
              [100, 0, 0, 1, 3],  # soldiers
              [50, 5, 0, 1, 2],  # droids
              [350, 20, 8, 10, 4],  # goliaths
              [-1, -1, -1, -1, -1],  # phantoms
              [150, 0, 10, 0, 5],  # psychics
              [150, 0, 0, 10, 5],  # agents
              [200, 8, 60, 5, 7],  # ghost ships
              [5000, 50, 0, 50, 4]]  # explors

required_unit_tech = [60, 0, 0, 40, 20, 0, 80, 120, 0, 0, 0, 160, 0]

unit_upkeep = [2.0, 1.6, 3.2, 12.0, 18.0, 0.4, 0.6, 2.8, 0.0, 0.8, 0.8, 2.4, 60.0]

#             not sure these correspond to phase of battle, speed, networth
unit_stats = [[0, 64, 24, 110, 4, 4],  # bombers
              [20, 120, 0, 60, 4, 3],  # fighters
              [0, 60, 0, 50, 4, 5],  # transports
              [70, 600, 70, 600, 4, 12],  # cruisers
              [0, 540, 0, 540, 4, 14],  # carriers
              [0, 48, 3, 16, 0, 1],  # soldiers
              [0, 48, 5, 30, 0, 1],  # droids
              [28, 140, 10, 90, 0, 4],  # goliaths
              [32, 130, 20, 130, 10, 7],  # phantoms
              [0, 0, 0, 0, 0, 2],  # psychics
              [0, 0, 0, 0, 8, 2],  # agents
              [0, 0, 0, 0, 8, 6],  # ghost ships
              [0, 0, 0, 0, 3, 30]]  # explors
unit_labels = ["Bombers", "Fighters", "Transports", "Cruisers", "Carriers", "Soldiers", "Droids", "Goliaths",
               "Phantoms", "Psychics", "Agents", "Ghost Ships", "Exploration Ships"]
unit_troops = ["bomber", "fighter", "transport", "cruiser", "carrier", "soldier", "droid", "goliath",
               "phantom", "wizard", "agent", "ghost", "exploration"]
unit_race_bonus_labels = ["bombers_coeff", "fighters_coeff", "transports_coeff", "cruisers_coeff", "carriers_coeff", \
                          "soldiers_coeff", "droids_coeff", "goliaths_coeff", "phantoms_coeff", "psychics_coeff", \
                          "agents_coeff", "ghost_ships_coeff", "exploration_ships_coeff", ]

building_labels = {
'SC': 'Solar Collectors',
'FR': 'Fission Reactors',
'MP': 'Mineral Plants',
'CL': 'Crystal Laboratories',
'RS': 'Refinement Stations',
'CT': 'Cities',
'RC': 'Research Centers',
'DS': 'Defense Satellites',
'SN': 'Shield Networks',
'PL': 'Portal'
}

# Build dictionary that will store all our unit info
unit_info = {}
# Order of this list much match the data above. Might as well store the order in the dict for reference in views
unit_info["unit_list"] = ['bomber', 'fighter', 'transport', 'cruiser', 'carrier', 'soldier', 'droid', 'goliath',
                          'phantom', 'wizard', 'agent', 'ghost', 'exploration']
for i, unit in enumerate(unit_info["unit_list"]):
    unit_info[unit] = {}
    unit_info[unit]['cost'] = unit_costs[i]
    unit_info[unit]['required_tech'] = required_unit_tech[i]
    unit_info[unit]['upkeep'] = unit_upkeep[i]
    unit_info[unit]['stats'] = unit_stats[i]
    unit_info[unit]['label'] = unit_labels[i]
    unit_info[unit]['troops'] = unit_troops[i]
    unit_info[unit]['i'] = i

unit_helper_list = {
    "Bombers": {
        "Attacking": "Phase 3 + 4", 
        "Defending": "None", 
        "Air Attack": "0", 
        "Air Defence": "64", 
        "Ground Attack": "24", 
        "Ground Defence": "110", 
        "Upkeep": "2"}, 
    "Fighters": {
        "Attacking": "Phase 2", 
        "Defending": "Phase 2", 
        "Air Attack": "20", 
        "Air Defence": "120", 
        "Ground Attack": "0", 
        "Ground Defence": "60", 
        "Upkeep": "1.6"}, 
    "Transports": {  
        "Air Defence": "60", 
        "Ground Defence": "50",
        "Soldiers": "100",
        "Droids": "100",
        "Goliaths": "25",
        "Upkeep": "3.2"}, 
    "Cruisers": {
        "Attacking": "All", 
        "Defending": "Phase 1 + 2", 
        "Air Attack": "70", 
        "Air Defence": "600", 
        "Ground Attack": "70", 
        "Ground Defence": "600", 
        "Upkeep": "12"}, 
    "Carriers": {
        "Air Defence": "540", 
        "Ground Defence": "540",
        "Bombers": "100",
        "Fighters": "100",
        "Transports": "100",
        "Upkeep": "18"},
    "Soldiers": {
        "Attacking": "Phase 4", 
        "Defending": "Phase 4", 
        "Air Attack": "0", "Air Defence": "48", 
        "Ground Attack": "3", 
        "Ground Defence": "16",
        "Upkeep": "0.4"}, 
    "Droids": {
        "Attacking": "Phase 4",
        "Defending": "Phase 4", 
        "Air Attack": "0", 
        "Air Defence": "48", 
        "Ground Attack": "5", 
        "Ground Defence": "30", 
        "Upkeep": "0.6"}, 
    "Goliaths": {
        "Attacking": "Phase 4", 
        "Defending": "Phase 3 + 4", 
        "Air Attack": "28", 
        "Air Defence": "140", 
        "Ground Attack": "10", 
        "Ground Defence": "90", 
        "Upkeep": "2.8"},
    "Phantoms": {
        "Attacking": "All", 
        "Defending": "All", 
        "Air Attack": "32", 
        "Air Defence": "120", 
        "Ground Attack": "20", 
        "Ground Defence": "130", 
        "Upkeep": "0"},
    "Psychics": {
        "Attacking": "Spells", 
        "Defending": "Spells + Incantations", 
        "Spells Attack": "1", 
        "Spells Defence": "1",  
        "Incantations Defence": "1/7", 
        "Upkeep": "0.8"}, 
    "Agents": {
        "Attacking": "Operations", 
        "Defending": "Operations", 
        "Operations Attack": "1", 
        "Operations Defence": "1", 
        "Upkeep": "0.8"},
    "Ghost Ships": {
        "Attacking": "Incantations",
        "Defending": "Incantations", 
        "Incantations Attack": "1",
        "Incantations Defence": "1", 
        "Upkeep": "2.4"},
    "Exploration Ships": {
        "Effect": "Capture Uninhabited Planets",
        "Upkeep": "60.0"}}

##########################################
# Global game settings from evconfig.ini #
##########################################

stockpile = 0
settings_num_value = 1  # still not sure what this is
tick_time = 600  # in seconds

###################
# Race Attributes #
###################

race_info_list = {
    "Harks": {
        "pop_growth": 0.8 * 0.02,
        "military_attack": 1.4,
        "military_defence": 0.9,
        "travel_speed": 1.4 * 2.0,
        "research_bonus_military": 1.2,
        "research_bonus_construction": 1.2,
        "research_bonus_tech": 1.2,
        "research_bonus_energy": 1.2,
        "research_bonus_population": 1.2,
        "research_bonus_culture": 0.6,
        "research_bonus_operations": 1.2,
        "research_bonus_portals": 1.2,
        "research_max_military": 250,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "fighters_coeff": 1.2,  # defaults to 1.0
        "energy_production": 0.9,  # defaults to 1.0
        "crystal_production": 1.25,
        "race_special": None,  # TODO paste list somewhere of possible specials
        },
    "Manticarias": {
        "pop_growth": 0.9 * 0.02,
        "military_attack": 0.7,
        "military_defence": 1.1,
        "travel_speed": 1.0 * 2.0,
        "research_bonus_military": 0.9,
        "research_bonus_construction": 0.9,
        "research_bonus_tech": 0.9,
        "research_bonus_energy": 0.9,
        "research_bonus_population": 0.9,
        "research_bonus_culture": 1.8,
        "research_bonus_operations": 0.9,
        "research_bonus_portals": 0.9,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "psychics_coeff": 1.4,
        "ghost_ships_coeff": 1.2,
        "energy_production": 1.4,
        "race_special": 'RACE_SPECIAL_SOLARP15',
        },
    "Foohons": {
        "pop_growth": 0.8 * 0.02,
        "military_attack": 1.2,
        "military_defence": 1.1,
        "travel_speed": 1.0 * 2.0,
        "research_bonus_military": 1.5,
        "research_bonus_construction": 1.5,
        "research_bonus_tech": 1.5,
        "research_bonus_energy": 1.5,
        "research_bonus_population": 1.5,
        "research_bonus_culture": 1.5,
        "research_bonus_operations": 1.5,
        "research_bonus_portals": 1.5,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "ghost_ships_coeff": 1.1,
        "energy_production": 0.8,
        "ectrolium_production": 1.2,
        "race_special": 'RACE_SPECIAL_POPRESEARCH',
        },
    "Spacebornes": {
        "pop_growth": 1.2 * 0.02,
        "military_attack": 1.0,
        "military_defence": 1.2,
        "travel_speed": 1.8 * 2.0,
        "research_bonus_military": 1.1,
        "research_bonus_construction": 1.1,
        "research_bonus_tech": 0.6,
        "research_bonus_energy": 1.1,
        "research_bonus_population": 1.1,
        "research_bonus_culture": 1.1,
        "research_bonus_operations": 1.1,
        "research_bonus_portals": 1.1,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 250,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "soldiers_coeff": 1.1,
        "droids_coeff": 1.1,
        "psychics_coeff": 0.7,
        "agents_coeff": 1.3,
        "energy_production": 1.3,
        "race_special": None,
        },
    "Dreamweavers": {
        "pop_growth": 1.1 * 0.02,
        "military_attack": 1.0,
        "military_defence": 0.7,
        "travel_speed": 1.0 * 2.0,
        "research_bonus_military": 1.0,
        "research_bonus_construction": 1.4,
        "research_bonus_tech": 2.8,
        "research_bonus_energy": 1.4,
        "research_bonus_population": 1.4,
        "research_bonus_culture": 1.4,
        "research_bonus_operations": 1.4,
        "research_bonus_portals": 1.4,
        "research_max_military": 100,
        "research_max_construction": 250,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "psychics_coeff": 1.5,
        "ghost_ships_coeff": 1.3,
        "energy_production": 0.8,
        "race_special": None,
        },
    "Wookiees": {
        "pop_growth": 1.2 * 0.02,
        "military_attack": 0.9,
        "military_defence": 1.3,
        "travel_speed": 1.6 * 2.0,
        "research_bonus_military": 1.0,
        "research_bonus_construction": 2.0,
        "research_bonus_tech": 1.0,
        "research_bonus_energy": 1.0,
        "research_bonus_population": 2.0,
        "research_bonus_culture": 1.0,
        "research_bonus_operations": 1.0,
        "research_bonus_portals": 2.0,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 250,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "cruiser_coeff": 1.15,
        "ghost_ships_coeff": 1.15,
        "energy_production": 0.7,
        "mineral_production": 1.25,
        "crystal_production": 1.25,
        "race_special": 'RACE_SPECIAL_WOOKIEE',
        },
    "Jackos": {
        "pop_growth": 1.0 * 0.02,
        "military_attack": 1.0,
        "military_defence": 1.0,
        "travel_speed": 1.0 * 2.0,
        "research_bonus_military": 0.8,
        "research_bonus_construction": 0.8,
        "research_bonus_tech": 0.8,
        "research_bonus_energy": 0.8,
        "research_bonus_population": 0.8,
        "research_bonus_culture": 0.8,
        "research_bonus_operations": 0.8,
        "research_bonus_portals": 0.8,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 250,
        "research_max_operations": 250,
        "research_max_portals": 200,
        "energy_production": 1.0,
        "mineral_production": 0.9,
        "race_special": 'RACE_SPECIAL_WOOKIEE',
        },
    "Shootout": {
        "pop_growth": 1.0 * 0.02,
        "military_attack": 1.0,
        "military_defence": 1.0,
        "travel_speed": 1.0 * 2.0,
        "research_bonus_military": 1.0,
        "research_bonus_construction": 1.0,
        "research_bonus_tech": 1.0,
        "research_bonus_energy": 1.0,
        "research_bonus_population": 1.0,
        "research_bonus_culture": 1.0,
        "research_bonus_operations": 1.0,
        "research_bonus_portals": 1.0,
        "research_max_military": 200,
        "research_max_construction": 200,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "energy_production": 1.0,
        },
    "Furtifons": {
        "pop_growth": 0.9 * 0.02,
        "military_attack": 1.0,
        "military_defence": 1.0,
        "travel_speed": 1.6 * 2.0,
        "research_bonus_military": 0.9,
        "research_bonus_construction": 0.9,
        "research_bonus_tech": 0.9,
        "research_bonus_energy": 0.9,
        "research_bonus_population": 0.9,
        "research_bonus_culture": 0.9,
        "research_bonus_operations": 1.8,
        "research_bonus_portals": 0.9,
        "research_max_military": 200,
        "research_max_construction": 250,
        "research_max_tech": 200,
        "research_max_energy": 200,
        "research_max_population": 200,
        "research_max_culture": 200,
        "research_max_operations": 200,
        "research_max_portals": 200,
        "energy_production": 1.0,
        "agents_coeff": 1.2,
        "ghost_ships_coeff": 1.2,
        "race_special": 'RACE_SPECIAL_FURTIFON'},
    "Samsonites": {
        "pop_growth": 1.0 * 0.02,
        "military_attack": 1.3,
        "military_defence": 1.2,
        "travel_speed": 0.8 * 2.0,
        "research_bonus_military": 1.1,
        "research_bonus_construction": 1.1,
        "research_bonus_tech": 1.1,
        "research_bonus_energy": 1.1,
        "research_bonus_population": 1.1,
        "research_bonus_culture": 1.1,
        "research_bonus_operations": 1.1,
        "research_bonus_portals": 1.1,
        "research_max_military": 185,
        "research_max_construction": 185,
        "research_max_tech": 185,
        "research_max_energy": 185,
        "research_max_population": 185,
        "research_max_culture": 185,
        "research_max_operations": 185,
        "research_max_portals": 185,
        "energy_production": 1.1,
        "psychics_coeff": 0.9,
        "agents_coeff": 0.9,
        "race_special": 'RACE_SPECIAL_SAMSONITES',
        }}    
        
race_display_list = {
    "Harks": {"bonuses":{
        "Population Growth": "-20",
        "Attack": "40",
        "Defence": "-10",
        "Speed": "40",
        "Fighters": "20",  # defaults to 1.0
        "Energy": "-10",  # defaults to 1.0
        "Crystal": "25",},
        "research":{
        "Military": "20",
        "Construction": "20",
        "Tech": "20",
        "Energy": "20",
        "Population": "20",
        "Culture": "-40",
        "Operations": "20",
        "Portals": "20",
        "Military Max": 250,},
        "op_list": ["Observe Planet", "Network Infiltration", "Infiltration", "Bio Infection", "Military Sabotage",
                    "Nuke Planet", "Diplomatic Espionage", "Bribe officials"],
        "spell_list": ["Irradiate Ectrolium", "Incandescence", "Black Mist", "War Illusions"],
        "incantation_list": ["Sense Artefact", "Portal Force Field", "Vortex Portal", "Energy Surge", "Call to Arms"]},
    "Manticarias": {"bonuses":{
        "Population Growth": "-10",
        "Attack": "-30",
        "Defence": "10",
        "Psychics": "40",
        "Ghost Ships": "20",
        "Solars": "15",
        "Energy": "40",},
        "research":{
        "Military": "-10",
        "Construction": "-10",
        "Tech": "-10",
        "Energy": "-10",
        "Population": "-10",
        "Culture": "80",
        "Operations": "-10",
        "Portals": "-10",},
        
        "op_list": ["Spy Target", "Observe Planet", "Hack mainframe"],
        "spell_list": ["Dark Web", "Black Mist", "War Illusions", "Psychic Assault", "Phantoms", "Enlightenment",
                       "Grow Planets Size"],
        "incantation_list": ["Sense Artefact", "Planetary Shielding", "Mind Control"]},
    "Foohons": {"bonuses":{
        "Population Growth": "-20",
        "Attack": "20",
        "Defence": "10",
        "Ghost Ships": "10",
        "Energy": "-20",
        "Ectrolium": "20",
        "Pop Research": "6000"},
        "research":{
        "Military": "50",
        "Construction": "50",
        "Tech": "50",
        "Energy": "50",
        "Population": "50",
        "Culture": "50",
        "Operations": "50",
        "Portals": "50",},
        
        "op_list": ["Spy Target", "Observe Planet", "Infiltration", "Military Sabotage",
                    "High Infiltration", "Planetary Beacon", "Maps theft"],
        "spell_list": ["Irradiate Ectrolium", "Dark Web", "Incandescence", "Psychic Assault", "Enlightenment"],
        "incantation_list": ["Sense Artefact", "Survey System", "Vortex Portal", "Mind Control"]},
    "Spacebornes": {"bonuses":{
        "Population Growth": "20",
        "Defence": "20",
        "Speed": "80",
        "Soldiers": "10",
        "Droids": "10",
        "Psychics": "-30",
        "Agents": "30",
        "Energy": "30",},
        "research":{
        "Military": "10",
        "Construction": "10",
        "Tech": "-40",
        "Energy": "10",
        "Population": "10",
        "Culture": "10",
        "Operations": "10",
        "Portals": "10",
        "Energy Max": 250,},
        "op_list": ["Spy Target", "Observe Planet", "Network Infiltration", "Bio Infection",
                    "Hack mainframe", \
                    "Nuke Planet", "Planetary Beacon", "Diplomatic Espionage", "Bribe officials", "Maps theft"],
        "spell_list": ["Irradiate Ectrolium", "Incandescence", "Black Mist"],
        "incantation_list": ["Sense Artefact", "Survey System", "Planetary Shielding"]},
    "Dreamweavers": {"bonuses":{
        "Population Growth": "10",
        "Defence": "-30",
        "Psychics": "50",
        "Ghost Ships": "30",
        "Energy": "-20",
        "Crystal": "25",},
        "research":{
        "Construction": "40",
        "Tech": "180",
        "Energy": "40",
        "Population": "40",
        "Culture": "40",
        "Operations": "40",
        "Portals": "40",
        "Military Max": 100,
        "Construction Max": 250,
        },
        
        "op_list": ["Observe Planet", "Network Infiltration", "Bio Infection", "Hack mainframe", "Military Sabotage"],
        "spell_list": ["Irradiate Ectrolium", "Dark Web", "Incandescence", "Black Mist", "War Illusions",
                       "Psychic Assault", "Phantoms", "Enlightenment", "Grow Planets Size"],
        "incantation_list": ["Sense Artefact", "Portal Force Field", "Mind Control", "Energy Surge"]},
    "Wookiees": {"bonuses":{
        "Population Growth": "20",
        "Attack": "-10",
        "Defence": "30",
        "Speed": "60",
        "Cruisers": "15",
        "Ghost Ships": "15",
        "Energy": "-10",
        "Mineral": "25",
        "Crystal": "25",
        "Interest": "0.5"},
        "research":{
        "Construction": "100",
        "Population": "100",
        "Portals": "100",
        "Population Max": 250,},
        
        
        "op_list": ["Observe Planet", "Infiltration", "Nuke Planet", "Planetary Beacon", "Diplomatic Espionage",
                    "Bribe officials"],
        "spell_list": ["Irradiate Ectrolium", "Incandescence", "War Illusions", "Grow Planets Size"],
        "incantation_list": ["Sense Artefact", "Survey System", "Portal Force Field", "Call to Arms"]},
    "Jackos": {"bonuses":{
        "Mineral": "-10",
        "Pop Research": "10000",
        "Solars": "10",
        "Interest": "0.2",},
        "research":{
        "Military": "-20",
        "Construction": "-20",
        "Tech": "-20",
        "Energy": "-20",
        "Population": "-20",
        "Culture": "-20",
        "Operations": "-20",
        "Portals": "-20",
        "Culture Max": 250,
        "Operations Max": 250,},
        "op_list": ["Spy Target",
                "Observe Planet",
                "Network Infiltration",
                "Infiltration",
                "Diplomatic Espionage",
                "Bio Infection",
                "Hack mainframe",
                "Military Sabotage",
                "Planetary Beacon",
                "Bribe officials",
                "Nuke Planet",
                "Maps theft",
                "High Infiltration"],
        "spell_list": ["Irradiate Ectrolium",
              "Dark Web",
              "Incandescence",
              "Black Mist",
              "War Illusions",
              "Psychic Assault",
              "Enlightenment",
              "Grow Planets Size",
              "Phantoms"],
        "incantation_list": ["Survey System", "Sense Artefact", "Planetary Shielding", "Portal Force Field", "Mind Control", "Call to Arms", "Energy Surge",
                "Vortex Portal"]},
    "Furtifons": {"bonuses":{
        "Speed": "60",
        "Population Growth": "-10",
        "Culture Research": "Increases FR costs when defending",
        "Agents": "20",
        "Ghost Ships": "20",},
        "research":{
        "Military": "-10",
        "Construction": "-10",
        "Tech": "-10",
        "Energy": "-10",
        "Population": "-10",
        "Culture": "-10",
        "Operations": "80",
        "Portals": "-10",
        "Construction Max": 250,},
        "op_list": ["Spy Target",
                "Observe Planet",
                "Infiltration",
                "Diplomatic Espionage",
                "Hack mainframe",
                "Planetary Beacon",
                "High Infiltration"],
        "spell_list": ["Incandescence",
              "War Illusions",
              "Enlightenment",
              "Grow Planets Size"],
        "incantation_list": ["Survey System", "Sense Artefact", "Planetary Shielding", "Portal Force Field", "Vortex Portal"]},
    "Samsonites": {"bonuses":{
        "Attacking": "20% Cheaper FR costs, ignore Dark Webs",
        "Speed": "-20",
        "Attack": "30",
        "Defence": "20",
        "Psychics": "-10",
        "Agents": "-10",
        "Energy": "10",},
        "research":{
        "Military": "10",
        "Construction": "10",
        "Tech": "10",
        "Energy": "10",
        "Population": "10",
        "Culture": "10",
        "Operations": "10",
        "Portals": "10",
        "Military Max": 185,
        "Construction Max": 185,
        "Technology Max": 185,
        "Energy Max": 185,
        "Population Max": 185,
        "Culture Max": 185,
        "Operations Max": 185,
        "Portals Max": 185,},
        "op_list": ["Observe Planet",
                "Military Sabotage",
                "Bribe officials",
                "Nuke Planet",
                "Maps theft"],
        "spell_list": ["Irradiate Ectrolium",
              "Black Mist",
              "Psychic Assault",
              "Phantoms"],
        "incantation_list": ["Sense Artefact", "Portal Force Field", "Mind Control", "Energy Surge", "Vortex Portal"]}}

###################
#    Relations    #
###################
war_declaration_timer = 144
min_relation_time = 26

###################
#    Battle       #
###################
shield_absorb = 1300
sats_attack = 110
sats_defence = 450

###################
#    news         #
###################
news_show = 288

# tag points

tag_points_names =[
"Player",
"Veteran",
"Chicken-soup-machine Repairman",
"3rd Technician",
"2nd Technician",
"1st Technician",
"Helmsman",
"Master-at-Arms",
"3rd Officer",
"2nd Officer",
"1st Officer",
"Patrol Officer",
"Squad Lieutenant",
"Lieutenant Commander",
"Wing Commander",
"Cruiser Captain",
"Squadron Commander",
"Fleet Admiral",
"Elite Strategist",
"Dear Leader",
"Master Wizard",
"Transcend",
"(personalized tag)",
]

tag_points_numbers =[
45,
80,
160,
240,
380,
460,
600,
850,
1150,
1320,
1700,
2250,
2600,
3100,
3500,
3900,
4600,
5800,
7000,
9000,
12500,
0xFFFFFFF
]

###################
#   op stuff      #
###################

all_spells = ["Irradiate Ectrolium",
              "Dark Web",
              "Incandescence",
              "Black Mist",
              "War Illusions",
              "Psychic Assault",
              "Phantoms",
              "Enlightenment",
              "Grow Planet's Size",
              "Alchemist"]

# tech, readiness, difficulty, self-spell
psychicop_specs = {
    "Irradiate Ectrolium": [0, 12, 1.5, False, 'IE',
                            "Your psychics will attempt to irradiate the target's ectrolium reserves, making it unusable.", ],
    "Incandescence": [0, 30, 2.5, True, 'IN',
                      "Your psychics will convert crystal into vast amounts of energy."],
    "Dark Web": [10, 18, 2.4, True, 'DW',
                 "Creating a thick dark web spreading in space around your planets will make them much harder to locate and attack."],
    "Black Mist": [50, 24, 3.0, False, 'BM',
                   "Creating a dense black mist around the target's planets will greatly reduce the effectiveness of solar collectors."],
    "War Illusions": [70, 30, 4.0, True, 'WI',
                      "These illusions will help keeping enemy fire away from friendly units."],
    "Psychic Assault": [90, 35, 1.7, False, 'PA',
                        "Your psychics will engage the targeted faction's psychics, to cause large casualities."],
    "Phantoms": [110, 40, 5.0, True, 'PM',
                 "Your psychics will create etheral creatures to join your fleets in battle."],
    "Grow Planet's Size": [110, 20, 2.5, True, 'GP',
                           "Your psychics will try to create new land on one of the planets of your empire. The more planets and psychic power you have, the better are the chances."],
    "Enlightenment": [120, 35, 1.0, True, 'EN',
                      "Philosophers and scientists will try to bring a golden Age of Enlightenment upon your empire."],
    "Alchemist": [0, 30, 2.5, True, 'AL',
                      "Your psychics will convert energy into vast amounts of resources."],
}

all_operations = ["Spy Target",
                "Observe Planet",
                "Network Infiltration",
                "Infiltration",
                "Diplomatic Espionage",
                "Bio Infection",
                "Hack mainframe",
                "Military Sabotage",
                "Planetary Beacon",
                "Bribe officials",
                "Nuke Planet",
                "Maps theft",
                "High Infiltration",
                "Steal Resources",
                ]

# tech, readiness, difficulty, stealth
agentop_specs = {
    "Spy Target": [0, 12, 1.5, True, 'ST',
                            "Spy target will reveal information regarding an faction resources and readiness.", ],
    "Observe Planet": [0, 5, 1.0, True, 'OP',
                      "Your agents will observe the planet and provide you with all information regarding it, habited or not."],
    "Network Infiltration": [25, 22, 4.5, False, 'NW',
                 "Your agents will try to infiltrate research network in order to steal new technologies."],
    "Infiltration": [40, 18, 2.5, True, 'IF',
                   "Infiltrating the target network will provide you with information regarding its resources, research and buildings."],
    "Diplomatic Espionage": [40, 15, 1.5, True, 'DE',
                             "Your diplomats will try to gather information regarding operations and spells, currently affecting the target faction."],
    "Bio Infection": [60, 25, 3.0, False, 'BI',
                      "Your agents will attempt to spread a dangerous infection which will kill most of the population and spread in nearby planets."],
    "Hack mainframe": [80, 22, 4.5, False, 'HM',
                        "Your agents will infiltrate the enemy energy storage facilities and temporarily divert income to your empire."],
    "Military Sabotage": [100, 30, 4.0, False, 'MS',
                 "Your agents will attempt to reach the enemy fleet and destroy military units."],
    "Planetary Beacon": [100, 7, 1.0, False, 'PB',
                         "Your agents will attempt to place a beacon on target planet, if successful it will remove any dark webs present."],
    "Nuke Planet": [120, 30, 2.5, False, 'NP',
                           "Your agents will place powerful nuclear devices on the surface of the planet, destroying all buildings and units, leaving in uninhabited."],
    "Bribe officials": [140, 60, 3.5, False, 'BO',
                        "Your spies will try to bribe officials of target faction causing great inneficiencies!"],
    "Maps theft": [140, 40, 4.5, False, 'MT',
                   "Your agents will try to steal the maps of the enemie's territory!"],
    "High Infiltration": [140, 40, 5.0, False, 'HI',
                      "Performing this operation will provide you with detailled information about an faction for several weeks."],
    "Steal Resources": [60, 24, 3.0, False, 'SR',
                      "Your Agents will attempt to steal resources!"],
}

all_incantations = ["Survey System",
                    "Sense Artefact", 
                    "Planetary Shielding", 
                    "Portal Force Field", 
                    "Mind Control", 
                    "Vortex Portal", 
                    "Call to Arms", 
                    "Energy Surge"]

inca_specs= {"Survey System": [40, 20, 1, True, 'SS', "Your Ghost Ships will try and reveal information of all the planets in the system!"], 
    "Sense Artefact": [80, 20, 3, False, 'FA', "Your Ghost Ships will attempt to reveal the location of nearby Artefacts!"], 
    "Call to Arms": [30, 30, 1, False, 'CA', "Your Ghost Ships will recruit population into your forces!"],
    "Planetary Shielding": [60, 30, 2, False, 'PS', "Your Ghost Ships will attempt to create a shield around the planet!"], 
    "Portal Force Field": [80, 30, 1.5, False, 'PF', "Your Ghost Ships will attempt to create a Force Field, drastically reducing the Portals capability!"], 
    "Vortex Portal": [100, 60, 1, True, 'VP', "Your Ghost Ships will attempt to create a temporary portal!"], 
    "Mind Control": [120, 40, 5, True, 'MC', "Your Ghost Ships will attempt to take control of the planet!"], 
    "Energy Surge": [140, 80, 6, False, 'ES', "Your Ghost Ships will attempt a surge throughout the enemies empire, destroying infrastructure, reserves and research!"], 
    
}