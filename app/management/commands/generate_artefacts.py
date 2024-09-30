from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from app.map_settings import *
from django.db import transaction
from app.round_functions import arti_list



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        # delete old
        Artefacts.objects.all().delete()
        empires = Empire.objects.all()
        for e in empires:
            if e.artefacts is not None:
                e.artefacts.clear()
                e.save()
        planets = Planet.objects.filter(home_planet=False)
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

