from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
from django.db import connection
from django.db.models import Q, Sum
from datetime import datetime
import copy
import math
from discord import SyncWebhook
#from app.models import NewsFeed
#from galtwo.models import *
from galtwo.models import RoundStatus as StatusRound
from app.models import *

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        def start():
            tick_start = RoundStatus.objects.get(id=1)
            tick_start.is_running = True
            tick_start.save()
            fast_tick = StatusRound.objects.get(id=1)
            msg = ""
            #if fast_tick.is_running == True:
            #    fast_tick.is_running = False
            #    fast_tick.save()
            #    msg = "Fast Round has now Ended! "
            msg += "The Regular Round has now started, Good Luck!"
            NewsFeed.objects.create(date_and_time = datetime.now(), message = msg)
            msg = "<@&1201666532753547315> " + str(msg)
            webhook = SyncWebhook.from_url("https://discord.com/api/webhooks/1225161748378681406/ModQRVgqG6teRQ0gi6_jWGKiguQgA0FBsRRWhDLUQcBNVfFxUb-sTQAkr6QsB7L8xSqE")
            webhook.send(msg)
            webhk = SyncWebhook.from_url("https://discord.com/api/webhooks/1227218151629000744/MeckPYnnT6hoiznfBz5oxm6pjWdgCXxVLOmLf7kFa78cYpimyDNK1BxgBdQOyZgD9qgu")
            webhk.send(msg)
            
        start()
        print("Round start took " + str(time.time() - start_t) + "seconds")


               
