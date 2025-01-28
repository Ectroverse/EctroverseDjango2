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


class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):                    
        t = Ticks_log.objects.filter(logtype="t")
        o = Ticks_log.objects.filter(logtype="o")
        i = Ticks_log.objects.filter(logtype="i")
        ttime = 0
        tcount = 0
        otime = 0
        ocount = 0
        itime = 0
        icount = 0
        for t in t:
            ttime += t.calc_time_ms
            tcount += 1
        for o in o:
            otime += o.calc_time_ms
            ocount += 1
        for i in i:
            itime += i.calc_time_ms
            icount += 1
            
        ttime = ttime / tcount
        otime = otime / ocount
        itime = itime / icount
        
        print("Tick: " + str(ttime))
        print("Operations: " + str(otime))
        print("Incantations: " + str(itime))

