from django.core.management.base import BaseCommand, CommandError
from app.models import UserStatus
from app.constants import *
from app.models import *
import time
from datetime import datetime
import random
from app.map_settings import *
from django.db import transaction



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        arte = Artefacts.objects.get(name="Flying Dutchman")
        
        if arte.empire_holding != None:
            user = UserStatus.objects.filter(empire=arte.empire_holding).first()
            users = UserStatus.objects.filter(empire=arte.empire_holding)
            system = random.choice(System.objects.filter(home=False))
            planets = Planet.objects.filter(x=system.x, y=system.y).order_by("i")
            planet = Planet.objects.get(x=system.x, y=system.y, i=0)
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
                    news_message += "\nOwned by: " + str(p.owner.userstatus.user_name)
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
                            
            ticks = random.randint(9, 29)
            arte.ticks_left = ticks
            arte.save()