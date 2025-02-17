from django.urls import include, path, re_path

from . import views
from django.conf import settings
from django.conf.urls.static import static
from galtwo.views import choose_empire
from galtwo.views import register as tworegister

urlpatterns = [
    path('', views.index, name='index'),  # root page
    path('headquarters', views.headquarters, name='headquarters'),
    path('council', views.council, name='council'),
    path('map', views.map, name='map'),
    path('smap', views.smap, name='smap'),
    path('pmap', views.pmap, name='pmap'),
    path('cmap', views.cmap, name='cmap'),
    path('amap', views.amap, name='amap'),
    path('planets', views.planets, name='planets'),
    re_path(r'^planet(?P<planet_id>[0-9]+)/$', views.planet, name='planet'),
    re_path(r'^system(?P<system_id>[0-9]+)/$', views.system, name='system'),
    re_path(r'^systmap(?P<system_id>[0-9]+)/$', views.systmap, name='systmap'),
    re_path(r'^tmap(?P<player_id>[0-9]+)/$', views.tmap, name='tmap'),
    re_path(r'^raze(?P<planet_id>[0-9]+)/$', views.raze, name='raze'),
    re_path(r'^razeall(?P<planet_id>[0-9]+)/$', views.razeall, name='razeall'),
    re_path(r'^build(?P<planet_id>[0-9]+)/$', views.build, name='build'),
    path('ranking', views.ranking, name='ranking'),
    path('empire_ranking', views.empire_ranking, name='empire_ranking'),
    re_path(r'^password/$', views.change_password, name='change_password'),
    path('units', views.units, name='units'),
    path('fleets', views.fleets, name='fleets'),
    path('fleetsend', views.fleetsend, name='fleetsend'),
    path('tgeneral', views.tgeneral, name='tgeneral'),
    path('search', views.search, name='search'),
    path('fsearch', views.fsearch, name='fsearch'),
    re_path(r'^empire(?P<empire_id>[0-9]+)/$', views.empire, name='empire'),
    path('vote', views.vote, name='vote'),
    path('vote_results', views.vote, name='voteresults'),
    path('pm_options', views.pm_options, name='prime_minister_options'),
    path('relations', views.relations, name='relations'),
    path('results', views.results, name='results'),
    path('research', views.research, name='research'),
    path('famaid', views.famaid, name='famaid'),
    path('famgetaid', views.famgetaid, name='famgetaid'),
    path('messages', views.game_messages, name='messages'),
    path('outbox', views.outbox, name='outbox'),
    re_path(r'^compose_message(?P<user_id>[0-9]*)/$', views.compose_message, name='compose_message'),
    re_path(r'^delete_message_inbox(?P<message_id>[0-9]+)/$', views.del_message_in, name='del_inbox'),
    re_path(r'^delete_message_outbox(?P<message_id>[0-9]+)/$', views.del_message_out, name='del_outbox'),
    path('delete_all_messages_inbox', views.bulk_del_message_in, name='delete_all_messages_inbox'),
    path('delete_all_messages_outbox', views.bulk_del_message_out, name='delete_all_messages_outbox'),
    path('faq', views.faq, name='faq'),
    path("registration/register", views.register, name="register"),
    path("galtwo/registration/register", tworegister, name="register"),
    path('logout', views.custom_logout, name='logout'),
    path('login', views.custom_login, name='login_page'),
    path('choose_empire_race', views.choose_empire_race, name='choose_empire_race'),
    path('galtwo/choose_empire', choose_empire, name='choose_empire'),
    path('fleets_orders_process', views.fleets_orders_process, name='fleets_orders_process'),
    path('fleets_disband', views.fleets_disband, name='fleets_disband'),
    path('fleets_disband', views.fleets_disband, name='fleets_disband'),
    path('famnews', views.famnews, name='famnews'),
    path('specops', views.specops, name='specops'),
    path('ops', views.ops, name='ops'),
    path('update', views.update, name='update'),
    path('btn', views.btn, name='btn'),
    path('ressies', views.ressies, name='ressies'),
    path('portal', views.portal, name='portal'),
	re_path(r'^battle(?P<fleet_id>[0-9]+)/$', views.battle, name='battle'),
    path('map_settings', views.map_settings, name='map_settings'),
    path('scouting', views.scouting, name='scouting'),
    path('offer', views.offer, name='offer'),
    path('halloffame', views.hall_of_fame, name='hall_of_fame'),
    re_path(r'^specop_show(?P<specop_id>[0-9]+)/$', views.specop_show, name='specop_show'),
    re_path(r'^account(?P<player_id>[0-9]+)/$', views.account, name='account'),
    path('mass_build', views.mass_build, name='mass_build'),
    path('races', views.races, name='races'),
    re_path(r'^plant(?P<planet_id>[0-9]+)/$', views.plant, name='plant'),
    re_path(r'^syst(?P<system_id>[0-9]+)/$', views.syst, name='syst'),
    re_path(r'^msyst(?P<system_id>[0-9]+)/$', views.msyst, name='msyst'),
    path('fleets_orders', views.fleets_orders, name='fleets_orders'),
    path('fleet_orders_process', views.fleet_orders_process, name='fleet_orders_process'),
    re_path(r'^batt(?P<fleet_id>[0-9]+)/$', views.batt, name='batt'),
    path('specs', views.specs, name='specs'),
    re_path(r'^mrazeall(?P<planet_id>[0-9]+)/$', views.mrazeall, name='mrazeall'),
    path('fleetssend', views.fleetssend, name='fleetssend'),
    
    path('guide', views.guide, name='guide'),
    path('guide/council', views.gcouncil, name='gcouncil'),
    path('guide/account', views.gaccount, name='gaccount'),
    path('guide/arti', views.garti, name='garti'),
    path('guide/buildings', views.gbuildings, name='gbuildings'),
    path('guide/buttons', views.gbuttons, name='gbuttons'),
    path('guide/calculator', views.gcalculator, name='gcalculator'),
    path('guide/portal', views.gportal, name='gportal'),
    path('guide/obcalc', views.gobcalc, name='gobcalc'),
    path('guide/combat', views.gcombat, name='gcombat'),
    path('guide/credits', views.gcredits, name='gcredits'),
    path('guide/delete', views.gdelete, name='gdelete'),
    path('guide/fam_func', views.gfam_func, name='gfam_func'),
    path('guide/family', views.gfamily, name='gfamily'),
    path('guide/fleet', views.gfleet, name='gfleet'),
    path('guide/fleet_detail', views.gfleet_detail, name='gfleet_detail'),
    path('guide/gal_map', views.ggal_map, name='ggal_map'),
    path('guide/history', views.ghistory, name='ghistory'),
    path('guide/leader', views.gleader, name='gleader'),
    path('guide/logout', views.glogout, name='glogout'),
    path('guide/map', views.gmap, name='gmap'),
    path('guide/messages', views.gmessages, name='gmessages'),
    path('guide/nerd', views.gnerd, name='gnerd'),
    path('guide/networth', views.gnetworth, name='gnetworth'),
    path('guide/opstats', views.gopstats, name='gopstats'),
    path('guide/planet_e', views.gplanet_e, name='gplanet_e'),
    path('guide/planet_mine', views.gplanet_mine, name='gplanet_mine'),
    path('guide/planets', views.gplanets, name='gplanets'),
    path('guide/player', views.gplayer, name='gplayer'),
    path('guide/population', views.gpopulation, name='gpopulation'),
    path('guide/race', views.grace, name='grace'),
    path('guide/ranks', views.granks, name='granks'),
    path('guide/readiness', views.greadiness, name='greadiness'),
    path('guide/receive_aid', views.greceive_aid, name='greceive_aid'),
    path('guide/relations', views.grelations, name='grelations'),
    path('guide/research', views.gresearch, name='gresearch'),
    path('guide/resources', views.gresources, name='gresources'),
    path('guide/search', views.gsearch, name='gsearch'),
    path('guide/specop', views.gspecop, name='gspecop'),
    path('guide/stats', views.gstats, name='gstats'),
    path('guide/tag', views.gtag, name='gtag'),
    path('guide/unitcalc', views.gunitcalc, name='gunitcalc'),
    path('guide/units', views.gunits, name='gunits'),
    path('guide/upkeep', views.gupkeep, name='gupkeep'),
    path('kbguide', views.kbguide, name='kbguide'),
    
    path('discord', views.discord, name='discord'),
    
    re_path(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,32})/$',
        views.activate, name='activate'),
    path('confirm', views.confirm, name='confirm'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
