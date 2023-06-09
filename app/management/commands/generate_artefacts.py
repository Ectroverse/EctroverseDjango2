from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from app.map_settings import *
from django.db import transaction



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

        # add new
        # artefact list:
        arti_list = {
            "Ether Gardens": ["Increases your energy production by 10%!", 10, 0, 0, 0, "/static/arti/artimg0.gif"],
            "Mirny Mine": ["Increases your mineral production by 15%!", 15, 0, 0, 0 ,"/static/arti/artimg1.gif"],
            "Foohon Technology": ["Increases your ectrolium production by 10%!", 10, 0, 0, 0, "/static/arti/artimg2.gif"],
            "Crystal Synthesis": ["Increases your crystal production by 15%!", 15, 0, 0, 0, "/static/arti/artimg3.gif"],
            "Research Laboratory": ["Increases your research production by 10%!", 10, 0, 0, 0, "/static/arti/artimg4.gif"],
            "t-Veronica": ["A strange virus in the air improves your populations fighting ability!", 0, 0, 0, 0, "/static/arti/artimg5.gif"],
            "Darwinism": ["Citizens have evolved, aiding in the cause!", 0, 0, 0, 0, "/static/arti/artimg6.gif"],
            "Military Might": ["Decreases unit upkeep by 10%!", 10, 0, 0, 0, "/static/arti/artimg14.gif"],
            "Terraformer": ["An ancient gate allows planets to be transformed!", 0, 0, 0, 1, "/static/arti/artimg7.gif"],
            "The Recycler": ["Your scientist have developed a new technology, reducing waste!", 0, 0, 0, 0, "/static/arti/artimg10.gif"],
        }

        arti_planets = random.sample(list(planets), len(arti_list))

        for i, (key, val) in enumerate(arti_list.items()):
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

