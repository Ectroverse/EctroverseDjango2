from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from django.db import transaction



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        user = UserStatus.objects.get(id=1)
        planet = Planet.objects.filter(owner=None)
        count = 0
        for p in planet:
            if p.home_planet == False:
                p.owner = user.user
                p.save()
                count += 1
            if count >= 100:
                break
                   
                
                                                
        print("Generating settings took " + str(time.time() - start_t) + "seconds")
