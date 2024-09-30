from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from app.map_settings import *
from django.db import transaction

arti_list = {
        "Ether Gardens": ["Increases your energy production by 10%!", 10, 0, 1, 0, "/static/arti/artimg0.gif"],
        "Mirny Mine": ["Increases your mineral production by 15%!", 15, 0, 0, 0 ,"/static/arti/artimg1.gif"],
        "Crystal Synthesis": ["Increases your crystal production by 15%!", 15, 0, 0, 0, "/static/arti/artimg3.gif"],
        "Research Laboratory": ["Increases your research production by 10%!", 10, 0, 0, 0, "/static/arti/artimg4.gif"],
        "t-Veronica": ["Improves populations fighting strength, also fight in stage 3!", 0, 0, 0, 0, "/static/arti/artimg5.gif"],   
        "Military Might": ["Decreases unit upkeep by 10%, or 20% with The General!", 10, 0, 1, 0, "/static/arti/artimg14.gif"],
        "Terraformer": ["An ancient gate allows planets to be transformed!", 0, 0, 0, 1, "/static/arti/artimg7.gif"],
        "The Recycler": ["Funds research from Energy Decay, Tech Research impoves performance!", 0, 0, 0, 0, "/static/arti/artimg10.gif"],       
        "Ironside Effect": ["The resting site of a great viking encourages your army to steal resources!", 0, 0, 0, 0, "/static/arti/artimg17.gif"],
        "Scroll of the Necromancer": ["Traps the souls of the dead, raising a great army!", 1000, 0, 0, 0, "/static/arti/artimg22.png"],
        "Foohon Technology": ["Increases your ectrolium production by 10%!", 10, 0, 0, 0, "/static/arti/artimg2.gif"],
        "Crystal Recharger": ["Quarters crystal Decay!", 0, 0, 0, 0, "/static/arti/artimg20.png"],
        "Darwinism": ["10% more population upkeep, population upkeep no longer capped!", 0, 0, 0, 0, "/static/arti/artimg6.gif"],
        "Churchills Brandy": ["The War Chest has been found, improving your Fleets Readiness return!", 0, 0, 0, 0, "/static/arti/artimg23.png"],
        "Advanced Robotics": ["Technology requirements are now halved!", 0, 0, 0, 0, "/static/arti/artimg24.png"],
        "Flying Dutchman": ["Travelling the galaxy, the Flying Dutchman reports back on the findings!", 0, 0, 0, 1, "/static/arti/artimg25.png"],
        "You Grow, Girl!": ["This Planet grows by 1 every week!", 0, 1, 0, 0, "/static/arti/artimg27.png"],
        "Playboy Quantum": ["Raises Portals Research maximum by 100% and improves Portals Research production by 50%!", 0, 0, 1, 0, "/static/arti/artimg30.png"],
        "The General": ["Enamoured by The Generals Presence, your troops are stronger defending! Range doubled with Military Might!", 0, 0, 1, 0, "/static/arti/artimg29.png"],
        "Shield Network": ["Connects your Shield Networks across the Galaxy, removes the Technology requirement but reduces their effectiveness to 1/3!", 0, 0, 0, 0, "/static/arti/artimg28.png"],
        "Double 0": ["Raises your Agents defence by 25% but lowers Military defence by 15%!", 0, 0, 1, 0, "/static/arti/artimg31.png"],
        "Rabbit Theorum": ["Doubles your Population Research production!", 0, 0, 0, 0, "/static/arti/artimg32.png"],
        "Engineers Son": ["A lifetime of watching his father has resulted in Fighters being 20% cheaper to build!", 0, 0, 0, 0, "/static/arti/artimg33.png"],
        "Engineer": ["Reduces building upkeep by 10% or 20% with the Engineers Son!", 0, 0, 0, 0, "/static/arti/artimg34.png"],
        "Magus Cloak": ["Grants all self spells and reduces their cost by 25%!", 0, 0, 1, 0, "/static/arti/artimg26.png"],
        "Genghis Effect": ["Reduces exploration costs by 25%!", 0, 0, 1, 0, "/static/arti/artimg35.png"],
        "Blackhole": ["Opening blackholes, Travel Speed is increased by 60%!", 0, 0, 1, 0, "/static/arti/artimg36.png"],
        "Tyrs Justice": ["Temporarily reduces attack costs after being attacked!", 0, 0, 1, 0, "/static/arti/artimg37.png"],
        
    }

def artifacts():
    start_t = time.time()
    # delete old
    Artefacts.objects.all().delete()
    empires = Empire.objects.all()
    for e in empires:
        if e.artefacts is not None:
            e.artefacts.clear()
            e.save()
    planets = Planet.objects.filter(home_planet=False, bonus_solar=0, bonus_mineral=0, bonus_crystal=0, bonus_ectrolium=0, bonus_fission=0)
    for p in planets:
        if p.artefact is not None:
            p.artefact = None
            p.save()

    arti_planets = random.sample(list(planets), len(arti_list))

    for i, (key, val) in enumerate(arti_list.items()):
        if val[3] == 1:
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
            arti_planets[i].save()
            
        else:
            arti = Artefacts.objects.create(name=key,
                                           description=val[0],
                                           effect1=val[1],
                                           effect2=val[2],
                                           effect3=val[3],
                                           ticks_left=val[4],
                                           on_planet=None,
                                           image=val[5])


    print(arti_planets)
    print("Generating artefacts took " + str(time.time() - start_t) + "seconds")
    
def settings():
    start_t = time.time()
    exclude_list = ['1','3','4','5','6','7','2']
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
    for p in Planet.objects.all():
        if Planet.objects.filter(x=p.x, y=p.y, i=p.i).count() > 1:
            print(str(p.id))
            if p.home_planet == False:
                p.delete()
               
            
                                            
    print("Generating settings took " + str(time.time() - start_t) + "seconds")
   
