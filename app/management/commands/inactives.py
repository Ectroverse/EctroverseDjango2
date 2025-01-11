from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
from django.db import connection
from django.db.models import Q, Sum
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from galtwo.models import RoundStatus as StatusRound
from app.models import *

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model() 
        inactive_users = User.objects.filter(date_joined__lt=datetime.now() - timedelta(seconds=86400), is_active=False)
        
        for user in inactive_users:
            user.delete()      
