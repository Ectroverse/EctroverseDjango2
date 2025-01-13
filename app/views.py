from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from .constants import *
from .calculations import *
from .helper_classes import *
from .tables import *
from .forms import *
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from io import BytesIO
import base64
from django_tables2 import SingleTableView
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash, logout, authenticate, login
from .forms import RegisterForm
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.exceptions import ObjectDoesNotExist
from django.template import RequestContext
from django.db.models import Q, Max, Sum, Count
from django.contrib.auth.decorators import user_passes_test
from app.map_settings import *
from app.helper_functions import *
from app.specops import *
from app.battle import *
from galtwo.views import choose_empire
from galtwo.models import RoundStatus as StatusRound, Artefacts as Fastartes, Planets, Empire as Empires, System as Systems, UserStatus as TwoStatus, Fleet as Fleets
from django.views.decorators.clickjacking import xframe_options_exempt
from app.round_functions import arti_list

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.sites.models import Site
import requests
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm

import json
import numpy as np
import time
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import datetime

from django.urls import include, path, re_path


# Remember that Django uses the word View to mean the Controller in MVC.  Django's "Views" are the HTML templates. Models are models.

bare = "No"

def race_check(user):
    userstatus = get_object_or_404(UserStatus, user=user)
    if userstatus.race == None or userstatus.empire == None:
        return False
    else:
        return True


def reverse_race_check(user):
    userstatus = get_object_or_404(UserStatus, user=user)
    if userstatus.race == None or userstatus.empire == None:
        return True
    else:
        return False

def index(request, *args):
    error = None
    if args:
        error = args[0]
    adminz=[]
    a_users = [1]
    for u in a_users:
        a_status = UserStatus.objects.get(id=u)
        if a_status.user_name != '':
            adminz.append(u)
    round_no = RoundStatus.objects.get().round_number
    tick_time = RoundStatus.objects.get().tick_number
    round_start = RoundStatus.objects.get().round_start
    week = tick_time % 52
    year = tick_time // 52
    no_planets = Planet.objects.all().count()
    no_system = System.objects.all().count()
    no_empires = Empire.objects.all().exclude(number=0).count()
    no_players = UserStatus.objects.exclude(user_name='').exclude(user_name='user-display-name').exclude(id__in=adminz).exclude(id=1).count()
    avail_spots = ((no_empires * players_per_empire) - no_players)
    avail_planets = Planet.objects.filter(owner=None).count()
    time_tick = RoundStatus.objects.filter().first()
    online_now = 0
    users = UserStatus.objects.filter().exclude(id__in=adminz).exclude(id=1)
    for u in users:
        active = u.last_active
        if (datetime.datetime.now() - active).seconds < 300:
            online_now += 1 
    round2 = StatusRound.objects.filter().first()
    round_no2 = StatusRound.objects.get().round_number
    tick_time2 = StatusRound.objects.get().tick_number
    week2 = tick_time2 % 52
    year2 = tick_time2 // 52
    no_planets2 = Planets.objects.all().count()
    no_system2 = Systems.objects.all().count()
    no_empires2 = Empires.objects.all().exclude(number=0).count()
    no_players2 = TwoStatus.objects.exclude(user_name='').exclude(user_name='user-display-name').exclude(id__in=adminz).exclude(id=1).count()
    avail_spots2 = (no_empires2 - no_players2)
    avail_planets2 = Planets.objects.filter(owner=None).count()
    time_tick2 = StatusRound.objects.filter().first()
    roun2 = StatusRound.objects.filter().first()
    gettime = roun2.round_start
    fortime = 0
    if round_start != None:
        fortime = round_start.strftime("%B %d, %y, %H:%M:%S") 
    gettime = roun2.round_start
    formtime = 0
    if gettime != None:
        formtime = gettime.strftime("%B %d, %y, %H:%M:%S") 
    context = {"news_feed": NewsFeed.objects.all().order_by('-date_and_time'),
                "round_no": round_no,
                "fortime": fortime,
                   "week": week,
                   "year": year,
                   "no_planets": no_planets,
                   "no_system": no_system,
                   "no_empires": no_empires,
                   "no_players": no_players,
                   "avail_spots": avail_spots,
                   "avail_planets": avail_planets,
                   "time_tick": time_tick,
                   "online_now": online_now,
                   "round2": round2,
                   "round_no2": round_no2,
                   "week2": week2,
                   "year2": year2,
                   "no_planets2": no_planets2,
                   "no_system2": no_system2,
                   "no_empires2": no_empires2,
                   "no_players2": no_players2,
                   "avail_spots2": avail_spots2,
                   "avail_planets2": avail_planets2,
                   "time_tick2": time_tick2,
                   "formtime": formtime,
                   "errors": error}
    return render(request, "login.html", context)
    
def update(request):
    return render(request, "update.html")


def faq(request):
    return render(request, "faq.html")


def custom_login(request):
    form = AuthenticationForm(request.POST)
    username = request.POST['username']
    password = request.POST['password']
    user = get_user_model().objects.filter(username=username).first()
    if user:
        if user.is_active:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                context = {"user": user}
                return redirect("/portal", context)
            else:
                context = {"news_feed": NewsFeed.objects.all().order_by('-date_and_time'),
                           "errors": "Wrong username/password!"}
                return index(request, "Wrong username/password!")
        else:
            current_site = Site.objects.get_current()
            mail_subject = 'Activate your Ectroverse account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = user.email
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return render(request, "confirm.html", {"msg": "Please reactivate your account by confirming through email"})
        


# In contrast to HttpRequest objects, which are created automatically by Django, HttpResponse objects are your responsibility. Each view you write is responsible for instantiating, populating, and returning an HttpResponse.
# The HttpResponse class lives in the django.http module.
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            #inactive_user = send_verification_email(response, form)
            user=form.save(commit=False)
            user.is_active = False
            user.save()
            current_site = Site.objects.get_current()
            mail_subject = 'Activate your Ectroverse account.'
            message = render_to_string('acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            email.send()
            return render(response, "confirm.html", {"msg": "Please confirm your email address to complete the registration"})
    else:
        form = RegisterForm()
    return render(response, "register.html", {"form": form})

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        if not UserStatus.objects.filter(id=user.id):
            UserStatus.objects.create(id=user.id, user=user)
        if not Fleet.objects.filter(owner=user, main_fleet=True):
            Fleet.objects.create(owner=user, main_fleet=True)
        if not TwoStatus.objects.filter(id=user.id):
            TwoStatus.objects.create(id=user.id, user=user)
        if not Fleets.objects.filter(owner=user, main_fleet=True):
            Fleets.objects.create(owner=user, main_fleet=True)
        return index(request, "Account Activated")
    else:
        return confirm(request, "Activation link is invalid!")

def confirm(request, step):
    msg = step
    context = {"msg":msg}
    return render(request, "confirm.html", context)

def csrf_failure(request, reason=""):
    return index(request, "Oops... It appears you have gone back and attempted to reuse a form, please try again.")

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def headquarters(request):
    status = get_object_or_404(UserStatus, user=request.user)
    
    tick_time = RoundStatus.objects.get().tick_number
    week = tick_time % 52
    year = tick_time // 52
    fresh_news = News.objects.filter(user1=request.user, is_read=False, is_personal_news=True).order_by(
        '-date_and_time')
    old_news = News.objects.filter(user1=request.user, is_read=True, is_personal_news=True).order_by('-date_and_time')
    for n in fresh_news:
        n.is_read = True
    News.objects.bulk_update(fresh_news, ['is_read'])
    
    msg = ''
    
    ground = RoundStatus.objects.get()
    skrull = Artefacts.objects.get(name="Skrullos Fragment")
    skrull_time = tick_hour = ((60/ground.tick_time) * 60)*24
    a_change = ""
    s_news = News.objects.filter(news_type='SK', user1=status.user)
    if not s_news:
        a_change = "Yes"
    else:
        s_news = News.objects.get(news_type='SK', user1=status.user)
        skrull_time = int((s_news.tick_number + skrull_time) - tick_time)
    
    if request.method == 'POST':
        if request.POST['accept']:
            planet = request.POST.get('off_planet', False)
            off_p = Planet.objects.get(id=planet)
            news = News.objects.get(planet=planet, news_type='E', user1=status.user)
            if planet and status.fleet_readiness >= -100:
                if off_p.owner == news.user2:
                    p = Planet.objects.get(id=planet)
                    frloss = battleReadinessLoss(status, news.user2.userstatus, p)
                    p.owner = status.user
                    p.solar_collectors = round(p.solar_collectors * 9 / 10)
                    p.fission_reactors = round(p.fission_reactors * 8 / 10)
                    p.mineral_plants = round(p.mineral_plants * 8 / 10)
                    p.crystal_labs = round(p.crystal_labs * 8 / 10)
                    p.refinement_stations = round(p.refinement_stations * 8 / 10)
                    p.cities = round(p.cities * 8 / 10)
                    p.research_centers = round(p.research_centers * 8 / 10)
                    p.defense_sats = round(p.defense_sats * 8 / 10)
                    p.shield_networks = round(p.shield_networks * 8 / 10)
                    p.portal = False
                    p.buildings_under_construction = 0
                    p.portal_under_construction = False
                    p.protection = 0
                    totbuild = (p.solar_collectors + p.fission_reactors + p.mineral_plants + p.crystal_labs + p.refinement_stations + p.cities + p.research_centers + p.defense_sats + p.shield_networks)
                    p.total_buildings = totbuild
                    p.overbuilt = calc_overbuild(p.size, totbuild - (p.defense_sats + p.shield_networks))
                    p.overbuilt_percent = (p.overbuilt - 1.0) * 100
                    p.save()
                    msg += "Planet taken!"
                    status.fleet_readiness -= frloss
                    status.save()
                    for con in Construction.objects.all():
                        if con.planet == p:
                            con.delete()
                    News.objects.create(user1=news.user2,
                        user2=status.user,
                        empire1=status.empire,
                        news_type='E',
                        date_and_time=datetime.datetime.now(),
                        planet=p,
                        extra_info="2",
                        is_personal_news=True,
                        is_empire_news=True,
                        tick_number=RoundStatus.objects.get().tick_number)
                    news.delete()
                else:
                    msg += "Unable to take control!"
                    news.delete()
    
    status.construction_flag = 0
    news = News.objects.filter(news_type='E', user1=status.user, extra_info="1")
    if not news:
        status.economy_flag = 0
    status.military_flag = 0
    status.save()
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Headquarters",
               "week": week,
               "year": year,
               "fresh_news": fresh_news,
               "old_news": old_news,
               "news_feed": NewsFeed.objects.last(),
               "artis": Artefacts.objects.get(name="Ether Gardens"),
               "skrull": skrull,
               "skrull_time": skrull_time,
               "a_change": a_change,
               "msg": msg}
    return render(request, "headquarters.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def offer(request):
    status = get_object_or_404(UserStatus, user=request.user)
    order_by = request.GET.get('order_by', 'planet')
    print("order by-", order_by)

    ordered = "No"
    # TODO, it currently does not support reversing the order by clicking it a second time
    if order_by == 'planet':
        yr_planets = Planet.objects.filter(owner=request.user).order_by('x', 'y', 'i')
        ordered = "Yes"
    else:
        yr_planets = Planet.objects.filter(owner=request.user).order_by(order_by)  # directly use the keyword
        ordered = "Yes"
    
    
    news = News.objects.filter(news_type='E', user1=status.user, extra_info="1")
    msg = ""
    
    plist = {}
    for p in news:
        p = Planet.objects.get(id=p.planet.id)
        plist[p.id] = {"coords": "", "owner": p.owner.userstatus.user_name, "distance": "", "cost": ""}
        plist[p.id]["coords"] = str(p.x) + "," + str(p.y) + ":" + str(p.i)
        portal_planets = Planet.objects.filter(owner=status.user, portal=True)
        if portal_planets:
            portal = find_nearest_portal(p.x, p.y,
                                                 portal_planets, status)
            min_dist = np.sqrt((portal.x - p.x) ** 2 +
                           (portal.y - p.y) ** 2)
            speed = travel_speed(status)
            travel_time = max(0,int(np.floor(min_dist / speed)))
        else:
            travel_time = "No Portals!"
        plist[p.id]["distance"] = travel_time
        plist[p.id]["cost"] = battleReadinessLoss(status, p.owner.userstatus, p)
        
    
    if request.method == 'POST':
        if 'accept' in request.POST:
            p = request.POST.getlist('exp_planets')
            count=0
            news_send = False
            for planet in p:
                p = Planet.objects.get(id=planet)
                news = News.objects.get(planet=p.id, news_type='E', user1=status.user, extra_info="1")
                if p and status.fleet_readiness >= -100:
                    if p.owner == news.user2:
                        p = Planet.objects.get(id=planet)
                        frloss = battleReadinessLoss(status, news.user2.userstatus, p)
                        p.owner = status.user
                        p.solar_collectors = round(p.solar_collectors * 8 / 10)
                        p.fission_reactors = round(p.fission_reactors * 8 / 10)
                        p.mineral_plants = round(p.mineral_plants * 8 / 10)
                        p.crystal_labs = round(p.crystal_labs * 8 / 10)
                        p.refinement_stations = round(p.refinement_stations * 8 / 10)
                        p.cities = round(p.cities * 8 / 10)
                        p.research_centers = round(p.research_centers * 8 / 10)
                        p.defense_sats = round(p.defense_sats * 8 / 10)
                        p.shield_networks = round(p.shield_networks * 8 / 10)
                        p.portal = False
                        p.buildings_under_construction = 0
                        p.portal_under_construction = False
                        p.protection = 0
                        totbuild = (p.solar_collectors + p.fission_reactors + p.mineral_plants + p.crystal_labs + p.refinement_stations + p.cities + p.research_centers + p.defense_sats + p.shield_networks)
                        p.total_buildings = totbuild
                        p.overbuilt = calc_overbuild(p.size, totbuild - (p.defense_sats + p.shield_networks))
                        p.overbuilt_percent = (p.overbuilt - 1.0) * 100
                        p.save()
                        msg = "Planet taken!"
                        status.fleet_readiness -= frloss
                        status.save()
                        for con in Construction.objects.all():
                            if con.planet == p:
                                con.delete()
                        News.objects.create(user1=news.user2,
                            user2=status.user,
                            empire1=status.empire,
                            news_type='E',
                            date_and_time=datetime.datetime.now(),
                            planet=p,
                            extra_info="2",
                            is_personal_news=False,
                            is_empire_news=False,
                            tick_number=RoundStatus.objects.get().tick_number)
                        news.delete()
                        count += 1
                        news_send = True
                        
                    else:
                        msg = "Unable to take control!"
            
            if news_send:
                News.objects.create(user1=news.user2,
                            user2=status.user,
                            empire1=status.empire,
                            news_type='M',
                            date_and_time=datetime.datetime.now(),
                            fleet1="Accept",
                            extra_info=count,
                            is_personal_news=True,
                            is_empire_news=True,
                            is_read=False,
                            tick_number=RoundStatus.objects.get().tick_number)

        if 'offer' in request.POST:
            p = request.POST.getlist('planets_offer')
            count = 0
            for p in p:
                
                planet = Planet.objects.get(id=p)
                if planet.home_planet == False:
                    stat2 = request.POST.get('player', False)
                    status2 = UserStatus.objects.get(id=stat2)
                    news = News.objects.filter(planet=planet, news_type='E', user1=status2.user, extra_info="1")
                    if news:
                        news = News.objects.get(planet=planet, news_type='E', user1=status2.user, extra_info="1")
                        news.user1 = status2.user
                        news.is_read = True
                        news.save()
                    else:
                        News.objects.create(user1=status2.user,
                            user2=status.user,
                            empire1=status.empire,
                            news_type='E',
                            date_and_time=datetime.datetime.now(),
                            planet=planet,
                            extra_info="1",
                            is_personal_news=False,
                            is_empire_news=False,
                            is_read=True,
                            tick_number=RoundStatus.objects.get().tick_number)
                    count += 1
                
            msg = str(count) + " planets offered to " + str(status2.user_name)
            status2.economy_flag == 1
            status2.save()
            
            News.objects.create(user1=status2.user,
                            user2=status.user,
                            empire1=status.empire,
                            news_type='M',
                            date_and_time=datetime.datetime.now(),
                            planet=planet,
                            extra_info=count,
                            is_personal_news=True,
                            is_empire_news=True,
                            is_read=False,
                            tick_number=RoundStatus.objects.get().tick_number)
    
    off_news = News.objects.filter(news_type='E', user2=status.user, extra_info="1")
    off_dict = {}
    for n in off_news:
        off_dict[n.planet.id] = n.user1.userstatus.user_name
        
    
    player_list = UserStatus.objects.filter(empire=status.empire)
    offd = "No"
    if status.economy_flag == 1:
        offd = "Yes"
        status.economy_flag = 0
    
    context = {"status": status,
               "plist": plist,
               "yr_planets": yr_planets,
               "msg": msg,
               "player_list": player_list,
               "ordered": ordered,
               "offd": offd,
               "off_dict": off_dict,
               }
    return render(request, "offer.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def btn(request):
    status = UserStatus.objects.get(id=request.user.id)
    
    # mail
    btn1 = "i09.jpg"
    if status.mail_flag == 1:  # blue
        btn1 = "i09a.jpg"
    # building
    btn2 = "i10.jpg"
    if status.construction_flag == 1:  # yellow
        btn2 = "i10a.jpg"
    # market
    btn3 = "i11.jpg"
    if status.economy_flag == 1:  # green
        btn3 = "i11a.jpg"
    # fleets
    btn4 = "i12.jpg"
    if status.military_flag == 1:  # red
        btn4 = "i12a.jpg"
    if status.military_flag == 2:  # green
        btn4 = "i12b.jpg"
    if status.military_flag == 3:  # yellow
        btn4 = "i12c.jpg"
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "btn1": btn1,
               "btn2": btn2,
               "btn3": btn3,
               "btn4": btn4
               }
    return render(request, "btn.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def ressies(request):
    status = UserStatus.objects.get(id=request.user.id)
    context = {"status": status,
                "twostatus": twostatus,
               "round": RoundStatus.objects.filter().first,
               }
    return render(request, "ressies.html", context)

@login_required
def portal(request, *args):
    error=None
    msg=''
    if args:
        msg = args[0]
    status = UserStatus.objects.get(user=request.user)
    status2 = TwoStatus.objects.get(user=request.user)
    
    if request.method == 'POST':
        
        if 'one' in request.POST:
            status.galsel = 1
            status.save()
            status2.galsel = 1
            status2.save()
            return redirect(choose_empire_race)
        
        if 'onemsg' in request.POST:
            status.galsel = 1
            status.save()
            status2.galsel = 1
            status2.save()
            return redirect(game_messages)

        if 'ten' in request.POST:
            status.galsel = 2
            status.save()
            status2.galsel = 2
            status2.save()
            return redirect(choose_empire)  
    
    
    races = status.Races.choices
    empires = Empire.objects.filter(numplayers__lt=players_per_empire)
    empires_have_pass = None
    if empires.count() < 1:
        error = "Sorry, the galaxy is full! Try writing to the admin on discord that he needs to enlarge the map!"
    else:
        empires_have_pass = {'Random': False}
        for emp in empires:
            if not emp.password:
                empires_have_pass[emp.number] = False
            else:
                empires_have_pass[emp.number] = True
    races2 = status2.Races.choices
    empires2 = Empires.objects.filter(numplayers__lt=1)
    empires_have_pass2 = None
    if empires2.count() < 1:
        error = "Sorry, the galaxy is full! Try writing to the admin on discord that he needs to enlarge the map!"
    else:
        empires_have_pass2 = {'Random': False}
        for emp in empires2:
            if not emp.password:
                empires_have_pass2[emp.number] = False
            else:
                empires_have_pass2[emp.number] = True
    
    roun1 = RoundStatus.objects.filter().first()
    gettim = roun1.round_start
    fortime = 0
    if gettim != None:
        fortime = gettim.strftime("%B %d, %y, %H:%M:%S")
    
    roun2 = StatusRound.objects.filter().first()
    gettime = roun2.round_start
    formtime = 0
    if gettime != None:
        formtime = gettime.strftime("%B %d, %y, %H:%M:%S")
    context = {"races": races,
               "races2": races2,
               "empires": empires_have_pass,
               "empires2": empires_have_pass2,
               'empires_json': json.dumps(empires_have_pass),
               'empires_json2': json.dumps(empires_have_pass2),
               'error': error,
               'msg': msg,
               "status": status,
                "round": RoundStatus.objects.filter().first(),
                "status2": status2,
                "round2": StatusRound.objects.filter().first(),
                "formtime": formtime,
                "fortime": fortime}
    
    return render(request, "portal.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def scouting(request):
    status = get_object_or_404(UserStatus, user=request.user)
    scouted = Scouting.objects.distinct('planet').filter(empire=status.empire)
    scouted_list = Scouting.objects.filter(empire=status.empire, scout__gte=1.0).values_list('planet_id', flat=True)
    order_by = request.GET.get('order_by', 'planet')
    if order_by == 'planet':
        scouted = Scouting.objects.select_related('planet').filter(empire=status.empire). \
            order_by('planet__x', 'planet__y', 'planet__i').distinct()

    elif order_by == 'size':
        scouted = Scouting.objects.filter(empire=status.empire,scout__gte=0.5).select_related('planet').order_by('planet__size').distinct().reverse()
    elif order_by == 'artefact':
        scouted = Scouting.objects.select_related('planet').filter(empire=status.empire, scout__gte=1.0). \
            order_by('planet__' + order_by).distinct()
    else:
        scouted = Scouting.objects.select_related('planet').filter(empire=status.empire, scout__gte=1.0). \
            order_by('planet__' + order_by).distinct().reverse()
    
    if order_by == 'unexplored':
        scouted = Scouting.objects.select_related('planet').filter(empire=status.empire). \
            order_by('-planet__owner')
    if order_by == 'user':
        scouted = Scouting.objects.select_related('planet').filter(empire=status.empire).order_by('planet__owner')
    
    main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
    msg = ""
    
    users = UserStatus.objects.all()
    
    if 'exp_scouting' in request.POST:
        planet = request.POST.getlist('exp_planets')
        msg = "Results:"
        for p in planet: 
            p = Planet.objects.get(id=p)
            if main_fleet.exploration == 0:
                msg += "\nYou do not have any Exploration Ships left!"
            elif status.fleet_readiness < 0:
                msg += "\nYour forces are to tired to send an Exploration Ship!"
            else:
                portal_planets = Planet.objects.filter(owner=status.user, portal=True)
                if not portal_planets:
                    msg += "\nYou need at least one portal to send the fleet from!"
                best_portal_planet = find_nearest_portal(p.x, p.y, portal_planets, status)
                min_dist = np.sqrt((best_portal_planet.x - p.x) ** 2 + (best_portal_planet.y - p.y) ** 2)
                speed = travel_speed(status)
                fleet_time = max(0,int(np.floor(min_dist / speed)))
                fleet_id = Fleet.objects.create(owner=status.user,
                     command_order=10,
                     target_planet=p,
                     x=p.x,
                     y=p.y,
                     i=p.i,
                     ticks_remaining=fleet_time,
                     current_position_x=best_portal_planet.x,
                     current_position_y=best_portal_planet.y,
                     exploration=1)
                msg += "\nExploration ship sent to " + str(p.x) + "," + str(p.y) + ":" + str(p.i)
                main_fleet.exploration -= 1
                main_fleet.save()
                exploration_cost = calc_exploration_cost(status)
                status.fleet_readiness -= exploration_cost
                status.save()
        fleets_buffer = Fleet.objects.filter(main_fleet=False, ticks_remaining__lt=1, command_order=10, owner=status.user)
        explore_planets(fleets_buffer)
    
    if 'landexp' in request.POST:
        planet = request.POST.getlist('hov_planets')
        msg = "Landed Hovers!"
        for p in planet: 
            p = Planet.objects.get(id=p)
            fleets_buffer = Fleet.objects.filter(main_fleet=False, exploration=1, ticks_remaining__lt=1, owner=status.user, target_planet=p)
            explore_planets(fleets_buffer)
    
    if 'sense_check' in request.POST:    
        sense = Sensing.objects.filter(empire_id=status.empire.id, scout__gte=3).values_list('system_id', flat=True)
        artis = Artefacts.objects.filter(on_planet__isnull=False)
        user = User.objects.get(id=status.id)
        for a in artis:
            p = a.on_planet
            system = System.objects.get(x=p.x, y=p.y)
            if system.id in sense:
                try:
                    scout = Scouting.objects.get(empire=status.empire, planet=p)
                    scout.scout = 1.0
                    scout.save()
                except:
                    Scouting.objects.create(user=user, planet=p, scout=1.0)
    
    expo_fleets = {}
    empmembs = UserStatus.objects.filter(empire=status.empire).values_list("user", flat=True)
    expfl = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, ticks_remaining__gt=0)
    for e in expfl:
        expo_fleets[e.target_planet.id] = e.owner.id
        
    hov_fleets = {}
    hovfl = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, ticks_remaining=0)
    for e in hovfl:
        hov_fleets[e.target_planet.id] = e.owner.id
    
    if 'landall' in request.POST:
        for p in hovfl: 
            msg = "Landed Hovers!"
            fleets_buffer = Fleet.objects.filter(main_fleet=False, exploration=1, ticks_remaining__lt=1, owner=status.user, target_planet=p.target_planet)
            explore_planets(fleets_buffer)
        if msg == '':
            msg = "No Exploration Ships Hovering!"
        request.session['msg'] = msg
        return redirect(request.META['HTTP_REFERER'])
    
    arts = Artefacts.objects.all().exclude(on_planet=None).values_list('on_planet_id', flat=True)
    known_arts = Artefacts.objects.filter(on_planet_id__in=scouted_list).count()
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Planatery Scouting",
               "scouted": scouted,
               "planets": planets,
               "msg": msg,
               "expo_fleets": expo_fleets,
               "hov_fleets": hov_fleets,
               "sql": scouted.query,
               "arts": arts,
               "arts_count": len(arts),
               "known_arts": known_arts
               }
    return render(request, "scouting.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def battle(request, fleet_id):
    status = get_object_or_404(UserStatus, user=request.user)
    fleet = get_object_or_404(Fleet, pk=fleet_id)
    attacked_planet = Planet.objects.get(x=fleet.x, y=fleet.y, i=fleet.i)
    roundstatus = RoundStatus.objects.filter().first()
    
    portal_xy_list = Planet.objects.filter(portal=True, owner=attacked_planet.owner.id).values_list('x', 'y')
    if Specops.objects.filter(user_to=attacked_planet.owner, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=attacked_planet.owner, name='Vortex Portal'):
            vort_por = Planet.objects.filter(id=vort.planet.id).values_list('x', 'y')
            portal_xy_list = portal_xy_list | vort_por
    
    por_cov = min(100, int(100.0 * battlePortalCalc(attacked_planet.x, attacked_planet.y, portal_xy_list, attacked_planet.owner.userstatus.research_percent_portals, attacked_planet.owner.userstatus)))
    
    if attacked_planet.home_planet:
        if attacked_planet.owner.userstatus.empire_role == "I" and attacked_planet.owner.userstatus.num_planets == 1:
            emp = attacked_planet.owner.userstatus.empire
            emp.numplayers -= 1
            emp.save()
            Construction.objects.filter(user=attacked_planet.owner).delete()
            Fleet.objects.filter(owner=attacked_planet.owner).delete()
            Fleet.objects.create(owner=attacked_planet.owner, main_fleet=True)
            UnitConstruction.objects.filter(user=attacked_planet.owner).delete()
            scouts = Scouting.objects.filter(user=attacked_planet.owner)
            for s in scouts:
                s.user = status.user
                s.save()
            nrg = attacked_planet.owner.userstatus.energy
            mins = attacked_planet.owner.userstatus.minerals
            crys = attacked_planet.owner.userstatus.crystals
            ect = attacked_planet.owner.userstatus.ectrolium
            status.energy += nrg
            status.minerals += mins
            status.crystals += crys
            status.ectrolium += ect
            status.save()
            attacked_planet.owner.userstatus.empire = None
            attacked_planet.owner.userstatus.energy = '120000'
            attacked_planet.owner.userstatus.minerals = '10000'
            attacked_planet.owner.userstatus.crystals = '5000'
            attacked_planet.owner.userstatus.ectrolium = '5000'
            attacked_planet.owner.userstatus.user_name = ""
            attacked_planet.owner.userstatus.fleet_readiness = 100
            attacked_planet.owner.userstatus.psychic_readiness = 100
            attacked_planet.owner.userstatus.agent_readiness = 100
            attacked_planet.owner.userstatus.empire_role = ''
            attacked_planet.owner.userstatus.save()
            attacked_planet.owner = None
            attacked_planet.buildings_under_construction = 0
            attacked_planet.overbuilt_percent = 0
            attacked_planet.overbuilt = 0
            attacked_planet.total_buildings = 200
            attacked_planet.save()
            return empire(request, status.empire.id)
        else:
            request.session['error'] = "You cannot attack a home planet!"
            return fleets(request)
    if attacked_planet.owner == request.user:
        request.session['error'] = "Why would you want to attack yourself?"
        messages.error(request, 'Document deleted.')
        return fleets(request)
    cdist = max(abs(status.home_planet.x-attacked_planet.x), abs(status.home_planet.y-attacked_planet.y))
    adist = 99
    if attacked_planet.owner:
        adist = max(abs(attacked_planet.owner.userstatus.home_planet.x-attacked_planet.x), abs(attacked_planet.owner.userstatus.home_planet.y-attacked_planet.y))
    if cdist > 8 and roundstatus.tick_number < 1008:
        if attacked_planet.artefact is None:
            request.session['error'] = "You cannot attack for " + str(1008 - roundstatus.tick_number) + " weeks!"
            messages.error(request, 'Document deleted.')
            return fleets(request)
    if cdist <= 8 and adist <= 8 and roundstatus.tick_number < 1008:
        request.session['error'] = "This system is safe for both parties for " + str(1008 - roundstatus.tick_number) + " weeks!"
        messages.error(request, 'Document deleted.')
        return fleets(request)
    if fleet.owner != status.user:
        return fleets(request)
    if fleet.ticks_remaining != 0:
        return fleets(request)
    battle_report = attack_planet(fleet)
    
    display_fleet = {}
    display_fleet_inner = {}
    for unit in unit_info["unit_list"]:
        if unit not in ['wizard', 'agent', 'ghost', 'exploration']:
            num = getattr(fleet, unit)
            if num > 0:
                print(unit, num)
                display_fleet_inner[unit_info[unit]["label"]] = num
                display_fleet[fleet] = display_fleet_inner
    
    
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Battle",
               "fleet": fleet,
               "display_fleet": display_fleet,
               "battle_report": battle_report,
               "Ironside": Artefacts.objects.get(name="Ironside Effect"),
               "por_cov": por_cov
               }
    return render(request, "battle.html", context)

@xframe_options_exempt    
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def batt(request, fleet_id):
    status = get_object_or_404(UserStatus, user=request.user)
    fleet = get_object_or_404(Fleet, pk=fleet_id)
    attacked_planet = Planet.objects.get(x=fleet.x, y=fleet.y, i=fleet.i)
    
    portal_xy_list = Planet.objects.filter(portal=True, owner=attacked_planet.owner.id).values_list('x', 'y')
    if Specops.objects.filter(user_to=attacked_planet.owner, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=attacked_planet.owner, name='Vortex Portal'):
            vort_por = Planet.objects.filter(id=vort.planet.id).values_list('x', 'y')
            portal_xy_list = portal_xy_list | vort_por
    
    por_cov = min(100, int(100.0 * battlePortalCalc(attacked_planet.x, attacked_planet.y, portal_xy_list, attacked_planet.owner.userstatus.research_percent_portals, attacked_planet.owner.userstatus)))
    
    if attacked_planet.home_planet:
        if attacked_planet.owner.userstatus.empire_role == "I" and attacked_planet.owner.userstatus.num_planets == 1:
            emp = attacked_planet.owner.userstatus.empire
            emp.numplayers -= 1
            emp.save()
            Construction.objects.filter(user=attacked_planet.owner).delete()
            Fleet.objects.filter(owner=attacked_planet.owner).delete()
            Fleet.objects.create(owner=attacked_planet.owner, main_fleet=True)
            UnitConstruction.objects.filter(user=attacked_planet.owner).delete()
            scouts = Scouting.objects.filter(user=attacked_planet.owner)
            for s in scouts:
                s.user = status.user
                s.save()
            nrg = attacked_planet.owner.userstatus.energy
            mins = attacked_planet.owner.userstatus.minerals
            crys = attacked_planet.owner.userstatus.crystals
            ect = attacked_planet.owner.userstatus.ectrolium
            status.energy += nrg
            status.minerals += mins
            status.crystals += crys
            status.ectrolium += ect
            status.save()
            attacked_planet.owner.userstatus.empire = None
            attacked_planet.owner.userstatus.energy = '120000'
            attacked_planet.owner.userstatus.minerals = '10000'
            attacked_planet.owner.userstatus.crystals = '5000'
            attacked_planet.owner.userstatus.ectrolium = '5000'
            attacked_planet.owner.userstatus.user_name = ""
            attacked_planet.owner.userstatus.fleet_readiness = 100
            attacked_planet.owner.userstatus.psychic_readiness = 100
            attacked_planet.owner.userstatus.agent_readiness = 100
            attacked_planet.owner.userstatus.empire_role = ''
            attacked_planet.owner.userstatus.save()
            attacked_planet.owner = None
            attacked_planet.buildings_under_construction = 0
            attacked_planet.overbuilt_percent = 0
            attacked_planet.overbuilt = 0
            attacked_planet.total_buildings = 200
            attacked_planet.save()
            return empire(request, status.empire.id)
        else:
            request.session['error'] = "You cannot attack a home planet!"
            return fleets(request)
    if attacked_planet.owner == request.user:
        request.session['error'] = "Why would you want to attack yourself?"
        messages.error(request, 'Document deleted.')
        return fleets(request)
    if fleet.owner != status.user:
        return fleets(request)
    if fleet.ticks_remaining != 0:
        return fleets(request)
    battle_report = attack_planet(fleet)
    
    display_fleet = {}
    display_fleet_inner = {}
    for unit in unit_info["unit_list"]:
        if unit not in ['wizard', 'agent', 'ghost', 'exploration']:
            num = getattr(fleet, unit)
            if num > 0:
                print(unit, num)
                display_fleet_inner[unit_info[unit]["label"]] = num
                display_fleet[fleet] = display_fleet_inner
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Battle",
               "fleet": fleet,
               "display_fleet": display_fleet,
               "battle_report": battle_report,
               "Ironside": Artefacts.objects.get(name="Ironside Effect"),
               "por_cov": por_cov
               }
    return render(request, "batt.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def map_settings(request):
    status = get_object_or_404(UserStatus, user=request.user)
    msg = ""
    err_msg = ""
    if request.method == 'POST':
        print(request.POST)
        if 'new_setting' in request.POST:
            nr_settings = MapSettings.objects.filter(user=request.user).count()
            if nr_settings > 19:
                err_msg = "You can have 20 settings at max!"
            else:
                if MapSettings.objects.filter(user=request.user, map_setting='SC').exists():
                    m_set = MapSettings.objects.get(user=request.user, map_setting='SC')
                    MapSettings.objects.create(user=request.user,  map_setting='SC', color_settings=m_set.color_settings)
                    m_set.map_setting = 'UE'
                    m_set.color_settings = 'G'
                    m_set.save()
                else:
                    MapSettings.objects.create(user=request.user)
                
                msg = "New setting created!"
        else:
            settings_id = request.POST.getlist("setting_object")
            color = request.POST.getlist("color")
            delete_setting2 = request.POST.getlist("delete_setting")
            delete_setting = []
            j = 0
            while j < len(delete_setting2):
                if j < len(delete_setting2) - 1 and delete_setting2[j] == "0":
                    if delete_setting2[j + 1] == "1":
                        delete_setting.append(1)
                        j += 2
                    else:
                        delete_setting.append(0)
                        j += 1
                else:
                    delete_setting.append(0)
                    j += 1
            print("delete_setting", delete_setting)

            map_settings = request.POST.getlist("map_settings")
            details = request.POST.getlist("details")
            sense_count = 0
            for i in range(0, len(settings_id)):
                if map_settings[i] == 'PF':
                    if not details[i]:
                        err_msg = "You have to specify faction id or name for setting # " + str(i) + " !"
                        break

                    faction_setting, err_msg = get_userstatus_from_id_or_name(details[i])
                    if faction_setting == None:
                        break
                elif map_settings[i] == 'SS':
                    if sense_count > 0:
                        err_msg = "You can only have 1 Sensed Systems setting!"
                        break
                elif map_settings[i] == 'PE':
                    if not details[i]:
                        err_msg = "You have to specify empire id or name for setting # " + str(i) + "!"
                        break
                    try:
                        if Empire.objects.filter(number=details[i]).first() is None:
                            err_msg = "The empire id " + str(details[i]) + " doesn't exist for setting # " + str(
                                i) + "!"
                            break
                        else:
                            empire_setting = Empire.objects.filter(number=details[i]).first()
                    except:
                        if Empire.objects.filter(name=details[i]).first() is None:
                            err_msg = "The empire name " + str(details[i]) + " doesn't exist for setting # " + str(
                                i) + "!"
                            break
                        else:
                            empire_setting = Empire.objects.filter(name=details[i]).first()
                setting = MapSettings.objects.get(id=settings_id[i])
                if delete_setting[i] == 1:
                    setting.delete()
                    msg = "Settings updated!"
                else:
                    setting.color_settings = color[i]
                    setting.map_setting = map_settings[i]

                    if map_settings[i] == 'PF':
                        setting.faction = faction_setting
                        setting.empire = None
                    elif map_settings[i] == 'PE' and details[i]:
                        setting.empire = empire_setting
                        setting.faction = None
                    else:
                        setting.empire = None
                        setting.faction = None
                    setting.save()
                    msg = "Settings updated!"
    
    if request.method == 'POST':
        print(request.POST)
        if 'add_user' in request.POST:
            user1 = UserStatus.objects.get(id=request.POST.get('add_user', 'value'))
            if MapSettings.objects.filter(user=request.user, map_setting='SC').exists():
                m_set = MapSettings.objects.get(user=request.user, map_setting='SC')
                MapSettings.objects.create(user=request.user,  map_setting='SC', color_settings=m_set.color_settings)
                m_set.map_setting = 'PF'
                m_set.faction = user1
                m_set.color_settings = 'R'
                m_set.save()
            else:
                MapSettings.objects.create(user=request.user, faction=user1, map_setting='PF', color_settings='R')
            
            msg = user1.user_name + " added to Map Settings!"
    
    map_gen_settings = MapSettings.objects.filter(user=request.user).order_by('id')
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Map Settings",
               "map_settings": map_gen_settings,
               "msg": msg,
               "err_msg": err_msg
               }
    return render(request, "map_settings.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def famnews(request):
    status = get_object_or_404(UserStatus, user=request.user)
    current_tick_number = RoundStatus.objects.get().tick_number
    empire_news = News.objects.filter(empire1=status.empire,
                                      is_empire_news=True,
                                      tick_number__gte=current_tick_number - news_show). \
        order_by('-date_and_time')

    current_empire = status.empire
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Empire News",
               "current_empire": current_empire,
               "news": empire_news}
    return render(request, "empire_news.html", context)


@login_required
@user_passes_test(reverse_race_check, login_url="/headquarters")
def choose_empire_race(request):
    status = get_object_or_404(UserStatus, user=request.user)
    error = None
    if request.POST and 'faction' in request.POST and 'chose_race' in request.POST and 'chose_emp' in request.POST:
        if request.POST['faction'] == "":
            error = "Faction name is required!"
        elif UserStatus.objects.filter(user_name=request.POST['faction']).count() > 0:
            error = "This faction name is already taken!"
        elif request.POST['faction'].endswith(" ") or request.POST['faction'].startswith(" "):
            error = "Faction names cannot start or end with a space!"
        else:
            if request.POST['chose_emp'] == 'Random':
                empires = Empire.objects.filter(numplayers__lt=players_per_empire, numplayers__gt=0, password='').first()
                if empires:
                    empire1 = empires
                else:
                    empires = Empire.objects.filter(numplayers__lt=players_per_empire, password='').first()
                    empire1 = empires
            else:
                empire1 = Empire.objects.get(number=int(request.POST['chose_emp']))
                if empire1.password == request.POST['fampass']:
                    empire1 = empire1
                else:    
                    error = "Wrong pass entered!"
                    empire1 = None

            if empire1 is not None:
                empire1.numplayers += 1
                empire1.planets += 1
                empire1.networth += 1250
                empire1.save()
                status.user_name = request.POST['faction']
                status.race = request.POST['chose_race']
                status.empire = empire1
                status.empire_role = ''
                status.construction_flag = 0
                status.economy_flag = 0
                status.military_flag = 0
                status.galsel = 1
                status.save()
                for p in Planet.objects.filter(x=empire1.x, y=empire1.y):
                    if p.owner is None:
                        give_first_planet(request.user, status, p)
                        give_first_fleet(Fleet.objects.get(owner=request.user, main_fleet=True))
                        break
                
                return redirect(choose_empire_race)
    
    
    
    races = status.Races.choices
    empires = Empire.objects.filter(numplayers__lt=players_per_empire)
    empires_have_pass = None
    if empires.count() < 1:
        error = "Sorry, the galaxy is full! Try writing to the admin on discord that he needs to enlarge the map!"
    else:
        empires_have_pass = {'Random': False}
        for emp in empires:
            if not emp.password:
                empires_have_pass[emp.number] = False
            else:
                empires_have_pass[emp.number] = True
    context = {"races": races,
               "empires": empires_have_pass,
               'empires_json': json.dumps(empires_have_pass),
               'error': error}
    return render(request, "choose_empire_race.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def council(request):
    status = get_object_or_404(UserStatus, user=request.user)

    msg = ""
    refund = [0, 0, 0, 0]
    game_tick = RoundStatus.objects.filter().first()
    if game_tick.is_running == False:
        rfund = 1
    else:
        rfund = 2
    
    if 'cancel_unit' in request.POST:
        cancelled_units = request.POST.getlist('cancel_unit')
        for cu in cancelled_units:
            cf = UnitConstruction.objects.get(id=cu)
            refund[0] += int(cf.energy_cost / rfund)
            refund[1] += int(cf.mineral_cost / rfund)
            refund[2] += int(cf.crystal_cost / rfund)
            refund[3] += int(cf.ectrolium_cost / rfund)
            cf.delete()
        msg += "You were refunded with: " + str(refund[0]) + " energy, " + str(refund[1]) + " minerals, " + \
               str(refund[2]) + " crystals, " + str(refund[3]) + " ectrolium! "

    if 'cancel_build' in request.POST:
        cancelled_buildings = request.POST.getlist('cancel_build')
        for cb in cancelled_buildings:
            cf = Construction.objects.get(id=cb)
            refund[0] += int(cf.energy_cost / rfund)
            refund[1] += int(cf.mineral_cost / rfund)
            refund[2] += int(cf.crystal_cost / rfund)
            refund[3] += int(cf.ectrolium_cost / rfund)
            cf.planet.buildings_under_construction -= cf.n
            if cf.building_type == "PL":
                cf.planet.portal_under_construction = False
            cf.planet.save()
            cf.delete()
        msg += "You were refunded with: " + str(refund[0]) + " energy, " + str(refund[1]) + " minerals, " + \
               str(refund[2]) + " crystals, " + str(refund[3]) + " ectrolium! "

    status.energy += refund[0]
    status.minerals += refund[1]
    status.crystals += refund[2]
    status.ectrolium += refund[3]
    status.save()

    main_fleet_list = []
    main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
    unit_total = 0
    for unit in unit_info["unit_list"]:
        num = getattr(main_fleet, unit)
        if num:
            main_fleet_list.append({"name": unit_info[unit]["label"], "value": num})
            unit_total += num

    constructions = Construction.objects.filter(user=request.user)
    built_fleet = UnitConstruction.objects.filter(user=request.user)

    construction_sum_filter = Construction.objects.filter(user=request.user). \
        values("building_type").annotate(buildings_sum=Sum("n"))
    fleets_sum_filter = UnitConstruction.objects.filter(user=request.user). \
        values("unit_type").annotate(units_sum=Sum("n"))
    print("fleets_sum_filter", fleets_sum_filter)

    fleets_sum = {}
    for unit_query in fleets_sum_filter:
        unit = unit_query['unit_type']
        num = unit_query['units_sum']
        fleets_sum[unit_info[unit]["label"]] = num

    construction_sum = {}
    for build_query in construction_sum_filter:
        building = build_query['building_type']
        num = build_query['buildings_sum']
        construction_sum[building_labels[building]] = num

    # fleets_sum = UnitConstruction.objects.filter(user=request.user).aggregate(Sum('unit_type'))
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "constructions": constructions,
               "main_fleet": main_fleet_list,
               "unit_total": unit_total,
               "built_fleet": built_fleet,
               "page_title": "Council",
               "construction_sum": construction_sum,
               "fleets_sum": fleets_sum,
               "msg": msg}
    return render(request, "council.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")    
def map(request, *args):
    start_t = time.time()

    tuser = ''
    show_s = None
    show_t = 'Red'
    show_p = None
    show_arts = None
    show_c = None
    if args:
        if args[0] == "portmap":
            show_p = True
        elif args[0] == "artmap":
            show_arts = True
        elif args[0] == "core":
            show_c = True
        elif UserStatus.objects.filter(id=args[0]):
            tuser = UserStatus.objects.get(id=args[0])
        elif System.objects.filter(id=args[0]):
            show_s = System.objects.get(id=args[0])

    status = get_object_or_404(UserStatus, user=request.user)
    systems = System.objects.all().order_by('x', 'y')
    mapgen = {}
    settings = MapSettings.objects.filter(user=status.id)
    maxX=0
    maxY=0
    minX=0
    minY=0
    sensed = Sensing.objects.filter(empire=status.empire, scout__gte=1.0).values_list("system_id", flat=True)
    for s in systems:
        sense = ''
        if s.id in sensed:
            ssettings = MapSettings.objects.filter(user=status.id, map_setting='SS')
            if ssettings:
                ssettings = MapSettings.objects.get(user=status.id, map_setting='SS')
                sense = ssettings.get_color_settings_display
        if s.home == True:
            mapgen[s.x*10000+s.y]={"id" : s.id, "color" : "Grey", "color2" : "None", "color3" : "None", "color4" : "None", "gradient": "", "x":s.x,"y":s.y, "imgarti" : "", "scout": "", "portal": "", "home": "/static/home_syst.png", "sense":sense, "show": "", "cover":"", "core": ""}
        else:
            mapgen[s.x*10000+s.y]={"id" : s.id, "color" : "Grey", "color2" : "None", "color3" : "None", "color4" : "None", "gradient": "", "x":s.x,"y":s.y, "imgarti" : "", "scout": "", "portal": "", "home": "", "sense":sense, "show": "", "cover":"", "core": ""}
        if s.x>maxX:
            maxX=s.x
        if s.y>maxY:
            maxY=s.y
        if s.x>minX:
            minX=s.x
        if s.y>minY:
            minY=s.y
        cdist = max(abs(status.home_planet.x-s.x), abs(status.home_planet.y-s.y))
        if show_c == True and cdist <= 8:
            yp_setting = MapSettings.objects.filter(user=status.id, map_setting="YP")
            if yp_setting:
                yp_setting = MapSettings.objects.get(user=status.id, map_setting="YP")
                colour = yp_setting.get_color_settings_display
            else:
                colour = "blue"
            mapgen[s.x*10000+s.y]['core']= colour
            
    if show_s != None:
        mapgen[show_s.x*10000+show_s.y]['show']= "gold"
    
    planets = Planet.objects.order_by('x','y','i')
    scouted_planets = Scouting.objects.filter(empire=status.empire, scout__gte=1.0).values_list("planet_id", flat=True)
    
    tot_p = len(planets)
    tot_c = 0
    
    if tuser != '':    
        for setting in settings:
            if setting.map_setting == "PF":
                if setting.faction.id == tuser.id:
                    show_t = setting.get_color_settings_display
    
    grad = 0
    count = 0
    ownercount = 0
    pcount = 0
    unexcount = 0
    porcount = 0
    factcount = 0
    yr_emp = 0
    o_emp = 0
    scout_color =""
    prevx=""
    prevy=""
    for p in planets:
        tot_c += 1
        key=p.x*10000+p.y
        if p.x != prevx or p.y != prevy:
            if count==pcount and count!=0:
                print(str(prevx)+","+str(prevy)+" fully scanned:"+str(pcount))
                mapgen[prevx*10000+prevy]["scout"]=scout_color
                
            count = 0
            ownercount = 0
            pcount = 0
            unexcount = 0
            porcount = 0
            factcount = 0
            yr_emp = 0
            o_emp = 0
        prevx=p.x
        prevy=p.y
        count+=1
        mapgen[prevx*10000+prevy]["gradient"]="gradient"+str(grad)
        grad+=1
        for setting in settings:
            color = setting.get_color_settings_display
            if setting.map_setting == "UE" and unexcount == 0:
                if p.owner == None:
                    unexcount += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
        
            if p.owner == status.user:
                if show_p != None:
                    por_cov = p.protection
                    if por_cov >= 70:
                        mapgen[p.x*10000+p.y]["show"] = "Green"
                    elif por_cov >= 40:
                        mapgen[p.x*10000+p.y]["show"] = "Yellow"
                    else:
                        mapgen[p.x*10000+p.y]["show"] = "Red"
                    mapgen[p.x*10000+p.y]["cover"] = p.protection
                if setting.map_setting == "YP" and ownercount == 0:
                    ownercount += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                       
            if setting.map_setting == "YE" and yr_emp == 0:
                
                if p.owner != None and p.owner.userstatus.empire == status.empire:
                    yr_emp += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                        
            if setting.map_setting == "PE" and o_emp == 0:
                
                if p.owner != None and p.owner.userstatus.empire.id == setting.empire.id:
                    o_emp += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
        
            if setting.map_setting == "YR":
                if p.owner == status.user and p.portal == True:
                    mapgen[p.x*10000+p.y]["portal"]=color
                elif p.owner == status.user and p.portal_under_construction == True:
                    mapgen[p.x*10000+p.y]["portal"]="con"
                
            if setting.map_setting == "PF" and factcount == 0:
                if p.owner != None and p.owner.id == setting.faction.id:
                    factcount += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
            
            if tuser != '':    
                if p.owner != None and p.owner.id == tuser.id:
                    mapgen[p.x*10000+p.y]["show"] = show_t
            
            if setting.map_setting == "SC":
                if p.id in scouted_planets:
                   pcount += 1
                   scout_color=color
                   
                if tot_c == tot_p:
                    c_plants = Planet.objects.filter(x=p.x, y=p.y).values_list("id", flat=True)
                    c_p_c = len(c_plants)
                    c_c = 0
                    for plnt in c_plants:
                        if plnt in scouted_planets:
                            c_c += 1
                    if c_c == c_p_c:
                        mapgen[p.x*10000+p.y]["scout"] = scout_color
                       
    narti = Artefacts.objects.get(name="The General")
    empmembs = UserStatus.objects.filter(empire=status.empire).values_list("user", flat=True)
    expfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=10)
    expfl = []
    for e in expfleets:
        esyst = System.objects.get(x=e.x, y=e.y)
        if esyst.id not in expfl:
            expfl.append(esyst.id)
    obsfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, agent__gt=0, specop="Observe Planet")
    obsfl = []
    for o in obsfleets:
        osyst = System.objects.get(x=o.x, y=o.y)
        if osyst.id not in obsfl:
            obsfl.append(osyst.id)
    
    suvfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, ghost__gt=0, specop="Survey System")
    suvfl = []
    for o in suvfleets:
        osyst = System.objects.get(x=o.x, y=o.y)
        if osyst.id not in suvfl:
            suvfl.append(osyst.id)
            
    hovfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=2)
    hovexp = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=10, ticks_remaining=0)
    hovfleets = hovfleets | hovexp
    hovfl = []
    for e in hovfleets:
        try:
            esyst = System.objects.get(x=e.x, y=e.y)
            if esyst.id not in hovfl:
                hovfl.append(esyst.id)
        except:
            pass
        
    artis = Artefacts.objects.exclude(on_planet=None)
    for art in artis:
        if status.id == 1:
            mapgen[art.on_planet.x*10000+art.on_planet.y]["imgarti"]=art.image 
            mapgen[art.on_planet.x*10000+art.on_planet.y]['show']= "gold" 
        else:
            if Scouting.objects.filter(empire=request.user.userstatus.empire,  scout__gte=1.0,  planet=art.on_planet).exists():
                mapgen[art.on_planet.x*10000+art.on_planet.y]["imgarti"]=art.image
                if show_arts == True:
                    mapgen[art.on_planet.x*10000+art.on_planet.y]["show"]="gold"
                
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "mapgen": mapgen,
               "narti": narti,
               "systems": systems,
               "maxX": maxX,
               "maxY": maxY,
               "minX": minX,
               "minY": minY,
               "expfl": expfl,
               "obsfl": obsfl,
               "hovfl": hovfl,
               "suvfl": suvfl,
               "page_title": "Map",
               "rangeX" : range(0,maxX),
               "rangeY" : range(0,maxY),}
    return render(request, "map.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def systmap(request, system_id):
    
    return map(request, system_id)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def tmap(request, player_id):
    return map(request, player_id)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def cmap(request):
    return map(request, "core")

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def pmap(request):
    return map(request, "portmap")

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def amap(request):
    return map(request, "artmap")
    
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def smap(request):
    start_t = time.time()

    status = get_object_or_404(UserStatus, user=request.user)
    systems = System.objects.all().order_by('x', 'y')
    mapgen = {}
    settings = MapSettings.objects.filter(user=status.id)
    maxX=0
    maxY=0
    minX=0
    minY=0
    sensed = Sensing.objects.filter(empire=status.empire, scout__gte=1.0).values_list("system_id", flat=True)
    for s in systems:
        sense = ''
        if s.id in sensed:
            ssettings = MapSettings.objects.filter(user=status.id, map_setting='SS')
            if ssettings:
                ssettings = MapSettings.objects.get(user=status.id, map_setting='SS')
                sense = ssettings.get_color_settings_display
        if s.home == True:
            mapgen[s.x*10000+s.y]={"id" : s.id, "color" : "Grey", "color2" : "None", "color3" : "None", "color4" : "None", "gradient": "", "x":s.x,"y":s.y, "imgarti" : "", "scout": "", "port": "", "home": "/static/home_syst.png", "sense":sense}
        else:
            mapgen[s.x*10000+s.y]={"id" : s.id, "color" : "Grey", "color2" : "None", "color3" : "None", "color4" : "None", "gradient": "", "x":s.x,"y":s.y, "imgarti" : "", "scout": "", "port": "", "home": "", "sense":sense}
        if s.x>maxX:
            maxX=s.x
        if s.y>maxY:
            maxY=s.y
        if s.x>minX:
            minX=s.x
        if s.y>minY:
            minY=s.y
    
    planets = Planet.objects.order_by('x','y','i')
    scouted_planets = Scouting.objects.filter(empire=status.empire, scout__gte=1.0).values_list("planet_id", flat=True)
      
    
    grad = 0
    count = 0
    ownercount = 0
    pcount = 0
    unexcount = 0
    porcount = 0
    yr_emp = 0
    scout_color =""
    prevx=""
    prevy=""
    empire=[]
    faction=[]
    for p in planets:
        key=p.x*10000+p.y
        if p.x != prevx or p.y != prevy:
            if count==pcount and count!=0:
                print(str(prevx)+","+str(prevy)+" fully scanned:"+str(pcount))
                mapgen[prevx*10000+prevy]["scout"]=scout_color
                
            count = 0
            ownercount = 0
            pcount = 0
            unexcount = 0
            porcount = 0
            yr_emp = 0
            empire=[]
            faction = []
        prevx=p.x
        prevy=p.y
        count+=1
        mapgen[prevx*10000+prevy]["gradient"]="gradient"+str(grad)
        grad+=1
        for setting in settings:
            color = setting.get_color_settings_display
            if setting.map_setting == "UE" and unexcount == 0:
                if p.owner == None:
                    unexcount += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
        
            if setting.map_setting == "YP" and ownercount == 0:
                if p.owner == status.user:
                    ownercount += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                       
            if setting.map_setting == "YE" and yr_emp == 0:
                
                if p.owner != None and p.owner.userstatus.empire == status.empire:
                    yr_emp += 1
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                        
            if setting.map_setting == "PE":
                
                if p.owner != None and p.owner.userstatus.empire == setting.empire and p.owner.userstatus.empire.id not in empire:
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                    empire.append(p.owner.userstatus.empire.id)
        
            if setting.map_setting == "YR" and porcount == 0:
                if p.owner == status.user and p.portal == True:
                    porcount += 1
                    mapgen[p.x*10000+p.y]["portal"]=color
                
            if setting.map_setting == "PF":
                if p.owner != None and p.owner.id == setting.faction.id and p.owner.id not in faction:
                    if mapgen[p.x*10000+p.y]["color"]== "Grey":
                        mapgen[p.x*10000+p.y]["color"]=color
                    elif mapgen[p.x*10000+p.y]["color2"]== "None":
                        mapgen[p.x*10000+p.y]["color2"]=color
                    elif mapgen[p.x*10000+p.y]["color3"]== "None":
                        mapgen[p.x*10000+p.y]["color3"]=color
                    else:
                        mapgen[p.x*10000+p.y]["color4"]=color
                    faction.append(p.owner.id)
        
            if setting.map_setting == "SC":
                if p.id in scouted_planets:
                   pcount += 1
                   scout_color=color
       
        
        
    artis = Artefacts.objects.exclude(on_planet=None)
    narti = Artefacts.objects.get(name="The General")
    for art in artis:
        if status.id == 1:
            mapgen[art.on_planet.x*10000+art.on_planet.y]["imgarti"]=art.image  
        else:
            if Scouting.objects.filter(empire=status.empire,  scout__gte=1.0,  planet=art.on_planet).exists():
                mapgen[art.on_planet.x*10000+art.on_planet.y]["imgarti"]=art.image 
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "mapgen": mapgen,
               "narti": narti,
               "systems": systems,
               "maxX": maxX,
               "maxY": maxY,
               "minX": minX,
               "minY": minY,
               "scouted_planets": scouted_planets,
               "page_title": "Full Map",
               "rangeX" : range(0,maxX),
               "rangeY" : range(0,maxY),}
    return render(request, "smap.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def planets(request):
    status = get_object_or_404(UserStatus, user=request.user)
    request.session['mass_build'] = None
    order_by = request.GET.get('order_by', 'planet')
    msg = ''
    print("order by-", order_by)

    # TODO, it currently does not support reversing the order by clicking it a second time
    if order_by == 'planet':
        planets = Planet.objects.filter(owner=request.user).order_by('x', 'y', 'i')
    else:
        planets = Planet.objects.filter(owner=request.user).order_by(order_by)  # directly use the keyword
    
    stationed = Fleet.objects.filter(owner=request.user, command_order=8)
    
    error = None
    if 'error' in request.session:
        error = request.session['error']
        request.session['error'] = ''
    
    currentpop = 0
    maxpop =0
    totbuilds = 0
    totsize = 0
    ob = 0
    for planet in Planet.objects.filter(owner=request.user):
        maxipop = int(planet.max_population)
        planpop = int(planet.current_population)
        buildings = int(planet.total_buildings)
        size = int(planet.size)
        totob = int(planet.overbuilt_percent)
        maxpop += maxipop
        currentpop += planpop
        totbuilds += buildings
        totsize += size
        ob += totob
    avgob = round(ob / status.num_planets)
    totpopp = currentpop / maxpop * 100
    
    planets_id = ''
    buildcount = 0
    dispbuilding = ''
    if request.method=='POST' and 'razeallbuild' in request.POST:
        planets_id = request.POST.getlist('planets_id_mass_build')
        for pid in planets_id:
            planet = Planet.objects.get(id=pid)
            if request.POST['buildingsel'] == "SC":
                dispbuilding = "Solar Collectors" 
                buildcount += planet.solar_collectors
                planet.total_buildings -= planet.solar_collectors
                planet.solar_collectors = 0
            if request.POST['buildingsel'] == "FI":
                dispbuilding = "Fission Reactor" 
                buildcount += planet.fission_reactors
                planet.total_buildings -= planet.fission_reactors
                planet.fission_reactors = 0
            if request.POST['buildingsel'] == "MP":
                dispbuilding = "Mineral Plants" 
                buildcount += planet.mineral_plants
                planet.total_buildings -= planet.mineral_plants
                planet.mineral_plants = 0
            if request.POST['buildingsel'] == "CL":
                dispbuilding = "Crystal Laboratories" 
                buildcount += planet.crystal_labs
                planet.total_buildings -= planet.crystal_labs
                planet.crystal_labs = 0
            if request.POST['buildingsel'] == "RS":
                dispbuilding = "Refinement Stations" 
                buildcount += planet.refinement_stations
                planet.total_buildings -= planet.refinement_stations
                planet.refinement_stations = 0
            if request.POST['buildingsel'] == "CI":
                dispbuilding = "Cities" 
                buildcount += planet.cities
                planet.total_buildings -= planet.cities
                planet.cities = 0
            if request.POST['buildingsel'] == "RC":
                dispbuilding = "Research Centers" 
                buildcount += planet.research_centers
                planet.total_buildings -= planet.research_centers
                planet.research_centers = 0
            if request.POST['buildingsel'] == "DS":
                dispbuilding = "Defense Satalites" 
                buildcount += planet.defense_sats
                planet.total_buildings -= planet.defense_sats
                planet.defense_sats = 0
            if request.POST['buildingsel'] == "SN":
                dispbuilding = "Shield Networks" 
                buildcount += planet.shield_networks
                planet.total_buildings -= planet.shield_networks
                planet.shield_networks = 0
            
            planet.overbuilt = calc_overbuild(planet.size, planet.total_buildings + planet.buildings_under_construction)
            planet.overbuilt_percent = (planet.overbuilt - 1.0) * 100            
            planet.save()
        
        msg += str(buildcount) + " " + str(dispbuilding) + " destroyed!"
        News.objects.create(user1=status.user,
                        user2=status.user,
                        empire1=status.empire,
                        news_type='E',
                        date_and_time=datetime.datetime.now(),
                        planet=planet,
                        extra_info=msg,
                        is_personal_news=False,
                        is_empire_news=False,
                        tick_number=RoundStatus.objects.get().tick_number)    

    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "planets": planets,
               "currentpop": currentpop,
               "maxpop": maxpop,
               "totbuilds": totbuilds,
               "totsize": totsize,
               "avgob": avgob,
               "totpopp": totpopp,
               "error": error,
               "msg": msg,
               "stationed": stationed,
               "a_arts": Planet.objects.filter(owner=request.user).exclude(artefact=None).values_list('id', flat=True),
               "a_sols": Planet.objects.filter(owner=request.user, bonus_solar__gt=0).values_list('id', flat=True),
               "a_minz": Planet.objects.filter(owner=request.user, bonus_mineral__gt=0).values_list('id', flat=True),
               "a_cryz": Planet.objects.filter(owner=request.user, bonus_crystal__gt=0).values_list('id', flat=True),
               "a_ectz": Planet.objects.filter(owner=request.user, bonus_ectrolium__gt=0).values_list('id', flat=True),
               "a_fisz": Planet.objects.filter(owner=request.user, bonus_fission__gt=0).values_list('id', flat=True),
               "a_none": Planet.objects.filter(owner=request.user, artefact=None, bonus_solar=0, bonus_mineral=0, bonus_crystal=0, bonus_ectrolium=0, bonus_fission=0).values_list('id', flat=True),
               "page_title": "Planets"}
    return render(request, "planets.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def planet(request, planet_id, *args):
    status = get_object_or_404(UserStatus, user=request.user)
    planet = get_object_or_404(Planet, pk=planet_id)
    attack_cost = None
    if planet.owner:  # if planet is owned by someone, grab that owner's status, in order to get faction and other info of owner
        planet_owner_status = UserStatus.objects.get(user=planet.owner)
        attack_cost = battleReadinessLoss(status, planet_owner_status, planet)
    else:
        planet_owner_status = None

    specops = "No"
    if Specops.objects.filter(user_to=planet.owner, name="Dark Web").exists():
        specops = "Webs"
        
    if Specops.objects.filter(planet=planet, name="Planetary Beacon").exists():
        specops = "Beacon"
    
    system = System.objects.get(x=planet.x, y=planet.y)
    system = system.id
    
    error = None
    if 'error' in request.session:
        error = request.session['error']
        request.session['error'] = ''
    
    con = []
    if planet.buildings_under_construction > 0: 
        for build in Construction.objects.filter(planet=planet):
            con.append({"number": build.n, "building": build.get_building_type_display})
    
    stationed = []
    if Fleet.objects.filter(owner=status.user, on_planet=planet, command_order=8):
        main_fleet = Fleet.objects.filter(owner=status.user, on_planet=planet, command_order=8)
        for fl in main_fleet:
            for unit in unit_info["unit_list"]:
                num = getattr(fl, unit)
                if num:
                    stationed.append({"name": unit_info[unit]["label"], "value": num})
    
    portal_planets = Planet.objects.filter(owner=status.user, portal=True)
    if portal_planets:
        portal = find_nearest_portal(planet.x, planet.y,
                                             portal_planets, status)
        min_dist = np.sqrt((portal.x - planet.x) ** 2 +
                       (portal.y - planet.y) ** 2)
        speed = travel_speed(status)
        travel_time = max(0,int(np.floor(min_dist / speed)))
    else:
        travel_time = "No Portals!"
    msg = ''
    news = News.objects.filter(planet=planet, user2=status.user, news_type='E', extra_info="1")
    exploration_cost = calc_exploration_cost(status)
    offd_to = ''
    if news:
        news = News.objects.get(planet=planet, user2=status.user, news_type='E', extra_info="1")
        offd_to = news.user1.userstatus.user_name
    
    offerp = request.POST.get("offer_planet", False)
    if offerp:
        if planet.home_planet == False:
            stat2 = request.POST.get('player', False)
            change = request.POST.get('offer', False)
            status2 = UserStatus.objects.get(id=stat2)
            if change == "1": 
                if news:
                    news.user1 = status2.user
                    news.is_read =False
                    news.save()
                else:
                    News.objects.create(user1=status2.user,
                        user2=status.user,
                        empire1=status.empire,
                        news_type='E',
                        date_and_time=datetime.datetime.now(),
                        planet=planet,
                        extra_info="1",
                        is_personal_news=True,
                        is_empire_news=True,
                        tick_number=RoundStatus.objects.get().tick_number)
                        
                msg += "Planet offered to: " + str(status2.user_name)
                status2.economy_flag == 1
            elif change == "2":                
                if news:
                    news.user2 = status2.user
                    news.delete()
                    msg += "Planet removed from offering"
        else:
            msg += "You cannot offer you home planet"
     
    main_fleet = Fleet.objects.get(owner=status.user, main_fleet=True)
    expp = request.POST.get("explore_planet", False)
    if expp:
            pid = request.POST.get('id_planet', False)
            if main_fleet.exploration > 0:
                if status.fleet_readiness >= 0:
                    setattr(main_fleet, 'exploration', getattr(main_fleet, 'exploration') - 1)

                    fleet = Fleet.objects.create(owner=request.user,
                                                 command_order=10,
                                                 x=planet.x,
                                                 y=planet.y,
                                                 i=planet.i,
                                                 ticks_remaining=travel_time,
                                                 current_position_x=portal.x,
                                                 current_position_y=portal.y,
                                                 target_planet=planet,
                                                 exploration=1)
                    status.fleet_readiness -= exploration_cost 
                    status.save()
                    main_fleet.save()
                    fleets_tmp = []
                    if travel_time == 0:
                        fleets_tmp.append(fleet)
                        explore_planets(fleets_tmp)
                        request.session['error'] = "Planet Explored!"
                        
                        return redirect(request.META['HTTP_REFERER'])

                    else:
                        msg += "Your Exploration Team will arrive in " + str(travel_time) + " weeks!"
                else:
                    msg += "Your forces are to tired to send an Exploration Ship"
            else:
                msg += "You dont have any Exploration Ships!"
    hover = request.POST.get("hover_planet", False)            
    if hover:
            pid = request.POST.get('id_planet', False)
            if main_fleet.exploration > 0:
                if status.fleet_readiness >= 0:
                    setattr(main_fleet, 'exploration', getattr(main_fleet, 'exploration') - 1)

                    fleet = Fleet.objects.create(owner=request.user,
                                                 command_order=2,
                                                 x=planet.x,
                                                 y=planet.y,
                                                 i=planet.i,
                                                 ticks_remaining=travel_time,
                                                 current_position_x=portal.x,
                                                 current_position_y=portal.y,
                                                 target_planet=planet,
                                                 exploration=1)
                    status.fleet_readiness -= exploration_cost 
                    status.save()
                    main_fleet.save()
                    if travel_time == 0:
                        msg += "Your Exploration Team has arrived!"

                    else:
                        msg += "Your Exploration Team will arrive in " + str(travel_time) + " weeks!"
                else:
                    msg += "Your forces are to tired to send an Exploration Ship"
            else:
                msg += "You dont have any Exploration Ships!"
            
    player_list = UserStatus.objects.filter(empire=status.empire)
    
    bare = "No"
    if args:
        bare = "Yes"
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "planet": planet,
               "attack_cost": attack_cost,
               "specops": specops,
               "system": system,
               "planet_owner_status": planet_owner_status,
               "page_title": "Planet " + str(planet.x) + ',' + str(planet.y) + ':' + str(planet.i),
               "con": con, 
               "exploration_cost": exploration_cost,
               "travel_time": travel_time,
               "player_list": player_list,
               "news": news,
               "msg": msg,
               "bare": bare,
               "offd_to": offd_to,
               "error": error,
               "stationed": stationed}
    
    return render(request, "planet.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def plant(request, planet_id):
    return planet(request, planet_id, "short")

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def system(request, system_id):
    return syst(request, system_id, "short")           

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def syst(request, system_id, *args):
    status = get_object_or_404(UserStatus, user=request.user)
    system = get_object_or_404(System, pk=system_id)
    planet = Planet.objects.filter(x=system.x, y=system.y)
    mapgen = {}
    title = ''
    scouted_planets = Scouting.objects.filter(empire=status.empire, scout__gte=1.0).values_list("planet_id", flat=True)
    users = UserStatus.objects.filter(empire=status.empire).values_list("user", flat=True)
    fleets = Fleet.objects.filter(owner__in=users, x=system.x, y=system.y)
    for p in planet:
        mapgen[p.id*10000]={"id" : p.id, "owner" : "", "color" : "None", "color2" : "None", "color3" : "None", "color4" : "None", "gradient": "", "x":"","y":"", "i": "", "imgp" : "", "scout": "", "port": "", "sta": ""}
    main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
    msg = ""
    if request.method == 'POST' and 'explore_all' in request.POST:
        msg = "Results:"
        for p in planet:
            if p.owner == None and p.home_planet == False:
                if main_fleet.exploration == 0:
                    msg += "\nYou do not have any Exploration Ships left!"
                elif status.fleet_readiness <= 0:
                    msg += "\nYour forces are to tired to send an Exploration Ship!"
                else:
                    portal_planets = Planet.objects.filter(owner=status.user, portal=True)
                    if not portal_planets:
                        msg += "\nYou need at least one portal to send the fleet from!"
                    best_portal_planet = find_nearest_portal(p.x, p.y, portal_planets, status)
                    min_dist = np.sqrt((best_portal_planet.x - p.x) ** 2 + (best_portal_planet.y - p.y) ** 2)
                    speed = travel_speed(status)
                    fleet_time = max(0,int(np.floor(min_dist / speed)))
                    fleet_id = Fleet.objects.create(owner=status.user,
                         command_order=10,
                         target_planet=p,
                         x=p.x,
                         y=p.y,
                         i=p.i,
                         ticks_remaining=fleet_time,
                         current_position_x=best_portal_planet.x,
                         current_position_y=best_portal_planet.y,
                         exploration=1)
                    msg += "\nExploration ship sent to " + str(p.x) + "," + str(p.y) + ":" + str(p.i)
                    main_fleet.exploration -= 1
                    main_fleet.save()
                    exploration_cost = calc_exploration_cost(status)
                    status.fleet_readiness -= exploration_cost
                    status.save()
        fleets_buffer = Fleet.objects.filter(main_fleet=False, ticks_remaining__lt=1, command_order=10)
        explore_planets(fleets_buffer)
    if request.method == 'POST' and 'observe_all' in request.POST:
        msg = "Results:"
        for p in planet:
            if p.owner == None and p.id not in scouted_planets:
                main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
                agents = int(request.POST.get('obsagents', 0)) 
                if main_fleet.agent < agents:
                    msg += "\nYou do not have enough Agents!"
                else:
                    msg += "\nAgents sent! \n" 
                    msg += send_agents_ghosts(status, int(agents), 0,
                                             p.x, p.y, p.i, "Observe Planet")
    
    if request.method == 'POST' and 'survey_syst' in request.POST:
        msg = "Results:"
        for p in planet:
            main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
            ghosts = int(request.POST.get('survghosts', 0)) 
            if main_fleet.ghost < ghosts:
                msg += "\nYou do not have enough Ghost Ships!"
            else:
                msg += "\nGhost Ships sent! \n" 
                msg += send_ghosts(status, 0, int(ghosts),
                                         p.x, p.y, p.i, "Survey System")
            break
    
    settings = MapSettings.objects.filter(user=status.id)
    
 
    grad = 0
    for p in planet:
        key=p.id*10000
        mapgen[p.id*10000]["gradient"]="gradient"+str(grad)
        grad+=1
        mapgen[p.id*10000]["i"] = p.i
        if p.owner == status.user and p.portal == True:
            mapgen[p.id*10000]["portal"] = "/static/buildings/Portal.png"
        elif p.owner == status.user and p.portal_under_construction == True:
            mapgen[p.id*10000]["portal"] = "/static/buildings/portcon.png"
        
        if p.owner == None:
            if p.home_planet == True:
                mapgen[p.id*10000]["owner"] = "Unavailable"
            else:
                mapgen[p.id*10000]["owner"] = "Unexplored"
        else:
            owner = UserStatus.objects.get(user=p.owner)
            mapgen[p.id*10000]["owner"] = owner.user_name
            
        if p.id % 10 == 1:
            mapgen[p.id*10000]["imgp"] = "/static/map/p00.png"
        if p.id % 10 == 2:
            mapgen[p.id*10000]["imgp"] = "/static/map/p11.png"
        if p.id % 10 == 3:
            mapgen[p.id*10000]["imgp"] = "/static/map/p01.png"
        if p.id % 10 == 4:
            mapgen[p.id*10000]["imgp"] = "/static/map/p10.png"
        if p.id % 10 == 5:
            mapgen[p.id*10000]["imgp"] = "/static/map/p03.png"
        if p.id % 10 == 6:
            mapgen[p.id*10000]["imgp"] = "/static/map/p04.png"
        if p.id % 10 == 7:
            mapgen[p.id*10000]["imgp"] = "/static/map/p05.png"
        if p.id % 10 == 8:
            mapgen[p.id*10000]["imgp"] = "/static/map/p06.png"
        if p.id % 10 == 9:
            mapgen[p.id*10000]["imgp"] = "/static/map/p07.png"
        if p.id % 10 == 0:
            mapgen[p.id*10000]["imgp"] = "/static/map/p08.png"
        if p.artefact != None and p.id in scouted_planets or p.artefact != None and status.id == 1:
            mapgen[p.id*10000]["imgp"] = p.artefact.image
            
        if p.i == 0:                                
            mapgen[p.id*10000]["x"] = 4
            mapgen[p.id*10000]["y"] = 50
            if p.home_planet == True:
                emp = Empire.objects.get(x=p.x, y=p.y)
                title = "Home System of " + str(emp.name_with_id) + ": " + str(system.x) + ',' + str(system.y)
            else:
                title = "System " + str(system.x) + ',' + str(system.y)
        if p.i == 1:                             
            mapgen[p.id*10000]["x"] = 19
            mapgen[p.id*10000]["y"] = 19
        if p.i == 2:                                
            mapgen[p.id*10000]["x"] = 50
            mapgen[p.id*10000]["y"] = 6
        if p.i == 3:                                 
            mapgen[p.id*10000]["x"] = 81
            mapgen[p.id*10000]["y"] = 19
        if p.i == 4:                                 
            mapgen[p.id*10000]["x"] = 96
            mapgen[p.id*10000]["y"] = 50
        if p.i == 5:                                
            mapgen[p.id*10000]["x"] = 81
            mapgen[p.id*10000]["y"] = 81
        if p.i == 6:                                 
            mapgen[p.id*10000]["x"] = 50
            mapgen[p.id*10000]["y"] = 93
        if p.i == 7:                                 
            mapgen[p.id*10000]["x"] = 19
            mapgen[p.id*10000]["y"] = 81

        for setting in settings:
            color = setting.get_color_settings_display
            if setting.map_setting == "UE":
                if p.owner == None:
                    if mapgen[p.id*10000]["color"]== "None":
                        mapgen[p.id*10000]["color"]=color
                    elif mapgen[p.id*10000]["color2"]== "None":
                        mapgen[p.id*10000]["color2"]=color
                    elif mapgen[p.id*10000]["color3"]== "None":
                        mapgen[p.id*10000]["color3"]=color
                    else:
                        mapgen[p.id*10000]["color4"]=color
        
            if setting.map_setting == "YP":
                if p.owner == status.user:
                    if mapgen[p.id*10000]["color"]== "None":
                        mapgen[p.id*10000]["color"]=color
                    elif mapgen[p.id*10000]["color2"]== "None":
                        mapgen[p.id*10000]["color2"]=color
                    elif mapgen[p.id*10000]["color3"]== "None":
                        mapgen[p.id*10000]["color3"]=color
                    else:
                        mapgen[p.id*10000]["color4"]=color
                       
            if setting.map_setting == "YE":
                
                if p.owner != None and p.owner.userstatus.empire == status.empire:
                    if mapgen[p.id*10000]["color"]== "None":
                        mapgen[p.id*10000]["color"]=color
                    elif mapgen[p.id*10000]["color2"]== "None":
                        mapgen[p.id*10000]["color2"]=color
                    elif mapgen[p.id*10000]["color3"]== "None":
                        mapgen[p.id*10000]["color3"]=color
                    else:
                        mapgen[p.id*10000]["color4"]=color
                
            if setting.map_setting == "PF":
                if p.owner != None and p.owner.id == setting.faction.id:
                    if mapgen[p.id*10000]["color"]== "None":
                        mapgen[p.id*10000]["color"]=color
                    elif mapgen[p.id*10000]["color2"]== "None":
                        mapgen[p.id*10000]["color2"]=color
                    elif mapgen[p.id*10000]["color3"]== "None":
                        mapgen[p.id*10000]["color3"]=color
                    else:
                        mapgen[p.id*10000]["color4"]=color
            
            if setting.map_setting == "PE":
                if p.owner != None:
                    owner = UserStatus.objects.get(user=p.owner)
                    if owner.empire == setting.empire:
                        if mapgen[p.id*10000]["color"]== "None":
                            mapgen[p.id*10000]["color"]=color
                        elif mapgen[p.id*10000]["color2"]== "None":
                            mapgen[p.id*10000]["color2"]=color
                        elif mapgen[p.id*10000]["color3"]== "None":
                            mapgen[p.id*10000]["color3"]=color
                        else:
                            mapgen[p.id*10000]["color4"]=color
            
            if setting.map_setting == "SC":
                if p.id in scouted_planets:
                   mapgen[p.id*10000]["scout"]=color
            
            if Fleet.objects.filter(owner=status.user, on_planet=p, command_order=8):
                mapgen[p.id*10000]["sta"] = "/static/units/forward-field.png"
    
    portal_xy_list = Planet.objects.filter(portal=True, owner=status.user.id).values_list('x', 'y')
    if Specops.objects.filter(user_to=status.user, name='Vortex Portal').exists():
        for vort in Specops.objects.filter(user_to=status.user, name='Vortex Portal'):
            vort_por = Planet.objects.filter(id=vort.planet.id).values_list('x', 'y')
            portal_xy_list = portal_xy_list | vort_por
    
    sys_cov = min(100, int(100.0 * battlePortalCalc(system.x, system.y, portal_xy_list, status.research_percent_portals, status)))
    
    portal_planets = Planet.objects.filter(owner=status.user, portal=True)
    if portal_planets:
        portal = find_nearest_portal(system.x, system.y,
                                             portal_planets, status)
        min_dist = np.sqrt((portal.x - system.x) ** 2 +
                       (portal.y - system.y) ** 2)
        speed = travel_speed(status)
        
        travel_time = max(0,int(np.floor(min_dist / speed)))
    else:
        travel_time = "No Portals!"
    
    narti = Artefacts.objects.get(name="The General")
    empmembs = UserStatus.objects.filter(empire=status.empire).values_list("user", flat=True)
    expfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=10)
    expfl = []
    for e in expfleets:
        expfl.append(e.target_planet.id)
    obsfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, agent__gt=0, specop="Observe Planet")
    obsfl = []
    for o in obsfleets:
        obsfl.append(o.target_planet.id)
    
    suvfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, ghost__gt=0, specop="Survey System")
    suvfl = ""
    for o in suvfleets:
        osyst = System.objects.get(x=o.x, y=o.y)
        if osyst == system:
            suvfl = "Yes"
            
    hovfleets = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=2)
    hovexp = Fleet.objects.filter(owner__in=empmembs, main_fleet=False, exploration=1, command_order=10, ticks_remaining=0)
    hovfleets = hovfleets | hovexp
    hovfl = []
    for e in hovfleets:
        hovfl.append(e.target_planet.id)
    
    context = {"status": status,
               "msg": msg,
               "round": RoundStatus.objects.filter().first,
               "mapgen": mapgen,
               "system": system,
               "scouted_planets": scouted_planets,
               "sys_cov": sys_cov,
               "travel_time": travel_time,
               "narti": narti,
               "expfl": expfl,
               "obsfl": obsfl,
               "suvfl": suvfl,
               "hovfl": hovfl,
               "fleets": fleets,
               "page_title": title} 
    if args:
        if args[0] == "short":
            return render(request, "system.html", context)
        else:
            return render(request, "msyst.html", context)
    else:
        return render(request, "syst.html", context)    
 
@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def msyst(request, system_id):
    return syst(request, system_id, "mobile") 
               
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def raze(request, planet_id):
    status = get_object_or_404(UserStatus, user=request.user)
    planet = get_object_or_404(Planet, pk=planet_id)

    # Make sure its owned by user
    if planet.owner != request.user:
        return HttpResponse("This is not your planet!")

    if request.method == 'POST':
        # print(request.POST)
        # List of building types, except portals
        building_list = [SolarCollectors(), FissionReactors(), MineralPlants(), CrystalLabs(), RefinementStations(),
                         Cities(), ResearchCenters(), DefenseSats(), ShieldNetworks()]
        top_msg = ''
        for building in building_list:
            num_to_raze = request.POST.get(building.short_label,
                                           None)  # number user entered to raze for this building type
            if num_to_raze == 'on':
                num_to_raze = 1
            elif num_to_raze:
                num_to_raze = int(num_to_raze)
            else:
                num_to_raze = 0
            num_on_planet = getattr(planet,
                                    building.model_name)  # This is how to access a field of a model using a string for the name of that field
            if (num_to_raze > 0) and (num_on_planet >= num_to_raze):
                setattr(planet, building.model_name, num_on_planet - num_to_raze)
                setattr(planet, 'total_buildings', getattr(planet, 'total_buildings') - num_to_raze)
                setattr(status, 'total_' + building.model_name,
                        getattr(status, 'total_' + building.model_name) - num_to_raze)
                setattr(status, 'total_buildings', getattr(status, 'total_buildings') - num_to_raze)
                top_msg += "You razed " + str(num_to_raze) + " " + building.label + "<p><p>"
            elif num_to_raze > 0:
                top_msg += "Did not have " + str(num_to_raze) + " " + building.label + " to raze<p><p>"
        # Do portal separately
        if request.POST.get("PL", None) and planet.portal:
            planet.portal = False
            top_msg += "You razed the Portal on this planet<p><p>"
        elif request.POST.get("PL", None):
            top_msg += "There is no Portal on this planet to raze<p><p>"
        # Any time we change buildings we need to update planet's overbuild factor
        pportal = 0
        if planet.portal:
            pportal = 1
            
        total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
        
        planet.overbuilt = calc_overbuild(planet.size, total_buildings + planet.buildings_under_construction)
        planet.overbuilt_percent = (planet.overbuilt - 1.0) * 100
        # Save our changes to planet and status
        planet.save()
        status.save()
    else:
        top_msg = None

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "planet": planet,
               "top_msg": top_msg,
               "page_title": "Raze Buildings on Planet " + str(planet.x) + ',' + str(planet.y) + ':' + str(planet.i)}
    return render(request, "raze.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def razeall(request, planet_id):  # TODO still need an html template for this page
    status = get_object_or_404(UserStatus, user=request.user)
    planet = get_object_or_404(Planet, pk=planet_id)
    if request.method == 'POST':
        # List of building types, except portals
        raze_all_buildings2(planet, status)
        context = {"status": status,
                   "round": RoundStatus.objects.filter().first,
                   "planet": planet,
                   "planet_owner_status": status,
                   "page_title": "Planet " + str(planet.x) + ',' + str(planet.y) + ':' + str(planet.i),
                   }
        return render(request, "planet.html", context)
    else:
        return HttpResponse("CAN ONLY GET HERE BY CLICKING RAZE ALL BUTTON")

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def mrazeall(request, planet_id):  # TODO still need an html template for this page
    status = get_object_or_404(UserStatus, user=request.user)
    planet = get_object_or_404(Planet, pk=planet_id)
    if request.method == 'POST':
        # List of building types, except portals
        raze_all_buildings2(planet, status)
        context = {"status": status,
                   "round": RoundStatus.objects.filter().first,
                   "planet": planet,
                   "planet_owner_status": status,
                   "page_title": "Planet " + str(planet.x) + ',' + str(planet.y) + ':' + str(planet.i),
                   }
        return render(request, "plant.html", context)
    else:
        return HttpResponse("CAN ONLY GET HERE BY CLICKING RAZE ALL BUTTON")

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def build(request, planet_id):
    # This entire view + template is reproducing iohtmlFunc_build()

    status = get_object_or_404(UserStatus, user=request.user)
    planet = get_object_or_404(Planet, pk=planet_id)
    msg = ""
    building_list = [SolarCollectors(), FissionReactors(), MineralPlants(), CrystalLabs(), RefinementStations(),
                     Cities(), ResearchCenters(), DefenseSats(), ShieldNetworks(), Portal()]

    list_costs = {"Energy": 0, "Minerals": 0, "Crystals": 0, "Ectrolium": 0}
    list_type = {}
    
    building_types = []
    
    for building in building_list:
        list_type[building.label]={"number":0}
        building_types.append(building.label)

    building_helper = building_info_list

    if request.method == 'POST':
        if planet.owner != request.user:
            return "This is not your planet!"
        
        for building in building_list:
            building_list_dict = {}
            num = None
            num = request.POST.get(str(building.building_index), None)
            building_list_dict[building] = request.POST.get(str(building.building_index), None)

            if num:
                list_building, list_cost = build_on_planet(status, planet, building_list_dict)
                for k, v in list_cost.items():
                    list_costs[k] += v
                for k, v in list_building.items():
                    for a, b in v.items():
                        if k in building_types:
                            list_type[k][a] += b
                        else:
                            msg += str(b)
                        
        
        total = 0
        for k, v in list_costs.items():
            total += int(v)
            
        if total > 0:
            msg += "\n\nTotals: \n"
            
            for k, v in list_type.items():
                for a, b in v.items():
                    if int(b) > 0:
                        msg += str(b) + " " + str(k) + "\n"

            for k, v in list_costs.items():
                    msg += str(v) + " " + str(k) + "\n"

    # Build up list of dicts, designed to be used easily by template
    costs = []
    for building in building_list:
        # Below doesn't include overbuild, it gets added below
        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == status.empire:
            tech = status.research_percent_tech * 2
        else:
            tech = status.research_percent_tech
        artesn = Artefacts.objects.get(name="Shield Network")
        if artesn.empire_holding == status.empire:
            if building.building_index == 8:
                tech = 140
            
        if building.building_index == 9:
            cost_list, penalty = building.calc_cost(1, status.research_percent_portals, tech,
                                                status)
        else:
            cost_list, penalty = building.calc_cost(1, status.research_percent_construction, tech,
                                                status)
        # Add resource names to the cost_list, for the sake of the for loop in the view
        if cost_list:  # Remember that cost_list will be None if the tech is too low
            cost_list_labeled = []
            cost_list_calc = []
            for i in range(5):  # 4 types of resources plus time
                if i < 4:
                    if building == building_list[9]:
                        cost_list_labeled.append({"value": int(np.ceil(cost_list[i])),
                                              "name": resource_names[i]})
                        cost_list_calc.append({"value": int(np.ceil(cost_list[i])),
                                              "name": resource_names[i]})
                        
                    else:
                        cost_list_labeled.append({"value": int(np.ceil(cost_list[i] * max(1, planet.overbuilt))),
                                              "name": resource_names[i]})
                        cost_list_calc.append({"value": int(np.ceil(cost_list[i])),
                                              "name": resource_names[i]})
                else:
                    cost_list_labeled.append({"value": int(np.ceil(cost_list[i])),
                                              "name": resource_names[i]})


        else:
            cost_list_labeled = None  # Tech was too low

        cost = {"cost": cost_list_labeled,
                "cost_calc": cost_list_calc,
                "penalty": penalty,
                "owned": getattr(status, 'total_' + building.model_name),
                "name": building.label}
        costs.append(cost)

    # Build context
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "planet": planet,
               "costs": costs,
               "portal": planet.portal,
               "portal_under_construction": planet.portal_under_construction,
               "msg": msg,
               "building_helper": building_helper,
               "page_title": "Build on Planet " + str(planet.x) + ',' + str(planet.y) + ':' + str(planet.i)}
    return render(request, "build.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def mass_build(request):
    status = get_object_or_404(UserStatus, user=request.user)
    if request.method != 'POST':
        return planets(request)
    building_list = [SolarCollectors(), FissionReactors(), MineralPlants(), CrystalLabs(), RefinementStations(),
                     Cities(), ResearchCenters(), DefenseSats(), ShieldNetworks(), Portal()]

    building_helper = building_info_list

    b_planets = []

    msg = ''
    building_list_dict = {}
    num_planets = 0
    total_ob = 0

    list_costs = {"Energy": 0, "Minerals": 0, "Crystals": 0, "Ectrolium": 0}
    list_type = {}
    
    building_types = []
    
    for building in building_list:
        list_type[building.label]={"number":0}
        building_types.append(building.label)
    
    if 'planets_id_mass_build' in request.POST:
        request.session['mass_build'] = request.POST.getlist('planets_id_mass_build')
        planets_id = request.session['mass_build']
        for pid in planets_id:
            planet = Planet.objects.get(id=pid)
            b_planets.append(planet)
            if planet.overbuilt_percent <= 0:
                num_planets += 1
                total_ob += planet.overbuilt
    elif 'mass_build' in request.session and request.session['mass_build'] is not None:            
        obchecked = request.POST.get("obcheck")
        if obchecked:    
            planets_id = request.session['mass_build']
            try:
                sc = int(request.POST.get('0'))
            except ValueError:
                sc = 0
            try:
                fi = int(request.POST.get('1', 0))
            except ValueError:
                fi = 0
            try:
                mp = int(request.POST.get('2', 0))
            except ValueError:
                mp = 0
            try:
                cl = int(request.POST.get('3', 0))
            except ValueError:
                cl = 0
            try:
                rf = int(request.POST.get('4', 0))
            except ValueError:
                rf = 0
            try:
                ci = int(request.POST.get('5', 0))
            except ValueError:
                ci = 0
            try:
                rc = int(request.POST.get('6', 0))
            except ValueError:
                rc = 0
            try:
                ds = int(request.POST.get('7', 0))
            except ValueError:
                ds = 0
            try:
                sn = int(request.POST.get('8', 0))
            except ValueError:
                sn = 0
            po = request.POST.get('9', None)       
            for pid in planets_id:
                building_list_dict = {}
                planet = Planet.objects.get(id=pid)
                b_planets.append(planet)
                obmax = int(request.POST.get('oblimit'))
                maxob = obmax / 100 +1
                maxob2 = np.sqrt(maxob)
                pportal = 0
                if planet.portal:
                    pportal = 1
                    
                total_buildings = planet.total_buildings - (planet.defense_sats + planet.shield_networks + pportal)
                totalbuild = maxob2 * planet.size
                totalbuild -= total_buildings
                totalbuild -= planet.buildings_under_construction
                if planet.overbuilt_percent <= obmax:
                    if sc >= totalbuild:
                        building_list_dict[SolarCollectors()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[SolarCollectors()] = sc
                        totalbuild -= sc
                    if fi >= totalbuild:
                        building_list_dict[FissionReactors()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[FissionReactors()] = fi
                        totalbuild -= fi
                    if mp >= totalbuild:
                        building_list_dict[MineralPlants()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[MineralPlants()] = mp
                        totalbuild -= mp
                    if cl >= totalbuild:
                        building_list_dict[CrystalLabs()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[CrystalLabs()] = cl
                        totalbuild -= cl
                    if rf >= totalbuild:
                        building_list_dict[RefinementStations()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[RefinementStations()] = rf
                        totalbuild -= rf
                    if ci >= totalbuild:
                        building_list_dict[Cities()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[Cities()] = ci
                        totalbuild -= ci
                    if rc >= totalbuild:
                        building_list_dict[ResearchCenters()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[ ResearchCenters()] = rc
                        totalbuild -= rc
                    if ds >= totalbuild:
                        building_list_dict[DefenseSats()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[DefenseSats()] = ds
                        totalbuild -= ds
                    if sn >= totalbuild:
                        building_list_dict[ShieldNetworks()] = totalbuild
                        totalbuild -= totalbuild
                    else:
                        building_list_dict[ShieldNetworks()] = sn
                        totalbuild -= sn
                    building_list_dict[Portal()] = po

                list_building, list_cost = build_on_planet(status, planet, building_list_dict)
                for k, v in list_cost.items():
                    list_costs[k] += v
                for k, v in list_building.items():
                    for a, b in v.items():
                            if k in building_types:
                                list_type[k][a] += b
                            else:
                                msg += str(b)
                del building_list_dict
                total_ob += planet.overbuilt

        else:
            planets_id = request.session['mass_build']
            for pid in planets_id:
                building_list_dict = {}
                planet = Planet.objects.get(id=pid)
                b_planets.append(planet)
                for building in building_list:
                    building_list_dict = {}
                    building_list_dict[building] = request.POST.get(str(building.building_index), None)
                

                    list_building, list_cost = build_on_planet(status, planet, building_list_dict)
                    for k, v in list_cost.items():
                        list_costs[k] += v
                    for k, v in list_building.items():
                        for a, b in v.items():
                            if k in building_types:
                                list_type[k][a] += b
                            else:
                                msg += str(b)
                                break
                    del building_list_dict
                    total_ob += planet.overbuilt

        total = 0
        for k, v in list_costs.items():
            total += int(v)
            
        if total > 0:
            msg += "\n\nTotals: \n"
            for k, v in list_type.items():
                for a, b in v.items():
                    if int(b) > 0:
                        msg += str(b) + " " + str(k) + "\n"
            for k, v in list_costs.items():
                    msg += str(v) + " " + str(k) + "\n"

        b_planets = b_planets

    if num_planets > 0:
        average_ob = total_ob / num_planets
    else:
        average_ob = 1

    costs = []
    for building in building_list:
        # Below doesn't include overbuild, it gets added below
        arte = Artefacts.objects.get(name="Advanced Robotics")
        if arte.empire_holding == status.empire:
            tech = status.research_percent_tech * 2
        else:
            tech = status.research_percent_tech
        artesn = Artefacts.objects.get(name="Shield Network")
        if artesn.empire_holding == status.empire:
            if building.building_index == 8:
                tech = 140
            
        if building.building_index == 9:
            cost_list, penalty = building.calc_cost(1, status.research_percent_portals, tech,
                                                status)
        else:
            cost_list, penalty = building.calc_cost(1, status.research_percent_construction, tech,
                                                status)
        # Add resource names to the cost_list, for the sake of the for loop in the view
        if cost_list:  # Remember that cost_list will be None if the tech is too low
            cost_list_labeled = []
            for i in range(5):  # 4 types of resources plus time
                if i < 4:
                    cost_list_labeled.append({"value": int(np.ceil(cost_list[i] * max(1, average_ob))), "name": resource_names[i]})
                else:
                    cost_list_labeled.append({"value": int(np.ceil(cost_list[i])),
                                              "name": resource_names[i]})
        else:
            cost_list_labeled = None  # Tech was too low

        cost = {"cost": cost_list_labeled,
                "penalty": penalty,
                "owned": getattr(status, 'total_' + building.model_name),
                "name": building.label}
        costs.append(cost)

    # Build context
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "costs": costs,
               "msg": msg,
               "building_helper": building_helper,
               "b_planets": b_planets,
               "num_planets": len(b_planets),
               "page_title": "Mass build"}
    return render(request, "mass_build.html", context)

def ranking(request):
    status = None
    try:
        status = UserStatus.objects.filter(user=request.user).first()
        my_template = 'base.html'
    except:
        my_template = 'front_page.html'
    
    round_no = RoundStatus.objects.get().round_number
    tick_time = RoundStatus.objects.get().tick_number
    week = tick_time % 52
    year = tick_time // 52
    no_planets = Planet.objects.all().count()
    no_system = System.objects.all().count()
    no_empires = Empire.objects.all().count()
    no_players = UserStatus.objects.exclude(user_name='').exclude(user_name='user-display-name').exclude(user='1').count()
    avail_spots = ((no_empires * players_per_empire) - no_players) - players_per_empire
    avail_planets = Planet.objects.filter(owner=None).count()
    time_tick = RoundStatus.objects.filter().first()
    
    table = UserStatus.objects.exclude(user_name='').exclude(user_name='user-display-name').order_by('-num_planets', '-networth')
    context = {"table": table,
               "page_title": "Faction ranking",
               "my_template": my_template,
               "round": RoundStatus.objects.filter().first,
               "round_no": round_no,
               "week": week,
               "year": year,
               "no_planets": no_planets,
               "no_system": no_system,
               "no_empires": no_empires,
               "no_players": no_players,
               "avail_spots": avail_spots,
               "avail_planets": avail_planets,
               "time_tick": time_tick,
               "status": status}
    return render(request, "ranking.html", context)


def empire_ranking(request):
    status = None
    empartis = 0
    arte_found = Artefacts.objects.filter(empire_holding__isnull=False).count()
    tot_arte = Artefacts.objects.filter().exclude(on_planet=None).count()
    try:
        status = UserStatus.objects.filter(user=request.user).first()
        my_template = 'base.html'
        
        empires = Empire.objects.filter(numplayers__gt=0).order_by("-planets", "-networth")
        table = {}
        max_artis = 0
        art_tab = {}
        all_artis = Artefacts.objects.exclude(on_planet=None)
        round_arti_nr = Artefacts.objects.exclude(on_planet=None).count()
        
        for a in all_artis:
            if a.empire_holding is not None:
                if a.empire_holding not in art_tab:
                    art_tab[a.empire_holding] = 1
                else:
                    art_tab[a.empire_holding] += 1
                max_artis = max(art_tab[a.empire_holding], max_artis)

        for e in empires:
            artefacts = []
            if arte_found != tot_arte:
                artis = Artefacts.objects.filter(empire_holding=e)
                if 3 * len(artis) >= round_arti_nr or 3 * max_artis / 2 >= round_arti_nr or e == status.empire:
                    for a in artis:
                        if status.id != 1:
                            artefacts.append(a)
            table[e.name_with_id] = {"planets": e.planets,
                                     "numplayers": e.numplayers,
                                     "nw": e.networth,
                                     "artefacts": artefacts,
                                     "empire_id":e.id,
                                     }

        artefacts_found = Artefacts.objects.filter(empire_holding__isnull=False)
        empartis = max_artis
        relations = Relations.objects.filter(relation_type="W")
        
    except:
        my_template = 'front_page.html'
        
        empires = Empire.objects.filter(numplayers__gt=0).order_by("-planets", "-networth")
        table = {}
        max_artis = 0
        art_tab = {}
        all_artis = Artefacts.objects.exclude(on_planet=None)
        round_arti_nr = Artefacts.objects.exclude(on_planet=None).count()
        
        
        for a in all_artis:
            if a.empire_holding is not None:
                if a.empire_holding not in art_tab:
                    art_tab[a.empire_holding] = 1
                else:
                    art_tab[a.empire_holding] += 1
                max_artis = max(art_tab[a.empire_holding], max_artis)

        for e in empires:
            artefacts = []
            artis = Artefacts.objects.filter(empire_holding=e)
            if 3 * len(artis) >= round_arti_nr or 3 * max_artis / 2 >= round_arti_nr:
                for a in artis:
                    artefacts.append(a)
            table[e.name_with_id] = {"planets": e.planets,
                                     "numplayers": e.numplayers,
                                     "nw": e.networth,
                                     "artefacts": artefacts,
                                     "empire_id":e.id,
                                     }

        artefacts_found = Artefacts.objects.filter(empire_holding__isnull=False)
        empartis = max_artis
        relations = Relations.objects.filter(relation_type="W") 
    
    
    context = {"table": table,
               "page_title": "Empire ranking",
               "status": status,
               "round": RoundStatus.objects.filter().first,
               "empire": empire,
               "artefacts_found": artefacts_found,
               "max_artis": art_tab,
               "round_arti_nr": round_arti_nr,
               "relations": relations,
               "all_artis": all_artis,
               "arte_found": arte_found,
               "tot_arte": tot_arte,
               "artis": Artefacts.objects.get(name="Ether Gardens"),
               "my_template": my_template,
               "empartis": empartis}
    return render(request, "empire_ranking.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def account(request, player_id):
    status = get_object_or_404(UserStatus, user=request.user)
    msg = ""
    ground = RoundStatus.objects.get()
    skrull = Artefacts.objects.get(name="Skrullos Fragment")
    a_change = ""
    s_news = News.objects.filter(news_type='SK', user1=status.user)
    if not s_news:
        a_change = "Yes"
    
    if 'chosen_race' in request.POST:
        status.race = request.POST['chosen_race']
        status.save()
        if skrull.empire_holding == status.empire:
            actskrull(skrull, status)
            return redirect(request.META['HTTP_REFERER'])
    
    elif request.method == 'POST':
        if ground.tick_number < 1:
            if 'Rejoin' in request.POST:
                emp = status.empire
                emp.numplayers -= 1
                emp.planets -= 1
                emp.networth -= 1250
                emp.save()
                status.empire = None
                status.energy = '120000'
                status.minerals = '10000'
                status.crystals = '5000'
                status.ectrolium = '5000'
                status.user_name = ""
                status.fleet_readiness = 100
                status.psychic_readiness = 100
                status.agent_readiness = 100
                status.empire_role = ''
                planets = Planet.objects.filter(owner=status.user)
                for p in planets:
                    p.buildings_under_construction = 0
                    p.overbuilt_percent = 0
                    p.overbuilt = 0
                    p.total_buildings = 200
                    p.owner = None
                    p.save()
                status.save()
                Construction.objects.filter(user=status.user).delete()
                Fleet.objects.filter(owner=status.user).delete()
                Fleet.objects.create(owner=status.user, main_fleet=True)
                UnitConstruction.objects.filter(user=status.user).delete()
                Scouting.objects.filter(user=status.user).delete()
                MapSettings.objects.filter(user=status.user).delete()
                return portal(request)
                
            if 'Uname' in request.POST:
                if request.POST['Uname'] == "":
                    msg += "Faction name is required!"
                elif UserStatus.objects.filter(user_name=request.POST['Uname']).count() > 0:
                    msg += "This faction name is already taken!"
                elif request.POST['Uname'].endswith(" ") or request.POST['Uname'].startswith(" "):
                    msg += "Faction names cannot start or end with a space!"
                else:
                    status.user_name = request.POST['Uname']
                    status.save()
            if 'chose_race' in request.POST:
                status.race = request.POST['chose_race']
                status.save()           
        
    player = UserStatus.objects.get(id=player_id)
    tag = ""
    hof = HallOfFame.objects.filter(userid=player.id).order_by('-round')
    races = status.Races.choices


    context = {"status": status,
               "player": player,
               "hof": hof,
               "page_title": "Account",
               "tag": tag,
               "races": races,
               "ground": ground,
               "skrull": skrull,
               "a_change": a_change,
               "msg": msg}
    return render(request, "account.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('change_password')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'change_password.html', {
        'form': form
    })


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def units(request):
    status = get_object_or_404(UserStatus, user=request.user)
    u_helper = unit_helper_list

    # bribe officials operation modifier
    bribe_resource_multiplier = 1
    bribe_time_multiplier = 1
    arte_multiplier = 1
    robo = Artefacts.objects.get(name="Advanced Robotics")
    eson = Artefacts.objects.get(name="Engineers Son")
    maryc = Artefacts.objects.get(name="Mary Celeste")
    if Specops.objects.filter(user_to=status.user, name="Bribe officials",
                              extra_effect="resource_cost").exists():
        bribe = Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                       extra_effect="resource_cost")
        for br in bribe:
            bribe_resource_multiplier *= 1 + br.specop_strength / 100

    if Specops.objects.filter(user_to=status.user, name="Bribe officials",
                              extra_effect="building_time").exists():
        bribe = Specops.objects.filter(user_to=status.user, name="Bribe officials",
                                       extra_effect="building_time")
        for br in bribe:
            bribe_time_multiplier *= 1 + br.specop_strength / 100

    if request.method == 'POST':
        msg = ''
        for i, unit in enumerate(unit_info["unit_list"]):
            arte_multiplier = 1
            if unit == 'phantom':
                continue
            num = request.POST.get(str(i),
                                   0)  # must match name of each inputfield in the template, in this case we are using integers
            if num == '':
                num = 0
            else:
                num = int(num)
            if num:
                # calc_building_cost was designed to give the View what it needed, so pull out just the values and multiply by num
                
                if robo.empire_holding == status.empire:
                    tech = unit_info[unit]['required_tech'] / 2
                else:
                    tech = unit_info[unit]['required_tech']
                mult, _ = unit_cost_multiplier(status.research_percent_construction, status.research_percent_tech,
                                               tech)
                if not mult:
                    msg += 'Not enough tech research to build ' + unit_info[unit]['label'] + '<br>'
                    continue

                if eson.empire_holding == status.empire and unit == 'fighter':
                    arte_multiplier = 1 - (eson.effect1/100)
                  
                if maryc.empire_holding == status.empire and unit == 'ghost':
                    arte_multiplier = 1 - (maryc.effect1/100)

                total_resource_cost = [int(np.ceil(x * mult * arte_multiplier)) for x in unit_info[unit]['cost']]
                
                for j in range(4):  # multiply all resources except time by number of units
                    total_resource_cost[j] *= num * bribe_resource_multiplier
                        
                # multiply time cost by bribe multiplier
                total_resource_cost[4] *= bribe_time_multiplier

                total_resource_cost = ResourceSet(total_resource_cost)  # convert to more usable object
                if not total_resource_cost.is_enough(status):
                    msg += 'Not enough resources to build ' + unit_info[unit]['label'] + '<br>'
                    continue

                # Deduct resources
                status.energy -= total_resource_cost.ene
                status.minerals -= total_resource_cost.min
                status.crystals -= total_resource_cost.cry
                status.ectrolium -= total_resource_cost.ect

                # Create new construction job
                msg += 'Building ' + str(num) + ' ' + unit_info[unit]['label'] + '<br>'
                UnitConstruction.objects.create(user=request.user,
                                                n=num,
                                                unit_type=unit,
                                                ticks_remaining=total_resource_cost.time,
                                                energy_cost=total_resource_cost.ene,
                                                mineral_cost=total_resource_cost.min,
                                                crystal_cost=total_resource_cost.cry,
                                                ectrolium_cost=total_resource_cost.ect
                                                )  # calculated ticks

        status.save()  # update user's resources
    else:
        msg = None

    resource_names = ['Energy', 'Mineral', 'Crystal', 'Ectrolium', 'Time']
    unit_dict = []  # idea here is to build up a dict we can nicely iterate over in the template
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)
    main_fleet_list = []
    
    for unit in unit_info["unit_list"]:
        num = getattr(main_fleet, unit)
        if num:
            main_fleet_list.append({"name": unit_info[unit]["label"], "value": num, "i": unit_info[unit]["i"]})
    for unit in unit_info["unit_list"]:
        arte_multiplier = 1
        if unit == 'phantom':
            continue
        d = {}
        if robo.empire_holding == status.empire:
            tech = unit_info[unit]['required_tech'] / 2
        else:
            tech = unit_info[unit]['required_tech']
        mult, penalty = unit_cost_multiplier(status.research_percent_construction, status.research_percent_tech,
                                             tech)

        if eson.empire_holding == status.empire and unit == 'fighter':
            arte_multiplier = 1 - (eson.effect1/100)

        if maryc.empire_holding == status.empire and unit == 'ghost':
            arte_multiplier = 1 - (maryc.effect1/100)

        if not mult:
            cost = None
        else:
            unit_cost_dict = []
            cost = []
            nrg = 999999999999999999999999
            cry = 999999999999999999999999
            ect = 999999999999999999999999
            mini = 999999999999999999999999
            for i, resource in enumerate(resource_names):
                if resource == 'Energy' and unit_info[unit]['cost'][i] > 0 and unit_info[unit]['cost'][i] < nrg:
                    nrg = int(status.energy/(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_resource_multiplier * arte_multiplier)))
                elif resource == 'Crystal' and unit_info[unit]['cost'][i] > 0 and unit_info[unit]['cost'][i] < cry:
                    cry = int(status.crystals/(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_resource_multiplier * arte_multiplier)))
                elif resource == 'Mineral' and unit_info[unit]['cost'][i] > 0 and unit_info[unit]['cost'][i] < mini:
                    mini = int(status.minerals/(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_resource_multiplier * arte_multiplier)))
                elif resource == 'Ectrolium' and unit_info[unit]['cost'][i] > 0 and unit_info[unit]['cost'][i] < ect:
                    ect = int(status.ectrolium/(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_resource_multiplier * arte_multiplier)))
                if resource != 'Time':
                    cost.append({"name": resource,
                                 "value": int(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_resource_multiplier * arte_multiplier))})     
                else:
                    cost.append({"name": resource,
                                 "value": int(np.ceil(mult * unit_info[unit]['cost'][i] * bribe_time_multiplier))})
            d["maxunit"] = round(min(nrg,cry,mini,ect))
            d["cost"] = cost
        d["penalty"] = penalty
        d["label"] = unit_info[unit]['label']
        d["troops"] = unit_info[unit]['troops']
        d["i"] = unit_info[unit]['i']
        totunits = Fleet.objects.filter(owner=status.user).values_list(d["troops"], flat=True)
        totalunits = sum(totunits)
        d["owned"] = totalunits
        unit_dict.append(d)

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Units",
               "unit_dict": unit_dict,
               "main_fleet": main_fleet,
               "totalunits": totalunits,
               "u_helper": u_helper,
               "msg": msg}
    return render(request, "units.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
@xframe_options_exempt
def fleets_orders(request):
    return fleets(request, "short")

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleets_orders_process(request, *args):
    status = get_object_or_404(UserStatus, user=request.user)
    round_params = get_object_or_404(RoundStatus)

    if not request.POST:
        request.session['error'] = "Not a right request!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)

    if not "fleet_select_hidden" in request.POST:
        request.session['error'] = "No fleets selected!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)
    if not "order" in request.POST:
        request.session['error'] = "No order selected!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)

    fleets_id = request.POST.getlist("fleet_select_hidden")
    order = int(request.POST.get("order"))

    if (order == 0 or order == 1 or order == 2 or order == 3 or order == 10) and not request.POST.get("X"):
        request.session['error'] = "You must enter x coordinate!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)
    if (order == 0 or order == 1 or order == 2 or order == 3 or order == 10) and not request.POST.get("Y"):
        request.session['error'] = "You must enter y coordinate!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)

    if order == 0 or order == 1 or order == 2 or order == 3 or order == 10:
        x = int(request.POST.get("X"))
        y = int(request.POST.get("Y"))

    if (order == 0 or order == 1 or order == 10) and not request.POST.get("I"):
        request.session['error'] = "You must enter planets number!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)

    if (order == 6) and not request.POST.get("split_pct"):
        request.session['error'] = "You must enter fleet split %!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)

    if order == 0 or order == 1 or order == 10:  # if attack planet or station on planet, make sure planet exists and get planet object
        i = request.POST.get("I")
        try:
            planet = Planet.objects.get(x=x, y=y, i=i)
        except Planet.DoesNotExist:
            request.session['error'] = "This planet doesn't exist"
            if args:
                return fleets(request, "short")
            else:
                return fleets(request)
    elif order == 2 or order == 3:  # if move to system, make sure x and y are actual coords
        if x < 0 or x >= round_params.galaxy_size or y < 0 or y >= round_params.galaxy_size:
            request.session['error'] = "Coordinates aren't valid"
            if args:
                return fleets(request, "short")
            else:
                return fleets(request)

    fleets_id2 = Fleet.objects.filter(id__in=fleets_id)
    # print("fleets_id2",fleets_id2)

    # option value="0" Attack the planet
    # option value="1" Station on planet
    # option value="2" Move to system
    # option value="3" Merge in system (chose system yourself)
    # option value="4" Merge in system (auto/optimal)
    # option value="5" Join main fleet
    # option value="6" Split fleet
    
    speed = travel_speed(status)
    if order == 0 or order == 1:
        for f in fleets_id2:
            generate_fleet_order(f, x, y, speed, order, i)
        # do instant merge of stationed fleets if allready present on that planet
        fleets_id3 = Fleet.objects.filter(id__in=fleets_id, ticks_remaining__lt=1, command_order=1)
        station_fleets(request, fleets_id3, status)
    if order == 2: 
        for f in fleets_id2:
            generate_fleet_order(f, x, y, speed, order)
    if order == 3:
        for f in fleets_id2:
            generate_fleet_order(f, x, y, speed, order)
        fleets_id3 = Fleet.objects.filter(id__in=fleets_id, ticks_remaining__lt=1)
        # do instant merge of fleets allready present in same systems
        merge_fleets(fleets_id3)
    # mass merge auto
    if order == 4:
        systems = []
        for f in fleets_id2:
            tmp = []
            tmp.append(f.current_position_x)
            tmp.append(f.current_position_y)
            systems.append(tmp)
        pos = find_bounding_circle(systems)
        for f in fleets_id2:
            generate_fleet_order(f, pos[0], pos[1], speed, order)
        fleets_id3 = Fleet.objects.filter(id__in=fleets_id, ticks_remaining__lt=1)
        # do instant merge of fleets allready present in same systems
        merge_fleets(fleets_id3)
    # join main fleet
    if order == 5:
        portal_planets = Planet.objects.filter(owner=request.user,
                                               portal=True)  # should always have at least the home planet, unless razed!!!
        # print(portal_planets)
        if not portal_planets:
            request.session['error'] = "You need at least one portal for fleet to returnto main fleet!"
            if args:
                return fleets(request, "short")
            else:
                return fleets(request)
        for f in fleets_id2:
            portal = find_nearest_portal(f.current_position_x, f.current_position_y, portal_planets, status)
            generate_fleet_order(f, portal.x, portal.y, speed, order)
        # do instant join of fleets allready present in systems with portals
        main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
        fleets_id3 = Fleet.objects.filter(id__in=fleets_id, ticks_remaining__lt=1)
        join_main_fleet(main_fleet, fleets_id3)
    if order == 6:
        split_pct = int(request.POST.get("split_pct"))
        total_fleets = Fleet.objects.filter(owner=status.user.id, main_fleet=False)
        split_fleets(fleets_id2, split_pct)
    if order == 10:
        for f in fleets_id2:
            generate_fleet_order(f, x, y, speed, order, i)
        # instant explore
        fleets_buffer = Fleet.objects.filter(main_fleet=False, ticks_remaining__lt=1, command_order=10)
        explore_planets(fleets_buffer)
    if args:
        return fleets_orders(request)
    else:
        return fleets(request)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleet_orders_process(request):
    return fleets_orders_process(request, "short")

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleets(request, *args):
    status = get_object_or_404(UserStatus, user=request.user)
    other_fleets = Fleet.objects.filter(owner=status.user.id, main_fleet=False)
    display_fleet_exploration = Fleet.objects.filter(owner=status.user.id, main_fleet=False, exploration=1)

    # show errors from fleetsend such as not having enough transports for droids, etc
    error = None
    if 'error' in request.session:
        error = request.session['error']
        request.session['error'] = ''

    planet_to_template_explore = None
    if request.method == 'POST' and 'explore_planet' in request.POST:
        try:
            pl_id = request.POST.get('explore_planet')
            planet_to_template_explore = Planet.objects.get(id=pl_id)
        except Planet.DoesNotExist:
            planet_to_template_explore = None

    planet_to_template_attack = None
    if request.method == 'POST' and 'attack_planet' in request.POST:
        try:
            pl_id = request.POST.get('attack_planet')
            planet_to_template_attack = Planet.objects.get(id=pl_id)
        except Planet.DoesNotExist:
            planet_to_template_attack = None
    
    travel_time = None
    exploration_cost = None
    if planet_to_template_explore:
        exploration_cost = calc_exploration_cost(status)
        portal_planets = Planet.objects.filter(owner=status.user, portal=True)
        portal = find_nearest_portal(planet_to_template_explore.x, planet_to_template_explore.y,
                                             portal_planets, status)
        min_dist = np.sqrt((portal.x - planet_to_template_explore.x) ** 2 +
                       (portal.y - planet_to_template_explore.y) ** 2)
        speed = travel_speed(status)
        travel_time = max(0,int(np.floor(min_dist / speed)))

    attack_cost = None
    status2 = None
    
    if planet_to_template_attack:
        status2 = UserStatus.objects.get(id=planet_to_template_attack.owner.id)
        attack_cost = battleReadinessLoss(status, status2, planet_to_template_attack)
        portal_planets = Planet.objects.filter(owner=status.user, portal=True)
        portal = find_nearest_portal(planet_to_template_attack.x, planet_to_template_attack.y,
                                             portal_planets, status)
        min_dist = np.sqrt((portal.x - planet_to_template_attack.x) ** 2 +
                       (portal.y - planet_to_template_attack.y) ** 2)
        speed = travel_speed(status)
        travel_time = max(0,int(np.floor(min_dist / speed)))
        

    # If user changed order after attack or percentages
    if request.method == 'POST' and 'attack' in request.POST:
        status.post_attack_order = int(request.POST["attack"])
        status.long_range_attack_percent = int(request.POST["f0"])
        status.air_vs_air_percent = int(request.POST["f1"])
        status.ground_vs_air_percent = int(request.POST["f2"])
        status.ground_vs_ground_percent = int(request.POST["f3"])
        status.save()

    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)  # should only ever be 1
    main_fleet_list = []
    send_fleet_list = []  # need to have a separate list that doesnt include agents/psycics/ghosts/explos
    explo_ships = main_fleet.exploration

    for unit in unit_info["unit_list"]:
        num = getattr(main_fleet, unit)
        if num:
            main_fleet_list.append({"name": unit_info[unit]["label"], "value": num, "i": unit_info[unit]["i"]})
            if unit not in ['wizard', 'agent', 'ghost', 'exploration']:
                send_fleet_list.append({"name": unit_info[unit]["label"], "value": num, "i": unit_info[unit]["i"]})

    display_fleet = {}
    for fleet in other_fleets:
        display_fleet_inner = {}
        for unit in unit_info["unit_list"]:
            if unit not in ['wizard', 'agent', 'ghost', 'exploration']:
                num = getattr(fleet, unit)
                if num > 0:
                    print(unit, num)
                    display_fleet_inner[unit_info[unit]["label"]] = num
                    display_fleet[fleet] = display_fleet_inner
                    
    
    tgeneral = Artefacts.objects.get(name="The General")
    gsystem = ''
    if tgeneral.on_planet != None:
        gsystem = System.objects.get(id=tgeneral.effect1)
    
    bare = "No"
    if args:
        bare = "Yes"
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Fleets",
               "main_fleet_list": main_fleet_list,
               "send_fleet_list": send_fleet_list,
               "other_fleets": other_fleets,
               "display_fleet": display_fleet,
               "display_fleet_exploration": display_fleet_exploration,
               "explo_ships": explo_ships,
               "error": error,
               "planet_to_template_explore": planet_to_template_explore,
               "planet_to_template_attack": planet_to_template_attack,
               "exploration_cost": exploration_cost,
               "owner_of_attacked_pl": status2,
               "planet": Planet.objects.all(),
               "attack_cost": attack_cost,
               "bare": bare,
               #"necro": Artefacts.objects.get(name="Scroll of the Necromancer"),
               "tgeneral": tgeneral,
               "gsystem": gsystem,
               "travel_time": travel_time}
    
    return render(request, "fleets.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def tgeneral(request):
    status = get_object_or_404(UserStatus, user=request.user)
    tgeneral = Artefacts.objects.get(name="The General")
    gsystem = System.objects.get(id=tgeneral.effect1)
    
    if request.method != 'POST':
        return HttpResponse("You shouldnt be able to get to this page!")
        
    print(request.POST)
    x = int(request.POST['X']) if request.POST['X'] else None
    y = int(request.POST['Y']) if request.POST['Y'] else None
    nsystem = System.objects.filter(x=x, y=y)
    if nsystem:
        nsystem = System.objects.get(x=x, y=y)
        min_dist = np.sqrt((gsystem.x - nsystem.x) ** 2 +
                       (gsystem.y - nsystem.y) ** 2)
        speed = travel_speed(status)
        travel_time = max(0,int(np.floor(min_dist / speed)))
        tgeneral.effect1 = nsystem.id
        tgeneral.ticks_left = travel_time
        tgeneral.save()
        request.session['error'] = "The General is moving to " + str(nsystem.x) + "," + str(nsystem.y) + " and will arrive in " + str(travel_time) + " weeks!"
        if args:
            return fleets(request, "short")
        else:
            return fleets(request)
    else:
        request.session['error'] = "This System doesnt exist!"
        return fleets(request)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleets_disband(request):
    status = get_object_or_404(UserStatus, user=request.user)
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)  # should only ever be 1
    main_fleet_list = []
    print("main_fleet", main_fleet)

    disband_info = {}

    if request.method == 'POST':
        for unit in unit_info["unit_list"]:
            if unit in request.POST:
                setattr(main_fleet, unit, max(0, getattr(main_fleet, unit) - int(request.POST.get(unit))))
                if int(request.POST.get(unit)) > 0:
                    disband_info[unit_info[unit]["label"]] = request.POST.get(unit)
        main_fleet.save()

    for unit in unit_info["unit_list"]:
        num = getattr(main_fleet, unit)
        if num:
            main_fleet_list.append(
                {"name": unit_info[unit]["label"], "value": num, "i": unit_info[unit]["i"], "db_name": unit})

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Fleets disband",
               "main_fleet": main_fleet_list,
               "disband_info": disband_info,
               }
    return render(request, "fleets_disband.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleetsend(request):
    status = get_object_or_404(UserStatus, user=request.user)
    round_params = get_object_or_404(RoundStatus)  # should only be one
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)  # should only ever be 1

    if request.method != 'POST':
        return HttpResponse("You shouldnt be able to get to this page!")

    total_fleets = Fleet.objects.filter(owner=status.user.id, main_fleet=False)
    if len(total_fleets) >= 50:
        request.session['error'] = "You cant send more than 50 fleets out at the same time!"
        return fleets(request)

    # Process POST
    print(request.POST)
    x = int(request.POST['X']) if request.POST['X'] else None
    y = int(request.POST['Y']) if request.POST['Y'] else None
    planet_i = int(request.POST['I']) if request.POST['I'] else None
    order = int(request.POST['order'])
    send_unit_dict = {}  # contains how many of each unit to send, dict so its quick to look up different unit counts
    total_sent_units = 0

    if 'exploration' in request.POST:
        if getattr(main_fleet, 'exploration') < 1:
            request.session['error'] = "You don't have any exploration ships!"
            return fleets(request)
        fr = UserStatus.objects.get(id=status.id)
        if getattr(fr, 'fleet_readiness') < 0:
            request.session['error'] = "Your forces are to tired to send an Exploration Ship!"
            return fleets(request)                
        send_unit_dict['exploration'] = 1
        total_sent_units = 1
    else:
        for i, unit in enumerate(unit_info["unit_list"][0:9]):
            # print('u' + str(i))
            if 'u' + str(i) in request.POST:
                if request.POST['u' + str(i)]:
                    num = int(request.POST['u' + str(i)])
                else:
                    num = 0
            else:
                num = 0
            if getattr(main_fleet, unit) < num:
                num = getattr(main_fleet, unit)
            send_unit_dict[unit] = num
            total_sent_units += num

    if total_sent_units == 0:
        request.session['error'] = "You must send some units to make a fleet"
        return fleets(request)

    # The rest mostly comes from cmdExecSendFleet in cmdexec.c
    if order == 0 or order == 1 or order == 10:  # if attack planet or station on planet orexplore, make sure planet exists and get planet object
        try:
            planet = Planet.objects.get(x=x, y=y, i=planet_i)
        except Planet.DoesNotExist:
            request.session['error'] = "This planet doesn't exist"
            return fleets(request)
    else:  # if move to system, make sure x and y are actual coords
        if not x or not y or x < 0 or x >= round_params.galaxy_size or y < 0 or y >= round_params.galaxy_size:
            request.session['error'] = "Coordinates aren't valid"
            return fleets(request)

    if not 'exploration' in request.POST:
        # Carrier/transport check
        if send_unit_dict['carrier'] * 100 < (
                send_unit_dict['bomber'] + send_unit_dict['fighter'] + send_unit_dict['transport']):
            request.session[
                'error'] = "You are not sending enough carriers, each carrier can hold 100 fighters, bombers or transports"
            return fleets(request)
        if send_unit_dict['transport'] * 100 < (
                send_unit_dict['soldier'] + send_unit_dict['droid'] + 4 * send_unit_dict['goliath']):
            request.session[
                'error'] = "You are not sending enough transports, each transport can hold 100 soldiers or droids, or 25 goliaths"
            return fleets(request)

    # Find closest portal and its distance away, which is done in specopVortexListCalc in cmd.c in the C code
    portal_planets = Planet.objects.filter(owner=request.user,
                                           portal=True)  # should always have at least the home planet, unless razed!!!

    if not portal_planets:
        request.session['error'] = "You need at least one portal to send the fleet from!"
        return fleets(request)

    best_portal_planet = find_nearest_portal(x, y, portal_planets, status)
    min_dist = np.sqrt((best_portal_planet.x - x) ** 2 + (best_portal_planet.y - y) ** 2)
    speed = travel_speed(status)
    race = status.race
    fleet_time = max(0,int(np.floor(min_dist / speed)))

    if not 'exploration' in request.POST:
        # Remove units from main fleet
        for unit in unit_info["unit_list"][0:9]:
            setattr(main_fleet, unit, getattr(main_fleet, unit) - send_unit_dict[unit])
    else:
        setattr(main_fleet, 'exploration', getattr(main_fleet, 'exploration') - 1)

    # Create new Fleet object
    planet = Planet.objects.get(x=x, y=y, i=planet_i)
    fleet = Fleet.objects.create(owner=request.user,
                                 command_order=order,
                                 x=x,
                                 y=y,
                                 i=planet_i,
                                 ticks_remaining=fleet_time,
                                 current_position_x=best_portal_planet.x,
                                 current_position_y=best_portal_planet.y,
                                 target_planet=planet,
                                 **send_unit_dict)

    main_fleet.save()
    # If instant travel then immediately do the cmdFleetAction stuff

    fleets_tmp = []
    if fleet_time == 0:
        fleets_tmp.append(fleet)

    if order == 10 or order == 11:
        fr_cost = calc_exploration_cost(status)
        status.fleet_readiness -= fr_cost
        status.save()
        # instant explore
        if fleet_time == 0 and order == 10:
            explore_planets(fleets_tmp)

    if order == 1 and fleet_time == 0:
        station_fleets(request, fleets_tmp, status)

    if fleet_time == 0:
        # TODO
        # cmdFleetAction()
        request.session['error'] = "The fleet reached its destination!"
        return fleets(request)
    else:
        request.session['error'] = "The fleet will reach its destination in " + str(fleet_time) + " weeks"

        return fleets(request)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleetssend(request):
    status = get_object_or_404(UserStatus, user=request.user)
    round_params = get_object_or_404(RoundStatus)  # should only be one
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)  # should only ever be 1

    if request.method != 'POST':
        return HttpResponse("You shouldnt be able to get to this page!")

    '''total_fleets = Fleet.objects.filter(owner=status.user.id, main_fleet=False)
    if len(total_fleets) >= 50:
        request.session['error'] = "You cant send more than 50 fleets out at the same time!"
        return fleets_orders(request)'''

    # Process POST
    print(request.POST)
    x = int(request.POST['X']) if request.POST['X'] else None
    y = int(request.POST['Y']) if request.POST['Y'] else None
    planet_i = int(request.POST['I']) if request.POST['I'] else None
    order = int(request.POST['order'])
    send_unit_dict = {}  # contains how many of each unit to send, dict so its quick to look up different unit counts
    total_sent_units = 0

    if 'exploration' in request.POST:
        if getattr(main_fleet, 'exploration') < 1:
            request.session['error'] = "You don't have any exploration ships!"
            return fleets_orders(request)
        fr = UserStatus.objects.get(id=status.id)
        if getattr(fr, 'fleet_readiness') < 0:
            request.session['error'] = "Your forces are to tired to send an Exploration Ship!"
            return fleets_orders(request)                
        send_unit_dict['exploration'] = 1
        total_sent_units = 1
    else:
        for i, unit in enumerate(unit_info["unit_list"][0:9]):
            # print('u' + str(i))
            if 'u' + str(i) in request.POST:
                if request.POST['u' + str(i)]:
                    num = int(request.POST['u' + str(i)])
                else:
                    num = 0
            else:
                num = 0
            if getattr(main_fleet, unit) < num:
                num = getattr(main_fleet, unit)
                '''request.session['error'] = "Don't have enough" + unit_info[unit]["label"]
                return fleets(request)'''
            send_unit_dict[unit] = num
            total_sent_units += num

    if total_sent_units == 0:
        request.session['error'] = "You must send some units to make a fleet"
        return fleets_orders(request)

    # The rest mostly comes from cmdExecSendFleet in cmdexec.c
    if order == 0 or order == 1 or order == 10:  # if attack planet or station on planet orexplore, make sure planet exists and get planet object
        try:
            planet = Planet.objects.get(x=x, y=y, i=planet_i)
        except Planet.DoesNotExist:
            request.session['error'] = "This planet doesn't exist"
            return fleets_orders(request)
    else:  # if move to system, make sure x and y are actual coords
        if not x or not y or x < 0 or x >= round_params.galaxy_size or y < 0 or y >= round_params.galaxy_size:
            request.session['error'] = "Coordinates aren't valid"
            return fleets_orders(request)

    if not 'exploration' in request.POST:
        # Carrier/transport check
        if send_unit_dict['carrier'] * 100 < (
                send_unit_dict['bomber'] + send_unit_dict['fighter'] + send_unit_dict['transport']):
            request.session[
                'error'] = "You are not sending enough carriers, each carrier can hold 100 fighters, bombers or transports"
            return fleets_orders(request)
        if send_unit_dict['transport'] * 100 < (
                send_unit_dict['soldier'] + send_unit_dict['droid'] + 4 * send_unit_dict['goliath']):
            request.session[
                'error'] = "You are not sending enough transports, each transport can hold 100 soldiers or droids, or 25 goliaths"
            return fleets_orders(request)

    # Find closest portal and its distance away, which is done in specopVortexListCalc in cmd.c in the C code
    portal_planets = Planet.objects.filter(owner=request.user,
                                           portal=True)  # should always have at least the home planet, unless razed!!!

    if not portal_planets:
        request.session['error'] = "You need at least one portal to send the fleet from!"
        return fleets_orders(request)

    best_portal_planet = find_nearest_portal(x, y, portal_planets, status)
    min_dist = np.sqrt((best_portal_planet.x - x) ** 2 + (best_portal_planet.y - y) ** 2)
    speed = travel_speed(status)
    fleet_time = max(0,int(np.floor(min_dist / speed)))

    if not 'exploration' in request.POST:
        # Remove units from main fleet
        for unit in unit_info["unit_list"][0:9]:
            setattr(main_fleet, unit, getattr(main_fleet, unit) - send_unit_dict[unit])
    else:
        setattr(main_fleet, 'exploration', getattr(main_fleet, 'exploration') - 1)

    # Create new Fleet object
    planet = Planet.objects.get(x=x, y=y, i=planet_i)
    fleet = Fleet.objects.create(owner=request.user,
                                 command_order=order,
                                 x=x,
                                 y=y,
                                 i=planet_i,
                                 ticks_remaining=fleet_time,
                                 current_position_x=best_portal_planet.x,
                                 current_position_y=best_portal_planet.y,
                                 target_planet=planet,
                                 **send_unit_dict)

    main_fleet.save()
    # If instant travel then immediately do the cmdFleetAction stuff

    fleets_tmp = []
    if fleet_time == 0:
        fleets_tmp.append(fleet)

    if order == 10 or order == 11:
        fr_cost = calc_exploration_cost(status)
        status.fleet_readiness -= fr_cost
        status.save()
        # instant explore
        if fleet_time == 0 and order == 10:
            explore_planets(fleets_tmp)

    if order == 1 and fleet_time == 0:
        station_fleets(request, fleets_tmp, status)

    if fleet_time == 0:
        request.session['error'] = "The fleet reached its destination!"
        return fleets_orders(request)
    else:
        request.session['error'] = "The fleet will reach its destination in " + str(fleet_time) + " weeks"

        return fleets_orders(request)

# TODO, COPY FROM RAZE VIEW
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def fleetdisband(request):
    status = get_object_or_404(UserStatus, user=request.user)
    return HttpResponse("GOT HERE")


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def empire(request, empire_id):
    status = get_object_or_404(UserStatus, user=request.user)
    player_list = UserStatus.objects.filter(empire=empire_id).order_by("-num_planets" , "-networth")
    empire1 = Empire.objects.get(pk=empire_id)
    print(empire_id)
    
    empires = Empire.objects.filter(numplayers__gt=0).order_by("-planets", "-networth")

    max_artis = 0
    art_tab = {}
    all_artis = Artefacts.objects.exclude(on_planet=None)
    arti_count = Artefacts.objects.exclude(on_planet=None).count()
    empcount = Artefacts.objects.filter(empire_holding=empire1).count()
    
    for a in all_artis:
        if a.empire_holding is not None:
            if a.empire_holding not in art_tab:
                art_tab[a.empire_holding] = 1
            else:
                art_tab[a.empire_holding] += 1
            max_artis = max(art_tab[a.empire_holding], max_artis)
   
    emparts = ''    
    if status.id == 1 or max_artis  > arti_count * 0.66:
        emparts = Artefacts.objects.filter(empire_holding=empire1)
    elif empcount > arti_count * 0.33:
        emparts = Artefacts.objects.filter(empire_holding=empire1)
    elif status.empire == empire1:
        emparts = Artefacts.objects.filter(empire_holding=status.empire)
        
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": empire1.name_with_id,
               "player_list": player_list,
               "empire": empire1,
               "emparts": emparts
               }
    return render(request, "empire.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def vote(request):
    status = get_object_or_404(UserStatus, user=request.user)
    player_list = UserStatus.objects.filter(empire=status.empire)
    try:
        new_voting_for = (request.POST['choice'])
    except (KeyError, ObjectDoesNotExist):
        context = {"status": status,
                   "round": RoundStatus.objects.filter().first,
                   "page_title": "Vote",
                   "player_list": player_list}
        return render(request, "vote.html", context)
    else:
        print("check votiung for", status.voting_for)
        if status.voting_for is not None:
            # find previous user voted for and remove one vote from him
            if status.voting_for.votes > 0:
                status.voting_for.votes -= 1
                status.voting_for.save()
        voted_for_status = get_object_or_404(UserStatus, user=new_voting_for)
        # check if user voted for himself, to avoid db saving conflicts
        status = get_object_or_404(UserStatus, user=request.user)
        if status.id == voted_for_status.id:
            status.votes += 1
            status.voting_for = status
        else:
            status.voting_for = voted_for_status
            voted_for_status.votes += 1
            voted_for_status.save()
        status.save()

        # part to check/make a new leader when someone has voted
        # if mutiple players have the same ammount of votes - the old leader stays, regarding of his votes
        # otherwise a player with max votes is chosen

        current_leader = None
        max_votes = 0
        for player in player_list:
            if player.empire_role == 'PM':
                current_leader = player
            if player.votes > max_votes:
                max_votes = player.votes
        leaders = []
        for player in player_list:
            if player.votes == max_votes:
                leaders.append(player)
        if len(leaders) == 1:
            if current_leader is not None:
                current_leader.empire_role = 'P'
                current_leader.save()
            leaders[0].empire_role = 'PM'
            leaders[0].save()

        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect("/results")


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def results(request):
    status = get_object_or_404(UserStatus, user=request.user)
    player_list = UserStatus.objects.filter(empire=status.empire)
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Results",
               "player_list": player_list}
    return render(request, "results.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def set_relation(request, relation, current_empire, target_empire, *rel_time_passed):
    if current_empire.id == target_empire.id:
        return
    if not rel_time_passed or rel_time_passed[0] == '':
        rel_time = 0
    else:
        # rel time is given in hours in leaders options, however is stored as number of ticks internally
        rel_time = int(rel_time_passed[0]) * 3600 / tick_time

    if current_empire is None or target_empire is None:
        return

    try:
        tmp_rel = Relations.objects.get(empire1=current_empire, empire2=target_empire)
    except(ObjectDoesNotExist):
        pass
    else:
        if tmp_rel.relation_type != 'CO':
            if tmp_rel.relation_type == 'AO' or tmp_rel.relation_type == 'NO':
                tmp_rel.delete()
            # if there allready is an established relation we cant create a new offer before the last one is canclled
            elif relation != "cancel_nap":
                return

    # check if there target empire already offered a relation:
    try:
        rel = Relations.objects.get(empire1=target_empire, empire2=current_empire)
    except ObjectDoesNotExist:
        rel = None

    if relation == 'ally':
        if rel is not None and rel.relation_type == 'AO':
            # if second empire allready offered an alliance, make two empires allies
            Relations.objects.create(empire1=current_empire,
                                     empire2=target_empire,
                                     relation_type='A',
                                     relation_length=rel_time,
                                     relation_creation_tick=RoundStatus.objects.get().tick_number,
                                     relation_remaining_time=rel_time)
            News.objects.create(empire1=current_empire,
                                empire2=target_empire,
                                news_type='RAD',
                                date_and_time=datetime.datetime.now() + timedelta(seconds=1),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
            rel.relation_type = 'A'
            rel.save()
        else:
            # make an alliance offer from current_empire to target_empire
            Relations.objects.create(empire1=current_empire,
                                     empire2=target_empire,
                                     relation_type='AO',
                                     relation_length=rel_time,
                                     relation_creation_tick=RoundStatus.objects.get().tick_number,
                                     relation_remaining_time=rel_time)
    if relation == 'war':
        Relations.objects.create(empire1=current_empire,
                                 empire2=target_empire,
                                 relation_type='W',
                                 relation_length=war_declaration_timer,
                                 relation_creation_tick=RoundStatus.objects.get().tick_number,
                                 relation_remaining_time=war_declaration_timer)
    if relation == 'nap':
        if rel is not None and rel.relation_type == 'NO' and rel.relation_length == rel_time:
            # if second empire allready offered a nap with the same timer, make two empires napped
            Relations.objects.create(empire1=current_empire,
                                     empire2=target_empire,
                                     relation_type='N',
                                     relation_length=rel_time,
                                     relation_creation_tick=RoundStatus.objects.get().tick_number,
                                     relation_remaining_time=rel_time)
            News.objects.create(empire1=current_empire,
                                empire2=target_empire,
                                news_type='RND',
                                date_and_time=datetime.datetime.now() + timedelta(seconds=1),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
            rel.relation_type = 'N'
            rel.save()
        else:
            # make a nap offer from current_empire to target_empire
            Relations.objects.create(empire1=current_empire,
                                     empire2=target_empire,
                                     relation_type='NO',
                                     relation_length=rel_time,
                                     relation_creation_tick=RoundStatus.objects.get().tick_number,
                                     relation_remaining_time=rel_time)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def cancel_relation(request, rel):
    try:
        rel2 = Relations.objects.get(empire1=rel.empire2, empire2=rel.empire1)
    except ObjectDoesNotExist:
        rel2 = None

    if rel.relation_type == 'AO' or rel.relation_type == 'NO' or rel.relation_type == 'CO':
        rel.delete()
    elif rel.relation_type == 'A' or rel.relation_type == 'W':
        if rel.relation_type == 'A':
            rel2.relation_type = 'AO'
            rel2.save()
        if RoundStatus.objects.get().tick_number - rel.relation_creation_tick > min_relation_time:
            rel.delete()
    elif rel.relation_length is not None:
        # cancel timed nap for both empires, any empire of two can trigger this
        # this will be cancelled in process_tick when the right time comes
        rel.relation_type = 'NC'
        rel.relation_cancel_tick = RoundStatus.objects.get().tick_number
        rel2.relation_type = 'NC'
        rel2.relation_cancel_tick = RoundStatus.objects.get().tick_number
        rel.save()
        rel2.save()
    else:
        # if this is a permanent NAP both parties need to cancel it for it to be deleted
        if rel2.relation_type == 'PC':
            rel.delete()
            rel2.delete()
        else:
            rel.relation_type = 'PC'
            rel.save()


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def pm_options(request):
    status = get_object_or_404(UserStatus, user=request.user)
    user_empire = status.empire
    relation_empires = Relations.objects.filter(empire1=status.empire)
    error = None
    msg = ""
    player_list = UserStatus.objects.filter(empire=status.empire)

    roundstat = RoundStatus.objects.get().tick_number
    if request.method == 'POST':
        print(request.POST)
        
        if request.FILES:
            if user_empire.empire_image is not None:
                user_empire.empire_image.delete(save=True)
            picture = request.FILES['empire_picture']
            user_empire.empire_image = picture
            user_empire.save()

        user_empire.name = request.POST['empire_name']
        user_empire.name_with_id = request.POST['empire_name'] + " #" + str(user_empire.number)
        user_empire.password = request.POST['empire_pass']
        user_empire.pm_message = (request.POST['empire_pm_message'])
        user_empire.relations_message = (request.POST['empire_relations_message'])
        
        if request.POST['empire_offer_alliance']:
            target_empire = Empire.objects.get(number=int(request.POST['empire_offer_alliance']))
            set_relation(request, 'ally', status.empire, target_empire)
            News.objects.create(empire1=status.empire,
                                empire2=target_empire,
                                news_type='RAP',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
        elif request.POST['empire_offer_nap']:
            target_empire = Empire.objects.get(number=int(request.POST['empire_offer_nap']))
            time = request.POST['naphr']
            n_extra = None
            if time == "tf":
                time = 144
                n_extra = "24 hour"
            elif time == "fe":
                time = 288
                n_extra = "48 hour"
            elif time == "tw":
                time = 72
                n_extra = "12 hour"
            
            Relations.objects.create(empire1=status.empire,
                                    empire2=target_empire,
                                    relation_type="NO",
                                    relation_length=time,
                                    relation_remaining_time=time)

            News.objects.create(empire1=status.empire,
                                empire2=target_empire,
                                news_type='RNP',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        elif request.POST['empire_offer_cf']:
            target_empire = Empire.objects.get(number=int(request.POST['empire_offer_cf']))
            time = request.POST['cfhr']
            n_extra = None
            if time == "tf":
                time = 144
                n_extra = "24 hour"
            elif time == "fe":
                time = 288
                n_extra = "48 hour"
            elif time == "tw":
                time = 72
                n_extra = "12 hour"
            
            Relations.objects.create(empire1=status.empire,
                                    empire2=target_empire,
                                    relation_type="CO",
                                    relation_length=time,
                                    relation_remaining_time=time)

            News.objects.create(empire1=status.empire,
                                empire2=target_empire,
                                news_type='RCP',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        elif request.POST['empire_cancel_relation']:
            relation = request.POST['empire_cancel_relation']
            try:
                rel = Relations.objects.get(id=relation)
            except ObjectDoesNotExist:
                rel = None
            if rel:
                if rel.empire1 == status.empire:
                    target_empire = rel.empire2
                else:
                    target_empire = rel.empire1

                if (rel.relation_type == 'A' or rel.relation_type == 'W') and RoundStatus.objects.get().tick_number - rel.relation_creation_tick <= min_relation_time:
                    error = "You can't cancel the relation for " + str(min_relation_time) + " ticks after creating it!"
                elif rel.relation_type == 'C':
                    error = "You cannot cancel a Ceasefire!"
                else:
                    n_type = 'N'
                    if rel.relation_type == 'W':
                        n_type = 'RWE'
                    elif rel.relation_type == 'A':
                        n_type = 'RAE'
                    elif rel.relation_type == 'N':
                        n_type = 'RNE'
                    
                    cancel_relation(request, rel)
                    News.objects.create(empire1=status.empire,
                                        empire2=target_empire,
                                        news_type=n_type,
                                        date_and_time=datetime.datetime.now(),
                                        is_personal_news=False,
                                        is_empire_news=True,
                                        tick_number=RoundStatus.objects.get().tick_number
                                        )
        elif request.POST['empire_declare_war']:
            target_empire = Empire.objects.get(number=int(request.POST['empire_declare_war']))
            attacker_size = Empire.objects.get(id=status.empire.id)
            defender_size = Empire.objects.get(id=target_empire.id)
            if defender_size.planets / attacker_size.planets < 0.6:
            	msg = "You cannot declare war on an empire less than 60% of your size!"
            
            elif roundstat < 1008:
                msg = "Peace for " + str(1008 - roundstat) + " weeks!"
            else:
                set_relation(request, 'war', status.empire, target_empire)
                News.objects.create(empire1=status.empire,
                                    empire2=target_empire,
                                    news_type='RWD',
                                    date_and_time=datetime.datetime.now(),
                                    is_personal_news=False,
                                    is_empire_news=True,
                                    tick_number=RoundStatus.objects.get().tick_number
                                    )
        
        elif request.POST['role']:
            stat2 = request.POST.get('player', False)
            if stat2:
                status2 = UserStatus.objects.get(id=stat2)
                emprole = request.POST.get('role')
            
                if emprole == "VM":    
                    status2.empire_role = "VM"
                    status2.save()
                if emprole == "P":    
                    status2.empire_role = "P"
                    status2.save()
                if emprole == "I":    
                    status2.empire_role = "I"
                    status2.save()
        
        
        user_empire.save()
    
        
    
        
    context = {"status": status,
               "round": roundstat,
               "page_title": "Prime Minister options",
               "empire": status.empire,
               "relation_empires": relation_empires,
               "msg": msg,
               'error': error,
               "player_list": player_list}
    return render(request, "pm_options.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def relations(request):
    status = get_object_or_404(UserStatus, user=request.user)
    relations_from_empire = Relations.objects.filter(empire1=status.empire).order_by('-relation_creation_tick')
    if status.id == 1:
        relations_from_empire = Relations.objects.all().order_by('-relation_creation_tick')
    relations_to_empire = Relations.objects.filter(empire2=status.empire).order_by('-relation_creation_tick')
    tick_time = RoundStatus.objects.get().tick_number
    
    if 'accept' in request.POST:
        rel = request.POST.get('acc_nap', False)
        rela = Relations.objects.get(id=rel)
        rela.relation_type = "N"
        rela.save()
        oth_emp = rela.empire1
        if rela.empire1 == status.empire:
            oth_emp == rela.empire2
        n_time = round(rela.relation_length / 6)
        n_extra = str(n_time) + " hour"
        News.objects.create(empire1=status.empire,
                                empire2=oth_emp,
                                news_type='RND',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        News.objects.create(empire1=oth_emp,
                                empire2=status.empire,
                                news_type='RND',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        if Relations.objects.filter(empire1=rela.empire1, empire2=rela.empire2, relation_type='W'):
            Relations.objects.filter(empire1=rela.empire1, empire2=rela.empire2, relation_type='W').delete()
        if Relations.objects.filter(empire1=rela.empire2, empire2=rela.empire1, relation_type='W'):
            Relations.objects.filter(empire1=rela.empire2, empire2=rela.empire1, relation_type='W').delete()
    elif 'acceptcf' in request.POST:
        rel = request.POST.get('acc_cf', False)
        rela = Relations.objects.get(id=rel)
        rela.relation_type = "C"
        rela.save()
        oth_emp = rela.empire1
        if rela.empire1 == status.empire:
            oth_emp == rela.empire2
        n_time = round(rela.relation_length / 6)
        n_extra = str(n_time) + " hour"
        News.objects.create(empire1=status.empire,
                                empire2=oth_emp,
                                news_type='RCD',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        News.objects.create(empire1=oth_emp,
                                empire2=status.empire,
                                news_type='RCD',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number,
                                extra_info=n_extra
                                )
        if Relations.objects.filter(empire1=rela.empire1, empire2=rela.empire2, relation_type='W'):
            Relations.objects.filter(empire1=rela.empire1, empire2=rela.empire2, relation_type='W').delete()
        if Relations.objects.filter(empire1=rela.empire2, empire2=rela.empire1, relation_type='W'):
            Relations.objects.filter(empire1=rela.empire2, empire2=rela.empire1, relation_type='W').delete()
    elif 'cancel' in request.POST:
        rel = request.POST.get('can_nap', False)
        rela = Relations.objects.get(id=rel)
        rela.relation_type = "NC"
        rela.save()
        oth_emp = rela.empire1
        if rela.empire1 == status.empire:
            oth_emp == rela.empire2
        News.objects.create(empire1=status.empire,
                                empire2=oth_emp,
                                news_type='RNE',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
        News.objects.create(empire1=oth_emp,
                                empire2=status.empire,
                                news_type='RNE',
                                date_and_time=datetime.datetime.now(),
                                is_personal_news=False,
                                is_empire_news=True,
                                tick_number=RoundStatus.objects.get().tick_number
                                )
    
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Relations",
               "relations_from_empire": relations_from_empire,
               "relations_to_empire": relations_to_empire,
               "empire": status.empire,
               "tick_time": tick_time}
    return render(request, "relations.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def research(request):
    status = get_object_or_404(UserStatus, user=request.user)
    message = ''
    race_info = race_info_list[status.get_race_display()]
    calcs = {"calc": 'None', "milpoints":'', "rpmil": '', "conpoints":'', "rpcon":'', "techpoints":'', "rptech":'', "nrgpoints":'', "rpnrg":'', "poppoints":'', "rppop":'', "culpoints":'', "rpcul":'', "opspoints":'', "rpops":'', "portpoints":'', "rpport":''}
    wks = 0
    print(request.POST)
    if request.method == 'POST':
        if 'fund_form' in request.POST:
            if request.POST['fund']:
                if status.energy >= int(request.POST['fund']):
                    status.energy -= int(request.POST['fund'])
                    status.current_research_funding += int(request.POST['fund'])
                    message = request.POST['fund'] + " energy was funded!"
                    status.save()
                else:
                    message = "You don't have so much energy!"
        if 'rc_alloc_form' in request.POST:
            total = 0
            for a, key in enumerate(request.POST.items()):
                if a > 0 and key[0] != 'rc_alloc_form':
                    print("key", a, key[1])
                    if key[1] != '':
                        total += int(key[1])
            if total != 100:
                message = "Research allocation percentages must be equal to 100% in total!"
            else:
                if request.POST['military'] != '':
                    status.alloc_research_military = request.POST['military']
                else:
                    status.alloc_research_military = 0
                if request.POST['construction'] != '':
                    status.alloc_research_construction = request.POST['construction']
                else:
                    status.alloc_research_construction = 0
                if request.POST['technology'] != '':
                    status.alloc_research_tech = request.POST['technology']
                else:
                    status.alloc_research_tech = 0
                if request.POST['energy'] != '':
                    status.alloc_research_energy = request.POST['energy']
                else:
                    status.alloc_research_energy = 0
                if request.POST['population'] != '':
                    status.alloc_research_population = request.POST['population']
                else:
                    status.alloc_research_population = 0
                if request.POST['culture'] != '':    
                    status.alloc_research_culture = request.POST['culture']
                else:
                    status.alloc_research_culture = 0
                if request.POST['operations'] != '':    
                    status.alloc_research_operations = request.POST['operations']
                else:
                    status.alloc_research_operations = 0
                if request.POST['portals'] != '':
                    status.alloc_research_portals = request.POST['portals']
                else:
                    status.alloc_research_portals = 0
                status.save()
        if 'rc_calc_form' in request.POST:
            rc = status.total_research_centers * 6 * 1.2
            arterl = Artefacts.objects.get(name="Research Laboratory")
            if arterl.empire_holding == status.empire:
                rc * 1.1
            wks = int(request.POST['weeks'])
            fund = status.current_research_funding
            fpoints = 0
            if fund > 9 and wks > 0:
                for _ in range(wks):
                    fpoints += round(fund/100)
                    fund = (fund * 9) /10
            mil = (rc * (status.alloc_research_military / 100)) * race_info["research_bonus_military"] 
            if status.race == "FH":
                mil += (status.population / 6000) * status.alloc_research_military / 100
            if status.race == "JK":
                mil += (status.population / 10000) * status.alloc_research_military / 100
            pwmil = mil
            mil *= wks
            mil += status.research_points_military 
            if wks > 0:
                pwmil += ((fpoints * (status.alloc_research_military / 100) * race_info["research_bonus_military"]) / wks)
                mil += (fpoints * (status.alloc_research_military/ 100) * race_info["research_bonus_military"])
            con = (rc * (status.alloc_research_construction / 100)) * race_info["research_bonus_construction"] 
            if status.race == "FH":
                con += (status.population / 6000) * status.alloc_research_construction / 100
            if status.race == "JK":
                con += (status.population / 10000) * status.alloc_research_construction / 100
            pwcon = con 
            con *= wks
            con += status.research_points_construction 
            if wks > 0:
                pwcon += ((fpoints * (status.alloc_research_construction / 100) * race_info["research_bonus_construction"] ) / wks)
                con += (fpoints * (status.alloc_research_construction/ 100) * race_info["research_bonus_construction"] )
            tech = (rc * (status.alloc_research_tech / 100)) * race_info["research_bonus_tech"] 
            if status.race == "FH":
                tech += (status.population / 6000) * status.alloc_research_tech / 100
            if status.race == "JK":
                tech += (status.population / 10000) * status.alloc_research_tech / 100
            pwtech = tech
            tech *= wks
            tech += status.research_points_tech
            if wks > 0:
                pwtech += ((fpoints * (status.alloc_research_tech / 100) * race_info["research_bonus_tech"] ) / wks)
                tech += (fpoints * (status.alloc_research_tech/ 100) * race_info["research_bonus_tech"] )
            nrg = (rc * (status.alloc_research_energy / 100)) * race_info["research_bonus_energy"] 
            if status.race == "FH":
                nrg += (status.population / 6000) * status.alloc_research_energy / 100
            if status.race == "JK":
                nrg += (status.population / 10000) * status.alloc_research_energy / 100
            pwnrg = nrg
            nrg *= wks
            nrg += status.research_points_energy
            if wks > 0:
                pwnrg += ((fpoints * (status.alloc_research_energy / 100) * race_info["research_bonus_energy"]) / wks)
                nrg += (fpoints * (status.alloc_research_energy/ 100) * race_info["research_bonus_energy"])
            pop = (rc * (status.alloc_research_population / 100)) * race_info["research_bonus_population"] 
            if status.race == "FH":
                pop += (status.population / 6000) * status.alloc_research_population / 100
            if status.race == "JK":
                pop += (status.population / 10000) * status.alloc_research_population / 100
            rabbit = Artefacts.objects.get(name="Rabbit Theorum")
            if rabbit.empire_holding == status.empire:
                pop *= 1 + (rabbit.effect1 /100)
            pwpop = pop
            pop *= wks
            pop += status.research_points_population 
            if wks > 0:
                pwpop += ((fpoints * (status.alloc_research_population/ 100) * race_info["research_bonus_population"]) / wks)
                pop += (fpoints * (status.alloc_research_population/ 100) * race_info["research_bonus_population"])
            cul = (rc * (status.alloc_research_culture / 100)) * race_info["research_bonus_culture"] 
            if status.race == "FH":
                cul += (status.population / 6000) * status.alloc_research_culture / 100
            if status.race == "JK":
                cul += (status.population / 10000) * status.alloc_research_culture / 100
            pwcul = cul 
            cul *= wks
            cul += status.research_points_culture
            if wks > 0:
                pwcul += ((fpoints * (status.alloc_research_culture / 100) * race_info["research_bonus_culture"] ) / wks)
                cul += (fpoints * (status.alloc_research_culture/ 100) * race_info["research_bonus_culture"] )
            ops = (rc * (status.alloc_research_operations / 100)) * race_info["research_bonus_operations"] 
            if status.race == "FH":
                ops += (status.population / 6000) * status.alloc_research_operations / 100
            if status.race == "JK":
                ops += (status.population / 10000) * status.alloc_research_operations / 100
            pwops = ops
            ops *= wks
            ops += status.research_points_operations
            if wks > 0:
                pwops += ((fpoints * (status.alloc_research_operations / 100) * race_info["research_bonus_operations"] ) / wks)
                ops += (fpoints * (status.alloc_research_operations/ 100) * race_info["research_bonus_operations"] )
            port = (rc * (status.alloc_research_portals / 100)) * race_info["research_bonus_portals"] 
            if status.race == "FH":
                port += (status.population / 6000) * status.alloc_research_portals / 100
            if status.race == "JK":
                port += (status.population / 10000) * status.alloc_research_portals / 100
            quantum = Artefacts.objects.get(name="Playboy Quantum")
            if quantum.empire_holding == status.empire:
                port *= 1 + (quantum.effect1/100)
            pwpor = port
            port *= wks
            port += status.research_points_portals
            if wks > 0:
                pwpor += ((fpoints * (status.alloc_research_portals / 100) * race_info["research_bonus_portals"] ) / wks)
                port += (fpoints * (status.alloc_research_portals/ 100) * race_info["research_bonus_portals"] )
            
            netw = status.networth
            netw += (rc+fpoints) * 0.002
            
            rpmil = int(race_info.get("research_max_military") * (1.0-np.exp(mil / (-10.0 * netw))))
            if status.race == "DW":
                rpmil = min(100, int(200* (1.0-np.exp(mil / (-10.0 * netw)))))
            if rpmil - status.research_percent_military > wks:
                rpmil = status.research_percent_military + wks
            rpcon = int(race_info.get("research_max_construction") * (1.0-np.exp(con / (-10.0 * netw))))
            if rpcon - status.research_percent_construction > wks:
                rpcon = status.research_percent_construction + wks
            rptech = int(race_info.get("research_max_tech") * (1.0-np.exp(tech / (-10.0 * netw))))
            if rptech - status.research_percent_tech > wks:
                rptech = status.research_percent_tech + wks
            rpnrg = int(race_info.get("research_max_energy") * (1.0-np.exp(nrg / (-10.0 * netw))))
            if rpnrg - status.research_percent_energy > wks:
                rpnrg = status.research_percent_energy + wks
            rppop = int(race_info.get("research_max_population") * (1.0-np.exp(pop / (-10.0 * netw))))
            if rppop - status.research_percent_population > wks:
                rppop = status.research_percent_population + wks
            rpcul = int(race_info.get("research_max_culture") * (1.0-np.exp(cul / (-10.0 * netw))))
            if rpcul - status.research_percent_culture > wks:
                rpcul = status.research_percent_culture + wks
            rpops= int(race_info.get("research_max_operations") * (1.0-np.exp(ops / (-10.0 * netw))))
            if rpops - status.research_percent_operations > wks:
                rpops = status.research_percent_operations + wks
            if quantum.empire_holding == status.empire:
                rpport = int((race_info.get("research_max_portals") + quantum.effect2) * (1.0-np.exp(port / (-10.0 * netw))))
            else:
                rpport = int(race_info.get("research_max_portals") * (1.0-np.exp(port / (-10.0 * netw))))
            if rpport - status.research_percent_portals > wks:
                rpport = status.research_percent_portals + wks
            
            calcs = {"calc": 1,
                     "milpoints":round(mil),
                     "rpmil":round(rpmil),
                     "conpoints":round(con),
                     "rpcon":round(rpcon),                     
                     "techpoints":round(tech),
                     "rptech":round(rptech),
                     "nrgpoints":round(nrg),
                     "rpnrg":round(rpnrg),
                     "poppoints":round(pop),
                     "rppop":round(rppop),
                     "culpoints":round(cul),
                     "rpcul":round(rpcul),
                     "opspoints":round(ops),
                     "rpops":round(rpops),
                     "portpoints":round(port),
                     "rpport":round(rpport),
                     "pwmil":round(pwmil),
                     "pwcon":round(pwcon),
                     "pwtech":round(pwtech),
                     "pwnrg":round(pwnrg),
                     "pwpop":round(pwpop),
                     "pwcul":round(pwcul),
                     "pwops":round(pwops),
                     "pwpor":round(pwpor),} 
            
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Research",
               "calcs": calcs,
               "wks": wks,
               "message": message}
    return render(request, "research.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def specops(request, *args):
    status = get_object_or_404(UserStatus, user=request.user)
    race_ops = race_display_list[status.get_race_display()]["op_list"]
    race_spells = race_display_list[status.get_race_display()]["spell_list"]
    race_inca = race_display_list[status.get_race_display()]["incantation_list"]
    
    user_to_template_specop = None
    planet_to_template_specop = None
    specop_planet_id = None
    specop_u_id = None
    error = None
    if 'error' in request.session:
        error = request.session['error']
        request.session['error'] = None
    if 'specop_planet_id' in request.session:
        specop_planet_id = request.session['specop_planet_id']
        request.session['specop_planet_id'] = None
    if 'specop_u_id' in request.session:
        specop_u_id = request.session['specop_u_id']
        request.session['specop_u_id'] = None
    
    if specop_planet_id != None:
        planet_to_template_specop = Planet.objects.get(id=specop_planet_id)
    
    if specop_u_id != None:
        user_to_template_specop = UserStatus.objects.get(id=specop_u_id)
    
    if request.method == 'POST' and 'specop_planet' in request.POST:
        try:
            pl_id = request.POST.get('specop_planet')
            planet_to_template_specop = Planet.objects.get(id=pl_id)
        except Planet.DoesNotExist:
            planet_to_template_specop = None
    
    if planet_to_template_specop is not None:
        if planet_to_template_specop.owner is not None:
            user_to_template_specop = (UserStatus.objects.get(id=planet_to_template_specop.owner.id))

    off_ops = ["Irradiate Ectrolium",
                "Black Mist", 
                "Psychic Assault", 
                "Network Infiltration", 
                "Bio Infection",
                "Hack mainframe",
                "Bribe officials",
                "Military Sabotage",
                "Nuke Planet",
                "Mind Control", 
                "Energy Surge"]

    roundstatus = RoundStatus.objects.filter().first()
    
    #Round Special, steal resources
    if roundstatus.tick_number >= 1008:
        race_ops.append("Steal Resources")
    
    # artis
    robo = Artefacts.objects.get(name="Advanced Robotics")
    cloak = Artefacts.objects.get(name="Magus Cloak")
    alch = Artefacts.objects.get(name="Alchemist")
    maryc = Artefacts.objects.get(name="Mary Celeste")
    
    ops = {}
    for o in Ops.objects.filter(specop_type="O"):
        if roundstatus.tick_number < 1008 and o.name not in off_ops or roundstatus.tick_number >= 1008:
            if o.name in race_ops:
                if user_to_template_specop:
                    fr = specopReadiness(o.name, "Op", status, user_to_template_specop)
                else:
                    fr = None
                if robo.empire_holding == status.empire:
                    tech = get_op_penalty(status.research_percent_operations, (o.tech/2))
                else:
                    tech = get_op_penalty(status.research_percent_operations, o.tech)
                ops[o.name] = [o.tech,o.readiness,o.difficulty,o.stealth,o.ident,o.description,fr,tech]

    spells = {}    
    for s in Ops.objects.filter(specop_type="S"):
        if s.name == "Alchemist" and alch.empire_holding == status.empire:
            if cloak.empire_holding == status.empire:
                b_cost = int(s.readiness * (1-(cloak.effect1/100)))
            else:
                b_cost = s.readiness
            spells[s.name] = [s.tech,b_cost,s.difficulty,s.selfsp,s.ident,s.description,None,s.tech]
        elif s.name != "Alchemist":
            if roundstatus.tick_number < 1008 and s.name not in off_ops or roundstatus.tick_number >= 1008:
                if s.name in race_spells:
                    if cloak.empire_holding == status.empire and s.selfsp == True:
                        b_cost = int(s.readiness * (1-(cloak.effect1/100)))
                    else:
                        b_cost = s.readiness            
                    if user_to_template_specop:
                        fr = specopReadiness(s.name, "Spell", status, user_to_template_specop)
                    else:
                        fr = None
                    if robo.empire_holding == status.empire:
                        tech = get_op_penalty(status.research_percent_culture, (s.tech/2))
                    else:
                        tech = get_op_penalty(status.research_percent_culture, s.tech)
                    spells[s.name] = [s.tech,b_cost,s.difficulty,s.selfsp,s.ident,s.description,fr,tech]
                elif cloak.empire_holding == status.empire and s.selfsp == True:
                    b_cost = int(s.readiness * (1-(cloak.effect1/100)))           
                    if user_to_template_specop:
                        fr = specopReadiness(s.name, "Spell", status, user_to_template_specop)
                    else:
                        fr = None
                    if robo.empire_holding == status.empire:
                        tech = get_op_penalty(status.research_percent_culture, (s.tech/2))
                    else:
                        tech = get_op_penalty(status.research_percent_culture, s.tech)
                    spells[s.name] = [s.tech,b_cost,s.difficulty,s.selfsp,s.ident,s.description,fr,tech]
    
    inca_ops = {}
    if maryc.empire_holding == status.empire:
        for g in Ops.objects.filter(specop_type="G"):
            inca_ops[g.name] = [g.name]
    else:
        inca_ops = race_inca
    inca = {}
    for g in Ops.objects.filter(specop_type="G"):
        if roundstatus.tick_number < 1008 and g.name not in off_ops or roundstatus.tick_number >= 1008:
            if g.name in inca_ops:
                if g.name == "Sense Artefact" and Artefacts.objects.filter(on_planet__isnull=False).count() == 0:
                    continue
                else:
                    if user_to_template_specop:
                        fr = specopReadiness(g.name, "Inca", status, user_to_template_specop)
                    else:
                        fr = None
                    if robo.empire_holding == status.empire:
                        tech = get_op_penalty(status.research_percent_operations, (g.tech/2))
                    else:
                        tech = get_op_penalty(status.research_percent_operations, g.tech)
                    inca[g.name] = [g.tech,g.readiness,g.difficulty,g.stealth,g.ident,g.description,fr,tech]
                
    
    msg = ""
    main_fleet = Fleet.objects.get(owner=status.user.id, main_fleet=True)

    if request.method == 'POST':
        if 'spell' in request.POST and 'unit_ammount' in request.POST:
            sp = Ops.objects.get(name=request.POST['spell'])
            if status.psychic_readiness < 0:
                msg = "You don't have enough psychic readiness to perform this operation!"
            elif int(request.POST['unit_ammount']) > main_fleet.wizard:
                msg = "You don't have that many psychics!"
            else:
                if sp.selfsp is False and request.POST['user_id2'] == "":
                    msg = "You must specify a target player for this spell!"
                else:
                    if psychicop_specs[request.POST['spell']][3] is False:
                        faction, err_msg = get_userstatus_from_id_or_name(request.POST['user_id2'])
                    else:
                        faction = None
                    # if second faction not found and not self spell
                    if faction is None and psychicop_specs[request.POST['spell']][3] is False:
                        msg = err_msg
                    else:
                        request.session['error'] = perform_spell(sp.name, int(request.POST['unit_ammount']), status, faction)
                        if sp.selfsp is False:
                            request.session['specop_u_id'] = faction.id    
                        return redirect(request.META['HTTP_REFERER'])

        print(request.POST)
        if 'operation' in request.POST and 'unit_ammount' in request.POST:
            op = Ops.objects.get(name=request.POST['operation'])
            if int(request.POST['unit_ammount']) > main_fleet.agent:
                msg = "You don't have that many agents!"
            elif request.POST['X'] == "" or request.POST['Y'] == "" or request.POST['I'] == "":
                msg = "You must specify a planet!"
            elif get_op_penalty(status.research_percent_operations, op.tech) == -1:
                msg = "You don't have enough operations research to perform this covert operation!"
            else:
                planet = None
                try:
                    planet = Planet.objects.get(x=request.POST['X'], y=request.POST['Y'], i=request.POST['I'])
                except Planet.DoesNotExist:
                    msg = "This planet doesn't exist"
                if planet:
                    request.session['error'] = "Agents sent! \n" + send_agents_ghosts(status, int(request.POST['unit_ammount']), 0,
                                             request.POST['X'], request.POST['Y'], request.POST['I'],
                                             request.POST['operation'])
                    request.session['specop_planet_id'] = planet.id    
                    return redirect(request.META['HTTP_REFERER'])

        if 'agent_select' in request.POST:
            agent_select = request.POST.getlist('agent_select')
            for agent_id in agent_select:
                # TODO remake later to 1 function
                speed = travel_speed(status)
                agent_fleet = Fleet.objects.get(id=agent_id)
                portal_planets = Planet.objects.filter(owner=request.user, portal=True)
                portal = find_nearest_portal(agent_fleet.current_position_x, agent_fleet.current_position_y,
                                             portal_planets, status)
                generate_fleet_order(agent_fleet, portal.x, portal.y, speed, 5)
                main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
                fleets_id3 = Fleet.objects.filter(id=agent_id, ticks_remaining__lt=1)
                join_main_fleet(main_fleet, fleets_id3)
                msg = "Agents returned"
        print(request.POST)        
        if 'incantation' in request.POST and 'unit_ammount' in request.POST:
            op = Ops.objects.get(name=request.POST['incantation'])
            if int(request.POST['unit_ammount']) > main_fleet.ghost:
                msg = "You don't have that many ghost ships!"
            elif request.POST['X'] == "" or request.POST['Y'] == "" and request.POST['I'] == "":
                msg = "You must specify a planet!"
            elif get_op_penalty(status.research_percent_culture, op.tech) == -1:
                msg = "You don't have enough culture research to perform this incantation!"
            else:
                planet = None
                try:
                    planet = Planet.objects.get(x=request.POST['X'], y=request.POST['Y'], i=request.POST['I'])
                except Planet.DoesNotExist:
                    msg = "This planet doesn't exist"
                if planet:
                    request.session['error'] = "Ghost Ships sent! \n" + send_ghosts(status, 0, int(request.POST['unit_ammount']),
                                             planet.x, planet.y, planet.i, request.POST['incantation'])
                    request.session['specop_planet_id'] = planet.id    
                    return redirect(request.META['HTTP_REFERER'])
                    
        if 'ghost_select' in request.POST:
            ghost_select = request.POST.getlist('ghost_select')
            for ghost_id in ghost_select:
                speed = travel_speed(status)
                ghost_fleet = Fleet.objects.get(id=ghost_id)
                portal_planets = Planet.objects.filter(owner=request.user, portal=True)
                portal = find_nearest_portal(ghost_fleet.current_position_x, ghost_fleet.current_position_y,
                                             portal_planets, status)
                generate_fleet_order(ghost_fleet, portal.x, portal.y, speed, 5)
                main_fleet = Fleet.objects.get(owner=request.user, main_fleet=True)
                fleets_id3 = Fleet.objects.filter(id=ghost_id, ticks_remaining__lt=1)
                join_main_fleet(main_fleet, fleets_id3)
                msg = "Ghost ships returned"
                
        print(request.POST)
    agent_fleets = Fleet.objects.filter(owner=status.user, agent__gt=0, main_fleet=False)
    ghost_fleets = Fleet.objects.filter(owner=status.user, ghost__gt=0, main_fleet=False)
    ops_in = Specops.objects.filter(user_to=status.user, specop_type='O').exclude(name="Diplomatic Espionage", stealth=True)
    ops_out = Specops.objects.filter(user_from=status.user, specop_type='O')
    spells_in = Specops.objects.filter(user_to=status.user, specop_type='S', stealth=False)
    spells_out = Specops.objects.filter(user_from=status.user, specop_type='S')
    inca_in = Specops.objects.filter(user_to=status.user, specop_type='G', stealth=False).exclude(name='Planetary Shielding')
    inca_out = Specops.objects.filter(user_from=status.user, specop_type='G')
    
    planets = Planet.objects.filter(owner=status.user)
    p_shields = Specops.objects.filter(name='Planetary Shielding', specop_type='G', planet__in=planets)
    inca_in = inca_in|p_shields
    o_shields = Specops.objects.filter(user_to=status.user, name='Planetary Shielding', specop_type='G').exclude(planet__in=planets)
    inca_out = inca_out|o_shields

    template_name = None
    if user_to_template_specop is not None:
        template_name = user_to_template_specop.user_name

    bare = "No"
    if args:
        bare = "Yes"

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Special Operations",
               "operations": ops,
               "spells": spells,
               "incantations": inca,
               "msg": msg,
               "main_fleet": main_fleet,
               "agent_fleets": agent_fleets,
               "ghost_fleets": ghost_fleets,
               "ops_out": ops_out,
               "ops_in": ops_in,
               "error": error,
               "spells_in": spells_in,
               "spells_out": spells_out,
               "inca_out": inca_out,
               "inca_in": inca_in,
               "bare": bare,
               "planet_to_template_specop": planet_to_template_specop,
               "user_to_template_specop": template_name,}
    
    return render(request, "specops.html", context)

@xframe_options_exempt
@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def specs(request):
    
    return specops(request, "short")


def ops(request):
    ops = {}
    for o in Ops.objects.filter(specop_type="O"):
        ops[o.name] = [o.tech,o.readiness,o.difficulty,o.stealth,o.description]

    spells = {}
    for o in Ops.objects.filter(specop_type="S"):
        spells[o.name] = [o.tech,o.readiness,o.difficulty,o.selfsp,o.description]

    inca = {}
    for o in Ops.objects.filter(specop_type="G"):
        inca[o.name] = [o.tech,o.readiness,o.difficulty,o.stealth,o.description]
    context = {"operations": ops,
               "spells": spells,
               "incantations": inca,
               "page_title": "Special Operations Information"
               }
    return render(request, "ops.html", context)

@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def specop_show(request, specop_id):
    status = get_object_or_404(UserStatus, user=request.user)
    specop = Specops.objects.get(id=specop_id)
    specop_info = ""
    if specop.name == "Diplomatic Espionage":
        specops_affecting_target = Specops.objects.filter(user_to=specop.user_to)
        specops_from_target = Specops.objects.filter(user_from=specop.user_to)
        spec_dict = Specops.objects.filter(user_to=specop.user_to).values_list("id", flat=True)
        for s in specops_affecting_target:
            specop_info += "Specop: " + str(s.name)
            specop_info += " Time remaining: " + str(s.ticks_left)
            if s.specop_strength > 0:
                specop_info += " Strength: " + str(s.specop_strength)
            if s.extra_effect is not None:
                specop_info += " Extra effect: " + str(s.extra_effect)
            if s.user_from != s.user_to:
                specop_info += " From: " + str(s.user_from.userstatus.user_name)
            specop_info += "\n"
        for s in specops_from_target:
            if s.id not in spec_dict:
                specop_info += "Specop: " + str(s.name)
                specop_info += " Time remaining: " + str(s.ticks_left)
                if s.specop_strength > 0:
                    specop_info += " Strength: " + str(s.specop_strength)
                if s.extra_effect is not None:
                    specop_info += " Extra effect: " + str(s.extra_effect)
                if s.user_to != s.user_from:
                    specop_info += " To: " + str(s.user_to.userstatus.user_name)
                specop_info += "\n"
    planets = None
    target_player = UserStatus.objects.get(user=specop.user_to)
    fleets = None
    if specop.name == "High Infiltration":
        if specop.specop_strength >= 1.5:
            planets = Planet.objects.filter(owner=specop.user_to)
            for p in planets:
                scouting = Scouting.objects.filter(planet=p, empire=status.empire).first()
                if scouting is None:
                    Scouting.objects.create(user=specop.user_from, planet=p, empire=status.empire, scout=1)
                elif scouting.scout < 1:
                    scouting.scout = 1
                    scouting.save()
        if specop.specop_strength >= 2.0:
            fleets = Fleet.objects.filter(owner=specop.user_to)

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": specop.name,
               "specop_info": specop_info,
               "planets": planets,
               "fleets": fleets,
               "target_player": target_player
               }
    return render(request, "specop_show.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def famaid(request):
    status = get_object_or_404(UserStatus, user=request.user)
    player_list = UserStatus.objects.filter(empire=status.empire)
    num_players = len(player_list)
    message = ''
    news_message = ''
    use1 = ''
    use2 = ''
    if request.method == 'POST':
        round = RoundStatus.objects.get()
        if round.tick_number > 0:
            status2 = get_object_or_404(UserStatus, user=request.POST['player'])
            total = 0
            if request.POST['energy']:
                e = int(request.POST['energy'])
                if e > status.energy:
                    message += "You don't have so much energy!<br>"
                else:
                    use1 += "Pre: " + str(status.energy)
                    use2 += "Pre: " + str(status2.energy)
                    status.energy -= e
                    status2.energy += e
                    message += str(e) + " Energy was transferred!<br>"
                    news_message += str(e) + " energy "
                    use1 += ", Post: " + str(status.energy)
                    use2 += ", Post: " + str(status2.energy)
                    total += e
            if request.POST['minerals']:
                m = int(request.POST['minerals'])
                if m > status.minerals:
                    message += "You don't have so much minerals!<br>"
                else:
                    use1 += "Pre: " + str(status.minerals)
                    use2 += "Pre: " + str(status2.minerals)
                    status.minerals -= m
                    status2.minerals += m
                    message += str(m) + " Minerals was transferred!<br>"
                    news_message += str(m) + " minerals "
                    use1 += ", Post: " + str(status.minerals)
                    use2 += ", Post: " + str(status2.minerals)
                    total += m
            if request.POST['crystals']:
                c = int(request.POST['crystals'])
                if c > status.crystals:
                    message += "You don't have so much crystals!<br>"
                else:
                    use1 += "Pre: " + str(status.crystals)
                    use2 += "Pre: " + str(status2.crystals)
                    status.crystals -= c
                    status2.crystals += c
                    message += str(c) + " Crystals was transferred!<br>"
                    news_message += str(c) + " crystals "
                    use1 += ", Post: " + str(status.crystals)
                    use2 += ", Post: " + str(status2.crystals)
                    total += c
            if request.POST['ectrolium']:
                e = int(request.POST['ectrolium'])
                if e > status.ectrolium:
                    message += "You don't have so much ectrolium!<br>"
                else:
                    use1 += "Pre: " + str(status.ectrolium)
                    use2 += "Pre: " + str(status2.ectrolium)
                    status.ectrolium -= e
                    status2.ectrolium += e
                    message += str(e) + " Ectrolium was transferred!<br>"
                    news_message += str(e) + " ectrolium "
                    use1 += ", Post: " + str(status.ectrolium)
                    use2 += " ,Post: " + str(status2.ectrolium)
                    total += e
            if total > 0:
                News.objects.create(user1=request.user,
                                    user2=status2.user,
                                    empire1=status.empire,
                                    news_type='SI',
                                    date_and_time=datetime.datetime.now(),
                                    is_personal_news=True,
                                    is_empire_news=True,
                                    extra_info=news_message,
                                    fleet1=use1,
                                    fleet2=use2,
                                    tick_number=RoundStatus.objects.get().tick_number
                                    )
            
            status.save()
            status2.economy_flag = 1
            status2.save()
        else:
            message = "Aid cannot be sent before round start!"
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "num_players": num_players,
               "page_title": "Send aid",
               "player_list": player_list,
               "message": message}
    return render(request, "famaid.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def famgetaid(request):
    status = get_object_or_404(UserStatus, user=request.user)
    player_list = UserStatus.objects.filter(empire=status.empire)
    num_players = len(player_list)
    message = ''
    news_message = ''
    use1 = ''
    use2 = ''
    if 'receive_aid' in request.POST:
        round = RoundStatus.objects.get()
        if round.tick_number > 0:
            status2 = get_object_or_404(UserStatus, user=request.POST['player'])
            if status2.request_aid == 'A' or (status2.request_aid == 'PM' and status.empire_role == 'PM') or \
                    (status2.request_aid == 'VM' and (status.empire_role == 'PM' or status.empire_role == 'VM')):
                total = 0
                if request.POST['energy']:
                    e = int(request.POST['energy'])
                    if e > status2.energy:
                        message += status2.user_name + " doesn't have so much energy!<br>"
                    else:
                        use1 += "Pre: " + str(status.energy)
                        use2 += "Pre: " + str(status2.energy)
                        status.energy += e
                        status2.energy -= e
                        message += str(e) + " Energy was transferred!<br>"
                        news_message += str(e) + " energy "
                        use1 += ", Post: " + str(status.energy)
                        use2 += ", Post: " + str(status2.energy)
                        total += e
                if request.POST['minerals']:
                    m = int(request.POST['minerals'])
                    if m > status2.minerals:
                        message += status2.user_name + " doesn't have so much minerals!<br>"
                    else:
                        use1 += "Pre: " + str(status.minerals)
                        use2 += "Pre: " + str(status2.minerals)
                        status.minerals += m
                        status2.minerals -= m
                        message += str(m) + " Minerals was transferred!<br>"
                        news_message += str(m) + " minerals "
                        use1 += ", Post: " + str(status.minerals)
                        use2 += ", Post: " + str(status2.minerals)
                        total += m
                if request.POST['crystals']:
                    c = int(request.POST['crystals'])
                    if c > status2.crystals:
                        message += status2.user_name + " doesn't have so much crystals!<br>"
                    else:
                        use1 += "Pre: " + str(status.crystals)
                        use2 += "Pre: " + str(status2.crystals)
                        status.crystals += c
                        status2.crystals -= c
                        message += str(c) + " Crystals was transferred!<br>"
                        news_message += str(c) + " crystals "
                        use1 += ", Post: " + str(status.crystals)
                        use2 += ", Post: " + str(status2.crystals)
                        total += c
                if request.POST['ectrolium']:
                    e = int(request.POST['ectrolium'])
                    if e > status2.ectrolium:
                        message += status2.user_name + " doesn't have so much ectrolium!<br>"
                    else:
                        use1 += "Pre: " + str(status.ectrolium)
                        use2 += "Pre: " + str(status2.ectrolium)
                        status.ectrolium += e
                        status2.ectrolium -= e
                        message += str(e) + " Ectrolium was transferred!<br>"
                        news_message += str(e) + " ectrolium "
                        use1 += ", Post: " + str(status.ectrolium)
                        use2 += ", Post: " + str(status2.ectrolium)
                        total += e
                if total > 0:
                    News.objects.create(user1=status.user,
                                        user2=status2.user,
                                        empire1=status.empire,
                                        news_type='RA',
                                        date_and_time=datetime.datetime.now(),
                                        is_personal_news=True,
                                        is_empire_news=True,
                                        extra_info=news_message,
                                        fleet1=use1,
                                        fleet2=use2,
                                        tick_number=RoundStatus.objects.get().tick_number
                                        )
                status.save()
                status2.economy_flag = 1
                status2.save()
            else:
                message = "You are not authorised to take aid from this faction!"
        else:
            message = "Aid cannot be sent before round start!"
    if 'aid_settings' in request.POST:
        status.request_aid = request.POST['settings']
        message = "Settings changed!"
        status.save()
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "num_players": num_players,
               "page_title": "Receive aid",
               "player_list": player_list,
               "message": message}
    return render(request, "famgetaid.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def game_messages(request):
    status = get_object_or_404(UserStatus, user=request.user)
    messages_from = Messages.objects.filter(user2=status.id, user2_deleted=False).order_by('-date_and_time')
    status.mail_flag = 0
    status.save()
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Inbox",
               "messages_from": messages_from,
               }
    return render(request, "messages.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def outbox(request):
    status = get_object_or_404(UserStatus, user=request.user)
    messages_to = Messages.objects.filter(user1=status.id, user1_deleted=False).order_by('-date_and_time')
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Outbox",
               "messages_to": messages_to,
               }
    return render(request, "outbox.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def compose_message(request, user_id):
    status = get_object_or_404(UserStatus, user=request.user)
    msg_on_top = ''
    user_found = True
    if request.method == 'POST':
        if UserStatus.objects.filter(user_name=request.POST['recipient']).exists():
            status2 = UserStatus.objects.get(user_name=request.POST['recipient'])
        else:
            if UserStatus.objects.filter(id=request.POST['recipient']).exists():
                status2 = UserStatus.objects.get(id=request.POST['recipient'])
            else:
                msg_on_top = 'This player is not found, try again!'
                user_found = False

        if user_found:
            msg = request.POST['message']
            if len(msg) > 0:
                Messages.objects.create(user1=status,
                                        user2=status2,
                                        message=msg,
                                        date_and_time=datetime.datetime.now())
                msg_on_top = 'Message sent!'
                News.objects.create(user1=request.user,
                                    user2=User.objects.get(id=request.POST['recipient']),
                                    news_type='MS',
                                    date_and_time=datetime.datetime.now(),
                                    is_personal_news=True,
                                    is_empire_news=False,
                                    tick_number=RoundStatus.objects.get().tick_number
                                    )
                News.objects.create(user1=User.objects.get(id=request.POST['recipient']),
                                    user2=request.user,
                                    news_type='MR',
                                    date_and_time=datetime.datetime.now(),
                                    is_personal_news=True,
                                    is_empire_news=False,
                                    tick_number=RoundStatus.objects.get().tick_number
                                    )
                status2.mail_flag = 1
                status2.save()
            else:
                msg_on_top = 'You cannot send an empty message!'

    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Compose message",
               "msg_on_top": msg_on_top,
               "user_id": user_id,
               }
    return render(request, "compose_message.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def del_message_in(request, message_id):
    status = get_object_or_404(UserStatus, user=request.user)
    message = get_object_or_404(Messages, id=message_id, user2=status.id)
    if message.user1_deleted:
        message.delete()
    else:
        message.user2_deleted = True
        message.save()
    messages_from = Messages.objects.filter(user2=status.id, user2_deleted=False).order_by('-date_and_time')
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Inbox",
               "messages_from": messages_from,
               }
    return render(request, "messages.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def del_message_out(request, message_id):
    status = get_object_or_404(UserStatus, user=request.user)
    message = get_object_or_404(Messages, id=message_id, user1=status.id)
    if message.user2_deleted:
        message.delete()
    else:
        message.user1_deleted = True
        message.save()
    messages_to = Messages.objects.filter(user1=status.id, user1_deleted=False).order_by('-date_and_time')
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Outbox",
               "messages_to": messages_to,
               }
    return render(request, "outbox.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def bulk_del_message_out(request):
    status = get_object_or_404(UserStatus, user=request.user)
    messages_buffer = Messages.objects.filter(user1=status.id)
    for message in messages_buffer:
        message.user1_deleted = True
    Messages.objects.bulk_update(messages_buffer, ['user1_deleted'])
    Messages.objects.filter(user1_deleted=True, user2_deleted=True).delete()
    messages_to = ''
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Outbox",
               "messages_to": messages_to,
               }
    return render(request, "outbox.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def bulk_del_message_in(request):
    status = get_object_or_404(UserStatus, user=request.user)
    messages_buffer = Messages.objects.filter(user2=status.id)
    for message in messages_buffer:
        message.user2_deleted = True
    Messages.objects.bulk_update(messages_buffer, ['user2_deleted'])
    Messages.objects.filter(user1_deleted=True, user2_deleted=True).delete()
    messages_from = ''
    context = {"status": status,
               "round": RoundStatus.objects.filter().first,
               "page_title": "Inbox",
               "messages_to": messages_from,
               }
    return render(request, "messages.html", context)


@login_required
@user_passes_test(race_check, login_url="/choose_empire_race")
def custom_logout(request):
    logout(request)
    return HttpResponseRedirect('/')


def hall_of_fame(request):
    rounds = HallOfFame.objects.aggregate(Max('round'))
    round_records = {}
    msg = ""

    if rounds["round__max"] is None:
        msg = "The hall of fame is empty!"
    else:
        num_rounds = int(rounds["round__max"])
        for i in range((num_rounds), -1, -1):
            round_records[i] = HallOfFame.objects.filter(round=i).order_by('-planets', '-networth')

    

    context = {"page_title": "Hall of Fame",
               "round_records": round_records,
               "msg": msg
               }

    return render(request, "hall_of_fame.html", context)


def races(request):
    hark_bonus = race_display_list["Harks"]["bonuses"]
    hark_research = race_display_list["Harks"]["research"]
    hark_ops = race_display_list["Harks"]["op_list"]
    hark_spells = race_display_list["Harks"]["spell_list"]
    hark_incas = race_display_list["Harks"]["incantation_list"]
    
    mant_bonus = race_display_list["Manticarias"]["bonuses"]
    mant_research = race_display_list["Manticarias"]["research"]
    mant_ops = race_display_list["Manticarias"]["op_list"]
    mant_spells = race_display_list["Manticarias"]["spell_list"]
    mant_incas = race_display_list["Manticarias"]["incantation_list"]
    
    foos_bonus = race_display_list["Foohons"]["bonuses"]
    foos_research = race_display_list["Foohons"]["research"]
    foos_ops = race_display_list["Foohons"]["op_list"]
    foos_spells = race_display_list["Foohons"]["spell_list"]
    foos_incas = race_display_list["Foohons"]["incantation_list"]
    
    space_bonus = race_display_list["Spacebornes"]["bonuses"]
    space_research = race_display_list["Spacebornes"]["research"]
    space_ops = race_display_list["Spacebornes"]["op_list"]
    space_spells = race_display_list["Spacebornes"]["spell_list"]
    space_incas = race_display_list["Spacebornes"]["incantation_list"]
    
    dweav_bonus = race_display_list["Dreamweavers"]["bonuses"]
    dweav_research = race_display_list["Dreamweavers"]["research"]
    dweav_ops = race_display_list["Dreamweavers"]["op_list"]
    dweav_spells = race_display_list["Dreamweavers"]["spell_list"]
    dweav_incas = race_display_list["Dreamweavers"]["incantation_list"]
    
    wkees_bonus = race_display_list["Wookiees"]["bonuses"]
    wkees_research = race_display_list["Wookiees"]["research"]
    wkees_ops = race_display_list["Wookiees"]["op_list"]
    wkees_spells = race_display_list["Wookiees"]["spell_list"]
    wkees_incas = race_display_list["Wookiees"]["incantation_list"]
    
    jacks_bonus = race_display_list["Jackos"]["bonuses"]
    jacks_research = race_display_list["Jackos"]["research"]
    jacks_ops = race_display_list["Jackos"]["op_list"]
    jacks_spells = race_display_list["Jackos"]["spell_list"]
    jacks_incas = race_display_list["Jackos"]["incantation_list"]
    
    furts_bonus = race_display_list["Furtifons"]["bonuses"]
    furts_research = race_display_list["Furtifons"]["research"]
    furts_ops = race_display_list["Furtifons"]["op_list"]
    furts_spells = race_display_list["Furtifons"]["spell_list"]
    furts_incas = race_display_list["Furtifons"]["incantation_list"]
    
    samts_bonus = race_display_list["Samsonites"]["bonuses"]
    samts_research = race_display_list["Samsonites"]["research"]
    samts_ops = race_display_list["Samsonites"]["op_list"]
    samts_spells = race_display_list["Samsonites"]["spell_list"]
    samts_incas = race_display_list["Samsonites"]["incantation_list"]

    context = {"page_title": "Races",
               "hark_bonus":hark_bonus,
               "hark_research":hark_research,
               "hark_ops":hark_ops,
               "hark_spells":hark_spells,
               "hark_incas":hark_incas,
               "mant_bonus":mant_bonus,
               "mant_research":mant_research,
               "mant_ops":mant_ops,
               "mant_spells":mant_spells,
               "mant_incas":mant_incas,
               "foos_bonus":foos_bonus,
               "foos_research":foos_research,
               "foos_ops":foos_ops,
               "foos_spells":foos_spells,
               "foos_incas":foos_incas,
               "space_bonus":space_bonus,
               "space_research":space_research,
               "space_ops":space_ops,
               "space_spells":space_spells,
               "space_incas":space_incas,
               "dweav_bonus":dweav_bonus,
               "dweav_research":dweav_research,
               "dweav_ops":dweav_ops,
               "dweav_spells":dweav_spells,
               "dweav_incas":dweav_incas,
               "wkees_bonus":wkees_bonus,
               "wkees_research":wkees_research,
               "wkees_ops":wkees_ops,
               "wkees_spells":wkees_spells,
               "wkees_incas":wkees_incas,
               "jacks_bonus":jacks_bonus,
               "jacks_research":jacks_research,
               "jacks_ops":jacks_ops,
               "jacks_spells":jacks_spells,
               "jacks_incas":jacks_incas,
               "furts_bonus":furts_bonus,
               "furts_research":furts_research,
               "furts_ops":furts_ops,
               "furts_spells":furts_spells,
               "furts_incas":furts_incas,
               "samts_bonus":samts_bonus,
               "samts_research":samts_research,
               "samts_ops":samts_ops,
               "samts_spells":samts_spells,
               "samts_incas":samts_incas,
               }

    return render(request, "races.html", context)


def kbguide(request):
    return render(request, "guide.html")


def search(request):
    try:
        status = UserStatus.objects.get(user=request.user)
    except:
        status = None
    try:
        u_inp = request.POST['u_inp']
    except:
        return fsearch(request)
    if status:
        if "!" in u_inp:
            try:
                g_syst = u_inp.split("!")
                
                f_syst = g_syst[1].split(",")

                u_out = System.objects.get(x=f_syst[0], y=f_syst[1])
                
                return systmap(request, u_out.id)
            except:
                return fsearch(request)
            
        elif ":" in u_inp: 
            try:   
                f_plant = u_inp.split(",")
            
                f_plant_i = f_plant[1].split(":")

                u_out = Planet.objects.get(x=f_plant[0], y=f_plant_i[0], i=f_plant_i[1])
                
                return planet(request, u_out.id)
            except:
                return fsearch(request)
        
        elif "," in u_inp: 
            try:
                f_syst = u_inp.split(",")

                u_out = System.objects.get(x=f_syst[0], y=f_syst[1])
                
                return redirect(system, u_out.id)
            except:
                return fsearch(request)
            
        elif u_inp.isalpha():
            try:
                u_out = UserStatus.objects.get(user_name__icontains=u_inp)
                
                return account(request, u_out.id)
            except:
                if "elp" in u_inp:
                    return guide(request)
                elif "lanet" in u_inp:
                    return gplanets(request)
        
                elif "map" in u_inp:
                    return gmap(request)
                    
                elif "art" in u_inp:
                    return garti(request)
                    
                elif "uni" in u_inp:
                    return gunits(request)
                    
                elif "esearch" in u_inp:
                    return gresearch(request)
                elif "ormul" in u_inp:
                    return gnerd(request)    
                else:
                    return fsearch(request)
            
        elif u_inp.isnumeric():
            try:
                u_out = Empire.objects.get(number=u_inp)
                
                return empire(request, u_out.id)
            except:
                return fsearch(request) 
        else:
            return fsearch(request)
    else:
        if "elp" in u_inp:
            return guide(request)
        elif "lanet" in u_inp:
            return gplanets(request)

        elif "map" in u_inp:
            return gmap(request)
            
        elif "art" in u_inp:
            return garti(request)
            
        elif "uni" in u_inp:
            return gunits(request)
            
        elif "esearch" in u_inp:
            return gresearch(request)
        elif "ormul" in u_inp:
            return gnerd(request)    
        else:
            return fsearch(request)

       
def fsearch(request):
    try:
        status = UserStatus.objects.get(user=request.user)
    except:
        status = None
    context = {"status": status,
            "msg": ""}
    return render(request, "search.html", context)

## Guide
def guide(request):
    return render(request, "hq.html")
    
def gcouncil(request):
    return render(request, "guide/council.htm")

def gaccount(request):
    return render(request, "guide/account.htm")
    
def garti(request):
    reg_arts={}
    fast_arts={}
    oth_arts={}
    regarts = Artefacts.objects.filter(on_planet__isnull=False).values_list('name', flat=True)
    fastarts = Fastartes.objects.filter(on_planet__isnull=False).values_list('name', flat=True)
    for k, v in arti_list.items():
        if k in regarts:
            reg_arts[k]={"img":v[5],"desc":v[0]}
        if k in fastarts:
            fast_arts[k]={"img":v[5],"desc":v[0]}
        if k not in regarts and k not in fastarts:
            oth_arts[k]={"img":v[5],"desc":v[0]}
            
    context = {"reg_arts": reg_arts,
                "oth_arts":oth_arts,
                "fast_arts":fast_arts,
                "reg_count": len(regarts),
                "fast_count": len(fastarts)}
    return render(request, "guide/arti.htm", context)

def gbuttons(request):
    return render(request, "guide/buttons.htm")    
    
def gbuildings(request):
    return render(request, "guide/buildings.htm")
    
def gcalculator(request):
    return render(request, "guide/calculator.htm")

def gporcalc(x, y, wks, xone, yone, xtwo, ytwo):
    cover = 0
    d = np.sqrt((x-xone)**2 + (y-yone)**2)
    cover += np.max((0, 1.0 - np.sqrt(d/(7.0*(1.0 + 0.01*wks)))))
    d = np.sqrt((x-xtwo)**2 + (y-ytwo)**2)
    cover += np.max((0, 1.0 - np.sqrt(d/(7.0*(1.0 + 0.01*wks)))))
    
    return min(100,round(cover*100))

def gportal(request):
    wks = 0
    xone = 5
    yone = 4
    xtwo = 5
    ytwo = 13
    if 'por_calc_form' in request.POST:
        wks = int(request.POST['weeks'])
        xone = int(request.POST['x1'])
        yone = int(request.POST['y1'])
        xtwo = int(request.POST['x2'])
        ytwo = int(request.POST['y2'])
    
    speedgen={}
    
    for x in range(11):
        for y in range(18):
            key = str(x) + str(y)
            cover = gporcalc(x, y, wks, xone, yone, xtwo, ytwo)
            if x == xone and y == yone or x == xtwo and y == ytwo:
                speedgen[key]={"x":x,"y":y,"color":"Grey","portal":"Yellow", "cover": cover}
            else:
                speedgen[key]={"x":x,"y":y,"color":"Grey","portal":"", "cover": cover}
    
            if cover >= 70:
                speedgen[key]['color']="Green"
            elif cover >= 40:
                speedgen[key]['color']="yellow"
            else:
                speedgen[key]['color']="red"
    
    try:
        status = UserStatus.objects.get(user=request.user)
        if status.galsel == 2:
            status = TwoStatus.objects.get(user=request.user)
    except:
        status = None
    
    context = {"wks": wks,
                "xone": xone,
                "yone": yone,
                "xtwo": xtwo,
                "ytwo": ytwo,
                "status": status,
                "speedgen":speedgen}
    return render(request, "guide/portal.html", context)
    
def gobcalc(request):
    ob = {}
    oba = 0
    obb = 300
    for i in range(100):
        ob[i+1]= oba
        oba += obb
        obb += 200
    context = {"ob": ob}
    return render(request, "guide/obcalc.htm", context)

def gcombat(request):
    context = {"units":unit_labels,
               "u_helper": unit_helper_list}
    return render(request, "guide/combat.htm", context)
    
def gcredits(request):
    return render(request, "guide/credits.htm")

def gdelete(request):
    return render(request, "guide/delete.htm")
    
def gfam_func(request):
    return render(request, "guide/fam_func.htm")

def gfamily(request):
    return render(request, "guide/family.htm")    
    
def gfleet(request):
    return render(request, "guide/fleet.htm")
    
def gfleet_detail(request):
    return render(request, "guide/fleet_detail.htm")

def ggal_map(request):
    return render(request, "guide/gal_map.htm")
    
def ghistory(request):
    return render(request, "guide/history.htm")

def gleader(request):
    return render(request, "guide/leader.htm")

def glogout(request):
    return render(request, "guide/logout.htm")

def gmap(request):
    mapgen={}
    mapgen[1]={"color" : "Blue", "color2" : "None", "x":5,"y":5, "imgarti" : "", "scout": "Orange", "portal": "Yellow", "home": "/static/home_syst.png",}
    mapgen[2]={"color" : "Green", "color2" : "None", "x":3,"y":3, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[3]={"color" : "Green", "color2" : "None", "x":4,"y":5, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[4]={"color" : "Green", "color2" : "None", "x":2,"y":1, "imgarti" : "", "scout": "", "portal": "", "home": "", "sense": "Purple"}
    mapgen[5]={"color" : "Green", "color2" : "None", "x":2,"y":2, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[6]={"color" : "Green", "color2" : "None", "x":7,"y":8, "imgarti" : "", "scout": "", "portal": "con", "home": "",}
    mapgen[7]={"color" : "Green", "color2" : "None", "x":7,"y":9, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[8]={"color" : "Green", "color2" : "None", "x":6,"y":2, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[9]={"color" : "Red", "color2" : "None", "x":8,"y":4, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[10]={"color" : "Green", "color2" : "None", "x":4,"y":7, "imgarti" : "/static/arti/artimg0.gif", "scout": "", "portal": "", "home": "",}
    mapgen[11]={"color" : "Green", "color2" : "None", "x":1,"y":6, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    mapgen[12]={"color" : "Green", "color2" : "None", "x":2,"y":9, "imgarti" : "", "scout": "Orange", "portal": "", "home": "", "sense": "Purple"}
    mapgen[13]={"color" : "Red", "color2" : "None", "x":10,"y":1, "imgarti" : "", "scout": "", "portal": "", "home": "",}
    obsfl=[5]
    expfl=[6]
    hovfl = [13]
    suvfl = [2]
    
    speedgen={}
    for x in range(9):
        for y in range(9):
            key = str(x) + str(y)
            if x == 4 and y == 4:
                speedgen[key]={"x":x,"y":y,"color":"Grey","portal":"Yellow"}
            else:
                speedgen[key]={"x":x,"y":y,"color":"Grey","portal":""}
    
            min_dist = np.sqrt((4 - x) ** 2 +
                                   (4 - y) ** 2)
            travel_time = max(0,int(np.floor(min_dist / 3.6)))
            if travel_time < 1:
                speedgen[key]["color"] = "Blue"    
            
            min_dist = np.sqrt((4 - x) ** 2 +
                                   (4 - y) ** 2)
            travel_time = max(0,int(np.floor(min_dist / 2.8)))
            if travel_time < 1:
                speedgen[key]["color"] = "Green"
            
            min_dist = np.sqrt((4 - x) ** 2 +
                                   (4 - y) ** 2)
            travel_time = max(0,int(np.floor(min_dist / 2)))
            if travel_time < 1:
                speedgen[key]["color"] = "Red"
    
    context = {"mapgen": mapgen,
                "obsfl":obsfl,
                "expfl":expfl,
                "hovfl":hovfl,
                "suvfl":suvfl,
                "speedgen":speedgen}
    return render(request, "guide/map.htm", context)
    
def gmessages(request):
    return render(request, "guide/messages.htm")

def gnerd(request):
    return render(request, "guide/nerd.htm")    
    
def gnetworth(request):
    return render(request, "guide/networth.htm")
    
def gopstats(request):
    return ops(request)

def gplanet_e(request):
    return render(request, "guide/planet_e.htm")
    
def gplanet_mine(request):
    return render(request, "guide/planet_mine.htm")

def gplanets(request):
    return render(request, "guide/planets.htm")
    
def gplayer(request):
    return render(request, "guide/player.htm")

def gpopulation(request):
    upkeep = 0
    try:
        status = UserStatus.objects.get(user=request.user)
        upkeep = status.buildings_upkeep + status.portals_upkeep + status.units_upkeep
        if status.galsel == 2:
            status = TwoStatus.objects.get(user=request.user)
            upkeep = status.buildings_upkeep + status.portals_upkeep + status.units_upkeep
    except:
        status = None
    context = {"status": status,
                "upkeep": upkeep}
    return render(request, "guide/population.htm", context)
    
def grace(request):
    return render(request, "guide/race.htm")

def granks(request):
    return render(request, "guide/ranks.htm")    
    
def greceive_aid(request):
    return render(request, "guide/receive_aid.htm")
    
def greadiness(request):
    return render(request, "guide/readiness.htm")
    
def grelations(request):
    return render(request, "guide/relations.htm")

def gresearch(request):
    return render(request, "guide/research.htm")
    
def gresources(request):
    return render(request, "guide/resources.htm")

def gsearch(request):
    return render(request, "guide/search.htm")

def gspecop(request):
    return ops(request)   
    
def gstats(request):
    return render(request, "guide/stats.htm")
    
def gtag(request):
    return render(request, "guide/tag.htm")

def gunitcalc(request):
    return render(request, "guide/unitcalc.htm")
    
def gunits(request):
    context = {"units":unit_labels,
                "unitcost": unit_costs,
                "tech": required_unit_tech,
                "upkeep": unit_upkeep,
                "battle": unit_stats}
    return render(request, "guide/units.htm", context)

def gupkeep(request):
    return render(request, "guide/upkeep.htm")
    
def discord(request):
    return render(request, "discord.html")
