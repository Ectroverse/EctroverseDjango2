import numpy as np
from .helper_classes import *
from app.constants import *
from app.models import *
from datetime import datetime
from django.db.models import Sum
import random
import secrets
import math
from app.calculations import *
from django.db import connection

def specopReadiness(specop, type, user1, *args):
    user2 = None
    if args:
        user2 = args[0]
    
    tech = Ops.objects.get(name=specop).tech
    readiness = Ops.objects.get(name=specop).readiness
    
    robo = Artefacts.objects.get(name="Advanced Robotics")  
    if robo.empire_holding == user1.empire:
        tech /= 2
    
    if type == "Spell":
        penalty = get_op_penalty(user1.research_percent_culture, tech)
        if user2 == None and specop[3] == False:
            return -1
        if specop[3]: #if self op
            fr = int((1.0 + 0.01 * penalty) * readiness)
            cloak = Artefacts.objects.get(name="Magus Cloak")
            if cloak.empire_holding == user1.empire:
                fr = round(fr*(1-(cloak.effect1/100)))
            return fr
    elif type == 'Incantation':
        penalty = get_op_penalty(user1.research_percent_culture, tech)
    else:
        penalty = get_op_penalty(user1.research_percent_operations, tech)

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

    fa = (1.0 + 0.01 * penalty) * readiness * fa

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
    if game_round.is_running == False:
        return "You cannot perform spells before the round has started!"
    else:
        if spell not in psychicop_specs:
            return "This spell is broken/doesnt exist!"

        tech = Ops.objects.get(name=spell).tech
        readiness = Ops.objects.get(name=spell).readiness
        difficulty = Ops.objects.get(name=spell).difficulty
        selfsp = Ops.objects.get(name=spell).selfsp
        
        robo = Artefacts.objects.get(name="Advanced Robotics")  
        if robo.empire_holding == status.empire:
            tech /= 2
        
        fa = 0.4 + (1.2 / 255.0) * (np.random.randint(0, 2147483647) & 255)

        attack = fa * race_info_list[status.get_race_display()].get("psychics_coeff", 1.0) * \
                 psychics * (1.0 + 0.005 * status.research_percent_culture)
                 
        attack /= float(difficulty)
        
        penalty = get_op_penalty(status.research_percent_culture, tech)
        

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
            if user2 == status and selfsp is False:
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
        
        if spell == "Alchemist":
            nrg_converted = attack * 5
            if nrg_converted > status.energy:
                nrg_converted = status.energy
            nrg_converted = int(nrg_converted)
            status.energy -= nrg_converted
            res = int((nrg_converted / 8.0) * (1.0 + 0.01 * status.research_percent_culture))
            element = ['Mineral', 'Crystal', 'Ectrolium']
            chosen = secrets.choice(element)
            if chosen == "Crystal":
                status.crystals += res
            if chosen == "Ectrolium":
                status.ectrolium += res
            if chosen == "Mineral":
                status.minerals += res
            status.save()
            news_message += str(nrg_converted) + " energy were converted into " + str(res) + " " + str(chosen) + "!"
            message += "Your " + str(nrg_converted) + " energy were converted into " + str(res) + " " + str(chosen) + "!"      
        
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

        if spell =="Phantoms":
            phantom_cast = round(attack / 2)
            fleet1.phantom += phantom_cast
            fleet1.save()

            news_message += status.user_name + " has summoned " + str(phantom_cast) + " Phantoms to fight in their army!"
            message += "You have summoned " + str(phantom_cast) + " Phantoms to join your army!"
        
        if spell =="Grow Planet's Size":
            plant = list(Planet.objects.filter(owner=status.user).order_by('size').reverse().values_list('id', flat=True))
            weight = []
            count = 1
            for _ in range(len(plant)):
                weight.append(count)
                count += 1
            plan = random.choices(plant,weight)
            planet = Planet.objects.get(id=str(*plan))
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
        
        prloss = specopReadiness(spell,"Spell", status)    
        status.psychic_readiness -= prloss
        status.save()

        if selfsp == True:
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

def perform_incantation(ghost_fleet):
    incantation = ghost_fleet.specop
    ghost = ghost_fleet.ghost
    user = ghost_fleet.owner
    target_planet = ghost_fleet.target_planet
    user1 = UserStatus.objects.get(user=user)
    #user2 = UserStatus.objects.get(id=target_planet.owner.id)
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

        fa = 0.6 + (0.8/ 255.0) * np.random.randint(0, 255)

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
        
        defense = 50
        defense2 = 50
        user2 = None
        empire2 = None


        n_check1 = ["Survey System", "Sense Artefact", "Vortex Portal", "Planetary Shielding"] #no defense
        n_check2 = ["Call to Arms"] #defense if not self op

        if target_planet.owner is not None and incantation not in n_check1 and not (incantation in n_check2 and target_planet.owner == user1.user):
            user2 = UserStatus.objects.get(id=target_planet.owner.id)
            empire2 = user2.empire
            fleet2 = Fleet.objects.get(owner=user2.id, main_fleet=True)
            ghosts2 = fleet2.wizard 
            ghosts3 = fleet2.ghost
            defense = (ghosts2 * race_info_list[user2.get_race_display()].get("psychics_coeff", 1.0) * \
                      (1.0 + 0.01 * user2.research_percent_culture)) / 7
            defense2 = ghosts3 * race_info_list[user2.get_race_display()].get("ghost_ships_coeff", 1.0) * \
                      (1.0 + 0.01 * user2.research_percent_culture)

        else:
            user2 = user1

        if incantation in n_check1 and incantation != "Vortex Portal" and incantation != "Planetary Shielding":
            defense = user1.networth / ghost

        success = attack / (defense + 1)
        gsuccess = attack / (defense2 + 1)
        news_message = ""
        news_message2 = ""
        stealth = True
        
        if gsuccess < 2.0 and target_planet.owner is not None and incantation not in n_check1 and not (incantation in n_check2 and target_planet.owner == user1.id):
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
        
        if success < 2.0 and target_planet.owner is not None and incantation not in n_check1 and not (incantation in n_check2 and target_planet.owner == user1.id):
            refdef = 0.5 * pow((0.5 * success), 1.1)
            tlosses = 1.0 - pow((0.5 * success), 0.2)
            fc = 0.75 + (0.5 / 255.0) * (np.random.randint(0, 2147483647) & 255)
            loss2 = min(ghosts2, round(fc * refdef * tlosses * ghosts2))
            if loss2 < 0:
                loss2 = 0
                success = 2.0
            fleet2.wizard -= loss2
            fleet2.save()
            if loss2 > 0:
                news_message += "Defender lost: " + str(loss2) + " psychics.\n"
                news_message2 += "Defender lost: " + str(loss2) + " psychics.\n"            
        
        if incantation == "Survey System":        
            with connection.cursor() as cursor:
                cursor.execute("call incantations("+str('1,')+str(ghost_fleet.id)+");")

        if incantation == "Sense Artefact":           
            arti = Planet.objects.all().exclude(artefact=None)
            news_message = "No Artefact was felt in the area!"
            system = System.objects.all()
            area = round(min(4, success))   
            for arte in arti:
                dist = max(abs(target_planet.x-arte.x), abs(target_planet.y-arte.y))
                if dist < area:
                    if success >= 3:
                        if "location" in news_message:
                            news_message += "\nYour Ghost Ships have located an Artefact at Planet: " + str(arte.x) + "," + str(arte.y) + ":" + str(arte.i) + "!"
                        else:
                            news_message = "Your Ghost Ships have located an Artefact at Planet: " + str(arte.x) + "," + str(arte.y) + ":" + str(arte.i) + "!"
                        foundarte = arte
                        scouting = Scouting.objects.filter(empire=user1.empire, planet=foundarte).first()
                        if scouting is None:
                            Scouting.objects.create(user=user, planet=foundarte, empire=user1.empire, scout=1.0)
                    elif success >= 2:
                        news_message = "Your Ghost Ships have felt an Artefact's presence in system: " + str(arte.x) + "," + str(arte.y) + "!"
                    elif success >= 1:
                        news_message = "Your Ghost Ships have felt an Artefact's presence, its location remains unknown!"
            if success >= 2:
                for s in system:
                    dist = max(abs(target_planet.x-s.x), abs(target_planet.y-s.y))
                    if dist <= area:
                        try:
                            sens = Sensing.objects.get(empire=user1.empire, system=s)
                            sens.scout = 3.0
                            sens.save()
                        except:
                            sens = Sensing.objects.create(empire=user1.empire, system=s, scout=success)

        if incantation == "Planetary Shielding":
            stealth = False
            user1 = UserStatus.objects.get(user=user)
            user2 = UserStatus.objects.get(user=target_planet.owner)
            empire2 = user2.empire
            if empire2 == user1.empire:
                empire2 = None
            ticks = random.randint(10,41)
            opstrength = round(attack * np.random.randint(250, 500))
            if ticks > 0 and opstrength > 0:
                Specops.objects.create(user_to=user2.user, user_from = user1.user, specop_type='G', name='Planetary Shielding', specop_strength=opstrength, ticks_left=ticks, planet=target_planet)
                news_message += "\nYour Ghost Ships managed to create a shield lasting " + str(ticks) + " weeks, able to withstand " + str(opstrength) + " damage!"
                news_message2 += "\nGhost Ships managed to create a shield lasting " + str(ticks) + " weeks, able to withstand " + str(opstrength) + " damage!"
            else:
                news_message += "\nYour Ghost Ships failed to create a shield!"
                news_message2 += "\nGhost Ships failed to create a shield!"
        
        if incantation == "Portal Force Field":
            ticks = random.randint(16,47)
            opstrength = 200 * (success - 0.5)
            if opstrength > 0:
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
                scouting = Scouting.objects.filter(empire=user1.empire, planet=target_planet).first()
                if scouting is None:
                    Scouting.objects.create(user= User.objects.get(id=user1.id),
                                    planet = target_planet,
                                    empire=user1.empire,
                                    scout = 1.0)
                else:
                    scouting.scout = 1.0
                    scouting.save
                news_message += "Your Ghost Ships took control of the planet!"
            elif success >= 1.0: 
                target_planet.owner = user
                target_planet.portal = False
                target_planet.protection = 0
                target_planet.current_population = target_planet.size * 20
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
                scouting = Scouting.objects.filter(empire=user1.empire, planet=target_planet).first()
                if scouting is None:
                    Scouting.objects.create(user= User.objects.get(id=user1.id),
                                    planet = target_planet,
                                    empire=user1.empire,
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
                news_message += "Resources Destroyed: \nEnergy: " + str(energy)
                news_message += "\nResearch Destroyed: " + str(rc) + "%"
                news_message2 += "Resources Destroyed: \nEnergy: " + str(energy)
                news_message2 += "\nResearch Destroyed: " + str(rc) + "%"  
                for p in Planet.objects.filter(owner=user2.id):
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
                for p in Planet.objects.filter(owner=user2.id):
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

            if success >= 1.0:
                fa = 0.8
            else:
                fa = 2 * (success - 0.6)

            fa *= np.random.randint(90, 110) /100
            total_pop_lost = 0

            if fa > 0:
                planets = Planet.objects.filter(owner=user2.user)

                for p in planets:
                    dist = math.sqrt((p.x-target_planet.x)**2 + (p.y-target_planet.y)**2)
                    if dist >= 16:
                        continue
                    fb = 1.0 - (dist / 16.0)
                    pop_killed = round(p.current_population * fa * fb )
                    total_pop_lost += pop_killed
                    p.current_population -= pop_killed
                    p.save()
                gained_soldiers = total_pop_lost/100 * (1.0 + 0.01 * user2.research_percent_military) / (race_info_list[user2.get_race_display()].get("research_max_military", 1.0)/100)
                gained_soldiers = round(gained_soldiers)
                m_fleet = Fleet.objects.get(owner=user2.user, main_fleet=True)
                sols = getattr(m_fleet, 'soldier')
                setattr(m_fleet, 'soldier', sols + gained_soldiers)
                if user2 == user1:
                    mfghost = getattr(m_fleet, 'ghost')
                    setattr(m_fleet, 'ghost', mfghost + ghost)   
                m_fleet.save()
                user2.population -= total_pop_lost
                user2.save()
                news_message += str(total_pop_lost) + " population has been recruited, training " + str(gained_soldiers) + " soldiers!"
                news_message2 += str(total_pop_lost) + " population has been recruited, training " + str(gained_soldiers) + " soldiers!"
            else:
                news_message += "Your Ghost Ships failed!"
                news_message2 += "Your Psychics managed to defend!"
             
            
        if incantation == "Vortex Portal":
            print(ghost)
            fa = 7 * attack / user.userstatus.networth
            length = round(min(144, 3 + (120*fa)))
            Specops.objects.create(user_to= user1.user, specop_type='G', name='Vortex Portal', ticks_left=length, planet=target_planet)
            news_message += "Vortex Portal created at " + str(target_planet.x) + "," + str(target_planet.y) + " for a duration of " + str(length) + " weeks!"

        if incantation != "Survey System": 
            n_check = ["Sense Artefact", "Vortex Portal"]
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

