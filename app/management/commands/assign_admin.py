from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models import *
from galtwo.models import UserStatus as TwoStatus
import time
from django.db.models import Q
from django.db import connection
import random
import datetime
import numpy as np

import requests

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):   
        User = get_user_model()
        user = User.objects.filter(id=1)
        UserStatus.objects.create(id=user.id, user=user)
        TwoStatus.objects.create(id=user.id, user=user)
