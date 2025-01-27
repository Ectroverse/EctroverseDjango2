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
        t = Ticks_log.objects.filter().delete()
        

