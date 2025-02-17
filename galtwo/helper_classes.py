import numpy as np
from app.constants import *
from .models import *
from .calculations import *


# Class used to represent resources in different ways
class ResourceSet:
    def __init__(self, *args):
        if len(args) == 0:
            self.ene = 0
            self.min = 0
            self.cry = 0
            self.ect = 0
            self.time = 0
        elif len(args) == 1: # used to convert a list of resources to this object
            self.ene = args[0][0]
            self.min = args[0][1]
            self.cry = args[0][2]
            self.ect = args[0][3]
            self.time = args[0][4]
        elif len(args) == 4: # pass in all four at init
            self.ene = args[0]
            self.min = args[1]
            self.cry = args[2]
            self.ect = args[3]
        elif len(args) == 5: # pass in all four plus time at init
            self.ene = args[0]
            self.min = args[1]
            self.cry = args[2]
            self.ect = args[3]
            self.time = args[4]
        else:
            print("INVALID ARGS")

    def is_enough(self, status): # designed to take in a status object and check if player has enough resources
        if (status.energy >= self.ene) and (status.minerals >= self.min) and (status.crystals >= self.cry) and (status.ectrolium >= self.ect):
            return True
        else:
            return False

    def apply_overbuild(self, overbuild):
        self.ene = int(np.ceil(overbuild * self.ene))
        self.min = int(np.ceil(overbuild * self.min))
        self.cry = int(np.ceil(overbuild * self.cry))
        self.ect = int(np.ceil(overbuild * self.ect))





# These classes below aren't designed to make multiples of, i.e. if you want to
# build 5 Solar Collectors you don't actually create 5 of the SolarCollector class,
# actually creating buildings is done through the construction related models in models.py
# These classes are just used to store equations and other conviences

class Building:
    def __init__(self):
        # self.building_index must be defined in child object, it points to the spot in building_costs (constants.py) with the cost data
        self.costs = building_costs[self.building_index]
        self.required_building_tech = required_building_tech[self.building_index]

    # Calc cost of N buildings, from cmdGetBuildCosts() in cmd.c
    def calc_costs(self, num_buildings, research_construction, research_tech, status):
        multiplier = 100.0 / (100.0 + research_construction)
        tech_penalty = self.required_building_tech - research_tech;
        #buffer[CMD_RESSOURCE_NUMUSED+1] = 0;
        #//Change build time depending on arti
        if tech_penalty > 0:
            penalty = tech_penalty**1.1
            if (penalty) >= 100:
                return None, None # cannot build due to tech being too low
            multiplier *= 1.0 + 0.01*(penalty)
        else:
            penalty = 0
        final_costs = []
        for i in range(4): # 4 types of resources
            final_costs.append(num_buildings * int(np.ceil(multiplier * self.costs[i])))
        final_costs.append(int(np.ceil(multiplier * self.costs[4]))) # Time doesn't get num_buildings multiplied by it
        penalty = np.round(penalty,2)

        # bribe officials operation modifier
        if Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                  extra_effect="resource_cost").exists():
            bribe = Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                           extra_effect="resource_cost")
            for br in bribe:
                for c in range(0, len(final_costs) - 1):
                    final_costs[c] *= 1 + br.specop_strength / 100

        if Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                  extra_effect="building_time").exists():
            bribe = Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                           extra_effect="building_time")
            for br in bribe:
                final_costs[len(final_costs) - 1] *= 1 + br.specop_strength / 100


        return final_costs, penalty # final_costs is a list of 5 ints, and pentaly is a float rounded to 2 decimal places

class SolarCollector(Building):
    def __init__(self):
        self.building_index = 0
        self.label = "Solar Collectors"
        self.short_label = 'SC'
        self.model_name = 'solar_collectors' # based on field of planet
        super().__init__() # calls parent class constructor

class FissionReactor(Building):
    def __init__(self):
        self.building_index = 1
        self.label = "Fission Reactors"
        self.short_label = 'FR'
        self.model_name = 'fission_reactors'
        super().__init__()

class MineralPlant(Building):
    def __init__(self):
        self.building_index = 2
        self.label = "Mineral Plants"
        self.short_label = 'MP'
        self.model_name = 'mineral_plants'
        super().__init__()

class CrystalLab(Building):
    def __init__(self):
        self.building_index = 3
        self.label = "Crystal Laboratories"
        self.short_label = 'CL'
        self.model_name = 'crystal_labs'
        super().__init__()

class RefinementStation(Building):
    def __init__(self):
        self.building_index = 4
        self.label = "Refinement Stations"
        self.short_label = 'RS'
        self.model_name = 'refinement_stations'
        super().__init__()

class Citie(Building):
    def __init__(self):
        self.building_index = 5
        self.label = "Cities"
        self.short_label = 'CT'
        self.model_name = 'cities'
        super().__init__()

class ResearchCenter(Building):
    def __init__(self):
        self.building_index = 6
        self.label = "Research Centers"
        self.short_label = 'RC'
        self.model_name = 'research_centers'
        super().__init__()

class DefenseSat(Building):
    def __init__(self):
        self.building_index = 7
        self.label = "Defense Satellites"
        self.short_label = 'DS'
        self.model_name = 'defense_sats'
        super().__init__()

class ShieldNetwork(Building):
    def __init__(self):
        self.building_index = 8
        self.label = "Shield Network"
        self.short_label = 'SN'
        self.model_name = 'shield_networks'
        super().__init__()

class Portals(Building):
    def __init__(self):
        self.building_index = 9
        self.label = "Portal"
        self.short_label = 'PL'
        self.model_name = 'portals' # since it ends up getting used for total_portals
        super().__init__()


def raze_all_buildings2(planet, status):
    building_list = [SolarCollector(), FissionReactor(), MineralPlant(), CrystalLab(), RefinementStation(),
                     Citie(), ResearchCenter(), DefenseSat(), ShieldNetwork()]
    for building in building_list:
        num_on_planet = getattr(planet, building.model_name)
        if num_on_planet > 0:
            setattr(planet, building.model_name, 0)
            setattr(status, 'total_' + building.model_name,
                    getattr(status, 'total_' + building.model_name) - num_on_planet)
            setattr(status, 'total_buildings', getattr(status, 'total_buildings') - num_on_planet)
    setattr(planet, 'total_buildings', 0)
    # Portal
    if planet.portal:
        planet.portal = False
        setattr(status, 'total_portals', getattr(status, 'total_portals') - 1)
        setattr(status, 'total_buildings', getattr(status, 'total_buildings') - 1)
    # Any time we change buildings we need to update planet's overbuild factor
    planet.overbuilt = calc_overbuild(planet.size, planet.total_buildings + planet.buildings_under_construction)
    planet.overbuilt_percent = (planet.overbuilt - 1.0) * 100
    planet.save()
    status.save()