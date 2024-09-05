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

class Command(BaseCommand): # must be called command, use file name to name the functionality
    @transaction.atomic # Makes it so all object saves get aggregated, otherwise process_tick would take a minute
    def handle(self, *args, **options):
        agent_fleets = Fleet.objects.filter(agent__gt=0, main_fleet=False, command_order=6, ticks_remaining=0)
        for agent_fleet in agent_fleets:
            # perform operation
            if agent_fleet.target_planet is None:
                agent_fleet.command_order = 2
                agent_fleet.save()
                continue

            perform_operation(agent_fleet)
            # (operation, agents, user1, planet):
            status = UserStatus.objects.get(id=agent_fleet.owner.id)
            speed = race_info_list[status.get_race_display()]["travel_speed"]

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

            perform_incantation(ghost_fleet)
            status = UserStatus.objects.get(id=ghost_fleet.owner.id)
            speed = race_info_list[status.get_race_display()]["travel_speed"]

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
        
        
        growart = Artefacts.objects.get(name="You Grow, Girl!")
        if growart.on_planet != None:
            growplant = growart.on_planet.id
            growplant = Planet.objects.get(id=growplant)
            growplant.size += 1
            growplant.save()
        
        if max_artis == arti_count:
            emp_holding = Artefacts.objects.get(name="Ether Gardens")
            holding = emp_holding.empire_holding.name_with_id
            if arte_timer.artedelay < 5:
                msg = "Artefact/s recaptured! Timer resumed! Round will end in " + str(arte_timer.artetimer) + " weeks!"
                arte_timer.artetimer -= 1
                arte_timer.artedelay = "5"
                arte_timer.save()
            elif int(arte_timer.artetimer) >= 1:
                arte_timer.artetimer -= 1
                arte_timer.save()
                time_left = arte_timer.artetimer * 10
                now = datetime.now()
                now_plus_10 = now + timedelta(minutes = time_left)
                fast.round_start = now_plus_10
                fast.save()
                if arte_timer.artetimer == 143:
                    msg = "All Artefacts held by " + str(holding) + "! Round will end in " + str(arte_timer.artetimer) + " weeks!"
        else:
            if arte_timer.artedelay > 0 and arte_timer.artetimer < 144:
                arte_timer.artedelay -= 1
                arte_timer.save()
                time_left = (arte_timer.artetimer + arte_timer.artedelay) * 10
                now = datetime.now()
                now_plus_10 = now + timedelta(minutes = time_left)
                fast.round_start = now_plus_10
                fast.save()
                if arte_timer.artedelay == 4:
                    msg = "Artefact/s lost! Timer will reset in 5 weeks!"
                
            else:
                if arte_timer.artedelay == 0:
                    msg = "Artefact/s lost! Timer reset!"
                    arte_timer.artetimer = "144"
                    arte_timer.artedelay = "5"
                    arte_timer.save()
                    fast.round_start = None
                    fast.save()
                
        
        if arte_timer.artetimer == 0:
            emp_holding = Artefacts.objects.get(name="Ether Gardens")
            holding = emp_holding.empire_holding.name_with_id
            arte_timer.is_running = False
            arte_timer.round_start = None
            arte_timer.save()
            fast.is_running = True
            fast.save()
            msg = "Congratulations " + str(holding) + "! Fast galaxy has now started, Good Luck! New Regular Round will be announced soon!"
            
        if msg != '':
            NewsFeed.objects.create(date_and_time = datetime.now(), message = msg)
            webhook = Webhook.from_url("https://discord.com/api/webhooks/1225161748378681406/ModQRVgqG6teRQ0gi6_jWGKiguQgA0FBsRRWhDLUQcBNVfFxUb-sTQAkr6QsB7L8xSqE", adapter=RequestsWebhookAdapter())
            webhook.send(msg)
