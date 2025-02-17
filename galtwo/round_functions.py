from django.core.management.base import BaseCommand, CommandError
from .models import *
from app.constants import *
import time
import random
from app.map_settings import *
from django.db import transaction
from app.round_functions import arti_list

def artifacts():
    start_t = time.time()
    # delete old
    Artefacts.objects.all().delete()
    empires = Empire.objects.all()
    for e in empires:
        if e.artefacts is not None:
            e.artefacts.clear()
            e.save()
    planets = Planets.objects.filter(home_planet=False, bonus_solar=0, bonus_mineral=0, bonus_crystal=0, bonus_ectrolium=0, bonus_fission=0)
    for p in planets:
        if p.artefact is not None:
            p.artefact = None
            p.save()

    arti_planets = random.sample(list(planets), len(arti_list))

    excluded = []

    for i, (key, val) in enumerate(arti_list.items()):        
        if key in excluded:
            arti = Artefacts.objects.create(name=key,
                                       description=val[0],
                                       effect1=val[1],
                                       effect2=val[2],
                                       effect3=val[3],
                                       ticks_left=val[4],
                                       on_planet=None,
                                       image=val[5])
        
        else:
            if key == "The General":
                gsyst = System.objects.get(x=arti_planets[i].x, y=arti_planets[i].y).id
            else:
                gsyst = val[1]
            arti = Artefacts.objects.create(name=key,
                                       description=val[0],
                                       effect1=gsyst,
                                       effect2=val[2],
                                       effect3=val[3],
                                       ticks_left=val[4],
                                       on_planet=arti_planets[i],
                                       image=val[5])
            arti_planets[i].artefact = arti
            if key == "You Grow, Girl!":
                arti_planets[i].size = 1
                arti.description = "This Planet grows by 1 every 10 weeks!"
                arti.save()
            arti_planets[i].save()
                                       
    print(arti_planets)
    print("Generating artefacts took " + str(time.time() - start_t) + "seconds")
    
def settings():
    start_t = time.time()
    exclude_list = ['1','3','4','5','6','7','8']
    user = UserStatus.objects.all().exclude(id__in=exclude_list)
    for u in user:
        if u.tag_points >= 12500:
            u.tag = "personalized tag"
        elif u.tag_points >= 9000:
            u.tag = "Transcend"
        elif u.tag_points >= 7000:
            u.tag = "Master Wizard"
        elif u.tag_points >= 5800:
            u.tag = "Dear Leader"
        elif u.tag_points >= 4600:
            u.tag = "Fleet Admiral"            
        elif u.tag_points >= 3900:
            u.tag = "Squadron Commander"
        elif u.tag_points >= 3500:
            u.tag = "Cruiser Captain"
        elif u.tag_points >= 3100:
            u.tag = "Wing Commander"                                        
        elif u.tag_points >= 2600:
            u.tag = "Lieutenant Commander"
        elif u.tag_points >= 2250:
            u.tag = "Squad Lieutenant"
        elif u.tag_points >= 1700:
            u.tag = "Patrol Officer"                
        elif u.tag_points >= 1320:
            u.tag = "1st Officer"                
        elif u.tag_points >= 1150:
            u.tag = "2nd Officer"                
        elif u.tag_points >= 850:
            u.tag = "3rd Officer"                
        elif u.tag_points >= 600:
            u.tag = "Master-at-Arms"                
        elif u.tag_points >= 460:
            u.tag = "Helmsman"                
        elif u.tag_points >= 380:
            u.tag = "1st Technician"                
        elif u.tag_points >= 240:
            u.tag = "2nd Technician"                
        elif u.tag_points >= 160:
            u.tag = "3rd Technician"
        elif u.tag_points >= 80:
            u.tag = "Chicken-soup-machine Repairman"                
        elif u.tag_points >= 45:
            u.tag = "Veteran"                
        else:
            u.tag = "Player"
        u.save()                    
            
                                            
    print("Generating settings took " + str(time.time() - start_t) + "seconds")
