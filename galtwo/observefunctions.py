from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from galtwo.models import *
import time
from django.db import connection
from app.botops import *
import random
from django.db.models import Q, Sum
import numpy as np
from datetime import datetime
import copy
import math
    
def observe(status):
        main_fleet = Fleet.objects.get(owner=status.id, main_fleet=True)
        operation = "Observe Planet"
        portal = Planets.objects.filter(owner=status.user, portal=True)
        systems = []
        for p in portal:
            for s in System.objects.all():
                distx = abs(p.x-s.x)
                disty = abs(p.y-s.y)
                if distx <= 5 and disty <= 5:
                    if s.id not in systems:
                        systems.append(s.id)

        for s in systems:
            system = System.objects.get(id=s)
            if systems.index(s) == 0:
                planet = Planets.objects.filter(x=system.x, y=system.y)
            else:
                system = System.objects.get(id=s)
                splanets = Planets.objects.filter(x=system.x, y=system.y)
                planet = planet | splanets
            
        print(planet)    

