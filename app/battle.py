from django.db.models import Q, Sum
from .models import *
from app.constants import *
from .helper_functions import generate_fleet_order, find_nearest_portal, join_main_fleet, travel_speed
import numpy as np
from .models import *
from .calculations import *
from datetime import datetime
import copy
import math


def battleReadinessLoss(user1, user2, planet):
    # print(user1, user2)
    fa = (1 + user1.num_planets) / (1 + user2.num_planets)
    empire1 = user1.empire
    empire2 = user2.empire
    max = 100

    if (empire1 == empire2):  # intra-fam attack
        fa = pow(fa, 1.3)
        fb = 1.0
        max = 16.0
    else:
        fa = pow(fa, 1.3);
        fb = (1 + empire1.planets) / (1 + empire2.planets)
        fb = pow(fb, 1.8)

    fdiv = 0.5
    if fb < fa:
        fdiv = 0.5 * pow(fb / fa, 0.8)
    fa = (fdiv * fa) + ((1.0 - fdiv) * fb)
    if fa < 0.50:
        fa = 0.50
    fa *= 11.5

    war = False
    ally = False
    nap = False

    relations_from_empire = Relations.objects.filter(empire1=empire1)
    relations_to_empire = Relations.objects.filter(empire2=empire1)

    for rel in relations_from_empire:
        if rel.empire2 == empire2:
            if rel.relation_type == 'W':
                war = True
            if rel.relation_type == 'A':
                ally = True
            if rel.relation_type == 'NC' or rel.relation_type == 'PC' or rel.relation_type == 'N' or rel.relation_type == 'C':
                nap = True

    for rel in relations_to_empire:
        if rel.empire1 == empire2:
            if rel.relation_type == 'W':
                war = True
            if rel.relation_type == 'A':
                ally = True
            if rel.relation_type == 'NC' or rel.relation_type == 'PC' or rel.relation_type == 'N' or rel.relation_type == 'C':
                nap = True

    if empire1.id == empire2.id or ally or war:
        fa /= 3

    if Specops.objects.filter(name="Planetary Beacon", planet=planet).exists() or user1.race == 'SM':
        fa = fa
    else:
        spec_ops = Specops.objects.filter(user_to=user2.user, name="Dark Web")
        for specop in spec_ops:
            fa *= 1 + specop.specop_strength / 100
        if user2.race == 'FT':
            fa *= (1 + (user2.research_percent_culture / 100))

    if Specops.objects.filter(user_to=user2.user, name="Enlightenment", extra_effect="BadFR").exists():
        en = Specops.objects.get(user_to=user2.user, name="Enlightenment", extra_effect="BadFR")
        fa /= (1 + en.specop_strength / 100)
    
    tyr = Artefacts.objects.get(name="Tyrs Justice")
    if empire1 == tyr.empire_holding and tyr.ticks_left > 0:
        fa *= 0.66
    
    if user1.race == 'SM':
        fa *= 0.8
        
    if user2.race == 'FT':
        fa *= (1 + (user2.research_percent_culture / 100))
    
    if nap == True:
        if fa < 50:
            fa = 50

    # add personal and fam news
    # dont forget to delete anempty fleet!
    # deparate losses for main fleet and stationed! grr

    return min(round(fa), max)

def calc_lost_units_attacker(attacking_fleet, attacker_losses):
    if attacker_losses["Carriers"]:
        units_lost = calc_lost_units_in_carriers(attacking_fleet, attacker_losses["Carriers"])
    else:
        units_lost = calc_lost_units_in_transports(attacking_fleet, attacker_losses["Transports"])
    
    attacker_losses["Bombers"] += units_lost["Bombers"]
    attacker_losses["Fighters"] += units_lost["Fighters"]
    attacker_losses["Transports"] += units_lost["Transports"]
    attacker_losses["Goliaths"] += units_lost["Goliaths"]
    attacker_losses["Droids"] += units_lost["Droids"]
    attacker_losses["Soldiers"] += units_lost["Soldiers"]

    attacking_fleet.carrier -= attacker_losses["Carriers"]
    attacking_fleet.cruiser -= attacker_losses["Cruisers"]
    attacking_fleet.phantom -= attacker_losses["Phantoms"]
    attacking_fleet.bomber -= attacker_losses["Bombers"]
    attacking_fleet.fighter -= attacker_losses["Fighters"]
    attacking_fleet.transport -= attacker_losses["Transports"]
    attacking_fleet.goliath -= attacker_losses["Goliaths"]
    attacking_fleet.droid -= attacker_losses["Droids"]
    attacking_fleet.soldier -= attacker_losses["Soldiers"]
    
    attacking_fleet.save()


def calc_lost_units_in_carriers(attacking_fleet, carrier_losses):
    # calc lost bombers, transports and fighters
    lost_units = {"Bombers":0, "Fighters":0, "Transports":0, "Goliaths":0, "Droids":0, "Soldiers":0}
    if attacking_fleet.carrier:
        fraction_carriers_lost = carrier_losses / attacking_fleet.carrier
        lost_units["Bombers"] = round(attacking_fleet.bomber * fraction_carriers_lost)
        lost_units["Fighters"] = round(attacking_fleet.fighter * fraction_carriers_lost)
        lost_units["Transports"] = round(attacking_fleet.transport * fraction_carriers_lost)

        lost_units_transports = calc_lost_units_in_transports(attacking_fleet, lost_units["Transports"])
        lost_units["Goliaths"] = lost_units_transports["Goliaths"]
        lost_units["Droids"] = lost_units_transports["Droids"]
        lost_units["Soldiers"] = lost_units_transports["Soldiers"]

    return lost_units

def calc_lost_units_in_transports(attacking_fleet, transports_losses):
    # calc lost goliahs, droids and soldiers
    lost_units = {"Bombers":0, "Fighters":0, "Transports":0, "Goliaths":0, "Droids":0, "Soldiers":0}
    if attacking_fleet.transport:
        fraction_transports_lost = transports_losses / attacking_fleet.transport
        lost_units["Goliaths"] = round(attacking_fleet.goliath * fraction_transports_lost)
        lost_units["Droids"] = round(attacking_fleet.droid * fraction_transports_lost)
        lost_units["Soldiers"] = round(attacking_fleet.soldier * fraction_transports_lost)

    return lost_units

def defenders_fleet_update(defender, battle_report, attacked_planet):
    main_fleet = Fleet.objects.get(owner=defender.id, main_fleet=True)
    stationed_fleet = Fleet.objects.filter(owner=defender.id, command_order=8,\
                                        x=attacked_planet.x, y=attacked_planet.y, i=attacked_planet.i).first()
    
    bomb = 0
    figs = 0
    trans = 0
    cruis = 0
    carr = 0
    sold = 0
    droi = 0
    gols = 0
    phants = 0
    
    if battle_report["p1"]["phase"]:
        for unit, losses in battle_report["p1"]["def_loss"].items():
            if losses > 0:
                if unit == "Bombers":
                    bomb += losses
                if unit == "Fighters":
                    figs += losses
                if unit == "Transports":
                    trans += losses
                if unit == "Cruisers":
                    cruis += losses
                if unit == "Carriers":
                    carr += losses
                if unit == "Soldiers":
                    sold += losses
                if unit == "Droids":
                    droi += losses    
                if unit == "Goliaths":
                    gols += losses
                if unit == "Phantoms":
                    phants += losses
  
                

    if battle_report["p2"]["phase"]:
        for unit, losses in battle_report["p2"]["def_loss"].items():
            if losses > 0:
                if unit == "Bombers":
                    bomb += losses
                if unit == "Fighters":
                    figs += losses
                if unit == "Transports":
                    trans += losses
                if unit == "Cruisers":
                    cruis += losses
                if unit == "Carriers":
                    carr += losses
                if unit == "Soldiers":
                    sold += losses
                if unit == "Droids":
                    droi += losses    
                if unit == "Goliaths":
                    gols += losses
                if unit == "Phantoms":
                    phants += losses
                

    if battle_report["p3"]["phase"]:
        for unit, losses in battle_report["p3"]["def_loss"].items():
            if losses > 0:
                if unit == "Bombers":
                    bomb += losses
                if unit == "Fighters":
                    figs += losses
                if unit == "Transports":
                    trans += losses
                if unit == "Cruisers":
                    cruis += losses
                if unit == "Carriers":
                    carr += losses
                if unit == "Soldiers":
                    sold += losses
                if unit == "Droids":
                    droi += losses    
                if unit == "Goliaths":
                    gols += losses
                if unit == "Phantoms":
                    phants += losses 
               
    
    if battle_report["p4"]["phase"]:
        for unit, losses in battle_report["p4"]["def_loss"].items():
            if losses > 0:
                if unit == "Bombers":
                    bomb += losses
                if unit == "Fighters":
                    figs += losses
                if unit == "Transports":
                    trans += losses
                if unit == "Cruisers":
                    cruis += losses
                if unit == "Carriers":
                    carr += losses
                if unit == "Soldiers":
                    sold += losses
                if unit == "Droids":
                    droi += losses    
                if unit == "Goliaths":
                    gols += losses
                if unit == "Phantoms":
                    phants += losses
    
    if stationed_fleet:
        # stationed fleet can only be 1, since it will all merge on that planet
        #bombers
        if bomb > 0:
            mf = min(1, stationed_fleet.bomber / main_fleet.bomber)
            if mf == 0:
                mf = 1
            st_bomb = round(bomb * mf)
            stationed_fleet.bomber -= st_bomb
            main_fleet.bomber -= (bomb - st_bomb)
        #fighters
        if figs > 0:
            mf = 1
            if main_fleet.fighter > 0:   
                mf = min(1, stationed_fleet.fighter / main_fleet.fighter)
            st_figs = round(figs * mf)
            stationed_fleet.fighter -= st_figs
            main_fleet.fighter -= (figs - st_figs)
        #transports
        if trans > 0:
            mf = min(1, stationed_fleet.transport/ main_fleet.transport)
            st_trans = round(trans * mf)
            stationed_fleet.transport -= st_trans
            main_fleet.transport -= (trans - st_trans)
        #cruisers
        if cruis > 0:
            mf = 1
            if main_fleet.cruiser > 0:
                mf = min(1, stationed_fleet.cruiser/ main_fleet.cruiser)
            st_cruis = round(cruis * mf)
            stationed_fleet.cruiser -= st_cruis
            main_fleet.cruiser -=  (cruis - st_cruis)
        #carriers
        if carr > 0:
            mf = min(1, stationed_fleet.carrier/ main_fleet.carrier)
            if mf == 0:
                mf = 1
            st_carr = round(carr * mf)
            stationed_fleet.carrier -= st_carr
            main_fleet.carrier -=  (carr - st_carr)
        # soldiers
        if sold > 0:
            mf = 1
            if main_fleet.soldier > 0:
                mf = min(1, stationed_fleet.soldier/ main_fleet.soldier)
            st_sold = round(sold * mf)
            stationed_fleet.soldier -= st_sold
            main_fleet.soldier -=  (sold - st_sold)
        # droids
        if droi > 0:
            mf = 1
            if main_fleet.droid > 0:
                mf = min(1, stationed_fleet.droid/ main_fleet.droid)
            st_droi = round(droi * mf)
            stationed_fleet.droid -= st_droi
            main_fleet.droid -=  (droi - st_droi)
        # goliaths
        if gols > 0:
            mf = 1
            if main_fleet.goliath > 0:
                mf = min(1, stationed_fleet.goliath/ main_fleet.goliath)
            st_gols = round(gols * mf)
            stationed_fleet.goliath -= st_gols
            main_fleet.goliath -=  (gols - st_gols)
        # phantoms
        if phants > 0:
            mf = 1
            if main_fleet.phantom > 0:
                mf = min(1, stationed_fleet.phantom/ main_fleet.phantom)
            st_phants = round(phants * mf)
            stationed_fleet.phantom -= st_phants
            main_fleet.phantom -=  (phants - st_phants)
        stationed_fleet.save()
    else:
        main_fleet.bomber -= bomb
        main_fleet.fighter -= figs
        main_fleet.transport -= trans
        main_fleet.cruiser -= cruis
        main_fleet.carrier -= carr
        main_fleet.soldier -= sold
        main_fleet.droid -= droi
        main_fleet.goliath -= gols
        main_fleet.phantom -= phants

    main_fleet.save()




def generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets):
    # SA = 'SA', _('Successfull Attack')
    # UA = 'UA', _('Unsuccessfull Attack')
    # SD = 'SD', _('Successfull Defence')
    # UD = 'UD', _('Unsuccessfull Defence')

    news_type_attacker = "SA" if battle_report["won"] == "A" else "UA"
    news_type_defender = "SD" if battle_report["won"] == "D" else "UD"

    attack_fleet_msg = ""
    
    ironside = Artefacts.objects.get(name="Ironside Effect")
    resources = ["Energy", "Mineral", "Crystal", "Ectrolium"]
    
    
    if battle_report["p1"]["phase"]:
        attack_fleet_msg += "Phase 1 losses: "
        for unit, losses in battle_report["p1"]["att_loss"].items():
            if losses > 0:
                attack_fleet_msg += str(unit) + ": " + str(losses) + " "
        if battle_report["p1"]["att_flee"]:
            attack_fleet_msg += "Attackers fleet was overwhelmed in stage 1."

    if battle_report["p2"]["phase"]:
        attack_fleet_msg += "\nPhase 2 losses: "
        for unit, losses in battle_report["p2"]["att_loss"].items():
            if losses > 0:
                attack_fleet_msg += str(unit) + ": " + str(losses) + " "
        if battle_report["p2"]["att_flee"]:
            attack_fleet_msg += "Attackers fleet was overwhelmed in stage 2."

    if battle_report["p3"]["phase"]:
        attack_fleet_msg += "\nPhase 3 losses: "
        for unit, losses in battle_report["p3"]["att_loss"].items():
            if losses > 0:
                attack_fleet_msg += str(unit) + ": " + str(losses) + " "
        if battle_report["p3"]["att_flee"]:
            attack_fleet_msg += "Attackers fleet was overwhelmed in stage 3."

    if battle_report["p4"]["phase"]:
        attack_fleet_msg += "\nPhase 4 losses: "
        for unit, losses in battle_report["p4"]["att_loss"].items():
            if losses > 0:
                attack_fleet_msg += str(unit) + ": " + str(losses) + " "
        if battle_report["p4"]["att_flee"]:
            attack_fleet_msg += "Attackers fleet was overwhelmed in stage 4."

    
    defender_fleet_msg = ""

    necro = Artefacts.objects.get(name="Scroll of the Necromancer")

    if battle_report["p1"]["phase"]:
        defender_fleet_msg += "Phase 1 losses: "
        for unit, losses in battle_report["p1"]["def_loss"].items():
            if losses > 0:
                defender_fleet_msg += str(unit) + ": " + str(losses) + " "
                if necro.empire_holding == defender.empire and unit != "Necromancers":
                    necro.effect1 += losses/10
                    necro.save()
        if battle_report["p1"]["def_flee"]:
            defender_fleet_msg += "Defending forces preferred not to directly engage in stage 1!"

    if battle_report["p2"]["phase"]:
        defender_fleet_msg += "\nPhase 2 losses: "
        for unit, losses in battle_report["p2"]["def_loss"].items():
            if losses > 0:
                defender_fleet_msg += str(unit) + ": " + str(losses) + " "
                if necro.empire_holding == defender.empire and unit != "Necromancers":
                    necro.effect1 += losses/10
                    necro.save()
        if battle_report["p2"]["def_flee"]:
            defender_fleet_msg += "Defending forces preferred not to directly engage in stage 2!"

    if battle_report["p3"]["phase"]:
        defender_fleet_msg += "\nPhase 3 losses: "
        for unit, losses in battle_report["p3"]["def_loss"].items():
            if losses > 0:
                defender_fleet_msg += str(unit) + ": " + str(losses) + " "
                if necro.empire_holding == defender.empire and unit != "Necromancers":
                    if unit != "Planet population":
                        necro.effect1 += losses/10
                        necro.save()
        if battle_report["p3"]["def_flee"]:
            defender_fleet_msg += "Defending forces preferred not to directly engage in stage 3!"
    
    if battle_report["p4"]["phase"]:
        defender_fleet_msg += "\nPhase 4 losses: "
        for unit, losses in battle_report["p4"]["def_loss"].items():
            if losses > 0 and unit not in resources:
                defender_fleet_msg += str(unit) + ": " + str(losses) + " "
                if necro.empire_holding == defender.empire and unit != "Necromancers":
                    if unit != "Planet population":
                        necro.effect1 += losses/10
                        necro.save()
            if ironside.empire_holding == attacker.empire:
                if losses > 0 and unit in resources:
                    if unit == "Energy":
                        defender_fleet_msg += "\n" + str(losses) + " " + str(unit) + ","
                    elif unit != "Ectrolium":
                        defender_fleet_msg += " " + str(losses) + " " + str(unit) + ","
                    else: 
                         defender_fleet_msg += " " + str(losses) + " " + str(unit) + " was stolen!"
        if battle_report["p4"]["def_flee"]:
            defender_fleet_msg += "\nDefending forces preferred not to directly engage in stage 4!"
        
    def_fleet_msg = 'Main Fleet'
    
    def_fleet_msg += "\nBomber: " + str(main_defender_fleet.bomber)
    def_fleet_msg += "\nFighter: " + str(main_defender_fleet.fighter)
    def_fleet_msg += "\nTransport: " + str(main_defender_fleet.transport)
    def_fleet_msg += "\nCruiser: " + str(main_defender_fleet.cruiser)
    def_fleet_msg += "\nCarrier: " + str(main_defender_fleet.carrier)
    def_fleet_msg += "\nSoldier: " + str(main_defender_fleet.soldier)
    def_fleet_msg += "\nDroid: " + str(main_defender_fleet.droid)
    def_fleet_msg += "\nGoliath: " + str(main_defender_fleet.goliath)
    def_fleet_msg += "\nPhantom: " + str(main_defender_fleet.phantom)
    
    def_fleet_msg += '\n Defending Fleet'
    
    for unit, losses in defending_fleets.items():
        def_fleet_msg += "\n" + str(unit) + ": " + str(losses)
    
        
    News.objects.create(user1=User.objects.get(id=attacker.id),
                        user2=User.objects.get(id=defender.id),
                        empire1=attacker.empire,
                        empire2=defender.empire,
                        fleet1=attack_fleet_msg,
                        fleet2=defender_fleet_msg,
                        news_type=news_type_attacker,
                        date_and_time=datetime.now(),
                        planet=attacked_planet,
                        is_personal_news=True,
                        is_empire_news=True,
                        tick_number=RoundStatus.objects.get().tick_number
                        )

    News.objects.create(user1=User.objects.get(id=defender.id),
                        user2=User.objects.get(id=attacker.id),
                        empire1=defender.empire,
                        empire2=attacker.empire,
                        fleet1=defender_fleet_msg,
                        fleet2=attack_fleet_msg,
                        extra_info=def_fleet_msg,
                        news_type=news_type_defender,
                        date_and_time=datetime.now(),
                        planet=attacked_planet,
                        is_personal_news=True,
                        is_empire_news=True,
                        tick_number=RoundStatus.objects.get().tick_number
                        )


def attack_planet(attacking_fleet):
    attacker = UserStatus.objects.get(id=attacking_fleet.owner.id)
    attacked_planet = Planet.objects.get(x=attacking_fleet.x, y=attacking_fleet.y, i=attacking_fleet.i)
    defender = UserStatus.objects.get(id=attacked_planet.owner.id)

    main_defender_fleet = Fleet.objects.get(owner=defender.id, main_fleet=True)
    stationed_defender_fleet = Fleet.objects.filter(owner=defender.id, command_order=8,\
                                        x=attacked_planet.x, y=attacked_planet.y, i=attacked_planet.i).first()
    
    defending_fleets = {"bomber":0,
                        "fighter": 0,
                        "transport": 0,
                        "cruiser": 0,
                        "carrier": 0,
                        "soldier": 0,
                        "droid": 0,
                        "goliath": 0,
                        "phantom": 0
                        }
    # portal coverage
    
    portal_xy_list = Planet.objects.filter(portal=True, owner=defender.user).values_list('x', 'y')
    if Specops.objects.filter(user_to=defender.user, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=defender.user, name='Vortex Portal'):
            vort_por = Planet.objects.filter(id=vort.planet.id).values_list('x', 'y')
            portal_xy_list = portal_xy_list | vort_por
    
    p_protection = min(100, round(100.0 * battlePortalCalc(attacking_fleet.x, attacking_fleet.y, portal_xy_list, defender.research_percent_portals, defender)))
    
    if Specops.objects.filter(planet=attacked_planet, user_to=defender.user, name='Portal Force Field').exists():
        op_str = 1
        for op in Specops.objects.filter(planet=attacked_planet, user_to=defender.user, name='Portal Force Field'):
            op_str *= (1+op.specop_strength/100)
        p_protection = max(0,(p_protection/op_str))
    
    if stationed_defender_fleet:
        for key in defending_fleets.keys():
            defending_fleets[key] = round(main_defender_fleet.__dict__[key] * p_protection / 100)
            defending_fleets[key] += stationed_defender_fleet.__dict__[key]
            
    else:
        for key in defending_fleets.keys():
            defending_fleets[key] = round(main_defender_fleet.__dict__[key] * p_protection / 100)

    
    attstats = {}
    defstats = {}
    battle_report = {}
    for i in range(0, len(unit_labels)):
        attstats[unit_labels[i]] = copy.deepcopy(unit_stats[i])
        unit_bonus = race_info_list[attacker.get_race_display()].get(unit_race_bonus_labels[i], 1.0)
        for j in range(0, 4):
            attstats[unit_labels[i]][j] = round(attstats[unit_labels[i]][j] * unit_bonus, 2)
        defstats[unit_labels[i]] = copy.deepcopy(unit_stats[i])
        unit_bonus = race_info_list[defender.get_race_display()].get(unit_race_bonus_labels[i], 1.0)
        for j in range(0, 4):
            defstats[unit_labels[i]][j] = round(defstats[unit_labels[i]][j] * unit_bonus, 2)

    battle_report["tired_forces"] = ""
    battle_report["won"] = "C"
    battle_report["p1"] = {}
    battle_report["p2"] = {}
    battle_report["p3"] = {}
    battle_report["p4"] = {}

    battle_report["p1"]["phase"] = False
    battle_report["p2"]["phase"] = False
    battle_report["p3"]["phase"] = False
    battle_report["p4"]["phase"] = False



    # battle_report += "\n\n defending_fleets2" + str(defending_fleets)
    battle_report["fleet_readiness"] = attacker.fleet_readiness
    if attacker.fleet_readiness < -100:
        return battle_report

    defender.military_flag = 1
    defender.save()

    fa = 1
    if attacker.fleet_readiness < 0:
        fa = 1.0 - attacker.fleet_readiness / 130.0

    attfactor = race_info_list[attacker.get_race_display()].get("military_attack", 1.0) / \
                race_info_list[defender.get_race_display()].get("military_defence", 1.0) * fa
    deffactor = race_info_list[defender.get_race_display()].get("military_attack", 1.0) / \
                race_info_list[attacker.get_race_display()].get("military_defence", 1.0) / fa            
    
    tgeneral = Artefacts.objects.get(name="The General")
    might = Artefacts.objects.get(name="Military Might")
    if defender.empire == tgeneral.empire_holding and tgeneral.ticks_left == 0:
        gsystem = System.objects.get(id=tgeneral.effect1)
        gdist = max(abs(gsystem.x-attacked_planet.x), abs(gsystem.y-attacked_planet.y))
        if gdist == 0 or gdist == 1 and might.empire_holding == defender.empire:
            attfactor /= 1.15
            deffactor *= 1.15
        elif gdist == 1 or gdist == 2 and might.empire_holding == defender.empire:
            attfactor /= 1.125
            deffactor *= 1.125
        elif gdist == 2 or gdist == 4 and might.empire_holding == defender.empire:
            attfactor /= 1.1
            deffactor *= 1.1
        elif gdist == 3 or gdist == 6 and might.empire_holding == defender.empire:
            attfactor /= 1.075
            deffactor *= 1.075
        elif gdist == 4 or gdist == 8 and might.empire_holding == defender.empire:
            attfactor /= 1.05
            deffactor *= 1.05
        elif gdist == 5 or gdist == 10 and might.empire_holding == defender.empire:
            attfactor /= 1.025
            deffactor *= 1.025
    
    arte = Artefacts.objects.get(name="Double 0")
    if defender.empire == arte.empire_holding:
        deffactor *= 0.85
    
    tyr = Artefacts.objects.get(name="Tyrs Justice")
    if defender.empire == tyr.empire_holding and attacker.empire != defender.empire:
        tyr.ticks_left = 36
        tyr.save()
    
    fr = battleReadinessLoss(attacker, defender, attacked_planet)
    if attacked_planet.artefact != None and fr > 20:
        fr = 20
    attacker.fleet_readiness -= fr
    attacker.save()

    if Specops.objects.filter(name="Planetary Beacon", planet=attacked_planet).exists():
        attfactor /= 1.1
        deffactor *= 1.1
    
    if Specops.objects.filter(name="War Illusions", user_to=attacker.user).exists():
        attackillusions= Specops.objects.get(name="War Illusions", user_to=attacker.user)
        attfactor *= 1 + (attackillusions.specop_strength/100)
    
    if Specops.objects.filter(name="War Illusions", user_to=defender.user).exists():
        defenceillusions= Specops.objects.get(name="War Illusions", user_to=defender.user)
        deffactor *= 1 + (defenceillusions.specop_strength/100)
    
    # defsatsbase = defsats = attacked_planet.defense_sats
    hpshield = 0
    for sh in Specops.objects.filter(user_to=defender.user, name='Planetary Shielding', planet=attacked_planet):
    	strength = sh.specop_strength
    	hpshield += strength
    shields = (shield_absorb * attacked_planet.shield_networks) + hpshield
    
    snetwork = Artefacts.objects.get(name="Shield Network")
    if defender.empire == snetwork.empire_holding:
        shields = hpshield
        shields += ((shield_absorb * defender.total_shield_networks) * 0.33)

    # phase1
    attacker_flee, defender_flee, \
    att_loss, def_loss = phase1(attacking_fleet, defending_fleets, attstats,
                                defstats, attfactor, deffactor, attacked_planet, attacker, defender, shields)
    battle_report["p1"]["phase"] = True
    battle_report["p1"]["att_flee"] = attacker_flee
    battle_report["p1"]["def_flee"] = defender_flee
    battle_report["p1"]["att_loss"] = att_loss
    battle_report["p1"]["def_loss"] = def_loss

    if attacker_flee:
        defenders_fleet_update(defender, battle_report, attacked_planet)
        battle_report["won"] = "D"
        generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets)
        return battle_report

    # phase2
    attacker_flee, defender_flee, \
    att_loss, def_loss = phase2(attacking_fleet, defending_fleets, attstats,
                                defstats, attfactor, deffactor, attacked_planet, attacker, defender, shields)
    battle_report["p2"]["phase"] = True
    battle_report["p2"]["att_flee"] = attacker_flee
    battle_report["p2"]["def_flee"] = defender_flee
    battle_report["p2"]["att_loss"] = att_loss
    battle_report["p2"]["def_loss"] = def_loss

    if attacker_flee:
        defenders_fleet_update(defender, battle_report, attacked_planet)
        battle_report["won"] = "D"
        generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets)
        return battle_report

    # phase3
    attacker_flee, defender_flee, \
    att_loss, def_loss = phase3(attacking_fleet, defending_fleets, attstats,
                                defstats, attfactor, deffactor, attacked_planet, attacker, defender, shields)
    battle_report["p3"]["phase"] = True
    battle_report["p3"]["att_flee"] = attacker_flee
    battle_report["p3"]["def_flee"] = defender_flee
    battle_report["p3"]["att_loss"] = att_loss
    battle_report["p3"]["def_loss"] = def_loss

    if attacker_flee:
        defenders_fleet_update(defender, battle_report, attacked_planet)
        battle_report["won"] = "D"
        generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets)
        return battle_report

    # phase4
    attacker_flee, defender_flee, \
    att_loss, def_loss = phase4(attacking_fleet, defending_fleets, attstats,
                                defstats, attfactor, deffactor, attacked_planet, attacker, defender, shields)
    battle_report["p4"]["phase"] = True
    battle_report["p4"]["att_flee"] = attacker_flee
    battle_report["p4"]["def_flee"] = defender_flee
    battle_report["p4"]["att_loss"] = att_loss
    battle_report["p4"]["def_loss"] = def_loss

    # spread losses among main fleet and stationed for the defender
    defenders_fleet_update(defender, battle_report, attacked_planet)

    if attacker_flee:
        battle_report["won"] = "D"
        generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets)
        return battle_report
        attacking_fleet.command_order = attacker.post_attack_order
        if attacker.post_attack_order == 5:
            portal_planets = Planet.objects.filter(owner=attacker.id, portal=True)  # should always have at least the home planet, unless razed!!!
                    # print(portal_planets)
            if not portal_planets:
                request.session['error'] = "You need at least one portal for fleet to return to main fleet!"
                return fleets(request)
            speed = travel_speed(status)
            portal = find_nearest_portal(attacking_fleet.current_position_x, attacking_fleet.current_position_y, portal_planets. attacker)
            generate_fleet_order(attacking_fleet, portal.x, portal.y, speed, attacker.post_attack_order, portal.i)
                # do instant join of fleets allready present in systems with portals
            main_fleet = Fleet.objects.get(owner=attacker.id, main_fleet=True)
            fleets_id3 = Fleet.objects.filter(id=attacking_fleet.id, ticks_remaining=0)
            join_main_fleet(main_fleet, fleets_id3)
    if defender_flee:
        battle_report["won"] = "A"
        # unstation fleet
        # give the planet to the attacker
        # attacked_planet.owner = attacker.id
        # destroy some buildings
        attacked_planet.owner = User.objects.get(id=attacker.id)
        attacker_size = int(attacker.num_planets)
        defender_size = int(defender.num_planets)
        if defender_size / attacker_size > 0.6:
            attacked_planet.solar_collectors = round(attacked_planet.solar_collectors * 9 / 10)
            attacked_planet.fission_reactors = round(attacked_planet.fission_reactors * 9 / 10)
            attacked_planet.mineral_plants = round(attacked_planet.mineral_plants * 9 / 10)
            attacked_planet.crystal_labs = round(attacked_planet.crystal_labs * 9 / 10)
            attacked_planet.refinement_stations = round(attacked_planet.refinement_stations * 9 / 10)
            attacked_planet.cities = round(attacked_planet.cities * 9 / 10)
            attacked_planet.research_centers = round(attacked_planet.research_centers * 9 / 10)
            attacked_planet.defense_sats = round(attacked_planet.defense_sats * 9 / 10)
            attacked_planet.shield_networks = round(attacked_planet.shield_networks * 9 / 10)
            totbuild = (attacked_planet.solar_collectors + attacked_planet.fission_reactors + attacked_planet.mineral_plants + attacked_planet.crystal_labs + attacked_planet.refinement_stations + attacked_planet.cities + attacked_planet.research_centers + attacked_planet.defense_sats + attacked_planet.shield_networks)
            attacked_planet.total_buildings = totbuild
            attacked_planet.overbuilt = calc_overbuild(attacked_planet.size, totbuild - (attacked_planet.defense_sats + attacked_planet.shield_networks))
            attacked_planet.overbuilt_percent = (attacked_planet.overbuilt - 1.0) * 100             
        else:
            attacked_planet.solar_collectors = 0
            attacked_planet.fission_reactors = 0
            attacked_planet.mineral_plants = 0
            attacked_planet.crystal_labs = 0
            attacked_planet.refinement_stations = 0
            attacked_planet.cities = 0
            attacked_planet.research_centers = 0
            attacked_planet.defense_sats = 0
            attacked_planet.shield_networks = 0
            attacked_planet.total_buildings = 0
            attacked_planet.overbuilt = 0
            attacked_planet.overbuilt_percent = 0
        attacked_planet.portal = False
        attacked_planet.portal_under_construction = False
        attacked_planet.buildings_under_construction = 0
        attacked_planet.protection = 0
        attacked_planet.save()
        for con in Construction.objects.all():
            if con.planet == attacked_planet:
                con.delete()
        if attacked_planet.artefact is not None:
            attacked_planet.artefact.empire_holding = attacker.empire
            attacked_planet.artefact.save()
        scouting = Scouting.objects.filter(empire=attacker.empire, planet=attacked_planet).first()
        if scouting is None:
            Scouting.objects.create(user= attacker.user,
                                empire=attacker.empire,
                                planet = attacked_planet,
                                scout = '1')
        else:
            scouting.scout = 1.0
            scouting.save()
            
        offered = News.objects.filter(news_type='E', user1=defender.user, extra_info="1")
        offering = News.objects.filter(news_type='E', user2=defender.user, extra_info="1")
        for o in offered:
            o.delete()
        for o in offering:
            o.delete()
        
        pshield = Specops.objects.filter(name="Planetary Shielding", planet=attacked_planet)
        for sh in pshield:
            sh.delete()
            
        beac = Specops.objects.filter(name="Planetary Beacon", planet=attacked_planet)
        for pb in beac:
            pb.delete()
        
        attacking_fleet.command_order = attacker.post_attack_order
        if attacker.post_attack_order == 5:
            portal_planets = Planet.objects.filter(owner=attacker.id, portal=True)  # should always have at least the home planet, unless razed!!!
                    # print(portal_planets)
            if not portal_planets:
                request.session['error'] = "You need at least one portal for fleet to return to main fleet!"
                return fleets(request)
            speed = travel_speed(attacker)
            portal = find_nearest_portal(attacking_fleet.current_position_x, attacking_fleet.current_position_y, portal_planets, attacker)
            generate_fleet_order(attacking_fleet, portal.x, portal.y, speed, attacker.post_attack_order, portal.i)
                # do instant join of fleets allready present in systems with portals
            main_fleet = Fleet.objects.get(owner=attacker.id, main_fleet=True)
            fleets_id3 = Fleet.objects.filter(id=attacking_fleet.id, ticks_remaining=0)
            join_main_fleet(main_fleet, fleets_id3)
    generate_news(battle_report, attacker, defender, attacked_planet, main_defender_fleet, defending_fleets)
    return battle_report


####################
#      PHASE 1     #
####################
def phase1(attacking_fleet,
           defending_fleets,
           attstats, defstats,
           attfactor,
           deffactor,
           attacked_planet,
           attacker,
           defender,
           shields):
    attacker_flee = False
    defender_flee = False

    # ========= Calculate damage factors =========#
    attdam = attacking_fleet.cruiser * attstats["Cruisers"][0] + \
             attacking_fleet.phantom * attstats["Phantoms"][0]
    
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        attdam += necro.effect1 * 3
    
    defdam = defending_fleets["cruiser"] * defstats["Cruisers"][0] + \
             defending_fleets["phantom"] * defstats["Phantoms"][0] + \
             sats_attack * attacked_planet.defense_sats 
    
    if necro.empire_holding == defender.empire:
        defdam += necro.effect1 * 3
    
    if Specops.objects.filter(user_to=attacker.user, name="War Illusions").exists():
        spec_ops = Specops.objects.filter(user_to=attacker.user, name="War Illusions")
        for specop in spec_ops:
            attfactor *= 1 + (specop.specop_strength / 100)


    if Specops.objects.filter(user_to=defender.user, name="War Illusions").exists():
        spec_ops = Specops.objects.filter(user_to=defender.user, name="War Illusions")
        for specop in spec_ops:
            deffactor *= 1 + (specop.specop_strength / 100)

        
    attdam = attdam * attfactor * ((1.0 + 0.005 * attacker.research_percent_military)/(1.0 + 0.005 * defender.research_percent_military))

    defdam = defdam * deffactor * ((1.0 + 0.005 * defender.research_percent_military)/(1.0 + 0.005 * attacker.research_percent_military))
    if attdam >= 1.0:
        attdam -= attdam * (1.0 - pow(2.5, -(shields / attdam)))

    # ========= Determine if anyone will flee =========#

    # damage is too high defender flee
    if (defdam < 1.0) or ((attdam / defdam) * 10.0 >= defender.long_range_attack_percent):
        defender_flee = True
        return attacker_flee, defender_flee, {}, {}
    # defender flees, if settings are 100% this means attacker deals 10x more damage than defender
    if (attdam / defdam) * 100.0 >= defender.long_range_attack_percent:
        defdam *= 0.15
        attdam *= 0.10
        # results[3] |= 0x100;
    # attacker flees, same logic as above
    if (attdam >= 1.0) and ((defdam / attdam) * 100.0 >= attacker.long_range_attack_percent):
        defdam *= 0.20
        attdam *= 0.10
        attacker_flee = True
    if attdam == 0:
        attacker_flee = True

    # ========= Damage to attacking fleets =========#
    hpcarrier = attacking_fleet.carrier * attstats["Carriers"][1]
    hpcruiser = attacking_fleet.cruiser * attstats["Cruisers"][1]
    hpphantom = attacking_fleet.phantom * attstats["Phantoms"][1]
    
    hpnecro = 0
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hpcarrier + hpcruiser + hpphantom + hpnecro
    
    damcarrier = 0
    damcruiser = 0
    damphantom = 0
    damnecro = 0

    # percentage of damage that wil be received by the unit
    if hptotal:
        damcarrier = hpcarrier / hptotal
        damcruiser = hpcruiser / hptotal
        damphantom = hpphantom / hptotal     
        if hpnecro >=1:
            damnecro = hpnecro / hptotal
    
    
    # calc attacking/defending cruiser ratio, transfer the damage from carriers to cruisers and phantoms
    fa = 0.0
    if defending_fleets["cruiser"] > 0:
        fa = attacking_fleet.cruiser / defending_fleets["cruiser"]
    damcarrier *= pow(1.50, -fa)

    fb = damcarrier + damcruiser + damphantom + damnecro

    if fb >= 0.00001:
        fa = defdam / fb
        damcarrier *= fa
        damcruiser *= fa
        damphantom *= fa
        damnecro *= fa

    if damcarrier > hpcarrier:
        damcruiser += damcarrier - hpcarrier
    if damcruiser > hpcruiser:
        damphantom += damcruiser - hpcruiser
    if damphantom > hpphantom:
        damcruiser += damphantom - hpphantom
    if damnecro > hpnecro:
        damcarrier += damnecro - hpnecro
    
    neckilled = 0
    if necro.empire_holding == attacker.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
    
    attacker_losses = {"Bombers": 0, "Fighters": 0, "Transports": 0,
                       "Cruisers": round(min(attacking_fleet.cruiser, damcruiser / attstats["Cruisers"][1])),
                       "Carriers": round(min(attacking_fleet.carrier, damcarrier / attstats["Carriers"][1])),
                       "Soldiers": 0, "Droids": 0, "Goliaths": 0,
                       "Phantoms": round(min(attacking_fleet.phantom, damphantom / attstats["Phantoms"][1])),
                       "Necromancers": neckilled}

    calc_lost_units_attacker(attacking_fleet, attacker_losses)
    attacking_fleet.save()

    # ========= Damage to defending fleets =========#
    hpcruiser = defending_fleets["cruiser"] * defstats["Cruisers"][1]
    hpphantom = defending_fleets["phantom"] * defstats["Phantoms"][1]
    hpsats = attacked_planet.defense_sats * sats_defence
    
    hpnecro = 0
    if necro.empire_holding == defender.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hpcruiser + hpphantom + hpsats + hpnecro
    
    damcruiser = 0
    damphantom = 0
    damsats = 0
    damnecro = 0

    if hptotal:
        damcruiser = hpcruiser / hptotal
        damphantom = hpphantom / hptotal
        damsats = hpsats / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    fa = 0.0
    if attacking_fleet.cruiser > 0:
        fa = defending_fleets["cruiser"] / attacking_fleet.cruiser
    damsats *= pow(2.80, -fa)

    fb = damcruiser + damphantom + damsats + damnecro

    if fb >= 0.00001:
        fa = attdam / fb
        damcruiser *= fa
        damphantom *= fa
        damsats *= fa
        damnecro *= fa

    if damcruiser > hpcruiser:
        damphantom += damcruiser - hpcruiser
    if damphantom > hpphantom:
        damsats += damphantom - hpphantom
    if damsats > hpsats:
        damcruiser += damsats - hpsats
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
    
    neckilled = 0
    if necro.empire_holding == defender.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
    
    defender_losses = {"Bombers": 0, "Fighters": 0, "Transports": 0,
                       "Cruisers": round(min(defending_fleets["cruiser"], damcruiser / defstats["Cruisers"][1])),
                       "Carriers": 0, "Soldiers": 0, "Droids": 0, "Goliaths": 0,
                       "Phantoms": round(min(defending_fleets["phantom"], damphantom / defstats["Phantoms"][1])),
                       "Defence Satellites": round(min(attacked_planet.defense_sats, damsats / sats_defence)),
                       "Necromancers": neckilled}

    attacked_planet.defense_sats -= defender_losses["Defence Satellites"]
    attacked_planet.save()

    defending_fleets["cruiser"] -= defender_losses["Cruisers"]
    defending_fleets["phantom"] -= defender_losses["Phantoms"]

    return attacker_flee, defender_flee, attacker_losses, defender_losses


####################
#      PHASE 2     #
####################
def phase2(attacking_fleet,
           defending_fleets,
           attstats, defstats,
           attfactor,
           deffactor,
           attacked_planet,
           attacker,
           defender,
           shields):
    attacker_flee = False
    defender_flee = False

    # ========= Calculate damage factors =========#
    attdam = attacking_fleet.cruiser * attstats["Cruisers"][0] + \
             attacking_fleet.phantom * attstats["Phantoms"][0] + \
             attacking_fleet.fighter * attstats["Fighters"][0]
    
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        attdam += necro.effect1 * 3
    
    defdam = defending_fleets["cruiser"] * defstats["Cruisers"][0] + \
             defending_fleets["phantom"] * defstats["Phantoms"][0] + \
             defending_fleets["fighter"] * defstats["Fighters"][0] + \
             sats_attack * attacked_planet.defense_sats

    if necro.empire_holding == defender.empire:
        defdam += necro.effect1 * 3

    attdam = attdam * attfactor * ((1.0 + 0.005 * attacker.research_percent_military) / \
                                   (1.0 + 0.005 * defender.research_percent_military))

    defdam = defdam * deffactor * ((1.0 + 0.005 * defender.research_percent_military) / \
                                   (1.0 + 0.005 * attacker.research_percent_military))

    if attdam >= 1.0:
        attdam -= attdam * (1.0 - pow(2.5, -(shields / attdam)))

    # ========= Determine if anyone will flee =========#
    # damage is too high defender flee
    if (defdam < 1.0) or (attdam / defdam) * 10.0 >= defender.air_vs_air_percent:
        defender_flee = True
        return attacker_flee, defender_flee, {}, {}
    # defender flees, if settings are 100% this means attacker deals 10x more damage than defender
    if (attdam / defdam) * 100.0 >= defender.air_vs_air_percent:
        defdam *= 0.15
        attdam *= 0.10
    # attacker flees, same logic as above
    if (attdam >= 1.0) and (defdam / attdam) * 100.0 >= attacker.air_vs_air_percent:
        defdam *= 0.50
        attdam *= 0.25
        attacker_flee = True
    if attdam == 0:
        attacker_flee = True

    # ========= Damage to attacking fleets =========#
    hptransport = attacking_fleet.transport * attstats["Transports"][1]
    hpcruiser = attacking_fleet.cruiser * attstats["Cruisers"][1]
    hpphantom = attacking_fleet.phantom * attstats["Phantoms"][1]
    hpbomber  = attacking_fleet.bomber * attstats["Bombers"][1]
    hpfighter = attacking_fleet.fighter * attstats["Fighters"][1]
    
    hpnecro = 0
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hptransport + hpcruiser + hpbomber + hpfighter + hpphantom + hpnecro

    damtransport = 0
    damcruiser = 0
    damphantom = 0
    damfighter = 0
    dambomber = 0
    damnecro = 0

    # percentage of damage that wil be received by the unit
    if hptotal:
        damtransport = hptransport / hptotal
        damcruiser = hpcruiser / hptotal
        damphantom = hpphantom / hptotal
        damfighter = hpfighter / hptotal
        dambomber = hpbomber / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    # calc attacking/defending cruiser/fighter ratio,
    # transfer the damage from transports to other fleet depending on the ratios
    fb = 6 * defending_fleets["cruiser"] + defending_fleets["fighter"]
    fa = 0.0
    if fb >= 0.00001:
        fa = (6 * attacking_fleet.cruiser + attacking_fleet.fighter) / fb
    damtransport *= pow(2.50, -fa)

    fa = 0.0
    if defending_fleets["fighter"] > 0:
        fa = attacking_fleet.fighter / defending_fleets["fighter"]
    damcruiser *= pow(1.25, -fa)

    fb = defending_fleets["fighter"] + 3 * defending_fleets["cruiser"]
    fa = 0.0

    if fb >= 0.00001:
        fa = (attacking_fleet.fighter + 3 * attacking_fleet.cruiser) / fb
    dambomber *= pow(1.75, -fa)

    fb = damtransport + damcruiser + dambomber + damfighter + damphantom

    if fb >= 0.00001:
        fa = defdam / fb
        damtransport *= fa
        damcruiser *= fa
        dambomber *= fa
        damfighter *= fa
        damphantom *= fa
        damnecro *= fa

    if damtransport > hptransport:
        damcruiser += damtransport - hptransport
    if damcruiser > hpcruiser:
        dambomber += damcruiser - hpcruiser
    if dambomber > hpbomber:
        damfighter += dambomber - hpbomber
    if damfighter > hpfighter:
        damphantom += damfighter - hpfighter
    if damphantom > hpphantom:
        damcruiser += damphantom - hpphantom
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
    
    neckilled = 0
    if necro.empire_holding == attacker.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
    
    attacker_losses = {"Bombers": round(min(attacking_fleet.bomber, dambomber / attstats["Bombers"][1])),
                       "Fighters": round(min(attacking_fleet.fighter, damfighter / attstats["Fighters"][1])),
                       "Transports": round(min(attacking_fleet.transport, damtransport / attstats["Transports"][1])),
                       "Cruisers": round(min(attacking_fleet.cruiser, damcruiser / attstats["Cruisers"][1])),
                       "Carriers": 0,
                       "Soldiers": 0, "Droids": 0, "Goliaths": 0,
                       "Phantoms": round(min(attacking_fleet.phantom, damphantom / attstats["Phantoms"][1])),
                       "Necromancers": neckilled}

    calc_lost_units_attacker(attacking_fleet, attacker_losses)
    attacking_fleet.save()

    # ========= Damage to defending fleets =========#
    hpcruiser = defending_fleets["cruiser"] * defstats["Cruisers"][1]
    hpphantom = defending_fleets["phantom"] * defstats["Phantoms"][1]
    hpfighter = defending_fleets["fighter"] * defstats["Fighters"][1]
    hpsats = attacked_planet.defense_sats * sats_defence

    hpnecro = 0
    if necro.empire_holding == defender.empire:
        hpnecro = necro.effect1 * 10 

    hptotal = hpcruiser + hpphantom + hpsats + hpfighter + hpnecro
    damcruiser = 0
    damphantom = 0
    damsats = 0
    damfighter = 0
    damnecro = 0

    if hptotal:
        damcruiser = hpcruiser / hptotal
        damphantom = hpphantom / hptotal
        damsats = hpsats / hptotal
        damfighter = hpfighter / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    fa = 0.0
    if attacking_fleet.fighter > 0:
        fa = defending_fleets["fighter"] / attacking_fleet.fighter
    damcruiser *= pow(1.25, -fa)

    fb = damcruiser + damphantom + damsats + damnecro

    if fb >= 0.00001:
        fa = attdam / fb
        damcruiser *= fa
        damfighter *= fa
        damphantom *= fa
        damsats *= fa
        damnecro *= fa

    if damcruiser > hpcruiser:
        damfighter += damcruiser - hpcruiser
    if damfighter > hpfighter:
        damphantom += damfighter - hpfighter
    if damphantom > hpphantom:
        damsats += damphantom - hpphantom
    if damsats > hpsats:
        damcruiser += damsats - hpsats
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
    
    neckilled = 0
    if necro.empire_holding == defender.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
    
    defender_losses = {"Bombers": 0,
                       "Fighters": round(min(defending_fleets["fighter"], damfighter / 120)),
                       "Transports": 0,
                       "Cruisers": round(min(defending_fleets["cruiser"], damcruiser / defstats["Cruisers"][1])),
                       "Carriers": 0, "Soldiers": 0, "Droids": 0, "Goliaths": 0,
                       "Phantoms": round(min(defending_fleets["phantom"], damphantom / defstats["Phantoms"][1])),
                       "Defence Satellites": round(min(attacked_planet.defense_sats, damsats / sats_defence)),
                       "Necromancers": neckilled}

    attacked_planet.defense_sats -= defender_losses["Defence Satellites"]
    attacked_planet.save()

    defending_fleets["cruiser"] -= defender_losses["Cruisers"]
    defending_fleets["phantom"] -= defender_losses["Phantoms"]
    defending_fleets["fighter"] -= defender_losses["Fighters"]

    return attacker_flee, defender_flee, attacker_losses, defender_losses

####################
#      PHASE 3     #
####################
def phase3(attacking_fleet,
           defending_fleets,
           attstats, defstats,
           attfactor,
           deffactor,
           attacked_planet,
           attacker,
           defender,
           shields):
    attacker_flee = False
    defender_flee = False

    # ========= Calculate damage factors =========#
    attdam = attacking_fleet.bomber * attstats["Bombers"][2] + \
             attacking_fleet.phantom * attstats["Phantoms"][2] + \
             attacking_fleet.cruiser * attstats["Cruisers"][2]

    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        attdam += necro.effect1 * 3

    defdam = defending_fleets["goliath"] * defstats["Goliaths"][0] + \
             defending_fleets["phantom"] * defstats["Phantoms"][2]
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        viruspop = attacked_planet.current_population * defstats["Goliaths"][0] / 100
        defdam += viruspop
        
    if necro.empire_holding == defender.empire:
        defdam += necro.effect1 * 3    
        
    if defdam > 0:
        if virus.empire_holding == defender.empire:
            defdam_goliath_fraction = ((defending_fleets["goliath"] * defstats["Goliaths"][0]) + viruspop) / defdam
        else: 
            defdam_goliath_fraction = defending_fleets["goliath"] * defstats["Goliaths"][0] / defdam

    else:
        defdam_goliath_fraction = 0

    attdam = attdam * attfactor * ((1.0 + 0.005 * attacker.research_percent_military) / \
                                   (1.0 + 0.005 * defender.research_percent_military))

    defdam = defdam * deffactor * ((1.0 + 0.005 * defender.research_percent_military) / \
                                   (1.0 + 0.005 * attacker.research_percent_military))


    if attdam >= 1.0:
        attdam -= attdam * (1.0 - pow(2.5, -(shields / attdam)))

    # ========= Determine if anyone will flee =========#
    # damage is too high defender flee
    if (defdam < 1.0) or (attdam / defdam) * 10.0 >= defender.ground_vs_air_percent:
        defender_flee = True
        return attacker_flee, defender_flee, {}, {}
    # defender flees, if settings are 100% this means attacker deals 10x more damage than defender
    if (attdam / defdam) * 100.0 >= defender.ground_vs_air_percent:
        defdam *= 0.15
        attdam *= 0.10
    # attacker flees, same logic as above
    if (attdam >= 1.0) and (defdam / attdam) * 100.0 >= attacker.ground_vs_air_percent:
        defdam *= 0.30
        attdam *= 0.15
        attacker_flee = True
    if attdam == 0:
        attacker_flee = True


    # ========= Damage to attacking fleets =========#
    hptransport = attacking_fleet.transport * attstats["Transports"][3]
    hpcruiser = attacking_fleet.cruiser * attstats["Cruisers"][3]
    hpphantom = attacking_fleet.phantom * attstats["Phantoms"][3]
    hpbomber = attacking_fleet.bomber * attstats["Bombers"][3]
    
    hpnecro = 0
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hptransport + hpcruiser + hpbomber + hpphantom + hpnecro

    damtransport = 0
    damcruiser = 0
    damphantom = 0
    dambomber = 0
    damnecro = 0

    # percentage of damage that wil be received by the unit
    if hptotal:
        damtransport = hptransport / hptotal
        damcruiser = hpcruiser / hptotal
        damphantom = hpphantom / hptotal
        dambomber = hpbomber / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    # calc attacking/defending goliath/bomber+cruiser ratio,
    # transfer the damage from transports to other fleet depending on the ratios
    if attacking_fleet.bomber > 0 or attacking_fleet.cruiser > 0:
        if virus.empire_holding == defender.empire:
            fa = (defending_fleets["goliath"] +( attacked_planet.current_population / 100))/ (attacking_fleet.bomber + attacking_fleet.cruiser)
        else:
            fa = defending_fleets["goliath"] / (attacking_fleet.bomber + attacking_fleet.cruiser)
    else:
        if virus.empire_holding == defender.empire:
            fa = defending_fleets["goliath"] +( attacked_planet.current_population / 100)
        else:
            fa = defending_fleets["goliath"]


    fb = damtransport + damcruiser + dambomber + damphantom + damnecro
    if fb >= 0.00001:
        fa = defdam / fb
        damtransport *= fa
        damcruiser *= fa
        dambomber *= fa
        damphantom *= fa
        damnecro *= fa

    if damtransport > hptransport:
        damcruiser += damtransport - hptransport
    if damcruiser > hpcruiser:
        dambomber += damcruiser - hpcruiser
    if dambomber > hpbomber:
        damphantom += dambomber - hpbomber
    if damphantom > hpphantom:
        damcruiser += damphantom - hpphantom
    if damnecro > hpnecro:
        damtransport += damnecro - hpnecro

    neckilled = 0
    if necro.empire_holding == attacker.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()

    attacker_losses = {"Bombers": round(min(attacking_fleet.bomber, dambomber / attstats["Bombers"][3])),
                       "Fighters": 0,
                       "Transports": round(min(attacking_fleet.transport, damtransport / attstats["Transports"][3])),
                       "Cruisers": round(min(attacking_fleet.cruiser, damcruiser / attstats["Cruisers"][3])),
                       "Carriers": 0,
                       "Soldiers": 0, "Droids": 0, "Goliaths": 0,
                       "Phantoms": round(min(attacking_fleet.phantom, damphantom / attstats["Phantoms"][3])),
                       "Necromancers": neckilled}

    calc_lost_units_attacker(attacking_fleet, attacker_losses)
    attacking_fleet.save()

    # ========= Damage to defending fleets =========#
    hpgoliath  = defending_fleets["goliath"] * defstats["Goliaths"][1]
    hpphantom = defending_fleets["phantom"] * defstats["Phantoms"][3]
    
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        hppop = attacked_planet.current_population * defstats["Goliaths"][1] / 100
    else:
        hppop = 0
    
    hpnecro = 0
    if necro.empire_holding == defender.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hpcruiser + hpphantom + hppop + hpnecro

    damgoliath = 0
    damphantom = 0
    dampop = 0
    damnecro = 0

    if hptotal:
        damgoliath = hpgoliath / hptotal
        damphantom = hpphantom / hptotal
        dampop = hppop / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    damgoliath *= attdam
    damphantom *= attdam
    dampop *= attdam
    damnecro *= attdam

    if damgoliath > hpgoliath:
        dampop += damgoliath - hpgoliath
    if damphantom > hpphantom:
        damgoliath += damphantom - hpphantom
    if dampop > hppop:    
        damphantom += dampop - hppop
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
    
    if virus.empire_holding == defender.empire:
        popkilled = round(min(attacked_planet.current_population, dampop * 100.0 / defstats["Goliaths"][3]))
    else:
        popkilled = 0
    
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    neckilled = 0
    if necro.empire_holding == defender.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
        
    defender_losses = {"Bombers": 0, "Fighters": 0,"Transports": 0,
                       "Cruisers": 0, "Carriers": 0, "Soldiers": 0, "Droids": 0,
                       "Goliaths": round(min(defending_fleets["goliath"], damgoliath / defstats["Goliaths"][1])),
                       "Phantoms": round(min(defending_fleets["phantom"], damphantom / defstats["Phantoms"][3])),
                       "Defence Satellites": 0, "Planet population": popkilled,
                       "Necromancers": neckilled}

    attacked_planet.defense_sats -= defender_losses["Defence Satellites"]
    attacked_planet.current_population -= popkilled
    attacked_planet.save()

    defending_fleets["goliath"] -= defender_losses["Goliaths"]
    defending_fleets["phantom"] -= defender_losses["Phantoms"]

    return attacker_flee, defender_flee, attacker_losses, defender_losses

####################
#      PHASE 4     #
####################
def phase4(attacking_fleet,
           defending_fleets,
           attstats, defstats,
           attfactor,
           deffactor,
           attacked_planet,
           attacker,
           defender,
           shields):
    attacker_flee = False
    defender_flee = False
    
    nrg = 0
    mins = 0
    crys = 0
    ectro = 0
    
    ironside = Artefacts.objects.get(name="Ironside Effect")
    if ironside.empire_holding == attacker.empire:
        nrg = round(defender.energy * 0.01)
        mins = round(defender.minerals * 0.005)
        crys = round(defender.crystals * 0.005)
        ectro = round(defender.ectrolium * 0.005)
    
    # ========= Calculate damage factors =========#
    attdam = attacking_fleet.soldier * attstats["Soldiers"][2] + \
             attacking_fleet.droid * attstats["Droids"][2] + \
             attacking_fleet.goliath * attstats["Goliaths"][2] + \
             attacking_fleet.phantom * attstats["Phantoms"][2]
    
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == attacker.empire:
        attdam += necro.effect1 * 3
    
    defdam = defending_fleets["soldier"] * defstats["Soldiers"][2] + \
             defending_fleets["droid"] * defstats["Droids"][2] + \
             defending_fleets["goliath"] * defstats["Goliaths"][2] + \
             defending_fleets["phantom"] * defstats["Phantoms"][2]
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        viruspop = attacked_planet.current_population * defstats["Goliaths"][2] / 100
    else:
        viruspop = attacked_planet.current_population * defstats["Soldiers"][2] / 100
    
    defdam += viruspop

    if necro.empire_holding == defender.empire:
        defdam += necro.effect1 * 3

    bomber_modifier = attacking_fleet.bomber * defstats["Bombers"][2] + \
                      attacking_fleet.cruiser *  defstats["Cruisers"][2]

    if attdam > 0:
        fa = bomber_modifier / attdam
        if fa < 0.5:
            attdam += bomber_modifier
        else:
            attdam += 0.5 * attdam * pow(2.0 * fa, 0.35)

    attdam = attdam * attfactor * ((1.0 + 0.005 * attacker.research_percent_military) / \
                                   (1.0 + 0.005 * defender.research_percent_military))

    defdam = defdam * deffactor * ((1.0 + 0.005 * defender.research_percent_military) / \
                                   (1.0 + 0.005 * attacker.research_percent_military))

    if attdam >= 1.0:
        attdam -= attdam * (1.0 - pow(2.5, -(shields / attdam)))

    # ========= Determine if anyone will flee =========#
    # damage is too high defender flee
    if (defdam < 1.0) or (attdam / defdam) * 10.0 >= defender.ground_vs_ground_percent:
        defender_flee = True
        defender_losses = {"Energy": nrg,
                       "Mineral": mins,
                       "Crystal": crys,
                       "Ectrolium": ectro}
        attacker.energy += nrg
        attacker.minerals += mins
        attacker.crystals += crys
        attacker.ectrolium += ectro
        attacker.save()
        
        defender.energy -= nrg
        defender.minerals -= mins
        defender.crystals -= crys
        defender.ectrolium -= ectro
        defender.save() 
        return attacker_flee, defender_flee, {}, defender_losses
    # defender flees, if settings are 100% this means attacker deals 10x more damage than defender
    if (attdam / defdam) * 100.0 >= defender.ground_vs_ground_percent:
        defdam *= 0.15
        attdam *= 0.10
    # attacker flees, same logic as above
    if (attdam >= 1.0) and (defdam / attdam) * 100.0 >= attacker.ground_vs_ground_percent:
        defdam *= 0.10
        attdam *= 0.20
        attacker_flee = True


    # ========= Damage to attacking fleets =========#
    hpsoldier  = attacking_fleet.soldier * attstats["Soldiers"][3]
    hpdroid  = attacking_fleet.droid * attstats["Droids"][3]
    hpphantom = attacking_fleet.phantom * attstats["Phantoms"][3]
    hpgoliath  = attacking_fleet.goliath * attstats["Goliaths"][3]
    hpnecro = 0
    
    if necro.empire_holding == attacker.empire:
        hpnecro = necro.effect1 * 10
    
    hptotal = hpsoldier + hpdroid + hpgoliath + hpphantom
    
    damsoldier = 0
    damdroid = 0
    damgoliath = 0
    damphantom = 0
    damnecro = 0

    # percentage of damage that wil be received by the unit
    if hptotal:
        damsoldier = hpsoldier / hptotal
        damdroid = hpdroid / hptotal
        damgoliath = hpgoliath / hptotal
        damphantom = hpphantom / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    # transfer the damage from goliahs to droids and soldiers
    fb = defending_fleets["soldier"] + defending_fleets["goliath"]
    fa = 0.0
    if fb >= 0.00001:
        fa = (attacking_fleet.soldier + attacking_fleet.droid) / fb
    damgoliath *= pow(1.50, -fa)

    fb = damsoldier + damdroid + damgoliath + damphantom + damnecro

    if fb >= 0.00001:
        fa = defdam / fb
        damsoldier *= fa
        damdroid *= fa
        damgoliath *= fa
        damphantom *= fa
        damnecro *= fa

    if damsoldier > hpsoldier:
        damdroid += damsoldier - hpsoldier
    if damdroid > hpdroid:
        damgoliath += damdroid - hpdroid
    if damgoliath > hpgoliath:
        damsoldier += damgoliath - hpgoliath
    if damsoldier > hpsoldier:
        damphantom += damsoldier - hpsoldier
    if damphantom > hpphantom:
        damdroid += damphantom - hpphantom
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
    
    neckilled = 0
    if necro.empire_holding == attacker.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()
    
    attacker_losses = {"Bombers": 0, "Fighters": 0, "Transports": 0, "Cruisers": 0, "Carriers": 0,
                       "Soldiers": round(min(attacking_fleet.soldier, damsoldier / attstats["Soldiers"][3])),
                       "Droids": round(min(attacking_fleet.droid, damdroid / attstats["Droids"][3])),
                       "Goliaths": round(min(attacking_fleet.goliath, damgoliath / attstats["Goliaths"][3])),
                       "Phantoms": round(min(attacking_fleet.phantom, damphantom / attstats["Phantoms"][3])),
                       "Necromancers": neckilled}
    
    calc_lost_units_attacker(attacking_fleet, attacker_losses)
    attacking_fleet.save()

    # ========= Damage to defending fleets =========#
    hpgoliath  = defending_fleets["goliath"] * defstats["Goliaths"][3]
    hpphantom = defending_fleets["phantom"] * defstats["Phantoms"][3]
    hpsoldier = defending_fleets["soldier"] * defstats["Soldiers"][3]
    hpdroid = defending_fleets["droid"] * defstats["Droids"][3]
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        hppop = attacked_planet.current_population * defstats["Goliaths"][3] / 100
    else:
        hppop = attacked_planet.current_population * defstats["Soldiers"][3] / 100
    
    hpnecro = 0
    necro = Artefacts.objects.get(name="Scroll of the Necromancer")
    if necro.empire_holding == defender.empire:
        hpnecro = necro.effect1 * 10 
    
    hptotal = hpsoldier + hpdroid + hpgoliath + hpphantom + hppop + hpnecro

    damsoldier = 0
    damdroid = 0
    damgoliath = 0
    damphantom = 0
    dampop =  0
    damnecro = 0

    if hptotal:
        damsoldier = hpsoldier / hptotal
        damdroid = hpdroid / hptotal
        damgoliath = hpgoliath / hptotal
        damphantom = hpphantom / hptotal
        dampop = hppop / hptotal
    
    if hpnecro >=1:
        damnecro = hpnecro / hptotal

    # transfer the damage from goliahs to droids and soldiers
    fb = (attacking_fleet.soldier + attacking_fleet.droid)
    fa = 0.0
    if fb >= 0.00001:
        fa = (defending_fleets["soldier"] + defending_fleets["goliath"]) / fb
    damgoliath *= pow(1.50, -fa)

    fb = damsoldier + damdroid + damgoliath + damphantom + dampop + damnecro

    if fb >= 0.00001:
        fa = attdam / fb
        damsoldier *= fa
        damdroid *= fa
        damgoliath *= fa
        damphantom *= fa
        dampop *= fa
        damnecro *= fa

    if damsoldier > hpsoldier:
        damdroid += damsoldier - hpsoldier
    if damdroid > hpdroid:
        damgoliath += damdroid - hpdroid
    if damgoliath > hpgoliath:
        dampop += damgoliath - hpgoliath
    if dampop > hppop:
        damsoldier += dampop - hppop
    if damsoldier > hpsoldier:
        damphantom += damsoldier - hpsoldier
    if damphantom > hpphantom:
        damdroid += damphantom - hpphantom
    if damnecro > hpnecro:
        damphantom += damnecro - hpnecro
        
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        popkilled = round(min(attacked_planet.current_population, dampop * 100.0 / defstats["Goliaths"][3]))
    else:
        popkilled = round(min(attacked_planet.current_population, dampop * 100.0 / defstats["Soldiers"][3]))
    
    neckilled = 0
    if necro.empire_holding == defender.empire:
        neckilled = round(min(necro.effect1, damnecro / 100.0))
        necro.effect1 -= neckilled
        necro.save()       
    
    defender_losses = {"Bombers": 0, "Fighters": 0,"Transports": 0,
                       "Cruisers": 0, "Carriers": 0,
                       "Soldiers": round(min(defending_fleets["soldier"], damsoldier / defstats["Soldiers"][3])),
                       "Droids": round(min(defending_fleets["droid"], damdroid / defstats["Droids"][3])),
                       "Goliaths": round(min(defending_fleets["goliath"], damgoliath / defstats["Goliaths"][3])),
                       "Phantoms": round(min(defending_fleets["phantom"], damphantom / defstats["Phantoms"][3])),
                       "Defence Satellites": 0,
                       "Planet population": popkilled,
                       "Necromancers": neckilled,
                       "Energy": nrg,
                       "Mineral": mins,
                       "Crystal": crys,
                       "Ectrolium": ectro}

    attacked_planet.current_population -= popkilled
    attacked_planet.save()

    defending_fleets["goliath"] -= defender_losses["Goliaths"]
    defending_fleets["phantom"] -= defender_losses["Phantoms"]
    defending_fleets["droid"] -= defender_losses["Droids"]
    defending_fleets["soldier"] -= defender_losses["Soldiers"]

    # calculate the ground attack /defence after the battle to see if the planet is taken
    attdam = attacking_fleet.soldier * attstats["Soldiers"][2] + \
             attacking_fleet.droid * attstats["Droids"][2] + \
             attacking_fleet.goliath * attstats["Goliaths"][2] + \
             attacking_fleet.phantom * attstats["Phantoms"][2]

    defdam = defending_fleets["soldier"] * defstats["Soldiers"][2] + \
             defending_fleets["droid"] * defstats["Droids"][2] + \
             defending_fleets["goliath"] * defstats["Goliaths"][2] + \
             defending_fleets["phantom"] * defstats["Phantoms"][2] + \
             necro.effect1 * 3
    virus = Artefacts.objects.get(name="t-Veronica")
    if virus.empire_holding == defender.empire:
        viruspop = attacked_planet.current_population * defstats["Goliaths"][2] / 100
    else:
        viruspop = attacked_planet.current_population * defstats["Soldiers"][2] / 100
    
    defdam += viruspop
    
    attacker.energy += nrg
    attacker.minerals += mins
    attacker.crystals += crys
    attacker.ectrolium += ectro
    attacker.save()
    
    defender.energy -= nrg
    defender.minerals -= mins
    defender.crystals -= crys
    defender.ectrolium -= ectro
    defender.save() 
    
    if attacker_flee or attdam <= defdam:
        attacker_flee = True
    else:
        defender_flee = True

    return attacker_flee, defender_flee, attacker_losses, defender_losses
    msg += str(attacking_fleet.owner)
