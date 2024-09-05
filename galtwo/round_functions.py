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

    for i, (key, val) in enumerate(arti_list.items()):
        if key == "You Grow, Girl!":
            arti_planets[i].size = 1
        arti_planets[i].save()
        
        if key == "Scroll of the Necromancer":
            arti = Artefacts.objects.create(name=key,
                                       description=val[0],
                                       effect1=val[1],
                                       effect2=val[2],
                                       effect3=val[3],
                                       ticks_left=val[4],
                                       image=val[5])
        
        else:
            arti = Artefacts.objects.create(name=key,
                                       description=val[0],
                                       effect1=val[1],
                                       effect2=val[2],
                                       effect3=val[3],
                                       ticks_left=val[4],
                                       on_planet=arti_planets[i],
                                       image=val[5])
            arti_planets[i].artefact = arti
            arti_planets[i].save()
                                       
    print(arti_planets)
    print("Generating artefacts took " + str(time.time() - start_t) + "seconds")
    
def bonuses():
    start_t = time.time()
    solar = 250
    mineral = 125
    crystal = 75
    ectrolium = 50
    for _ in range(solar):
        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', artefact=None))
        bonus = random.randint(10,200)
        planet.bonus_solar += bonus
        planet.save()
    for _ in range(crystal):
        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', artefact=None))
        bonus = random.randint(10,200)
        planet.bonus_crystal += bonus
        planet.save()
    for _ in range(mineral):
        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', artefact=None))
        bonus = random.randint(10,200)
        planet.bonus_mineral += bonus
        planet.save()
    for _ in range(ectrolium):
        planet = random.choice(Planets.objects.filter(home_planet=False, bonus_solar='0', bonus_mineral='0', bonus_crystal='0', bonus_ectrolium='0', artefact=None))
        bonus = random.randint(10,200)
        planet.bonus_ectrolium += bonus
        planet.save()

    print("Generating bonuses took " + str(time.time() - start_t) + "seconds")
    
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
    for p in Planets.objects.all():
        if Planets.objects.filter(x=p.x, y=p.y, i=p.i).count() > 1:
            print(str(p.id))
            if p.home_planet == False:
                p.delete()
               
            
                                            
    print("Generating settings took " + str(time.time() - start_t) + "seconds")
    
def systems():
    start_t = time.time()
    System.objects.all().delete()
    planets = Planets.objects.all().order_by('x', 'y')
    for p in planets:
        system = System.objects.filter(x=p.x, y=p.y).first()
        if system is None:
            if p.home_planet == True:
                System.objects.create(x=p.x, y=p.y, home=True)
            else:
                System.objects.create(x=p.x, y=p.y)
                
    systems = System.objects.all()
    for s in systems:
        if s.id % 10 == 0 or s.id % 10 == 5:
            s.img = "/static/map/s1.png"
        if s.id % 10 == 1 or s.id % 10 == 6:
            s.img = "/static/map/s2.png"
        if s.id % 10 == 2 or s.id % 10 == 7:
            s.img = "/static/map/s3.png"
        if s.id % 10 == 3 or s.id % 10 == 8:
            s.img = "/static/map/s4.png"
        if s.id % 10 == 4 or s.id % 10 == 9:
            s.img = "/static/map/s5.png"
        s.save()

    print("Generating systems took " + str(time.time() - start_t) + "seconds")
