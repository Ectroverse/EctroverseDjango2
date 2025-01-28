from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.calculations import *
from app.constants import *
from app.round_functions import *
import time
import matplotlib.pyplot as plt
import random
from app.map_settings import *
from django.db import transaction
from galtwo.models import HallOfFame as Fame
import requests 
from discord import SyncWebhook
from django.core.mail import send_mail

def random_combination(iterable, r):
    pool = tuple(iterable)
    n = len(pool)
    indices = sorted(random.sample(range(n), r))
    return tuple(pool[i] for i in indices)


def fill_system(x,y):
    system = System.objects.filter(x=x, y=y).first()
    if system is None:
        planet_buffer_fill = []
        planets_in_system = np.random.randint(1,9) # max of 8 planets per system with the way we are visualizing it
        positions = random_combination(range(8), planets_in_system)
        
        sid = np.random.randint(1,5)
        if sid == 1:
            simg = "/static/map/s1.png"
        if sid == 2:
            simg = "/static/map/s2.png"
        if sid == 3:
            simg = "/static/map/s3.png"
        if sid == 4:
            simg = "/static/map/s4.png"
        if sid == 5:
            simg = "/static/map/s5.png"
        
        system = System.objects.create(x=x, y=y, img=simg)
        
        bonus = random.choices(["SL","MN","CR","EC","NO"],[25,20,15,10,30])
        
        for i in range(planets_in_system):
            bonus_sl = 0
            bonus_mn = 0
            bonus_cr = 0
            bonus_ec = 0
            size = planet_size_distribution()
            b = np.random.randint(1,3)
            if b == 1:
                if bonus == ['SL']:
                    bonus_sl = np.random.randint(10,101)
                elif bonus == ['MN']:
                    bonus_mn = np.random.randint(10,101)
                elif bonus == ['CR']:
                    bonus_cr = np.random.randint(10,101)
                elif bonus == ['EC']:
                    bonus_ec = np.random.randint(10,101)
            planet_buffer_fill.append(Planet(home_planet=False,
                                             x=x,
                                             y=y,
                                             i=i,
                                             system=system,
                                             pos_in_system=positions[i],
                                             current_population=size*20,
                                             max_population=size*200,
                                             bonus_solar=bonus_sl,
                                             bonus_mineral=bonus_mn,
                                             bonus_crystal=bonus_cr,
                                             bonus_ectrolium=bonus_ec,
                                             size=size)) # create is the same as new() and add()
        
        return planet_buffer_fill


class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        game_round = RoundStatus.objects.filter().first()
        # record data for hall of fame
        for status in UserStatus.objects.all():
            if status.empire is not None:
                artis = Artefacts.objects.filter(empire_holding=status.empire).count()
                HallOfFame.objects.create(round=game_round.round_number,
                                          userid=status.id,
                                          user=status.user_name,
                                          empire=status.empire.name_with_id,
                                          artefacts=artis,
                                          planets=status.num_planets,
                                          networth=status.networth,
                                          race=status.get_race_display())
                tags = status.num_planets
                t_artis = Artefacts.objects.filter(effect3=1).count()
                if artis == t_artis:
                    tags *= 3
                status.tag_points += tags
                status.save()

        start_t = time.time()
        Planet.objects.all().delete() # remove all planets
        Relations.objects.all().delete()
        News.objects.all().delete()
        Construction.objects.all().delete()
        Fleet.objects.all().delete()
        UnitConstruction.objects.all().delete()
        Messages.objects.all().delete()
        MapSettings.objects.all().delete()
        Scouting.objects.all().delete()
        Specops.objects.all().delete()
        System.objects.all().delete()
        Sensing.objects.all().delete()
        Empire.objects.all().delete()  # remove all empires -remove after players
        Ticks_log.objects.all().delete()
        planet_buffer = [] # MUCH quicker to save them all at once, like 100x faster
        empires_buffer = []
        game_round = RoundStatus.objects.filter().first()
        game_round.galaxy_size = map_size
        game_round.tick_number = 0
        game_round.is_running = False
        #game_round.round_number += 1
        game_round.artetimer = 144
        game_round.artedelay = 5
        game_round.save()

        # We also need to purge all the non-needed info of players, without actualy deleting them!
        theta = 0
        systies = []
        for j in range(num_homes):
            home_x = round(distance*np.sin(theta) + map_size/2)
            home_y = round(distance*np.cos(theta) + map_size/2)
            theta += 2*np.pi/num_homes
            empires_buffer.append(Empire(number=j,
                                         x=home_x,
                                         y=home_y,
                                         name="Empire",
                                         name_with_id="Empire #" + str(j),
                                         pm_message="Welcome to empire #" + str(j)

            ))
            for i in range(players_per_empire): # max 8 players per empire/system
                size = 450
                planet_buffer.append(Planet(home_planet=True,
                                            x=home_x,
                                            y=home_y,
                                            i=i,
                                            pos_in_system=i,
                                            current_population=size*population_base_factor,
                                            max_population=size*population_size_factor,
                                            total_buildings=200,
                                            size=size)) # create is the same as new() and add()
                                            
                if i == 0:
                    sid = np.random.randint(1,5)
                    if sid == 1:
                        simg = "/static/map/s1.png"
                    if sid == 2:
                        simg = "/static/map/s2.png"
                    if sid == 3:
                        simg = "/static/map/s3.png"
                    if sid == 4:
                        simg = "/static/map/s4.png"
                    if sid == 5:
                        simg = "/static/map/s5.png"
                    System.objects.create(x=home_x, y=home_y, home=True, img=simg)


            # Now add N systems in a small area around the home system
            N = 12
            d_from_home = 5
            history = []
            while len(history) < N:
                x = np.random.randint(-1*d_from_home, d_from_home+1) + home_x
                y = np.random.randint(-1*d_from_home, d_from_home+1) + home_y
                if x + y != home_x + home_y:
                    if (x,y) not in history:
                        history.append((x,y))
                        systies.append((x,y))
                        planet_buffer.extend(fill_system(x,y))

        # Main core in the center
        for x in range(map_size):
            for y in range(map_size):
                d_to_center = max(0, map_size*0.4 - np.sqrt((x-map_size/2)**2 + (y-map_size/2)**2))/(map_size*0.4) # between 0 and 1, higher is closer to center
                density = 0.6 # between 0 and 1
                roll_off_factor = 1.1 # higher means more planets clustered in the middle
                if (np.random.rand() < d_to_center**roll_off_factor) and (np.random.rand() < density) and (x,y) not in systies: # higher density towards center of map, everyone starts towards the perimeter
                    systies.append((x,y))
                    try:
                        planet_buffer.extend(fill_system(x,y))
                    except:
                        pass

        start_tt = time.time()
        Planet.objects.bulk_create(planet_buffer)
        Empire.objects.bulk_create(empires_buffer)
        print("Saving planets to db took this many seconds", time.time() - start_tt)

        # reset round user data
        for status in UserStatus.objects.all():
            Fleet.objects.create(owner=status.user, main_fleet=True)

            status.user_name = ""
            
            status.fleet_readiness = 100
            status.psychic_readiness = 100
            status.agent_readiness = 100
            status.fleet_readiness_max = 100
            status.psychic_readiness_max = 100
            status.agent_readiness_max = 100

            status.long_range_attack_percent = 200
            status.air_vs_air_percent = 200
            status.ground_vs_air_percent = 200
            status.ground_vs_ground_percent = 200

            status.post_attack_order = 2

            # Loop through user's planets, lines 499 - 608 in cmdtick.c
            
            status.population = '9000'  # clear user's population
            status.num_planets = 1
            status.total_solar_collectors = 100
            status.total_fission_reactors = 0
            status.total_mineral_plants = 50
            status.total_crystal_labs = 25
            status.total_refinement_stations = 25
            status.total_cities = 0
            status.total_research_centers = 0
            status.total_defense_sats = 0
            status.total_shield_networks = 0
            status.total_portals = 0

            status.total_buildings = '201'

            status.research_points_military = '0'
            status.research_points_construction = '0'
            status.research_points_tech = '0'
            status.research_points_energy = '0'
            status.research_points_population = '0'
            status.research_points_culture = '0'
            status.research_points_operations = '0'
            status.research_points_portals = '0'

            status.current_research_funding = '0'

            status.research_percent_military = '0'
            status.research_percent_construction = '0'
            status.research_percent_tech = '0'
            status.research_percent_energy = '0'
            status.research_percent_population = '0'
            status.research_percent_culture = '0'
            status.research_percent_operations = '0'
            status.research_percent_portals = '0'

            status.alloc_research_military = '12'
            status.alloc_research_construction = '16'
            status.alloc_research_tech = '12'
            status.alloc_research_energy = '12'
            status.alloc_research_population = '12'
            status.alloc_research_culture = '12'
            status.alloc_research_operations = '12'
            status.alloc_research_portals = '12'

            status.energy_production = '0'
            status.energy_decay = '0'
            status.buildings_upkeep = '0'
            status.units_upkeep = '0'
            status.population_upkeep_reduction = '0'
            status.portals_upkeep = '0'
            status.population_upkeep_reduction = '0'

            status.crystal_production = '0'
            status.crystal_decay = '0'
            status.mineral_production = '0'
            status.ectrolium_production = '0'

            status.energy_income = '0'
            status.energy_specop_effect = '0'
            status.mineral_income = '0'
            status.crystal_income = '0'
            status.ectrolium_income = '0'

            status.energy_interest = '0'
            status.mineral_interest = '0'
            status.crystal_interest = '0'
            status.ectrolium_interest = '0'
            status.energy = '120000'
            status.minerals = '10000'
            status.crystals = '5000'
            status.ectrolium = '5000'

            status.networth = '1250'

            status.empire_role = ''
            status.votes = 0

            status.mail_flag = 0
            status.construction_flag = 0
            status.economy_flag = 0
            status.military_flag = 0
            
            if status.id == 1:
                aemp = Empire.objects.get(number=0)
                aemp.numplayers = 1
                aemp.planets = 1
                aemp.networth = 1250
                aemp.password = 123456
                aemp.save()
                ahp = Planet.objects.get(x=aemp.x, y =aemp.y, i=0)
                ahp.owner = status.user
                ahp.current_population = 9000
                ahp.max_population = 90000
                ahp.solar_collectors = 100
                ahp.mineral_plants = 50
                ahp.refinement_stations = 25
                ahp.crystal_labs = 25
                ahp.portal = True
                ahp.save()
                status.home_planet = ahp
                status.race = 'FH'
                status.user_name = "Admin"
                status.num_planets = 1
                status.empire = aemp
                status.empire_role = 'PM'
            
            status.save()

        settings()
        artifacts()
        game_round.round_start = datetime(2024, 12, 30, 18, 00, 00)
        game_round.save()
        msg = "Regular Round has been reset, starting 30th December at 6PM UTC, ending 30th January at 6PM UTC. No artefacts, most planets wins."
        NewsFeed.objects.create(date_and_time = datetime.now(), message = msg)
        dmsg = "<@&1201666532753547315> " + str(msg)

        print("Generating planets and resetting users took " + str(time.time() - start_t) + "seconds")

