from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models import *
#from galtwo.calculations import *
import time
from django.db.models import Q
from django.db import connection
#from galtwo.helper_functions import *
#from galtwo.botfunctions import *
import random
import datetime
import numpy as np
from app.round_functions import arti_list

import requests
from discord import Webhook, RequestsWebhookAdapter




class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        '''sense = Sensing.objects.filter(empire_id=889).values_list('system_id', flat=True)
        artis = Artefacts.objects.filter(on_planet__isnull=False)
        user = User.objects.get(id=84)
        for a in artis:
            p = a.on_planet
            system = System.objects.get(x=p.x, y=p.y)
            if system.id in sense:
                scout = Scouting.objects.filter(user=user, planet=p)
                if scout:
                    scout = Scouting.objects.get(user=user, planet=p)
                    scout.scout = 1.0
                    scout.save()
                else:
                    Scouting.objects.create(user=user, planet=p, scout=1.0)
                    
                    
        game_round = RoundStatus.objects.filter().first()
        # record data for hall of fame
        for status in UserStatus.objects.all():
            if status.empire is not None:
                artis = Artefacts.objects.filter(empire_holding=status.empire).count()
                HallOfFame.objects.create(round=game_round.round_number,
                                          userid=status.id,
                                          user=status.user_name,
                                          empire=status.empire.name_with_id,
                                          artefacts=artis,
                                          planets=status.num_planets,
                                          networth=status.networth,
                                          race=status.get_race_display())
                tags = status.num_planets
                t_artis = Artefacts.objects.filter(effect3=1).count()
                if artis == t_artis:
                    tags *= 3
                status.tag_points += tags
                status.save()'''
        
        
        
        '''status = UserStatus.objects.get(id=98)
        mf = Fleet.objects.get(owner=status.user)
        psyhics = mf.wizard
        plants = Planets.objects.filter(owner=status.user)
        ps = {}
        fa = 0.4 + (1.2 / 255.0) * (np.random.randint(0, 2147483647) & 255)
        attack = fa * psychics * (1.0 + 0.005 * status.research_percent_culture)         
        attack /= psychicop_specs[spell][2]
        planet = secrets.choice(Planets.objects.filter(owner=status.user))
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
        
        status = UserStatus.objects.get(id=1)
        print(status.race)'''
        
        '''get_emp = []
        get_system = []
        for s in Sensing.objects.all():
            if s.empire.id not in get_emp:
                get_emp.append(s.empire.id)
            if s.system.id not in get_system:
                get_system.append(s.system.id)
        
        get_p = []
        for s in Scouting.objects.all():
            if s.planet.id not in get_p:
                get_p.append(s.planet.id)

        
        emps = Empire.objects.filter(id__in=get_emp)
        for p in Planets.objects.filter(id__in=get_p):
            for emp in emps:
                user = UserStatus.objects.get(empire=emp)
                if Scouting.objects.filter(user=user.user, planet=p).count() > 1:
                   Scouting.objects.filter(user=user.user, planet=p).delete()
                   Scouting.objects.create(user=user.user, empire=emp, scout=1, planet=p)
        for s in System.objects.filter(id__in=get_system):
            for emp in emps:
                if Sensing.objects.filter(empire=emp, system=s).count() > 1:
                   Sensing.objects.filter(empire=emp, system=s).delete()
                   Sensing.objects.create(empire=emp, scout=3, system=s)
                   
        for a in Artefacts.objects.filter(on_planet__isnull=False):
            for emp in Empire.objects.filter(numplayers=1):
                user = UserStatus.objects.get(empire=emp)
                if Scouting.objects.filter(user=user.user, planet=a.on_planet).count() > 1:
                    for s in Scouting.objects.filter(user=user.user, planet=a.on_planet):
                        s.delete()
                    Scouting.objects.create(user=user.user, empire=emp, scout=1, planet=a.on_planet)
                s = System.objects.get(x=a.on_planet.x, y=a.on_planet.y)
                if Sensing.objects.filter(empire=emp, system=s).count() > 1:
                    for s in Sensing.objects.filter(empire=emp, system=s):
                        s.delete()
                    Sensing.objects.create(empire=emp, scout=3, system=s)
                    
        for i, (key, val) in enumerate(arti_list.items()):
            if key != "The General":
                try:
                    arte = Artefacts.objects.get(name=key)
                    arte.effect1=val[1]
                    arte.effect2=val[2]
                    arte.effect3=val[3]
                    arte.save()
                except:
                    a=1'''
                    
        for i, (key, val) in enumerate(agentop_specs.items()):
            spec = Ops.objects.get(name=key)
            spec.difficulty=val[2]
            spec.save()

