from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from datetime import datetime
from app.map_settings import *
from django.db import transaction



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        arte = Artefacts.objects.get(name="Terraformer")
         
        if arte.empire_holding != None:
            for player in UserStatus.objects.filter(empire=arte.empire_holding):
                if player.num_planets > 1:
                    choosebonus = random.randint(1,5)
                    if player.id == 3 or player.id == 6:
                        choosebonus = 5
                    elif player.id == 4 or player.id == 7:
                        choosebonus = random.randint(2,4)
                    bonus = random.randint(10,100)
                    planet = []
                    plcount = 0
                    pl = Planet.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', bonus_fission = '0', owner=player.id, artefact=None)
                    for p in pl:
                        planet.append(p)
                        plcount += 1
                    if plcount == 0:
                        if choosebonus == 1:
                            try:
                                planet = random.choice(Planet.objects.filter(home_planet=False, bonus_solar__gte=1, owner=player.id, artefact=None))
                            except:
                                return None
                        elif choosebonus == 2:
                            try:
                                planet = random.choice(Planet.objects.filter(home_planet=False, bonus_crystal__gte=1, owner=player.id, artefact=None))
                            except:
                                return None
                        elif choosebonus == 3:
                            try:
                                planet = random.choice(Planet.objects.filter(home_planet=False, bonus_mineral__gte=1, owner=player.id, artefact=None))
                            except:
                                return None
                        elif choosebonus == 4:
                            try:
                                planet = random.choice(Planet.objects.filter(home_planet=False, bonus_ectrolium__gte=1, owner=player.id, artefact=None))
                            except:
                                return None
                        elif choosebonus == 5:
                            try:
                                planet = random.choice(Planet.objects.filter(home_planet=False, bonus_fission__gte=1, owner=player.id, artefact=None))
                            except:
                                return None
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
                                is_empire_news=True,
                                extra_info=news_message,
                                planet=planet,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
            ticks = random.randint(10, 59)
            arte.ticks_left = ticks
            arte.save()
        print("Generating terraformer took " + str(time.time() - start_t) + "seconds")
