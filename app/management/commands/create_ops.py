from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models import *
from galtwo.models import UserStatus as TwoStatus, RoundStatus as StatusRound, Ops as Op
from app.constants import *
import time
from django.db.models import Q
from django.db import connection
import random
import datetime
import numpy as np
from django.contrib.auth import get_user_model

import requests

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):   
        Ops.objects.all().delete()
        for i, (key, val) in enumerate(inca_specs.items()):
            Ops.objects.create(specop_type='G',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
            Op.objects.create(specop_type='G',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
                                
        for i, (key, val) in enumerate(agentop_specs.items()):
            Ops.objects.create(specop_type='O',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
            Ops.objects.create(specop_type='o',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
                                
        for i, (key, val) in enumerate(psychicop_specs.items()):
            Ops.objects.create(specop_type='S',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                selfsp=val[3],
                                description=val[5])
            Op.objects.create(specop_type='S',
                                name=key,
                                tech=val[0],
                                ident=val[4],
                                readiness=val[1],
                                difficulty=val[2],
                                stealth=val[3],
                                description=val[5])
        
