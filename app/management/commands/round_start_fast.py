from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
import time
from django.db import connection
from django.db.models import Q, Sum
from datetime import datetime
import copy
import math
from discord import Webhook, RequestsWebhookAdapter
from app.models import NewsFeed
from galtwo.models import *


class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        def start():
            tick_start = RoundStatus.objects.get(id=1)
            tick_start.is_running = True
            tick_start.save()
            msg = "The Fast Round has now started, Good Luck and Have Fun!"
            #msg += "The Regular Round has now started, Good Luck!"
            NewsFeed.objects.create(date_and_time = datetime.now(), message = msg)
            msg = "<@&1201666532753547315> " + str(msg)
            webhook = Webhook.from_url("https://discord.com/api/webhooks/1225161748378681406/ModQRVgqG6teRQ0gi6_jWGKiguQgA0FBsRRWhDLUQcBNVfFxUb-sTQAkr6QsB7L8xSqE", adapter=RequestsWebhookAdapter())
            webhook.send(msg)
            webhk = Webhook.from_url("https://discord.com/api/webhooks/1227218151629000744/MeckPYnnT6hoiznfBz5oxm6pjWdgCXxVLOmLf7kFa78cYpimyDNK1BxgBdQOyZgD9qgu", adapter=RequestsWebhookAdapter())
            webhk.send(msg)
            
        start()
        print("Round start took " + str(time.time() - start_t) + "seconds")


               
