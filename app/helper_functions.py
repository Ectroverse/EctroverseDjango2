from .models import *
import numpy as np
import miniball
from collections import defaultdict
from .map_settings import *
from .specops import perform_incantation
from datetime import datetime
from datetime import timedelta
from django.template import RequestContext
from .helper_classes import *
from .calculations import *
from django.db import connection

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
    Scouting.objects.create(user=status.user, planet=planet, scout=1.0, empire=status.empire )
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
    # print("find_nearest_portal",x,y,portal_list)
    if Specops.objects.filter(user_to=status.user, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=status.user, name='Vortex Portal'):
            vort_por = Planet.objects.filter(id=vort.planet.id)
            portal_list = portal_list | vort_por
    min_dist = (portal_list[0].x- x)**2+ (portal_list[0].y -y)**2;
    portal = portal_list[0]
    for p in portal_list:
        dist = (p.x-x)**2 + (p.y-y)**2
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
    if args:
        fleet.i = args[0]
        planet = Planet.objects.filter(x=target_x, y=target_y, i=args[0]).first()
        if planet is not None:
            fleet.target_planet = planet
        # print(fleet.current_position_x,fleet.current_position_y)
    else:
        planet = Planet.objects.filter(x=target_x, y=target_y, i=0).first()
        if planet is not None:
            fleet.target_planet = planet
    min_dist = np.sqrt((fleet.current_position_x - float(target_x)) ** 2 +
                       (fleet.current_position_y - float(target_y)) ** 2)
    ticks_remaining = max(0,int(np.floor(min_dist / speed)))
    fleet.x = target_x
    fleet.y = target_y
    fleet.ticks_remaining = ticks_remaining
    #if ticks_remaining < 1:
        #fleet.current_position_x = target_x
        #fleet.current_position_y = target_y
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
        planet = Planet.objects.filter(x=f.x, y=f.y, i=f.i).first()
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
            planet = Planet.objects.get(x=fl.x, y=fl.y, i=fl.i)
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
                if not Scouting.objects.filter(planet = planet, empire=status.empire).exists():
                    Scouting.objects.create(user= fl.owner,
                                            planet = planet,
                                            empire = status.empire,
                                            scout = '1')
                else:
                    sc = Scouting.objects.get(planet = planet, empire=status.empire)
                    sc.scout = 1
                    sc.save()
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
    pl_number = Planet.objects.filter(owner = status.user).count()
    exp_cost = (pl_number + expo_ship_nr + 40) >> 2
    art = Artefacts.objects.get(name="Genghis Effect")
    if status.empire == art.empire_holding:
        exp_cost *= 0.75
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

    planet = Planet.objects.filter(x=x, y=y, i=i).first()
    if planet is None:
        return "This planet doesn't exist!"
    portal_planets = Planet.objects.filter(owner=status.user, portal=True)
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
    msg = None
    rstatus = RoundStatus.objects.get(id=1)
    if fleet_time < 1 and rstatus.is_running == True:
        msg = "instant"
        if agents > 0:
            with connection.cursor() as cursor:
                cursor.execute("call operations("+str('1,')+str(agent_fleet.id)+");")

    return msg
    
def send_ghosts(status, agents, ghost, x, y, i, specop):
    x = int(x)
    y = int(y)
    i = int(i)

    planet = Planet.objects.filter(x=x, y=y, i=i).first()
    if planet is None and specop != 'Big Bang':
        return "This planet doesn't exist!"
    portal_planets = Planet.objects.filter(owner=status.user, portal=True)
    if not portal_planets:
        return "You need at least one portal to send the fleet from!"
    best_portal_planet = find_nearest_portal(x, y, portal_planets, status)
    min_dist = np.sqrt((best_portal_planet.x - x) ** 2 + (best_portal_planet.y - y) ** 2)
    speed = travel_speed(status)
    fleet_time = max(0,int(np.floor((min_dist / speed))))
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
    msg = None
    if fleet_time < 1:
        if ghost > 0:
            msg = "instant"
            print(ghost_fleet)
            with connection.cursor() as cursor:
                cursor.execute("call incantations("+str('1,')+str(ghost_fleet.id)+");")

    return msg

def build_on_planet(status, planet, building_list_dict):
    # Make sure its owned by user

    # Create list of building classes, it's making 1 object of each
    building_list = [SolarCollectors(), FissionReactors(), MineralPlants(), CrystalLabs(), RefinementStations(),
                     Cities(), ResearchCenters(), DefenseSats(), ShieldNetworks(), Portal()]

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
                    total_resource_cost, penalty = building.calc_cost(num, status.research_percent_portals, tech,
                                                        status)
                else:
                    total_resource_cost, penalty = building.calc_cost(num, status.research_percent_construction, tech,
                                                status)

                if not total_resource_cost:
                    list_buildings[planet]['number'] += "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nNot enough tech research to build"  + building.label  + "\n"
                    continue
                
                pportal = 0
                if planet.portal:
                    pportal = 1
                    
                total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
                
                total_resource_cost = ResourceSet(total_resource_cost)  # convert to more usable object
                if isinstance(building, Portal):
                    ob_factor = 1
                else:
                    ob_factor = calc_overbuild_multi(planet.size,
                                                 total_buildings + planet.buildings_under_construction, num)
                
                total_resource_cost.apply_overbuild(
                    ob_factor)  # can't just use planet.overbuilt, need to take into account how many buildings we are making

                if not total_resource_cost.is_enough(status):
                    list_buildings[planet]['number'] = "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nNot enough resources to build " + building.label +"\n"
                    continue

                if isinstance(building, Portal) and planet.portal:
                    list_buildings[planet]['number'] = "Planet "+ str(planet.x) + ":" + str(planet.y) + "," + str(planet.i) + "\nA portal is already on this planet! \n"
                    continue

                if isinstance(building, Portal) and planet.portal_under_construction:
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
                if isinstance(building, Portal):
                    planet.portal_under_construction = True

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
    