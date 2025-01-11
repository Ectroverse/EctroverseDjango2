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
        for i, (key, val) in enumerate(inca_specs.items()):
            spec = Ops.objects.create(specop_type='G',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
                                
        for i, (key, val) in enumerate(agentop_specs.items()):
            spec = Ops.objects.create(specop_type='O',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
                                
        for i, (key, val) in enumerate(psychicop_specs.items()):
            spec = Ops.objects.create(specop_type='S',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                selfsp=val[3],
                                description=val[5])

