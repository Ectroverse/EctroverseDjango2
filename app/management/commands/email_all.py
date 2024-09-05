from django.core.management.base import BaseCommand, CommandError
from app.models import *
from app.constants import *
import time
import random
from app.map_settings import *
from django.db import transaction
from django.core.mail import send_mail



class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic
    def handle(self, *args, **options):
        start_t = time.time()
        
        subject = "A new round is starting soon!"
        message = "Hello! \nCan you conquer the Galaxy? \nA new round is starting soon, Sunday 5th, May 2024 at 2PM, UTC\n\n https://ectroverse.org"
        recievers = []
        for user in User.objects.all():
            recievers.append(user.email)

        send_mail(subject, message, "admin@ectroverse.co.uk", recievers)
        
        print("Sending mail took " + str(time.time() - start_t) + "seconds")
