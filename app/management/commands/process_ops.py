from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from app.models import *
from app.calculations import *
from app.constants import *
from app.helper_functions import *
from galtwo.models import RoundStatus as RoundStat
from datetime import datetime, timedelta
import requests
from discord import Webhook, RequestsWebhookAdapter
import time
from django.db.transaction import get_connection

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic # Makes it so all object saves get aggregated, otherwise process_tick would take a minute
    def handle(self, *args, **options):
        start_t = time.time()
        
        cursor = get_connection().cursor()
        cursor.execute(f'LOCK TABLE app_fleet; lock table app_userstatus; \
            lock table app_news; lock table app_scouting; lock table app_artefacts;\
            lock table app_specops;') 
        fleets_processed = 0 
        try:
            
            agent_fleets = Fleet.objects.filter(agent__gt=0, main_fleet=False, command_order=6, ticks_remaining=0)
            for agent_fleet in agent_fleets:
                # perform operation
                if agent_fleet.target_planet is None:
                    agent_fleet.command_order = 2
                    agent_fleet.save()
                    continue
                fleets_processed += 1
                perform_operation(agent_fleet)
                # (operation, agents, user1, planet):
                status = UserStatus.objects.get(id=agent_fleet.owner.id)
                speed = travel_speed(status)

                # send agents home after operation
                portals = Planet.objects.filter(owner=agent_fleet.owner.id, portal=True)
                if portals is None:
                    agent_fleet.command_order = 2 #if no portals the fleet cant return, make it hoover
                    agent_fleet.save()
                    continue

                portal = find_nearest_portal(agent_fleet.x, agent_fleet.y, portals, status)
                generate_fleet_order(agent_fleet, portal.x, portal.y, speed, 5)
                
            ghost_fleets = Fleet.objects.filter(ghost__gt=0, main_fleet=False, command_order=7, ticks_remaining=0)
            for ghost_fleet in ghost_fleets:
                # perform incantation
                if ghost_fleet.target_planet is None:
                    ghost_fleet.command_order = 2
                    ghost_fleet.save()
                    continue
                
                fleets_processed += 1
                perform_incantation(ghost_fleet)
                status = UserStatus.objects.get(id=ghost_fleet.owner.id)
                speed = travel_speed(status)

                # send home
                if ghost_fleet.specop == "Vortex Portal":
                    main_fleet = Fleet.objects.get(owner=ghost_fleet.owner.id, main_fleet=True)
                    main_fleet.ghost += ghost_fleet.ghost
                    main_fleet.save()
                    ghost_fleet.delete()
                else:
                    portals = Planet.objects.filter(owner=ghost_fleet.owner.id, portal=True)
                    portal = find_nearest_portal(ghost_fleet.x, ghost_fleet.y, portals, status)
                    generate_fleet_order(ghost_fleet, portal.x, portal.y, speed, 5)
        finally:
            cursor.close()    
            
            

        
        empires = Empire.objects.filter(numplayers__gt=0).order_by("-planets", "-networth")
        arti_count = Artefacts.objects.exclude(on_planet=None).count()
        all_artis = Artefacts.objects.exclude(on_planet=None)
        arte_timer = RoundStatus.objects.first()
        fast = RoundStat.objects.first()
        max_artis = 0
        art_tab = {}
        msg = ''
        for a in all_artis:
            if a.empire_holding is not None:
                if a.empire_holding not in art_tab:
                    art_tab[a.empire_holding] = 1
                else:
                    art_tab[a.empire_holding] += 1
                max_artis = max(art_tab[a.empire_holding], max_artis)
            
            # process_artis
            if a.name == "Obelisk":
                actobelisk()
                
            if a.name == "Terraformer":
                if a.ticks_left == 0 and a.empire_holding != None:
                    terraformer()
                
            if a.name == "Flying Dutchman":
                if a.ticks_left == 0 and a.empire_holding != None:
                    dutchman()            
        
        holding = ""
        game_round = RoundStatus.objects.filter().first()
        tick_hour = (60/game_round.tick_time) * 60
        
        if arte_timer.tick_number == 1008:
            msg += "Peace has ended and a new Agent Operation has entered the galaxy, allowing all races to Steal Resources!"
            
        
        if game_round.emphold != None:
            holding = game_round.emphold.name_with_id
        if arte_timer.artedelay < (tick_hour - 1) and max_artis == arti_count:
            msg += "Artefact/s recaptured! Timer resumed! Round will end in " + str(arte_timer.artetimer) + " weeks!"
            arte_timer.artedelay = tick_hour - 1
            arte_timer.save()
        if arte_timer.artetimer == (tick_hour*24) - 1:
            msg += "All Artefacts held by " + str(holding) + "! Round will end in " + str(arte_timer.artetimer) + " weeks!"
        if arte_timer.artedelay == tick_hour - 2:
            msg += "Artefact/s lost! Timer will reset in " + str(int(tick_hour-1)) + " weeks!"
        if arte_timer.artedelay < 0:
            msg += "Artefact/s lost! Timer reset!"
                
        if arte_timer.artetimer == 0:
            msg += "Congratulations " + str(holding) + "!"
            
        if msg != '':
            NewsFeed.objects.create(date_and_time = datetime.now(), message = msg)
            webhook = Webhook.from_url("https://discord.com/api/webhooks/1225161748378681406/ModQRVgqG6teRQ0gi6_jWGKiguQgA0FBsRRWhDLUQcBNVfFxUb-sTQAkr6QsB7L8xSqE", adapter=RequestsWebhookAdapter())
            #webhook.send(msg) 
            
        print("Process ops took: " +  str(time.time() - start_t) )
        
        f = open("process_ops_log.txt", "a")
        f.write("Process ops took: " +  str(time.time() - start_t) + ' fleets processed ' + str(fleets_processed) + "\n")
        f.close()
