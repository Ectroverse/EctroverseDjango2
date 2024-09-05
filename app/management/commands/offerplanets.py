from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models import *
from app.calculations import *
from app.constants import *
import time
from django.db.models import Q
from django.db import connection
from app.helper_functions import *
from app.botfunctions import *
from app.helper_classes import *
from app.battle import *
import random



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        status = UserStatus.objects.get(id=5)
        planets = Planet.objects.filter(owner=status.user, portal=False, portal_under_construction=False)
        user3 = UserStatus.objects.get(id=3)
        user4 = UserStatus.objects.get(id=4)
        if planets:
            for p in planets:
                if p.bonus_mineral > 0:
                    taker = user4
                elif p.bonus_crystal > 0:
                    taker = user4
                elif p.bonus_ectrolium > 0:
                    taker = user4
                else:
                    taker = user3
                
                
                frloss = battleReadinessLoss(taker, status, p)
                if taker.fleet_readiness > 0:
                    taker.fleet_readiness -= frloss
                    p.owner = taker.user
                    p.save()
                    taker.num_planets += 1
                    taker.save()
                    status.num_planets -= 1
                    status.save()
        
        status = UserStatus.objects.get(id=8)
        planets = Planet.objects.filter(owner=status.user, portal=False, portal_under_construction=False)
        user3 = UserStatus.objects.get(id=6)
        user4 = UserStatus.objects.get(id=7)
        if planets:
            for p in planets:
                if p.bonus_mineral > 0:
                    taker = user4
                elif p.bonus_crystal > 0:
                    taker = user4
                elif p.bonus_ectrolium > 0:
                    taker = user4
                else:
                    taker = user3
                
                
                frloss = battleReadinessLoss(taker, status, p)
                if taker.fleet_readiness > 0:
                    taker.fleet_readiness -= frloss
                    p.owner = taker.user
                    p.save()
                    taker.num_planets += 1
                    taker.save()
                    status.num_planets -= 1
                    status.save()

        print("Generating botoffer took " + str(time.time() - start_t) + "seconds")      
