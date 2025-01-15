from .models import *
import numpy as np
import miniball
from collections import defaultdict
from .map_settings import *
from .specops import perform_operation, perform_incantation
from datetime import datetime
from datetime import timedelta
from django.template import RequestContext
from .helper_classes import *
from .calculations import *
import random


def give_first_planet(user, status, planet):
    planet.solar_collectors = staring_solars
    planet.mineral_plants = starting_meral_planets
    planet.refinement_stations = starting_ectrolium_refs
    planet.crystal_labs = starting_crystal_labs
    planet.cities = starting_cities
    planet.current_population = 9000
    planet.max_population = 90000
    planet.portal = True
    planet.owner = user
    planet.save()
    status.networth = 1250
    status.total_solar_collectors = staring_solars
    status.total_mineral_plants = starting_meral_planets
    status.total_refinement_stations = starting_ectrolium_refs
    status.total_crystal_labs = starting_crystal_labs
    status.total_cities = starting_cities
    status.total_portals = 1
    status.total_buildings = 201
    status.home_planet = planet
    status.num_planets = 1
    if players_per_empire == 1:
        status.empire_role = 'PM'
    status.save()
    Scouting.objects.create(user=status.user, planet=planet, scout=1.0, empire=status.empire)
    MapSettings.objects.create(user=status.user, map_setting="YP", color_settings="B")
    MapSettings.objects.create(user=status.user, map_setting="YR", color_settings="Y")
    MapSettings.objects.create(user=status.user, map_setting="UE", color_settings="G")
    MapSettings.objects.create(user=status.user, map_setting="SS", color_settings="W")
    MapSettings.objects.create(user=status.user, map_setting="SC", color_settings="W")

def give_first_fleet(main_fleet):
    for i,unit in enumerate(unit_info["unit_list"]):
        print(i, unit, len(starting_fleet))
        setattr(main_fleet, unit, starting_fleet[i])
    main_fleet.save()

def find_nearest_portal(x, y, portal_list, status):
    if Specops.objects.filter(user_to=status.user, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=status.user, name='Vortex Portal'):
            vort_por = Planets.objects.filter(id=vort.planet.id)
            portal_list = portal_list | vort_por
    min_dist = (portal_list[0].x- x)**2+ (portal_list[0].y -y)**2;
    portal = portal_list[0]
    for p in portal_list:
        dist = (p.x-x)**2 + (p.y-y)**2
        print(p.x,p.y, dist)
        if dist < min_dist:
            min_dist = dist
            portal = p
    return portal

# use this function to find the minimum max distance from all systems to
def find_bounding_circle(systems):
    S = np.array(systems)
    # The algorithm implemented is Welzl’s algorithm. It is a pure Python implementation,
    # it is not a binding of the popular C++ package Bernd Gaertner’s miniball.
    # The algorithm, although often presented in its recursive form, is here implemented in an iterative fashion.
    # Python have an hard-coded recursion limit, therefore a recursive implementation of Welzl’s
    # algorithm would have an artificially limited number of point it could process.
    C, r2 = miniball.get_bounding_ball(S)
    return C

def travel_speed(status):
    speed = race_info_list[status.get_race_display()]["travel_speed"]
    speed_boost_enlightement = 1
    if Specops.objects.filter(user_to=status.user, name="Enlightenment", extra_effect="Speed"):
        en = Specops.objects.get(user_to=status.user, name="Enlightenment", extra_effect="Speed")
        speed_boost_enlightement = (1 + en.specop_strength / 100)
    speed *= speed_boost_enlightement
    bhole_art = Artefacts.objects.get(name="Blackhole")
    if bhole_art.empire_holding == status.empire:
        speed *= 1.6
    return speed

# option value="0" Attack the planet
# option value="1" Station on planet
# option value="2" Move to system
# option value="3" Merge in system (chose system yourself)
# option value="4" Merge in system (auto/optimal)
# option value="5" Join main fleet
def generate_fleet_order(fleet, target_x, target_y, speed, order_type, *args):
    # args[0] - planet number
    print(fleet)
    print(order_type)
    print(target_x)
    print(target_y)
    fleet.x = target_x
    fleet.y = target_y
    if args:
        fleet.i = args[0]
        planet = Planets.objects.filter(x=target_x, y=target_y, i=args[0]).first()
        if planet is not None:
            fleet.target_planet = planet
        # print(fleet.current_position_x,fleet.current_position_y)
    else:
        planet = Planets.objects.filter(x=target_x, y=target_y, i=0).first()
        if planet is not None:
            fleet.target_planet = planet
    min_dist = np.sqrt((fleet.current_position_x - float(target_x)) ** 2 +
                       (fleet.current_position_y - float(target_y)) ** 2)
    speed_boost_enlightement = 1
    if Specops.objects.filter(user_to=fleet.owner, name="Enlightenment", extra_effect="Speed").exists():
        en = Specops.objects.get(user_to=fleet.owner, name="Enlightenment", extra_effect="Speed")
        speed_boost_enlightement = (1 + en.specop_strength / 100)
    speed *= speed_boost_enlightement
    fleet.ticks_remaining = max(0,int(np.floor(min_dist / speed)))
    fleet.command_order = order_type
    fleet.save()

def merge_fleets(fleets):
    fleet1 = None
    d = defaultdict(list)
    for fl in fleets:
        coords = 'x' + str(fl.x) + 'y' + str(fl.y)
        d[coords].append(fl)
    for coord,fleet in d.items():
        fleet1 = fleet[0]
        for i in range(1,len(fleet)):
            for unit in unit_info["unit_list"]:
                setattr(fleet1, unit, getattr(fleet1, unit) + getattr(fleet[i], unit))
            fleets[i].delete()
        fleet1.save()
    return fleet1

def station_fleets(request, fleets, status):
    stationed_fleets = Fleet.objects.filter(owner=status.id,command_order=1,ticks_remaining=0)
    sf_dict = {}
    for f in stationed_fleets:
        if f.on_planet is not None:
            sf_dict[f.on_planet.id] = f

    for f in fleets:
        planet = Planets.objects.filter(x=f.x, y=f.y, i=f.i).first()
        msg = ""
        fleet_units = ""
        for u in unit_info["unit_list"]:
            if getattr(f, u) > 0:
                fleet_units += str(unit_info[u]['label']) + ": " + str(getattr(f, u)) + " "

        if planet is None:
            f.command_order = 2
            f.save()
            msg = "could not station because it doesn't exist!"
            request.session['error'] = "Could not station on " \
                                       + str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) \
                                       + " because the planet doesnt exist!"
            news_type = 'FU'
        elif planet.owner is None or planet.owner.id != status.id:
            f.command_order = 2
            f.save()
            msg = "could not station because you do not own it!"
            request.session['error'] = "Could not station on " \
                                       + str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) \
                                        + " because you do not own the planet!"
            news_type = 'FU'
        elif planet.id in sf_dict:
            stationed_fleet = sf_dict[planet.id]
            for unit in unit_info["unit_list"]:
                setattr(stationed_fleet, unit, getattr(stationed_fleet, unit))
            stationed_fleet.command_order=8
            f.delete()
            stationed_fleet.save()
            news_type = 'FS'
            msg = "successfully merged with the other fleet allready stationed on planet: " \
                  + str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "!"
        else:
            f.on_planet = planet
            f.command_order = 8
            f.save()
            sf_dict[planet.id] = f
            news_type = 'FS'
            msg = "successfully stationed on planet: " \
                  + str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "!"

        News.objects.create(user1=User.objects.get(id=status.id),
                            empire1=status.empire,
                            fleet1=fleet_units,
                            planet=planet,
                            news_type=news_type,
                            date_and_time=datetime.now() + timedelta(seconds=1),
                            is_read=False,
                            is_personal_news=True,
                            is_empire_news=False,
                            tick_number=RoundStatus.objects.get().tick_number,
                            extra_info=msg
                            )



def join_main_fleet(main_fleet, fleets):
    for fl in fleets:
        for unit in unit_info["unit_list"]:
            setattr(main_fleet, unit, getattr(main_fleet, unit) + getattr(fl, unit))
        fl.delete()
    main_fleet.save()

def join_bot_fleet(main_fleet, fl):
    for unit in unit_info["unit_list"]:
        setattr(main_fleet, unit, getattr(main_fleet, unit) + getattr(fl, unit))
    fl.delete()
    main_fleet.save()

def split_fleets(fleets, split_pct):
    for fl in fleets:
        fl2 = {}
        total_fl2 = 0
        for i, unit in enumerate(unit_info["unit_list"]):
            unit_num = int(getattr(fl, unit)*split_pct/100)
            fl2[unit] = unit_num
            setattr(fl, unit, getattr(fl, unit) - unit_num)
            total_fl2 += unit_num
            fl.save()
        if total_fl2 > 0:
            Fleet.objects.create(owner=fl.owner,
                                 command_order=fl.command_order,
                                 x=fl.x,
                                 y=fl.y,
                                 i=fl.i,
                                 ticks_remaining=fl.ticks_remaining,
                                 current_position_x=fl.current_position_x,
                                 current_position_y=fl.current_position_y,
                                 **fl2)


def explore_planets(fleets):
    for fl in fleets:
        status = UserStatus.objects.get(user=fl.owner)
        try:
            planet = Planets.objects.get(x=fl.x, y=fl.y, i=fl.i)
        except Planet.DoesNotExist:
            planet = None
        if planet:
            if not planet.home_planet and planet.owner == None:
                planet.owner = fl.owner
                fl.delete()
                # arti
                if planet.artefact is not None:
                    planet.artefact.empire_holding = status.empire
                    planet.artefact.save()
                planet.save()
                status.military_flag = 1;
                News.objects.create(user1 = fl.owner,
                                    empire1 = status.empire,
                                    news_type = 'SE',
                                    date_and_time=datetime.now(),
                                    is_personal_news=True,
                                    is_empire_news=True,
                                    tick_number = RoundStatus.objects.get().tick_number,
                                    planet = planet)
                if not Scouting.objects.filter(user=status.user, planet = planet).exists():
                    Scouting.objects.create(user= fl.owner,
                                            planet = planet,
                                            scout = '1', empire=status.empire)
                else:
                    scout = Scouting.objects.get(user=status.user, planet = planet)
                    scout.scout = 1
                    scout.save()
                    
            else:
                fl.command_order = 2
                fl.save()
                status.military_flag = 2;
                status.save()
                News.objects.create(user1 = fl.owner,
                                    empire1 = status.empire,
                                    news_type = 'UE',
                                    date_and_time=datetime.now(),
                                    is_personal_news = True,
                                    is_empire_news = True,
                                    tick_number = RoundStatus.objects.get().tick_number,
                                    planet = planet)


def calc_exploration_cost(status):
    expo_ship_nr = Fleet.objects.filter(owner = status.user, main_fleet = False, exploration = 1).count()
    pl_number = Planets.objects.filter(owner = status.user).count()
    exp_cost = (pl_number + expo_ship_nr + 40) >> 2
    art = Artefacts.objects.get(name="Genghis Effect")
    if status.empire == art.empire_holding:
        exp_cost *= round(0.75)
    return exp_cost


def get_userstatus_from_id_or_name(d):
    try:
        detail = int(d)
    except ValueError:
        detail = str(d)

    faction_setting = None
    err_msg = ""

    if isinstance(detail, int):
        if UserStatus.objects.filter(id=detail).first() is None:
            err_msg += "The faction id " + str(detail) + " doesn't exist!"
        else:
            faction_setting = UserStatus.objects.filter(id=detail).first()
    else:
        if UserStatus.objects.filter(user_name=detail).first() is None:
            err_msg += "The faction name " + str(detail) + " doesn't exist!"
        else:
            faction_setting = UserStatus.objects.filter(user_name=detail).first()

    return faction_setting, err_msg


def send_agents_ghosts(status, agents, ghost, x, y, i, specop):
    x = int(x)
    y = int(y)
    i = int(i)

    planet = Planets.objects.filter(x=x, y=y, i=i).first()
    if planet is None:
        return "This planet doesn't exist!"
    portal_planets = Planets.objects.filter(owner=status.user, portal=True)
    if not portal_planets:
        return "You need at least one portal to send the fleet from!"
    best_portal_planet = find_nearest_portal(x, y, portal_planets, status)
    min_dist = np.sqrt((best_portal_planet.x - x) ** 2 + (best_portal_planet.y - y) ** 2)
    speed = travel_speed(status)
    fleet_time = max(0,int(np.floor(min_dist / speed)))
    agent_fleet = Fleet.objects.create(owner=status.user,
                         command_order=6,
                         target_planet=planet,
                         x=x,
                         y=y,
                         i=i,
                         ticks_remaining=fleet_time,
                         current_position_x=best_portal_planet.x,
                         current_position_y=best_portal_planet.y,
                         agent=agents,
                         specop=specop)
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)
    main_fleet.agent -= agents
    main_fleet.save()
    msg = ""
    if fleet_time < 1:
	    if agents > 0:
	        msg = perform_operation(agent_fleet)
	        ignore = ["Observe Planet", "Spy Target"]
            if specop not in ignore:
                main_fleet.agent += agent_fleet.agent
                main_fleet.save()
                agent_fleet.delete()
    return msg
    
def send_ghosts(status, agents, ghost, x, y, i, specop):
    x = int(x)
    y = int(y)
    i = int(i)

    planet = Planets.objects.filter(x=x, y=y, i=i).first()
    if planet is None:
        return "This planet doesn't exist!"
    portal_planets = Planets.objects.filter(owner=status.user, portal=True)
    if not portal_planets:
        return "You need at least one portal to send the fleet from!"
    best_portal_planet = find_nearest_portal(x, y, portal_planets, status)
    min_dist = np.sqrt((best_portal_planet.x - x) ** 2 + (best_portal_planet.y - y) ** 2)
    speed = travel_speed(status)
    fleet_time = max(0,int(np.floor(min_dist / speed)))
    ghost_fleet = Fleet.objects.create(owner=status.user,
                         command_order=7,
                         target_planet=planet,
                         x=x,
                         y=y,
                         i=i,
                         ticks_remaining=fleet_time,
                         current_position_x=best_portal_planet.x,
                         current_position_y=best_portal_planet.y,
                         ghost=ghost,
                         specop=specop)
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)
    main_fleet.ghost -= ghost
    main_fleet.save()
    msg = ""
    if fleet_time < 1:
        if ghost > 0:
            msg = perform_incantation(ghost_fleet)
            if specop != "Call to Arms" and planet.owner.id != status.id:
                ignore = ["Survey System"]
                if specop not in ignore:
                    main_fleet.ghost += ghost_fleet.ghost
                    main_fleet.save()
                    ghost_fleet.delete()
    return msg

def build_on_planet(status, planet, building_list_dict):
    # Make sure its owned by user

    # Create list of building classes, it's making 1 object of each
    building_list = [SolarCollector(), FissionReactor(), MineralPlant(), CrystalLab(), RefinementStation(),
                     Citie(), ResearchCenter(), DefenseSat(), ShieldNetwork(), Portals()]

    # Might be a cleaner way to do it that ties it more directly with the model

    # Following is a rewrite of cmdExecAddBuild in cmd.c, a function that got called for each building type
    list_costs = {"Energy": 0, "Minerals": 0, "Crystals": 0, "Ectrolium": 0}
    list_buildings = {}
    msg = ""

    for building, num in building_list_dict.items():
        list_buildings[planet] = {"number": ""}
        list_buildings[building.label] = {"number": 0}
        if num == 'on':
            num = 1
        if num == '0':
            num = None
        if num:
            num = int(num)
            if num >= 1:
                # calc_building_cost was designed to give the View what it needed, so pull out just the values and multiply by num
                arte = Artefacts.objects.get(name="Advanced Robotics")
                if arte.empire_holding == status.empire:
                    tech = status.research_percent_tech * 2
                else:
                    tech = status.research_percent_tech
                artesn = Artefacts.objects.get(name="Shield Network")
                if artesn.empire_holding == status.empire:
                    if building.building_index == 8:
                        tech = 140
                
                if building.building_index == 9:
                    total_resource_cost, penalty = building.calc_costs(num, status.research_percent_portals, tech,
                                                        status)
                else:
                    total_resource_cost, penalty = building.calc_costs(num, status.research_percent_construction, tech,
                                                status)

                if not total_resource_cost:
                    list_buildings[planet]['number'] += "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nNot enough tech research to build"  + building.label  + "\n"
                    continue
                
                pportal = 0
                if planet.portal:
                    pportal = 1
                    
                total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
                
                total_resource_cost = ResourceSet(total_resource_cost)  # convert to more usable object
                if isinstance(building, Portals) or isinstance(building, DefenseSat) or isinstance(building, ShieldNetwork):
                    ob_factor = 1
                else:
                    ob_factor = calc_overbuild_multi(planet.size,
                                                 total_buildings + planet.buildings_under_construction, num)
                
                total_resource_cost.apply_overbuild(
                    ob_factor)  # can't just use planet.overbuilt, need to take into account how many buildings we are making

                if not total_resource_cost.is_enough(status):
                    list_buildings[planet]['number'] = "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nNot enough resources to build " + building.label +"\n"
                    continue

                if isinstance(building, Portals) and planet.portal:
                    list_buildings[planet]['number'] = "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nA portal is already on this planet! \n"
                    continue

                if isinstance(building, Portals) and planet.portal_under_construction:
                    list_buildings[planet]['number'] = "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nA portal is already under construction on this planet!\n"
                    continue
                
                # Deduct resources
                status.energy -= total_resource_cost.ene
                status.minerals -= total_resource_cost.min
                status.crystals -= total_resource_cost.cry
                status.ectrolium -= total_resource_cost.ect

                ticks = total_resource_cost.time  # calculated ticks

                # Create new construction job
                list_buildings[building.label]['number'] += num
                list_costs['Energy'] += total_resource_cost.ene
                list_costs['Minerals'] += total_resource_cost.min
                list_costs['Crystals'] += total_resource_cost.cry
                list_costs['Ectrolium'] += total_resource_cost.ect

                Construction.objects.create(user=status.user,
                                            planet=planet,
                                            n=num,
                                            building_type=building.short_label,
                                            ticks_remaining=ticks,
                                            energy_cost=total_resource_cost.ene,
                                            mineral_cost=total_resource_cost.min,
                                            crystal_cost=total_resource_cost.cry,
                                            ectrolium_cost=total_resource_cost.ect)
                planet.buildings_under_construction += num
                if building.label == "Portal":
                    planet.portal_under_construction = True
                planet.save()

    # Any time we add buildings we need to update planet's overbuild factor
    pportal = 0
    if planet.portal:
        pportal = 1
        
    total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
    planet.overbuilt = calc_overbuild(planet.size, total_buildings + planet.buildings_under_construction)
    planet.overbuilt_percent = (planet.overbuilt - 1.0) * 100
    planet.save()
    status.save()  # update user's resources

    return list_buildings, list_costs

def color_code(color):
    if color=="R":
        return (255,0,0)
    elif color=="B":
        return (0,0,255)
    elif color=="G":
        return (0,255,0)
    elif color=="O":
        return (255,165,0)
    elif color=="Y":
        return (255,255,0)
    elif color=="I":
        return (75,0,130)
    elif color=="V":
        return (238,130,238)
    elif color=="P":
        return (255,192,203)
    elif color=="W":
        return (255,255,255)
    return (0,0,0)

def clamp(x): 
  return max(0, min(x, 255))

def hex_format(x):
    r,g,b = x
    return "#{0:02x}{1:02x}{2:02x}".format(clamp(r), clamp(g), clamp(b))

def sum_tuple(a,b):
    return tuple(item1 + item2 for item1, item2 in zip(a, b))

def terraformer():
    arte = Artefacts.objects.get(name="Terraformer")    
    choosebonus = random.randint(1,5)
    bonus = random.randint(10,100)
    if arte.empire_holding != None:
        for player in UserStatus.objects.all():
            if player.empire == arte.empire_holding:
                planet = []
                plcount = 0
                pl = Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', bonus_fission = '0', owner=player.id, artefact=None)
                for p in pl:
                    planet.append(p)
                    plcount += 1
                if plcount == 0:
                    if choosebonus == 1:
                        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar__gte=1, owner=player.id, artefact=None))
                    if choosebonus == 2:
                        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_crystal__gte=1, owner=player.id, artefact=None))
                    if choosebonus == 3:
                        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_mineral__gte=1, owner=player.id, artefact=None))
                    if choosebonus == 4:
                        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_ectrolium__gte=1, owner=player.id, artefact=None))
                    if choosebonus == 5:
                        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_fission__gte=1, owner=player.id, artefact=None))
                else:
                    planet = random.choice(planet)
                if choosebonus == 1:
                    planet.bonus_solar += bonus
                    planet.save()
                    news_message = str(bonus) +"% Solar "
                elif choosebonus == 2:
                    planet.bonus_crystal += bonus
                    planet.save()
                    news_message = str(bonus) +"% Crystal "
                elif choosebonus == 3:
                    planet.bonus_mineral += bonus
                    planet.save()
                    news_message = str(bonus) +"% Mineral "
                elif choosebonus == 4:
                    planet.bonus_ectrolium += bonus
                    planet.save()
                    news_message = str(bonus) +"% Ectrolium "
                elif choosebonus == 5:
                    planet.bonus_fission += bonus
                    planet.save()
                    news_message = str(bonus) +"% Fission "
                print(planet)
                News.objects.create(user1=User.objects.get(id=player.id),
                            user2=User.objects.get(id=player.id),
                            empire1=player.empire,
                            fleet1="Terraformer",
                            news_type='TE',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=False,
                            extra_info=news_message,
                            planet=planet,
                            tick_number=RoundStatus.objects.get().tick_number
                            )
        game_tick = RoundStatus.objects.filter().first()
        tick_hour = (60/game_tick.tick_time) * 60
        ticks = random.randint(tick_hour*3, tick_hour*6)
        arte.ticks_left = ticks
        arte.save()
        
def dutchman():
    arte = Artefacts.objects.get(name="Flying Dutchman")     
    if arte.empire_holding != None:
        user = UserStatus.objects.filter(empire=arte.empire_holding).first()
        system = random.choice(System.objects.filter(home=False))
        planets = Planets.objects.filter(x=system.x, y=system.y).order_by("i")
        planet = Planets.objects.get(x=system.x, y=system.y, i=0)
        news_message = "System " + str(system.x) + "," + str(system.y) + " has been scouted by the Flying Dutchman!"
        for p in planets:
            try:
                scouting = Scouting.objects.get(user=user.user, planet=p)
                scouting.scout += 1.0
                scouting.save()
            except:
                Scouting.objects.create(empire = user.empire,
                                    user = user.user,
                                    planet = p,
                                    scout = '1')
            
            
            news_message += "\nPlanet: " + str(p.i)
            if p.owner is not None:
                news_message += "\nOwned by: " + str(p.owner.galtwouser.user_name)
            news_message += "\nPlanet size: " + str(p.size)
            if p.bonus_solar > 0:
                news_message += "\nSolar bonus: " + str(p.bonus_solar)
            if p.bonus_fission > 0:
                news_message += "\nFission bonus: " + str(p.bonus_fission)
            if p.bonus_mineral > 0:
                news_message += "\nMineral bonus: " + str(p.bonus_mineral)
            if p.bonus_crystal > 0:
                news_message += "\nCrystal bonus: " + str(p.bonus_crystal)
            if p.bonus_ectrolium > 0:
                news_message += "\nEctrolium bonus: " + str(p.bonus_ectrolium)
            if p.owner is not None:
                news_message += "\nCurrent population: " + str(p.current_population)
                news_message += "\nMax population: " + str(p.max_population)
                news_message += "\nPortal protection: " + str(p.protection)
                news_message += "\nSolar collectors: " + str(p.solar_collectors)
                news_message += "\nFission Reactors: " + str(p.fission_reactors)
                news_message += "\nMineral Plants: " + str(p.mineral_plants)
                news_message += "\nCrystal Labs: " + str(p.crystal_labs)
                news_message += "\nRefinement Stations: " + str(p.refinement_stations)
                news_message += "\nCities: " + str(p.cities)
                news_message += "\nResearch Centers: " + str(p.research_centers)
                news_message += "\nDefense Sats: " + str(p.defense_sats)
                news_message += "\nShield Networks: " + str(p.shield_networks)
                if p.portal:
                    news_message += "\nPortal: Present"
                elif p.portal_under_construction:
                    news_message += "\nPortal: Under construction"
                else:
                    news_message += "\nPortal: Absent"
            if p.artefact is not None:
                news_message += "\nArtefact: Present, the " + p.artefact.name
                news_message += "\n"
                
        News.objects.create(user1=User.objects.get(id=user.id),
                user2=User.objects.get(id=user.id),
                empire1=user.empire,
                fleet1="Dutchman",
                news_type='DU',
                date_and_time=datetime.now(),
                is_personal_news=True,
                planet = planet,
                is_empire_news=True,
                extra_info=news_message,
                tick_number=RoundStatus.objects.get().tick_number
                )
                        
        game_tick = RoundStatus.objects.filter().first()
        tick_hour = (60/game_tick.tick_time) * 60
        ticks = random.randint(tick_hour*3, tick_hour*6)
        arte.ticks_left = ticks
        arte.save()
    for player in UserStatus.objects.filter(empire=arte.empire_holding):
        planet = []
        plcount = 0
        pl = Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', bonus_fission = '0', owner=player.id, artefact=None)
        for p in pl:
            planet.append(p)
            plcount += 1
        if plcount == 0:
            if choosebonus == 1:
                planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar__gte=1, owner=player.id, artefact=None))
            if choosebonus == 2:
                planet = random.choice(Planets.objects.filter(home_planet=False, bonus_crystal__gte=1, owner=player.id, artefact=None))
            if choosebonus == 3:
                planet = random.choice(Planets.objects.filter(home_planet=False, bonus_mineral__gte=1, owner=player.id, artefact=None))
            if choosebonus == 4:
                planet = random.choice(Planets.objects.filter(home_planet=False, bonus_ectrolium__gte=1, owner=player.id, artefact=None))
            if choosebonus == 5:
                planet = random.choice(Planets.objects.filter(home_planet=False, bonus_fission__gte=1, owner=player.id, artefact=None))
        else:
            planet = random.choice(planet)
        if choosebonus == 1:
            planet.bonus_solar += bonus
            planet.save()
            news_message = str(bonus) +"% Solar "
        elif choosebonus == 2:
            planet.bonus_crystal += bonus
            planet.save()
            news_message = str(bonus) +"% Crystal "
        elif choosebonus == 3:
            planet.bonus_mineral += bonus
            planet.save()
            news_message = str(bonus) +"% Mineral "
        elif choosebonus == 4:
            planet.bonus_ectrolium += bonus
            planet.save()
            news_message = str(bonus) +"% Ectrolium "
        elif choosebonus == 5:
            planet.bonus_fission += bonus
            planet.save()
            news_message = str(bonus) +"% Fission "
        print(planet)
        News.objects.create(user1=User.objects.get(id=player.id),
                    user2=User.objects.get(id=player.id),
                    empire1=player.empire,
                    fleet1="Terraformer",
                    news_type='TE',
                    date_and_time=datetime.now(),
                    is_personal_news=True,
                    is_empire_news=False,
                    extra_info=news_message,
                    planet=planet,
                    tick_number=RoundStatus.objects.get().tick_number
                    )
    game_tick = RoundStatus.objects.filter().first()
    tick_hour = (60/game_tick.tick_time) * 60
    ticks = random.randint(tick_hour*3, tick_hour*6)
    arte.ticks_left = ticks
    arte.save()
        
def dutchman():
    arte = Artefacts.objects.get(name="Flying Dutchman")     
    user = UserStatus.objects.filter(empire=arte.empire_holding).first()
    users = UserStatus.objects.filter(empire=arte.empire_holding)
    system = random.choice(System.objects.filter(home=False))
    planets = Planets.objects.filter(x=system.x, y=system.y).order_by("i")
    planet = Planets.objects.get(x=system.x, y=system.y, i=0)
    news_message = "System " + str(system.x) + "," + str(system.y) + " has been scouted by the Flying Dutchman!"
    for p in planets:
        try:
            scouting = Scouting.objects.get(empire=user.empire, planet=p)
            scouting.scout += 1.0
            scouting.save()
        except:
            Scouting.objects.create(empire = user.empire,
                                user = user.user,
                                planet = p,
                                scout = '1')
        
        
        news_message += "\nPlanet: " + str(p.i)
        if p.owner is not None:
            news_message += "\nOwned by: " + str(p.owner.galtwouser.user_name)
        news_message += "\nPlanet size: " + str(p.size)
        if p.bonus_solar > 0:
            news_message += "\nSolar bonus: " + str(p.bonus_solar)
        if p.bonus_fission > 0:
            news_message += "\nFission bonus: " + str(p.bonus_fission)
        if p.bonus_mineral > 0:
            news_message += "\nMineral bonus: " + str(p.bonus_mineral)
        if p.bonus_crystal > 0:
            news_message += "\nCrystal bonus: " + str(p.bonus_crystal)
        if p.bonus_ectrolium > 0:
            news_message += "\nEctrolium bonus: " + str(p.bonus_ectrolium)
        if p.owner is not None:
            news_message += "\nCurrent population: " + str(p.current_population)
            news_message += "\nMax population: " + str(p.max_population)
            news_message += "\nPortal protection: " + str(p.protection)
            news_message += "\nSolar collectors: " + str(p.solar_collectors)
            news_message += "\nFission Reactors: " + str(p.fission_reactors)
            news_message += "\nMineral Plants: " + str(p.mineral_plants)
            news_message += "\nCrystal Labs: " + str(p.crystal_labs)
            news_message += "\nRefinement Stations: " + str(p.refinement_stations)
            news_message += "\nCities: " + str(p.cities)
            news_message += "\nResearch Centers: " + str(p.research_centers)
            news_message += "\nDefense Sats: " + str(p.defense_sats)
            news_message += "\nShield Networks: " + str(p.shield_networks)
            if p.portal:
                news_message += "\nPortal: Present"
            elif p.portal_under_construction:
                news_message += "\nPortal: Under construction"
            else:
                news_message += "\nPortal: Absent"
        if p.artefact is not None:
            news_message += "\nArtefact: Present, the " + p.artefact.name
            news_message += "\n"
            
    for u in users:
        if u.id == user.id:
            News.objects.create(user1=User.objects.get(id=u.id),
                    user2=User.objects.get(id=u.id),
                    empire1=user.empire,
                    fleet1="Dutchman",
                    news_type='DU',
                    date_and_time=datetime.now(),
                    is_personal_news=True,
                    planet = planet,
                    is_empire_news=True,
                    extra_info=news_message,
                    tick_number=RoundStatus.objects.get().tick_number
                    )
        else:
            News.objects.create(user1=User.objects.get(id=u.id),
                    user2=User.objects.get(id=u.id),
                    empire1=user.empire,
                    fleet1="Dutchman",
                    news_type='DU',
                    date_and_time=datetime.now(),
                    is_personal_news=True,
                    planet = planet,
                    is_empire_news=False,
                    extra_info=news_message,
                    tick_number=RoundStatus.objects.get().tick_number
                    )
                    
    game_tick = RoundStatus.objects.filter().first()
    tick_hour = (60/game_tick.tick_time) * 60
    ticks = random.randint(tick_hour*3, tick_hour*6)
    arte.ticks_left = ticks
    arte.save()
    
def actskrull(arte, status):
    News.objects.create(user1=User.objects.get(id=status.id),
            user2=User.objects.get(id=status.id),
            empire1=status.empire,
            news_type='SK',
            date_and_time=datetime.now(),
            is_read=True,
            is_personal_news=False,
            is_empire_news=False,
            tick_number=RoundStatus.objects.get().tick_number
            )
    
def actobelisk():
    user = UserStatus.objects.filter(fleet_readiness_max__gt=100)
    arte = Artefacts.objects.get(name="Obelisk")
    emp = UserStatus.objects.filter(empire=arte.empire_holding)
    for u in user:
        u.fleet_readiness_max = 100
        u.psychic_readiness_max = 100
        u.agent_readiness_max = 100
        u.save()
    for e in emp:
        e.fleet_readiness_max = 115
        e.psychic_readiness_max = 115
        e.agent_readiness_max = 115
        e.save()
