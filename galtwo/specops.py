import numpy as np
from .helper_classes import *
from app.constants import *
from galtwo.models import *
from datetime import datetime
from django.db.models import Sum
import random
import secrets
import math
from galtwo.calculations import *
from app.specops import psychicop_specs, agentop_specs, inca_specs


all_spells = ["Irradiate Ectrolium",
              "Dark Web",
              "Incandescence",
              "Black Mist",
              "War Illusions",
              "Psychic Assault",
              "Phantoms",
              "Enlightenment",
              "Grow Planet's Size"]
    
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
                "Spoil Resources",
                ]

all_incantations = ["Survey System", "Sense Artefact", "Planetary Shielding", "Portal Force Field", "Mind Control", "Call to Arms", "Energy Surge"]

def specopReadiness(specop, type, user1, *args):
    user2 = None
    if args:
        user2 = args[0]

    if type == "Spell":
        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == user1.empire:
            penalty = get_op_penalty(user1.research_percent_culture, (specop[0]/2))
        else:
            penalty = get_op_penalty(user1.research_percent_culture, specop[0])
        if user2 == None and specop[3] == False:
            return -1
        if specop[3]: #if self op
            fr = int((1.0 + 0.01 * penalty) * specop[1])
            arte = Artefacts.objects.get(name="Magus Cloak")
            if arte.empire_holding == user1.empire:
                fr = round(fr*0.75)
            return fr
    else:
        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == user1.empire:
            penalty = get_op_penalty(user1.research_percent_operations, (specop[0]/2))
        else:
            penalty = get_op_penalty(user1.research_percent_operations, specop[0])


    if penalty == -1:
        return -1


    empire1 = user1.empire
    empire2 = user2.empire

    fa = (1 + user1.num_planets) / (1 + user2.num_planets)
    fb = (1 + empire1.planets) / (1 + empire2.planets)
    fa = pow(fa, 1.8)
    fb = pow(fb, 1.2)
    fa = 0.5 * (fa + fb)

    if fa < 0.75:
        fa = 0.75

    fa = (1.0 + 0.01 * penalty) * specop[1] * fa

    relations_from_empire = Relations.objects.filter(empire1=empire1)
    relations_to_empire = Relations.objects.filter(empire2=empire1)

    war = False
    ally = False
    nap = False

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

    if nap:
        fa = max(50, fa)

    if fa > 300:
        fa = 300

    return round(fa)


def get_op_penalty(research, requirement):
    a = requirement - research
    if a <= 0:
        return 0
    da = pow(a, 1.20)
    if da >= 150.0:
        return -1
    return round(da)


def perform_spell(spell, psychics, status, *args):
    game_round = RoundStatus.objects.filter().first()
    if game_round.tick_number == 0:
        return "You cannot perform spells before the round has started!"
    else:
        if spell not in psychicop_specs:
            return "This spell is broken/doesnt exist!"

        fa = 0.4 + (1.2 / 255.0) * (np.random.randint(0, 2147483647) & 255)

        attack = fa * race_info_list[status.get_race_display()].get("psychics_coeff", 1.0) * \
                 psychics * (1.0 + 0.005 * status.research_percent_culture)
                 
        attack /= psychicop_specs[spell][2]
        
        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == status.empire:
            penalty = get_op_penalty(status.research_percent_culture, (psychicop_specs[spell][0]/2))
        else:
            penalty = get_op_penalty(status.research_percent_culture, psychicop_specs[spell][0])
        

        if penalty == -1:
            return "You don't have enough psychic research to perform this spell!"

        if penalty > 0:
            attack /= 1.0 + 0.01 * penalty

        fleet1 = Fleet.objects.get(owner=status.id, main_fleet=True)
        news_message = ""
        news_message2 = ""
        message = ""

        if args[0]:
            user2 = args[0]
            if user2 == status and psychicop_specs[spell][3] is False:
                message += "You cannot perform this spell on yourself!"
                return message
            empire2 = user2.empire
            fleet2 = Fleet.objects.get(owner=user2.id, main_fleet=True)
            psychics2 = fleet2.wizard
            print(psychics2)
            defence = race_info_list[user2.get_race_display()].get("psychics_coeff", 1.0) * psychics2 * \
                      (1.0 + 0.005 * user2.research_percent_culture)
            success = attack / (defence + 1)
            if success < 2.0:
                refdef = 0.5 * pow((0.5 * success), 1.1)
                refatt = 1.0 - refdef
                tlosses = 1.0 - pow((0.5 * success), 0.2)
                fc = 0.75 + (0.5 / 255.0) * (np.random.randint(0, 2147483647) & 255)
                loss1 = min(psychics,round(fc * refatt * tlosses * psychics))
                loss2 = min(psychics2,round(fc * refdef * tlosses * psychics2))
                if loss1 > 0:
                    fleet1.wizard -= loss1
                    fleet1.save()
                if loss2 > 0:
                    fleet2.wizard -= loss2
                    fleet2.save()
                if loss1 > 0 or loss2 > 0:
                    message += "Attacker lost " + str(loss1) + " Psychics. Defender lost: " + str(loss2) + " Psychics. "
                    news_message += "Attacker lost " + str(loss1) + " Psychics. Defender lost: " + str(loss2) + " Psychics.\n"
                    news_message2 += "Attacker lost " + str(loss1) + " Psychics. Defender lost: " + str(loss2) + " Psychics.\n"
        if penalty > 0:
            attack = attack / (1.0 + 0.01 * penalty)

        if spell == "Incandescence":
            cry_converted = attack * 5
            if cry_converted > status.crystals:
                cry_converted = status.crystals
            cry_converted = int(cry_converted)
            status.crystals -= cry_converted

            energy = int(cry_converted * 24.0 * (1.0 + 0.01 * status.research_percent_culture))
            status.energy += energy
            news_message += str(cry_converted) + " crystals were converted into " + str(energy) + " energy!"
            message += "Your " + str(cry_converted) + " crystals were converted into " + str(energy) + " energy!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)
        if spell == "Irradiate Ectrolium":
            destroyed_ectro = 0
            if success >= 1:
                frac_destroyed = 0.2
            elif success >= 0.6:
                frac_destroyed = (20.0 / 0.6) * (success - 0.4) * 0.01
            else:
                frac_destroyed = 0

            if frac_destroyed > 0:
                destroyed_ectro = int(frac_destroyed * user2.ectrolium)
                user2.ectrolium -= destroyed_ectro
                user2.military_flag = 1
                user2.save()
                news_message += str(destroyed_ectro) + " ectrolium was destroyed!"
                message += "You have irradiated " + str(destroyed_ectro) + " ectrolium!"
            else:
                news_message += "Your psychics failed!"
                message += "Your psychics failed!"
                news_message2 += "Your psychics overpowered the Enemy!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status, user2)
            

        if spell == 'Dark Web':
            web = 100 * (attack / status.networth)
            effect = round(web * 3.5)
            time = random.randint(1,31)+24
            Specops.objects.create(user_to=status.user,
                                   user_from=status.user,
                                   specop_type='S',
                                   name="Dark Web",
                                   specop_strength=effect,
                                   ticks_left=time)

            news_message += status.user_name + "'s' psychics have given them " + str(effect) + "% extra protection for " + str(time) + " weeks!"
            message += "Your psychics have given you " + str(effect) + "% extra protection for " + str (time) + " weeks!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)
        if spell == "Black Mist":
            if success >= 1.0:
                effect = 25
            elif success >= 0.6:
                effect = int((25.0 / 0.6) * (success - 0.4))
            else:
                effect = 0
                
            if effect > 0:
                time = random.randint(26, 57)
                Specops.objects.create(user_to=user2.user,
                                       user_from=status.user,
                                       specop_type='S',
                                       name="Black Mist",
                                       specop_strength=effect,
                                       ticks_left=time)
                news_message += " solar power reduced by " + str(effect) + "%!"
                message += "A black mist is spreading over " + str(user2.user_name) + \
                          " planets, reducing solar collectors efficiency by " + str(effect)
            else:
                news_message += " solar power wasn't reduced!"
                message += "Your psychic power wasn't enough to cast a black mist!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status, user2)
        if spell == 'War Illusions':
            Specops.objects.filter(user_to=status.user, name="War Illusions").delete()
            illusion = 100 * (attack / status.networth)
            illusions = illusion * 4.5
            effect = min(50, round(illusions * (random.randint(1,20)/25)))
            time = random.randint(1,31)+32
            Specops.objects.create(user_to=status.user,
                                   user_from=status.user,
                                   specop_type='S',
                                   name="War Illusions",
                                   specop_strength=effect,
                                   ticks_left=time)

            news_message += status.user_name + "'s' psychics powerful illusions have given their forces " + str(effect) + "% extra strength for " + str(time) + " weeks!"
            message += "Your psychics have given your forces " + str(effect) + "% extra strength for " + str (time) + " weeks!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)
        if spell == "Psychic Assault":
            refdef = pow(attack / (attack + defence), 1.1)
            refatt = pow(defence / (attack + defence), 1.1)
            tlosses = 0.2

            psychics_loss1 = min(int(refatt * tlosses * psychics), psychics)
            fleet1.wizard -= psychics_loss1
            fleet1.save()

            psychics_loss2 = min(int(refdef * tlosses * psychics2), psychics2)
            fleet2.wizard -= psychics_loss2
            fleet2.save()

            news_message += str(psychics_loss1) + " psychics were lost by " + status.user_name + \
                           " and " + str(psychics_loss2) + " were lost by " + user2.user_name + "!"
            message += "You have assaulted " + str(psychics_loss2) + " enemy psychics of " + user2.user_name + \
                      " however " + str(psychics_loss1) + " of your psychics have also suffered critical brain damages!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status, user2)
        if spell =="Phantoms":
            phantom_cast = round(attack / 2)
            fleet1.phantom += phantom_cast
            fleet1.save()

            news_message += status.user_name + " has summoned " + str(phantom_cast) + " Phantoms to fight in their army!"
            message += "You have summoned " + str(phantom_cast) + " Phantoms to join your army!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)
        
        if spell =="Grow Planet's Size":
            planet = random.choice(Planets.objects.filter(owner=status.user))
            grow = (attack * 1.3)
            growth = np.clip(round(200 * grow / status.networth / 2 * (status.num_planets/10)),0,300)
            planet.size += growth
            pportal = 0
            if planet.portal:
                pportal = 1
                
            total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
            planet.overbuilt = calc_overbuild(planet.size, total_buildings)
            planet.overbuilt_percent = (planet.overbuilt - 1.0) * 100
            planet.save()

            news_message += status.user_name + "'s planet " + str(planet.x) + "," + str(planet.y) + ":" + str(planet.i) + " has grown by " + str(growth)
            message += "Your planet  " + str(planet.x) + "," + str(planet.y) + ":" + str(planet.i) + " has grown by " + str(growth)
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)
        if spell == "Enlightenment":
            Specops.objects.filter(user_to=status.user, name="Enlightenment").delete()
            time = 52
            power = (100 * (attack / status.networth) / 10)
            boost = round(power * 3.5)
            element = ['Energy', 'Mineral', 'Crystal', 'Ectrolium', 'Research']
            chosen = secrets.choice(element)
            if chosen == "Energy" or "Crystal":
                bonus = np.clip(boost, 0, 15)
            if chosen == "Ectrolium" or "Research":
                bonus = np.clip(boost, 0, 10)
            if chosen == "Mineral":
                bonus = np.clip(boost, 0, 20)
            if chosen == "Speed":
                bonus = np.clip((boost * 2.5), 0, 50)
            if chosen == "BadFR":
                bonus = max(round(100.0*(1.0 - 100.0 / (boost + 100.0))), 30)

            Specops.objects.create(user_to=status.user,
                                   user_from=status.user,
                                   specop_type='S',
                                   name="Enlightenment",
                                   specop_strength=bonus,
                                   extra_effect=chosen,
                                   ticks_left=time)

            news_message += status.user_name + "'s Psychics have blessed them with " + str(bonus) + "% extra " + str(
                chosen) + " for 52 weeks!"
            message += "Your Psychics have blessed you with " + str(bonus) + "% extra " + str(chosen) + " for 52 weeks!"
            prloss = specopReadiness(psychicop_specs[spell],"Spell", status)    

        status.psychic_readiness -= prloss
        status.save()

        if psychicop_specs[spell][3] == True:
            News.objects.create(user1=User.objects.get(id=status.id),
                                user2=User.objects.get(id=status.id),
                                empire1=status.empire,
                                fleet1=spell,
                                news_type='PD',
                                date_and_time=datetime.now(),
                                is_personal_news=True,
                                is_empire_news=True,
                                extra_info=news_message,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
        else:
            News.objects.create(user1=User.objects.get(id=status.id),
                                user2=User.objects.get(id=user2.id),
                                empire1=status.empire,
                                empire2=empire2,
                                fleet1=spell,
                                news_type='PA',
                                date_and_time=datetime.now(),
                                is_personal_news=True,
                                is_empire_news=True,
                                extra_info=news_message,
                                tick_number=RoundStatus.objects.get().tick_number
                                )

            News.objects.create(user1=User.objects.get(id=user2.id),
                                user2=User.objects.get(id=status.id),
                                empire1=empire2,
                                empire2=status.empire,
                                fleet1=spell,
                                news_type='PD',
                                date_and_time=datetime.now(),
                                is_personal_news=True,
                                is_empire_news=True,
                                extra_info=news_message,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
        return message

        # if news_message2_empire1:
        #
        #
        #
        # if news_message2_empire2:


def perform_operation(agent_fleet):
    operation = agent_fleet.specop
    agents = agent_fleet.agent
    user = agent_fleet.owner
    target_planet = agent_fleet.target_planet
    user1 = UserStatus.objects.get(user=user)
    if user1.agent_readiness < 0:
        news_message = "Not enough Agents Readiness, Agents returning!"
        user1.military_flag = 1
        user1.save()
        News.objects.create(user1=User.objects.get(id=user.id),
                            user2=None,
                            empire1=user1.empire,
                            fleet1=operation,
                            news_type='AA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
    else:    
    
        user1.military_flag = 2
        user1.save
        if operation not in agentop_specs:
            return "This operation is broken/doesnt exist!"

        fa = 0.6 + (0.8/ 255.0) * (np.random.randint(0, 2147483647) & 255)

        attack = fa * race_info_list[user1.get_race_display()].get("agents_coeff", 1.0) * \
                 agents * (1.0 + 0.01 * user1.research_percent_operations)

        attack /= agentop_specs[operation][2]

        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == user1.empire:
            penalty = get_op_penalty(user1.research_percent_operations, (agentop_specs[operation][0]/2))
        else:
            penalty = get_op_penalty(user1.research_percent_operations, agentop_specs[operation][0])
        

        if penalty == -1:
            return "You don't have enough operations research to perform this covert operation!"

        if penalty > 0:
            attack /= 1.0 + 0.01 * penalty

        defense = 50
        user2 = None
        stealth = True
        empire2 = None

        if target_planet.owner is not None:
            user2 = UserStatus.objects.get(id=target_planet.owner.id)
            empire2 = user2.empire
            fleet2 = Fleet.objects.get(owner=user2.id, main_fleet=True)
            agents2 = fleet2.agent
            defense = agents2 * race_info_list[user2.get_race_display()].get("agents_coeff", 1.0) * \
                      (1.0 + 0.01 * user2.research_percent_operations)

        success = min(3.0, attack / (defense + 1))
        news_message = ""
        news_message2 = ""

        if success < 2.0 and target_planet.owner is not None:
            stealth = False
            refdef = 0.5 * pow((0.5 * success), 1.1)
            refatt = 1.0 - refdef
            tlosses = 1.0 - pow((0.5 * success), 0.2)
            fc = 0.75 + (0.5 / 255.0) * (np.random.randint(0, 2147483647) & 255)
            loss1 = min(agents, round(fc * refatt * tlosses *agents))
            loss2 = min(agents2, round(fc * refdef * tlosses * agents2))
            agent_fleet.agent -= loss1
            agent_fleet.save()
            fleet2.agent -= loss2
            fleet2.save()
            news_message += "Attacker lost " + str(loss1) + " agents. Defender lost: " + str(loss2) + " agents.\n"
            news_message2 += "Attacker lost " + str(loss1) + " agents. Defender lost: " + str(loss2) + " agents.\n"


        if operation == "Observe Planet":
            if success < 0.4:
                news_message += "No information was gathered about this planet!"
            if success >= 0.4:
                news_message += "Planet size: " + str(target_planet.size)
            if success >= 0.9:
                if target_planet.bonus_solar > 0:
                    news_message += "\nSolar bonus: " + str(target_planet.bonus_solar)
                if target_planet.bonus_fission > 0:
                    news_message += "\nFission bonus: " + str(target_planet.bonus_fission)
                if target_planet.bonus_mineral > 0:
                    news_message += "\nMineral bonus: " + str(target_planet.bonus_mineral)
                if target_planet.bonus_crystal > 0:
                    news_message += "\nCrystal bonus: " + str(target_planet.bonus_crystal)
                if target_planet.bonus_ectrolium > 0:
                    news_message += "\nEctrolium bonus: " + str(target_planet.bonus_ectrolium)
            if target_planet.owner is not None:
                if success >= 0.5:
                    news_message += "\nCurrent population: " + str(target_planet.current_population)
                if success >= 0.6:
                    news_message += "\nMax population: " + str(target_planet.max_population)
                if success >= 0.7:
                    news_message += "\nPortal protection: " + str(target_planet.protection)
                if success >= 0.8:
                    news_message += "\nSolar collectors: " + str(target_planet.solar_collectors)
                    news_message += "\nFission Reactors: " + str(target_planet.fission_reactors)
                    news_message += "\nMineral Plants: " + str(target_planet.mineral_plants)
                    news_message += "\nCrystal Labs: " + str(target_planet.crystal_labs)
                    news_message += "\nRefinement Stations: " + str(target_planet.refinement_stations)
                    news_message += "\nCities: " + str(target_planet.cities)
                    news_message += "\nResearch Centers: " + str(target_planet.research_centers)
                    news_message += "\nDefense Sats: " + str(target_planet.defense_sats)
                    news_message += "\nShield Networks: " + str(target_planet.shield_networks)
                if success >= 1.0:
                    if target_planet.portal:
                        news_message += "\nPortal: Present"
                    elif target_planet.portal_under_construction:
                        news_message += "\nPortal: Under construction"
                    else:
                        news_message += "\nPortal: Absent"
            if target_planet.artefact is not None:
            	if success >= 1.0:
                    news_message += "\nArtefact: Present, the " + target_planet.artefact.name
            scouting = Scouting.objects.filter(user=user, planet=target_planet).first()
            if scouting is None:
                Scouting.objects.create(user=user, planet=target_planet, scout=success)
            else:
                if scouting.scout < success:
                    scouting.scout = success
                    scouting.save()

        if operation == "Spy Target":
            if success < 0.4:
                news_message += "No information was gathered about this faction!"
            if success >= 0.5:
                news_message += "\nFleet readiness: " + str(user2.fleet_readiness)
            if success >= 0.7:
                news_message += "\nPsychic readiness: " + str(user2.psychic_readiness)
            if success >= 0.9:
                news_message += "\nAgent readiness: " + str(user2.agent_readiness)
            if success >= 1.0:
                news_message += "\nEnergy: " + str(user2.energy)
            if success >= 0.6:
                news_message += "\nMinerals: " + str(user2.minerals)
            if success >= 0.4:
                news_message += "\nCrystals: " + str(user2.crystals)
            if success >= 0.8:
                news_message += "\nEctrolium: " + str(user2.ectrolium)
            if success >= 0.9:
                news_message += "\nPopulation: " + str(user2.population)

        if operation == "Network Infiltration":
            lost_research_pct = 0
            if success >= 1.0:
                lost_research_pct = 3
            else: 
                lost_research_pct = min(3, round((3.0 / 0.6) * (success - 0.4), 2))
            if lost_research_pct > 0:
                fa = 0.3 + (0.7 / 255.0) * (np.random.randint(0, 2147483647) & 255)
                gained_research_pct = round(lost_research_pct * fa, 2)
                for research in researchNames:
                    lost_research_points = int(getattr(user2, research) * (0.01 * lost_research_pct))
                    research_points_new2 = getattr(user2, research) - lost_research_points
                    setattr(user2, research, research_points_new2)
                    research_points_new1 = getattr(user1, research) + int(lost_research_points * fa)
                    setattr(user1, research, research_points_new1)
                news_message += "\n" + str(lost_research_pct) + "% research was lost by the defender! " + \
                                       str(gained_research_pct) + "% research was stolen for our faction!"
                news_message2 += "\n" + str(lost_research_pct) + "% research was lost!"
                user2.save()
                user1.save()
            else:
                news_message += "\nNo research was stolen!"
                news_message2 += "\nNo research was lost!"

        if operation == "Diplomatic Espionage":
            if success >= 1.0:
                if success >= 1:
                    time = 50
                else:
                    time = min(50, int(pow(7, success)))
                Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       extra_effect="show special operations affecting target",
                                       stealth=stealth,
                                       name="Diplomatic Espionage",
                                       ticks_left=time)
                news_message += "Your agents gathered information about all special operations affecting" \
                               " the target faction currently!"
            else:
                news_message += "Your agents couldn't gather any information!"
        if target_planet.owner is not None:
            user1.agent_readiness -= specopReadiness(agentop_specs[operation],"Operation", user1, user2)
            user1.save()
        else: 
            user1.agent_readiness -= agentop_specs[operation][1]
            user1.save()
        

        if operation == "Maps theft":
            if success < 1:
                news_message += "Your agents couldn't gather any information!"
                news_message2 += "Your agents defended your maps information!"
            else:
                scouting1 = Scouting.objects.filter(user=user)
                scouting2 = Scouting.objects.filter(user=user2.user)

                planets ={}
                for s1 in scouting1:
                    planets[s1.planet.id] = s1

                fa = min(100, round(pow(success,3)*12.5))
                news_message += "Your agents managed to gather scouting informaton about " +str(fa) \
                                +'% planets of target faction!'

                news_message2 += "Your scouting maps were stolen!"

                for s2 in scouting2:
                    r = random.randint(0, 100)
                    if r > fa:
                        continue
                    if s2.planet.id in planets:
                        tmp_scouting = planets[s2.planet.id]
                        tmp_scouting.scout = max(tmp_scouting.scout, s2.scout)
                        tmp_scouting.save()
                    else:
                        Scouting.objects.create(user=user1.user,
                                                planet=s2.planet,
                                                scout=s2.scout)

        if operation == "Planetary Beacon":
            if success >= 1:
                Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       name="Planetary Beacon",
                                       stealth=stealth,
                                       ticks_left=24,
                                       planet=target_planet)
                news_message += "All dark web effects were removed from the planet, however the planet defenders gained +10% military bonus!"
                news_message2 += "All dark web effects were removed from the planet, however the planet defenders gained +10% military bonus!"

        
        if operation == "Spoil Resources":
            lost_resource_pct = 0
            if success > 1.0:
                lost_resource_pct = 1
                time = 32
            else:
                lost_resource_pct = min(1, round((1.0 / 0.6) * (success -0.4), 2))
                time = min(32, int(pow(7, success)))
            if lost_resource_pct > 0:
                news_message += "\n" + str(lost_resource_pct) + "% decay rate among resources for " + str(time) + " weeks!" 
                news_message2 += "\nWe are currently losing " + str(lost_resource_pct) + "% of our resources for " + str(time) + " weeks!"
                Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       specop_strength=lost_resource_pct,
                                       stealth=stealth,
                                       name="Spoil Resources",
                                       ticks_left=time)
            else:
                news_message += "\nNo resources were damaged"
                news_message2 += "\nNo resources were damaged"
        
        if operation == "Hack mainframe":
            if success >= 1.0:
                energy_pct1 = 20
                energy_pct2 = 20
            else:
                energy_pct1 = round((20.0 / 0.6) * (success - 0.4))
                energy_pct2 = round((20.0 / 0.6) * (success - 0.4))

            if energy_pct1 > 0:
                length = min(32, round(pow(6,success+0.6)))
                if success >= 1.0:
                    Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       specop_strength=energy_pct1,
                                       specop_strength2=energy_pct2,
                                       stealth=stealth,
                                       name="Hack mainframe",
                                       ticks_left=length,
                                       date_and_time=datetime.now())
                                       
                news_message += "Mainframe computer network was successfully hacked, energy flows transferred to our empire!"
                news_message += "\nTarget income lost: " + str(energy_pct1) +"%"
                news_message += "\nOur income increase: " + str(energy_pct2)  +"%"
                news_message2 += "Our mainframe computers were hacked, energy production channelled away from our grid!"
                news_message2 += "\nOur income lost: " + str(energy_pct1) +"%"
            else:
                news_message += "\nYour agents didn't succeed!"
                news_message2 += "\nYour agents managed to defend!"

        if operation == "Infiltration":
            if success < 0.4:
                news_message += "No information was gathered about this faction!"
            if success >= 0.5:
                news_message += "Energy: " + str(user2.energy)
            if success >= 0.6:
                news_message += "\nMinerals: " + str(user2.minerals)
            if success >= 0.4:
                news_message += "\nCrystals: " + str(user2.crystals)
            if success >= 0.8:
                news_message += "\nEctrolium: " + str(user2.ectrolium)
            if success >= 0.7:
                news_message += "\nSolar Collectors: " + str(user2.total_solar_collectors)
            if success >= 1.0:
                news_message += "\nFission Reactors: " + str(user2.total_fission_reactors)
            if success >= 0.7:
                news_message += "\nMineral Plants: " + str(user2.total_mineral_plants)
            if success >= 0.6:
                news_message += "\nCrystal Laboratories: " + str(user2.total_crystal_labs)
            if success >= 0.9:
                news_message += "\nRefinement Stations: " + str(user2.total_refinement_stations)
            if success >= 0.5:
                news_message += "\nCities: " + str(user2.total_cities)
            if success >= 0.6:
                news_message += "\nResearch Centers: " + str(user2.total_research_centers)
            if success >= 0.4:
                news_message += "\nDefense Satellites: " + str(user2.total_defense_sats)
            if success >= 0.9:
                news_message += "\nShield Network: " + str(user2.total_shield_networks)
            if success >= 1.0:
                news_message += "\nMilitary Research: " + str(user2.research_percent_military) + "%"
            if success >= 0.9:
                news_message += "\nContruction Research: " + str(user2.research_percent_construction) + "%"
            if success >= 0.8:
                news_message += "\nTechnology Research: " + str(user2.research_percent_tech) + "%"
            if success >= 0.6:
                news_message += "\nEnergy Research: " + str(user2.research_percent_energy) + "%"
            if success >= 0.7:
                news_message += "\nPopulation Research: " + str(user2.research_percent_population) + "%"
            if success >= 0.8:
                news_message += "\nCulture Research: " + str(user2.research_percent_culture) + "%"
            if success >= 1.0:
                news_message += "\nTOperations Research: " + str(user2.research_percent_operations) + "%"
            if success >= 1.0:
                news_message += "\nPortals Research: " + str(user2.research_percent_portals) + "%"

        if operation == "Bribe officials":
            if success >= 0.6:
                r = random.randint(0,1)
                news_message += "Your agents managed to successfully bribe certain officials!\n"
                news_message2 += "Your corrupt officials are slowing down our economy!\n"
                if r == 1: #increase resource cost
                    fa = min(300, round(success**2 * 33))
                    news_message += "Building costs increased by " + str(fa) + "%!"
                    news_message2 += "Building costs increased by " + str(fa) + "%!"
                    extra = "resource_cost"
                else: #increase building time
                    fa = min(900, round(success ** 2 * 100))
                    news_message += "Building time increased by " + str(fa) + "%!"
                    news_message2 += "Building time increased by " + str(fa) + "%!"
                    extra = "building_time"
                length = min(72, round(success *24))
                Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       specop_strength=fa,
                                       stealth=stealth,
                                       extra_effect=extra,
                                       name="Bribe officials",
                                       ticks_left=length)
            else:
                news_message += "Your agents didn't succeed!"
                news_message2 += "Your politicians seem to live the life of saints!"

        if operation == "Military Sabotage":
            if success >= 1.0:
                a = 8
            else:
                a = int((8.0 / 0.5) * (success - 0.5))
            if a > 0:
                news_message += "The following units from the main fleet were destroyed:\n"
                news_message2 += "The following units from the main fleet were destroyed:\n"
                main_fleet = Fleet.objects.get(owner=user2.user, main_fleet=True)
                no_units = True
                for unit in unit_info["unit_list"]:
                    num = getattr(main_fleet, unit)
                    if num:
                        fa = 0.01 * (a + random.randint(0, 3))
                        num_lost = int(num * fa)
                        if num_lost > 0:
                            no_units = False
                            news_message += unit_info[unit]['label'] + " : " + str(num_lost) +"\n"
                            news_message2 += unit_info[unit]['label'] + " : " + str(num_lost) + "\n"
                            setattr(main_fleet, unit, max(0, num - num_lost))
                main_fleet.save()
                if no_units:
                    news_message += "Your opponent has barely any fleet to destroy!"
            else:
                news_message += "Your agents didn't succeed!"
                news_message2 += "Your agents managed to defend!"

        if operation == "Nuke Planet":
            if success >= 1.0:
                news_message += "The planet was nuked! Most of population is dead. Planet's building size is reduced.\n"
                news_message2 += "The planet was nuked! Most of population is dead. Planet's building size is reduced.\n"
                target_planet.owner = None
                if target_planet.artefact is not None:
                    target_planet.artefact.empire_holding = None
                    target_planet.artefact.save()
                if target_planet.owner != None:
                    raze_all_buildings2(target_planet, user2)
                target_planet.protection = 0
                target_planet.overbuilt = 0
                target_planet.overbuilt_percent = 0
                target_planet.buildings_under_construction = 0
                target_planet.portal_under_construction = False
                target_planet.portal = False
                for con in Construction.objects.all():
                        if con.planet == target_planet:
                            con.delete()
                stationed_fleet = Fleet.objects.filter(on_planet=target_planet).first()
                if stationed_fleet is not None:
                    stationed_fleet.delete()
                    news_message += "Stationed fleet was completely destroyed in the blast!"
                    news_message2 += "Stationed fleet was completely destroyed in the blast!"
                target_planet.size *= random.randint(80,99)/100
                target_planet.current_population = target_planet.size * 20
                if target_planet.bonus_solar == 0 and target_planet.bonus_mineral == 0 and target_planet.bonus_crystal == 0 and target_planet.bonus_ectrolium == 0:
                    target_planet.bonus_fission += random.randint(10,100)
                target_planet.save()

            else:
                news_message += "Your agents didn't succeed!"
                news_message2 += "Your agents managed to defend!"


        if operation == "Bio Infection":
            if success >= 1.0:
                fa = 0.6
            else:
                fa = (0.6 / 0.4) * (success - 0.6)
            total_pop_lost = 0

            if fa > 0:
                planets = Planets.objects.filter(owner=user2.user)

                for p in planets:
                    dist = math.sqrt((p.x-target_planet.x)**2 + (p.y-target_planet.y)**2)
                    if dist >= 16:
                        continue
                    fb = 1.0 - (dist / 16.0)
                    pop_killed = int(p.current_population * fa * fb)
                    total_pop_lost += pop_killed
                    p.current_population -= pop_killed
                    p.save()
                user2.population -= total_pop_lost
                user2.save()
                news_message += "Your agents have spread a dangerous infection around target planets."
                news_message += "A total of " + str(total_pop_lost) + " people were killed!"
                news_message2 += "A pandemic is causing a lot of deaths around your planets!"
                news_message2 += "A total of " + str(total_pop_lost) + " people were killed!"
            else:
                news_message += "Your agents didn't succeed!"
                news_message2 += "Your agents managed to defend!"


        if operation == "High Infiltration":
            if success >= 1.0:
                Specops.objects.create(user_to=user2.user,
                                       user_from=user1.user,
                                       specop_type='O',
                                       specop_strength=success,
                                       stealth=stealth,
                                       extra_effect="show high infiltration",
                                       name="High Infiltration",
                                       ticks_left=104)

                news_message += "You succesfully got faction information!"
                news_message2 += "Our Information was stolen!"
            else:
                news_message += "Your agents didn't succeed!"
                news_message2 += "Your agents managed to defend!"


        if empire2 is None:
            News.objects.create(user1=User.objects.get(id=user.id),
                            user2=None,
                            empire1=user1.empire,
                            fleet1=operation,
                            news_type='AA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
        else:
            News.objects.create(user1=User.objects.get(id=user.id),
                            user2=User.objects.get(id=user2.id),
                            empire1=user1.empire,
                            empire2=empire2,
                            fleet1=operation,
                            news_type='AA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
            if not stealth:
                user2.military_flag = 1
                user2.save()
                News.objects.create(user1=User.objects.get(id=user2.id),
                            user2=User.objects.get(id=user.id),
                            empire1=empire2,
                            empire2=user1.empire,
                            fleet1=operation,
                            news_type='AD',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message2,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet)
            
            elif stealth and agentop_specs[operation][3] == False:
                user2.military_flag = 1
                user2.save()
                News.objects.create(user1=User.objects.get(id=user2.id),
                            user2=None,
                            empire1=empire2,
                            empire2=None,
                            fleet1=operation,
                            news_type='AD',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message2,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet)

        return news_message

def perform_incantation(ghost_fleet):
    incantation = ghost_fleet.specop
    ghost = ghost_fleet.ghost
    user = ghost_fleet.owner
    target_planet = ghost_fleet.target_planet
    user1 = UserStatus.objects.get(user=user)
    if user1.psychic_readiness < 0:
        news_message = "Not enough Psychics Readiness, Ghost Ships returning!"
        user1.military_flag = 1
        user1.save()
        News.objects.create(user1=User.objects.get(id=user.id),
                            user2=None,
                            empire1=user1.empire,
                            fleet1=incantation,
                            news_type='GA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
    else:
        user1.military_flag = 2
        user1.save()
        if incantation not in inca_specs:
            return "This operation is broken/doesnt exist!"

        fa = 0.6 + (0.8/ 255.0) * (np.random.randint(0, 2147483647) & 255)

        attack = fa * race_info_list[user1.get_race_display()].get("ghost_ships_coeff", 1.0) * \
                 ghost * (1.0 + 0.01 * user1.research_percent_culture)
                 
        attack /= inca_specs[incantation][2]

        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == user1.empire:
            penalty = get_op_penalty(user1.research_percent_culture, (inca_specs[incantation][0]/2))
        else:
            penalty = get_op_penalty(user1.research_percent_culture, inca_specs[incantation][0])
        

        if penalty == -1:
            return "You don't have enough culture research to perform this Incantation!"

        if penalty > 0:
            attack /= 1.0 + 0.01 * penalty
        
        defense = 0
        defense2 = 0
        user2 = None
        empire2 = None
        stealth = True

        n_check = ["Survey System", "Sense Artefact", "Vortex Portal", "Planetary Shielding"]
        if target_planet.owner is not None and incantation not in n_check:
            user2 = UserStatus.objects.get(id=target_planet.owner.id)
            empire2 = user2.empire
            fleet2 = Fleet.objects.get(owner=user2.id, main_fleet=True)
            ghosts2 = (fleet2.wizard / 7)
            ghosts3 = fleet2.ghost
            defense = ghosts2 * race_info_list[user2.get_race_display()].get("psychics_coeff", 1.0) * \
                      (1.0 + 0.01 * user2.research_percent_culture)
            defense2 = ghosts3 * race_info_list[user2.get_race_display()].get("ghost_ships_coeff", 1.0) * \
                      (1.0 + 0.01 * user2.research_percent_culture)
        
        if incantation in n_check:
            defense = user1.networth / ghost
        
        success = attack / (defense + 1)
        gsuccess = attack / (defense2 + 1)
        news_message = ""
        news_message2 = ""
        
        if gsuccess < 2.0 and target_planet.owner is not None and incantation not in n_check:
            stealth = False
            refdef = 0.5 * pow((0.5 * gsuccess), 1.1)
            refatt = 1.0 - refdef
            tlosses = 1.0 - pow((0.5 * gsuccess), 0.2)
            fc = 0.75 + (0.5 / 255.0) * (np.random.randint(0, 2147483647) & 255)
            loss1 = min(ghost, round(fc * refatt * tlosses *ghost))
            loss2 = min(ghosts3, round(fc * refdef * tlosses *ghosts3))
            ghost_fleet.ghost -= loss1
            ghost_fleet.save()
            fleet2.ghost -= loss2
            fleet2.save()
            news_message += "Attacker lost " + str(loss1) + " ghost ships. \nDefender lost: " + str(loss2) + " ghost ships.\n"
            news_message2 += "Attacker lost " + str(loss1) + " ghost ships. \nDefender lost: " + str(loss2) + " ghost ships.\n"
        
        if target_planet.owner is not None and incantation not in n_check:
            refdef = 0.5 * pow((0.5 * success), 1.1)
            tlosses = 1.0 - pow((0.5 * success), 0.2)
            fc = 0.75 + (0.5 / 255.0) * (np.random.randint(0, 2147483647) & 255)
            loss2 = min(ghosts2, round(fc * refdef * tlosses *ghosts2))
            if loss2 < 0:
                loss2 = fleet2.wizard
            fleet2.wizard -= loss2
            fleet2.save()
            news_message += "Defender lost: " + str(loss2) + " psychics.\n"
            news_message2 += "Defender lost: " + str(loss2) + " psychics.\n"
            
        if incantation == "Survey System":        
            planets = Planets.objects.filter(x=target_planet.x, y=target_planet.y).order_by('i')
            for p in planets:
                if p.owner is not None:
                    user3 = UserStatus.objects.get(id=p.owner.id)
                    fleet3 = Fleet.objects.get(owner=user3.id, main_fleet=True)
                    ghosts3 = fleet3.wizard / 7
                    defense = ghosts3 * race_info_list[user3.get_race_display()].get("psychics_coeff", 1.0) * \
                      (1.0 + 0.01 * user3.research_percent_culture)
                    success = attack / (defense + 1)
                else:
                    fleet = Fleet.objects.get(owner=user, main_fleet=True)
                    defense = user1.networth / ghost
                    success = attack / (defense + 1)
                if success < 0.4:
                    if p.owner is not None:
                        news_message += "\n\nPlanet " + str(p.x) + "," +str(p.y) + ":" + str(p.i) + " owned by " +str(p.owner.galtwouser.user_name)
                    else:
                        news_message += "\n\nPlanet " + str(p.x) + "," +str(p.y) + ":" + str(p.i)
                    news_message += "\nNo information was gathered about this planet!"
                if success >= 0.4:
                    if p.owner is not None:
                        news_message += "\nPlanet " + str(p.x) + "," +str(p.y) + ":" + str(p.i) + " owned by " +str(p.owner.galtwouser.user_name)
                    else:
                        news_message += "\nPlanet " + str(p.x) + "," +str(p.y) + ":" + str(p.i)
                    news_message += "\nPlanet size: " + str(p.size) + ""
                if success >= 0.9:
                    if p.bonus_solar > 0:
                        news_message += "\nSolar Bonus: " + str(p.bonus_solar)
                    if p.bonus_fission > 0:
                        news_message += "\nFission Bonus: " + str(p.bonus_fission)
                    if p.bonus_mineral > 0:
                        news_message += "\nMineral Bonus: " + str(p.bonus_mineral)
                    if p.bonus_crystal > 0:
                        news_message += "\nCrystal Bonus: " + str(p.bonus_crystal)
                    if p.bonus_ectrolium > 0:
                        news_message += "\nEctrolium Bonus: " + str(p.bonus_ectrolium)
                if p.artefact is not None:
                    if success >= 1.0:
                        news_message += "\nArtefact: Present, the " + p.artefact.name
                if success >= 1:
                    if p.owner is not None:
                        if p.portal:
                            news_message += "\nPortal"
                        else:
                            news_message += "\nPortal Protection: " + str(p.protection) + "%"
                scouting = Scouting.objects.filter(user=user, planet=p).first()
                if scouting is None:
                    Scouting.objects.create(user=user, planet=p, scout=success)
                else:
                    if success > scouting.scout:
                        scouting.scout = success
                        scouting.save()

        if incantation == "Sense Artefact":           
            arti = Planets.objects.all().exclude(artefact=None)
            news_message = "No Artefact was felt in the area!"
            system = System.objects.all()
            area = round(min(5, success))   
            for arte in arti:
                dist = max(abs(target_planet.x-arte.x), abs(target_planet.y-arte.y))
                if dist <= area:
                    if success / 5 >= 3:
                        news_message = "Your Ghost Ships have located an Artefact at Planet: " + str(arte.x) + "," + str(arte.y) + ":" + str(arte.i) + "!"
                        foundarte = arte
                        scouting = Scouting.objects.filter(user=user1.user, planet=foundarte).first()
                        if scouting is None:
                            Scouting.objects.create(user=user, planet=foundarte, scout=1.0)
                        else:
                            scouting = Scouting.objects.get(user=user1.user, planet=foundarte)
                            scouting.scout = 1.0
                            scouting.save()
                    elif success / 5 >= 2:
                        news_message = "Your Ghost Ships have felt an Artefact's presence in system: " + str(arte.x) + "," + str(arte.y) + "!"
                    elif success / 5 >= 1:
                        news_message = "Your Ghost Ships have felt an Artefact's presence, its location remains unknown!"
            if success >= 0.7:
                for s in system:
                    dist = max(abs(target_planet.x-s.x), abs(target_planet.y-s.y))
                    if dist <= area:
                        sens = Sensing.objects.create(empire=user1.empire, system=s, scout=success)             
                    	

        if incantation == "Planetary Shielding":
            ticks = round(min(72, (random.randint(1,6) * (success))))
            opstrength = min(2147483647,round(attack * (np.random.randint(0, 2147483647) & 255)))
            if ticks > 0 and opstrength > 0:
                Specops.objects.create(user_to=user1.user, specop_type='G', name='Planetary Shielding', specop_strength=opstrength, ticks_left=ticks, planet=target_planet)
                news_message += "\nYour Ghost Ships managed to create a shield lasting " + str(ticks) + " weeks, able to withstand " + str(opstrength) + " damage!"
            else:
                news_message += "\nYour Ghost Ships failed to create a shield!"
        
        if incantation == "Portal Force Field":
            ticks = round(min(48, (random.randint(1,6) * (success / 100))))
            opstrength = min(100,round(attack * (np.random.randint(0, 2147483647) & 255)))
            if ticks > 0 and opstrength > 0:
                Specops.objects.create(user_to=target_planet.owner, user_from= user1.user, specop_type='G', name='Portal Force Field', specop_strength=opstrength, ticks_left=ticks, planet=target_planet)
                news_message += "\nYour Ghost Ships managed to create a force field lasting "+ str(ticks) + " weeks, reducing portal capability by " + str(opstrength) + "%"
                news_message2 += "\nYour portal was the target of a force field, reducing portal capability by " + str(opstrength) + "%, for " + str(ticks) + " weeks!"
            else:
                news_message += "\nYour Ghost Ships failed to create a force field"
                news_message2 += "\nYour Psychics managed to defend a Portal Force Field"
                
        if incantation == "Mind Control":
            if success >= 2.0:
                target_planet.owner = user
                target_planet.portal = False
                target_planet.current_population = target_planet.size * 20
                target_planet.protection = 0
                target_planet.buildings_under_construction = 0
                target_planet.portal_under_construction = False
                if target_planet.artefact is not None:
                    target_planet.artefact.empire_holding = user1.empire
                    target_planet.artefact.save()
                target_planet.save()
                for con in Construction.objects.all():
                        if con.planet == target_planet:
                            con.delete()
                scouting = Scouting.objects.filter(user=user, planet=target_planet).first()
                if scouting is None:
                    Scouting.objects.create(user= User.objects.get(id=user1.id),
                                    planet = target_planet,
                                    scout = 1.0)
                else:
                    scouting.scout = 1.0
                    scouting.save
                news_message += "Your Ghost Ships took control of the planet!"
            elif success >= 1.0: 
                target_planet.owner = user
                target_planet.portal = False
                target_planet.protection = 0
                target_planet.current_population = target_planet.size
                target_planet.solar_collectors = 0
                target_planet.fission_reactors = 0
                target_planet.mineral_plants = 0
                target_planet.crystal_labs = 0
                target_planet.refinement_stations = 0
                target_planet.cities = 0
                target_planet.research_centers = 0
                target_planet.defense_sats = 0
                target_planet.shield_networks = 0
                target_planet.total_buildings = 0
                target_planet.buildings_under_construction = 0
                target_planet.portal_under_construction = False
                for con in Construction.objects.all():
                        if con.planet == target_planet:
                            con.delete()
                if target_planet.artefact is not None:
                    target_planet.artefact.empire_holding = user1.empire
                    target_planet.artefact.save()
                target_planet.save()
                scouting = Scouting.objects.filter(user=user, planet=target_planet).first()
                if scouting is None:
                    Scouting.objects.create(user= User.objects.get(id=user1.id),
                                    planet = target_planet,
                                    scout = 1.0)
                else:
                    scouting.scout = 1.0
                    scouting.save             
                news_message += "Your Ghost Ships took control of the planet!"
                news_message2 += "Your planet was lost!"
                
            else:
                news_message += "Your Ghost Ships failed to take control of the planet!"
                news_message2 += "Your Psychics saved the planet!"

        if incantation == "Energy Surge":
            resource = min(1.0, success)
            research = round(min(0.05, success/100), 2)
            rc = research * 100
            buildings = round(min(0.1, success/100), 2)
            if success >= 2.0:
                energy = round(user2.energy * resource)
                user2.energy -= energy
                mili = user2.research_points_military * research
                user2.research_points_military -= mili
                con = user2.research_points_construction * research
                user2.research_points_construction -= con
                tech = user2.research_points_tech * research
                user2.research_points_tech -= tech
                nrg = user2.research_points_energy * research
                user2.research_points_energy -= nrg
                pop = user2.research_points_population * research
                user2.research_points_population -= pop
                cult = user2.research_points_culture * research
                user2.research_points_culture -= cult
                ops = user2.research_points_operations * research
                user2.research_points_operations -= ops
                por = user2.research_points_portals * research
                user2.research_points_portals -= por
                user2.save()
                solars= 0
                fission = 0
                news_message += "Resources Destroyed: \nEnergy: " + str(energy) + "\nMineral: " + str(mineral) + "\nCrystal: " + str(crystal) + "\nEctrolium: " + str(ectrolium)
                news_message += "\nResearch Destroyed: " + str(rc) + "%"
                news_message2 += "Resources Destroyed: \nEnergy: " + str(energy) + "\nMineral: " + str(mineral) + "\nCrystal: " + str(crystal) + "\nEctrolium: " + str(ectrolium)
                news_message2 += "\nResearch Destroyed: " + str(rc) + "%"  
                for p in Planets.objects.filter(owner=user2.id):
                    sols = round(p.solar_collectors * buildings)
                    fis = round(p.fission_reactors * buildings)
                    p.solar_collectors -= sols
                    p.fission_reactors -= fis
                    p.save()
                    solars += sols
                    fission += fis
                news_message += "\nBuildings Destroyed:\nSolar Collectors: " + str(solars) + "\nFission Reactors: " + str(fission)
                news_message2 += "\nBuildings Destroyed:\nSolar Collectors: " + str(solars) + "\nFission Reactors: " + str(fission)
            elif success >= 1.0:
                energ = user2.energy * resource
                energy = round(energ)
                user2.energy -= energy
                nrg = user2.research_points_energy * research
                user2.research_points_energy -= nrg
                user2.save()
                solars= 0
                news_message += "Resources Destroyed: \nEnergy: " + str(energy)
                news_message += "\nResearch Destroyed: \nEnergy: " + str(rc) + "%"
                news_message2 += "Resources Destroyed: \nEnergy: " + str(energy)
                news_message2 += "\nResearch Destroyed: \nEnergy: " + str(rc) + "%" 
                for p in Planets.objects.filter(owner=user2.id):
                    sols = round(p.solar_collectors * buildings)
                    p.solar_collectors -= sols
                    p.save()
                    solars += sols
                news_message += "\nBuildings Destroyed:\nSolar Collectors: " + str(solars)
                news_message2 += "\nBuildings Destroyed:\nSolar Collectors: " + str(solars) 
            else:
                news_message += "Your Ghost Ships failed!"
                news_message2 += "Your Psychics managed to defend!"
        
        if incantation == "Call to Arms":
            pop = 0
            sol = 0
            for p in Planets.objects.filter(owner=target_planet.owner):
                pops = round(p.current_population * (success/100))
                p.current_population -= pops
                p.save()
                sols = round(pops/100)
                pop += pops
                sol += sols
            UnitConstruction.objects.create(user=user, n=sol, ticks_remaining=1, unit_type='soldier')
            news_message += str(pop) + " population has been recruited, training " + str(sol) + " soldiers!"

        if incantation == "Vortex Portal":
            print(ghost)
            fa = 7 * attack / user.userstatus.networth
            length = round(min(144, 3 + (120*fa)))
            Specops.objects.create(user_to= user1.user, specop_type='G', name='Vortex Portal', ticks_left=length, planet=target_planet)
            news_message += "Vortex Portal created at " + str(target_planet.x) + "," + str(target_planet.y) + " for a duration of " + str(length) + " weeks!"
            
                            
        if target_planet.owner is not None and incantation not in n_check:
            user1.psychic_readiness -= specopReadiness(inca_specs[incantation],"Incantation", user1, user2)
        else: 
            user1.psychic_readiness -= inca_specs[incantation][1]
        user1.save()

                
        if empire2 is None:
            News.objects.create(user1=User.objects.get(id=user.id),
                            user2=None,
                            empire1=user1.empire,
                            fleet1=incantation,
                            news_type='GA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
        else:
            News.objects.create(user1=User.objects.get(id=user.id),
                            user2=User.objects.get(id=user2.id),
                            empire1=user1.empire,
                            empire2=empire2,
                            fleet1=incantation,
                            news_type='GA',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet
                            )
            if not stealth:
                user2.military_flag = 1
                user2.save()
                News.objects.create(user1=User.objects.get(id=user2.id),
                            user2=User.objects.get(id=user.id),
                            empire1=empire2,
                            empire2=user1.empire,
                            fleet1=incantation,
                            news_type='GD',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message2,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet

                            )
            if stealth and inca_specs[incantation][3] == False:
                user2.military_flag = 1
                user2.save()
                News.objects.create(user1=User.objects.get(id=user2.id),
                            user2=None,
                            empire1=empire2,
                            empire2=None,
                            fleet1=incantation,
                            news_type='GD',
                            date_and_time=datetime.now(),
                            is_personal_news=True,
                            is_empire_news=True,
                            extra_info=news_message2,
                            tick_number=RoundStatus.objects.get().tick_number,
                            planet=target_planet

                            )
    return news_message

