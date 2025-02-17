from django.db import models
from django.contrib.auth.models import User # from Django's built-in user management system
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _ # for the enumeration's labels
from app.constants import *
from django.db.models.signals import post_save # used to auto create UserStatus and fleet after a new user is created
from app.map_settings import *
from django.contrib.postgres.fields import ArrayField
from datetime import datetime

# Is there any reason to have a model for solar system?  That would then contain N planet objects
class Artefacts(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True, default=None)
    description = models.CharField(max_length=300, blank=True, null=True, default=None)
    on_planet = models.ForeignKey('Planets', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    effect1 = models.IntegerField(default=0)
    effect2 = models.IntegerField(default=0)
    effect3 = models.IntegerField(default=0)
    ticks_left = models.IntegerField(default=0)
    extra_effect = models.CharField(max_length=50, blank=True, null=True, default=None)
    empire_holding = models.ForeignKey('Empire', related_name='arteempire', blank=True, null=True,
                                  default=None, on_delete=models.SET_DEFAULT)
    date_and_time = models.DateTimeField(blank=True, null=True, default=None)
    image = models.CharField(max_length=50, blank=True, null=True, default=None)


class Planets(models.Model):
    class Meta:
        db_table = 'PLANETS'

    # Static
    x = models.IntegerField()
    y = models.IntegerField()
    i = models.IntegerField() # index of planet in system, starting at 0
    
    system =  models.ForeignKey('System', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    
    # note that each user's status contains their home planet as a child object, the field below is more for quick checks
    home_planet = models.BooleanField(default=False) # players start with their home planet and it cannot be attacked
    pos_in_system = models.IntegerField(default=0) # used to spread out the planets around the circle better
    size = models.IntegerField()

    owner = models.ForeignKey(User, null=True, blank=True, default=None, on_delete=models.SET_NULL) # if owner is removed from game set back to null

    # Calculated each tick
    current_population = models.BigIntegerField(default=0) # calculated each tick
    max_population = models.BigIntegerField(default=0) # calculated each tick
    protection = models.IntegerField(default=0) # in % points, the calculation will round it
    overbuilt = models.FloatField(default=0.0) # DecimalField was being weird with its rounding
    overbuilt_percent = models.FloatField(default=0.0)

    # Bonuses
    bonus_solar = models.IntegerField(default=0) # in % points, e.g. 104 for 104% bonus.  Note that the solar energy bonus does NOT apply to fission reactors
    bonus_mineral = models.IntegerField(default=0)
    bonus_crystal = models.IntegerField(default=0)
    bonus_ectrolium = models.IntegerField(default=0)
    bonus_fission = models.IntegerField(default=0)

    # Buildings (I decided to break them out into separate fields instead of having an array, to make the code easier to read in the various spots these buildings will be involved in calculaitons and such
    solar_collectors = models.IntegerField(default=0)
    fission_reactors = models.IntegerField(default=0)
    mineral_plants = models.IntegerField(default=0)
    crystal_labs = models.IntegerField(default=0)
    refinement_stations = models.IntegerField(default=0)
    cities = models.IntegerField(default=0)
    research_centers = models.IntegerField(default=0)
    defense_sats = models.IntegerField(default=0)
    shield_networks = models.IntegerField(default=0)
    portal = models.BooleanField(default=False)
    portal_under_construction = models.BooleanField(default=False)
    total_buildings = models.IntegerField(default=0) # on this planet. doesn't include under construction
    buildings_under_construction = models.IntegerField(default=0) # number of total buildings under construction. NOTE- the C code doesnt have a field for this, it jsut calculates it each time, since it uses a single array for the buildings

    artefact = models.ForeignKey(Artefacts, on_delete=models.SET_NULL, blank=True, null=True, default=None)


class Empire(models.Model):
    number = models.IntegerField(default=0)
    x = models.IntegerField(default=0)
    y = models.IntegerField(default=0)
    rank = models.IntegerField(default=0)
    numplayers = models.IntegerField(default=0)
    planets = models.IntegerField(default=0)
    taxation = models.FloatField(default=0.0)
    networth = models.BigIntegerField(default=0)
    name = models.CharField(max_length=30, default="")
    name_with_id = models.CharField(max_length=35, default="")
    password = models.CharField(max_length=30, default="", blank=True)
    fund_energy = models.IntegerField(default=0)
    fund_minerals = models.IntegerField(default=0)
    fund_crystals = models.IntegerField(default=0)
    fund_ectrolium = models.IntegerField(default=0)
    pm_message = models.CharField(max_length=300, default="")
    relations_message = models.CharField(max_length=300, default="No relations message.")
    empire_image = models.ImageField(upload_to='empire_images/', blank=True)
    artefacts = models.ManyToManyField(Artefacts)

class News(models.Model): # a single type of building under construction
    user1 = models.ForeignKey(User, related_name='user1n', on_delete=models.SET_NULL, blank=True, null=True,
                                default=None)
    user2 = models.ForeignKey(User, related_name='user2n', on_delete=models.SET_NULL, blank=True, null=True,
                                default=None)
    empire1 = models.ForeignKey(Empire, related_name='Empire1', on_delete=models.SET_NULL, blank=True, null=True,
                                default=None)
    empire2 = models.ForeignKey(Empire, related_name='Empire2', on_delete=models.SET_NULL, blank=True, null=True,
                                default=None)
    class NewsType(models.TextChoices):
        SA = 'SA', _('Successfull Attack')
        UA = 'UA', _('Unsuccessfull Attack')
        SD = 'SD', _('Successfull Defence')
        UD = 'UD', _('Unsuccessfull Defence')
        SE = 'SE', _('Successfull Exploration')
        UE = 'UE', _('Unsuccessfull Exploration')
        PA = 'PA', _('Psychic Attack')
        PD = 'PD', _('Psychic Defence')
        AA = 'AA', _('Agent Attack')
        AD = 'AD', _('Agent Defence')
        GA = 'GA', _('Ghost Attack')
        GD = 'GD', _('Ghost Defence')
        SI = 'SI', _('Sent aid')
        RA = 'RA', _('Requested aid')
        M = 'M', _('Market operation')
        N = 'N', _('None')
        BB = 'BB', _('Buildings Built')
        UB = 'UB', _('Units Built')
        MS = 'MS', _('Message Sent')
        MR = 'MR', _('Message Received')
        RWD = 'RWD', _('Relation War Declared')
        RWE = 'RWE', _('Relation War Ended')
        RNP = 'RNP', _('Relation Nap Proposed')
        RND = 'RND', _('Relation Nap Declared')
        RNE = 'RNE', _('Relation Nap Ended')
        RAP = 'RAP', _('Relation Alliance Proposed')
        RAD = 'RAD', _('Relation Alliance Declared')
        RAE = 'RAE', _('Relation Alliance Ended')
        FS = 'FS', _('Fleet Stationed')
        FU = 'FU', _('Fleet Station Unsuccessful')
        FM = 'FM', _('Fleet Merged')
        FJ = 'FJ', _('Fleet Joined Main')
        E = 'E', _('Something Extra')
        RCP = 'RCP', _('Ceasefire Proposed')
        RCD = 'RCD', _('Ceasefire Declared')
        DU = 'DU', _('Flying Dutchman')
        TE = 'TE', _('Terraformer')
        SK = 'SK', _('Skrull')

    news_type = models.CharField(max_length=3, choices=NewsType.choices, default=NewsType.N)
    tick_number = models.IntegerField(default=0)
    date_and_time = models.DateTimeField(blank=True, null=True, default=None)
    is_read = models.BooleanField(default=False)
    is_personal_news = models.BooleanField(default=False)
    is_empire_news = models.BooleanField(default=False)
    planet = models.ForeignKey(Planets, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    fleet1 = models.TextField(blank=True, null=True, default=None)
    fleet2 = models.TextField(blank=True, null=True, default=None)
    extra_info = models.TextField(blank=True, null=True, default=None)

class UserStatus(models.Model):
    user = models.OneToOneField(User, related_name='galtwouser', on_delete=models.CASCADE) # when referenced object is deleted, also delete this

    # Info that doesn't change over the round
    user_name = models.CharField(max_length=30, default="user-display-name") # Display name
    # empire_num = models.IntegerField()
    empire = models.ForeignKey(Empire, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    home_planet = models.ForeignKey(Planets, on_delete=models.SET_NULL, blank=True,
                                    null=True)  # only time we delete planets will be mid-round

    #flags section 0 - no flag, 1 - green flag, 2-yellow flag, 3- red flag
    mail_flag = models.IntegerField(default=0)
    construction_flag = models.IntegerField(default=0)
    economy_flag = models.IntegerField(default=0)
    military_flag = models.IntegerField(default=0)

    # empire politics section
    class EmpireRoles(models.TextChoices):
        PM = 'PM', _('Prime Minister')
        VM = 'VM', _('Vice Minister')
        P = 'P', _('') #normal player
        I = 'I', _('Independent')
    empire_role = models.CharField(max_length=2, choices=EmpireRoles.choices, default=EmpireRoles.P)
    votes =  models.IntegerField(default=0) #number of people voting for this user to be a leader of their empire
    voting_for =  models.ForeignKey('self', on_delete=models.SET_NULL, blank=True, null=True, default=None)

    # empire aid
    class EmpireAid(models.TextChoices):
        PM = 'PM', _('Prime minister')
        VM = 'VM', _('Prime minister and vice ministers')
        A = 'A', _('All players') #normal player
        N = 'N', _('Nobody')
    request_aid = models.CharField(max_length=2, choices=EmpireAid.choices, default=EmpireAid.N)

    # Race
    class Races(models.TextChoices):
        HK = 'HK', _('Harks')
        MT = 'MT', _('Manticarias')
        FH = 'FH', _('Foohons')
        SB = 'SB', _('Spacebornes')
        DW = 'DW', _('Dreamweavers')
        WK = 'WK', _('Wookiees')
        #JK = 'JK', _('Jackos')
        #SO = 'SO', _('Shootout')
        FT = 'FT', _('Furtifons')
        SM = 'SM', _('Samsonites')
    race = models.CharField(max_length=2, choices=Races.choices, blank=True, default=None, null=True)

    # Resources
    energy = models.BigIntegerField(default=120000, validators = [MinValueValidator(0)])
    minerals = models.BigIntegerField(default=10000, validators = [MinValueValidator(0)])
    crystals = models.BigIntegerField(default=5000, validators = [MinValueValidator(0)])
    ectrolium = models.BigIntegerField(default=5000, validators = [MinValueValidator(0)])

    # Current resource production/decay, calculated in process_tick
    energy_production = models.BigIntegerField(default=0)
    energy_decay = models.BigIntegerField(default=0)
    energy_interest = models.BigIntegerField(default=0) # wookies only
    energy_income = models.BigIntegerField(default=0)
    energy_specop_effect = models.BigIntegerField(default=0)

    mineral_production = models.IntegerField(default=0)
    mineral_decay = models.IntegerField(default=0)
    mineral_interest = models.IntegerField(default=0) # wookies only
    mineral_income = models.IntegerField(default=0)
    crystal_production = models.IntegerField(default=0)
    crystal_decay = models.IntegerField(default=0)
    crystal_interest = models.IntegerField(default=0) # wookies only
    crystal_income = models.IntegerField(default=0)
    ectrolium_production = models.IntegerField(default=0)
    ectrolium_decay = models.IntegerField(default=0)
    ectrolium_interest = models.IntegerField(default=0) # wookies only
    ectrolium_income = models.IntegerField(default=0)

    # Misc info that must be recalculated
    num_planets = models.IntegerField(default=1) # number of planets, will get calculated
    population = models.BigIntegerField(default=0)
    networth = models.BigIntegerField(default=1)
    buildings_upkeep = models.BigIntegerField(default=0) # stored as a positive number
    units_upkeep = models.BigIntegerField(default=0) # stored as a positive number
    portals_upkeep = models.IntegerField(default=0) # stored as a positive number
    population_upkeep_reduction = models.BigIntegerField(default=0)

    total_solar_collectors = models.IntegerField(default=staring_solars) # all of these are across all planets (which is why its in status and not planet)
    total_fission_reactors = models.IntegerField(default=0)
    total_mineral_plants = models.IntegerField(default=starting_meral_planets)
    total_crystal_labs = models.IntegerField(default=starting_crystal_labs)
    total_refinement_stations = models.IntegerField(default=starting_ectrolium_refs)
    total_cities = models.IntegerField(default=starting_cities)
    total_research_centers = models.IntegerField(default=0)
    total_defense_sats = models.IntegerField(default=0)
    total_shield_networks = models.IntegerField(default=0)
    total_portals = models.IntegerField(default=1)
    total_buildings = models.IntegerField(default=starting_total)

    # Readiness
    fleet_readiness = models.IntegerField(default=100)
    psychic_readiness = models.IntegerField(default=100)
    agent_readiness = models.IntegerField(default=100)

    fleet_readiness_max = models.IntegerField(default=100)
    psychic_readiness_max  = models.IntegerField(default=100)
    agent_readiness_max  = models.IntegerField(default=100)


    # Research (names might seem verbose but it makes various spots in the code way less confusing to read)
    research_percent_military = models.IntegerField(default=0) # stored as integer, in percentage points
    research_percent_construction = models.IntegerField(default=0)
    research_percent_tech = models.IntegerField(default=0)
    research_percent_energy = models.IntegerField(default=0)
    research_percent_population = models.IntegerField(default=0)
    research_percent_culture = models.IntegerField(default=0)
    research_percent_operations = models.IntegerField(default=0)
    research_percent_portals = models.IntegerField(default=0)

    research_points_military = models.BigIntegerField(default=0)
    research_points_construction = models.BigIntegerField(default=0)
    research_points_tech = models.BigIntegerField(default=0)
    research_points_energy = models.BigIntegerField(default=0)
    research_points_population = models.BigIntegerField(default=0)
    research_points_culture = models.BigIntegerField(default=0)
    research_points_operations = models.BigIntegerField(default=0)
    research_points_portals = models.BigIntegerField(default=0)

    alloc_research_military = models.IntegerField(default=16) # stored as integer, in percentage points
    alloc_research_construction = models.IntegerField(default=12)
    alloc_research_tech = models.IntegerField(default=12)
    alloc_research_energy = models.IntegerField(default=12)
    alloc_research_population = models.IntegerField(default=12)
    alloc_research_culture = models.IntegerField(default=12)
    alloc_research_operations = models.IntegerField(default=12)
    alloc_research_portals = models.IntegerField(default=12)

    current_research_funding = models.BigIntegerField(default=0)

    # Fleet related
    long_range_attack_percent = models.IntegerField(default=200)
    air_vs_air_percent = models.IntegerField(default=200)
    ground_vs_air_percent = models.IntegerField(default=200)
    ground_vs_ground_percent = models.IntegerField(default=200)
    class PostAttackOrder(models.IntegerChoices):
        STATION_ON_PLANET = 1
        WAIT_IN_SYSTEM    = 2
        RECALL_TO_MAIN    = 5
    post_attack_order = models.IntegerField(choices=PostAttackOrder.choices, default=2)

    tag_points = models.IntegerField(default=0)
    tag = models.CharField(max_length=50, blank=True, default="Player", null=True)
    galsel =  models.IntegerField(default=1)
    last_active = models.DateTimeField(default=datetime.now)


class Construction(models.Model): # a single type of building under construction
    user = models.ForeignKey(User, related_name='galtwocon', on_delete=models.CASCADE)
    planet = models.ForeignKey(Planets, on_delete=models.CASCADE)
    n = models.IntegerField() # number of them
    ticks_remaining = models.IntegerField()

    # Building type enumeration
    class BuildingTypes(models.TextChoices): # must match the short_label in buildings class
        SC = 'SC', _('Solar Collectors')
        FR = 'FR', _('Fission Reactors')
        MP = 'MP', _('Mineral Plants')
        CL = 'CL', _('Crystal Laboratories')
        RS = 'RS', _('Refinement Stations')
        CT = 'CT', _('Cities')
        RC = 'RC', _('Research Centers')
        DS = 'DS', _('Defense Satellites')
        SN = 'SN', _('Shield Networks')
        PL = 'PL', _('Portal')
    building_type = models.CharField(max_length=2, choices=BuildingTypes.choices)
    # so we know how much to refund if needed
    energy_cost = models.BigIntegerField(default=0)
    mineral_cost = models.BigIntegerField(default=0)
    crystal_cost = models.BigIntegerField(default=0)
    ectrolium_cost = models.BigIntegerField(default=0)


class Fleet(models.Model):
    owner = models.ForeignKey(User, related_name='galtwofleet', null=True, blank=True, default=None, on_delete=models.SET_NULL) # if owner is removed from game set back to null
    main_fleet = models.BooleanField(default=False) # should only be 1 per user, assigned only at user creation
    on_planet = models.ForeignKey(Planets, null=True, blank=True, default=None, on_delete=models.SET_NULL) # planet object if stationed, or None
    ticks_remaining = models.IntegerField(default=0) # for traveling

    current_position_x = models.FloatField(default=0.0)  # for traveling
    current_position_y = models.FloatField(default=0.0)  # for traveling

    # Order (if fleet is being sent somewhere)
    class CommandOrder(models.IntegerChoices):
        ATTACK_PLANET     = 0
        STATION_ON_PLANET = 1
        MOVE_TO_SYSTEM    = 2
        MERGE_IN_SYSTEM   = 3
        MERGE_IN_SYSTEM_A = 4
        JOIN_MAIN_FLEET   = 5
        PERFORM_OPERATION = 6
        PERFORM_INCANTATION = 7
        STATIONED = 8
        EXPLORE_PLANET = 10
    command_order = models.IntegerField(choices=CommandOrder.choices, default=0)

    # Destination coords for when its traveling
    x = models.IntegerField(null=True, blank=True, default=None)
    y = models.IntegerField(null=True, blank=True, default=None)
    i = models.IntegerField(null=True, blank=True, default=None)

    # Number of each type of unit
    bomber      = models.BigIntegerField(default=0, verbose_name="Bombers")
    fighter     = models.BigIntegerField(default=0, verbose_name="Fighters")
    transport   = models.BigIntegerField(default=0, verbose_name="Transports")
    cruiser     = models.BigIntegerField(default=0, verbose_name="Cruisers")
    carrier     = models.BigIntegerField(default=0, verbose_name="Carriers")
    soldier     = models.BigIntegerField(default=0, verbose_name="Soldiers")
    droid       = models.BigIntegerField(default=0, verbose_name="Droids")
    goliath     = models.BigIntegerField(default=0, verbose_name="Goliaths")
    phantom     = models.BigIntegerField(default=0, verbose_name="Phantoms")
    wizard      = models.BigIntegerField(default=0, verbose_name="Psychics")
    agent       = models.BigIntegerField(default=0, verbose_name="Agents")
    ghost       = models.BigIntegerField(default=0, verbose_name="Ghost Ships")
    exploration = models.BigIntegerField(default=0, verbose_name="Exploration Ships")

    specop = models.CharField(max_length=50, blank=True, null=True, default=None)

    # got sick of having to search for it everytime actually, so decided to add it
    target_planet = models.ForeignKey(Planets, related_name="target", on_delete=models.SET_DEFAULT, blank=True,
                                      null=True, default=None)
    random = models.IntegerField(null=True, blank=True, default=None)                                 

class UnitConstruction(models.Model):
    user = models.ForeignKey(User, related_name='galtwoucon', on_delete=models.CASCADE)
    n = models.IntegerField() # number of them
    ticks_remaining = models.IntegerField()

    class UnitTypes(models.TextChoices):
        bomber = 'bomber', _('Bombers')
        fighter = 'fighter', _('Fighters')
        transport = 'transport', _('Transports')
        cruiser = 'cruiser', _('Cruisers')
        carrier = 'carrier', _('Carriers')
        soldier = 'soldier', _('Soldiers')
        droid = 'droid', _('Droids')
        goliath = 'goliath', _('Goliaths')
        phantom = 'phantom', _('Phantoms')
        wizard = 'wizard', _('Psychics')
        agent = 'agent', _('Agents')
        ghost = 'ghost', _('Ghost Ships')
        exploration = 'exploration', _('Exploration Ships')

    unit_type = models.CharField(max_length=11, choices=UnitTypes.choices) # exploration is longest name, so 11 chars is enough

    # so we know how much to refund if needed
    energy_cost = models.BigIntegerField(default=0)
    mineral_cost = models.BigIntegerField(default=0)
    crystal_cost = models.BigIntegerField(default=0)
    ectrolium_cost = models.BigIntegerField(default=0)


class RoundStatus(models.Model):
    galaxy_size = models.IntegerField(default=100)
    tick_number = models.IntegerField(default=0)
    is_running = models.BooleanField(default=False)
    round_number = models.IntegerField(default=0)
    artetimer = models.IntegerField(default=1440)
    round_start = models.DateTimeField(blank=True, null=True, default=None)
    artedelay = models.IntegerField(default=59)
    tick_time = models.IntegerField(default=30)
    emphold = models.ForeignKey(Empire, on_delete=models.SET_NULL, blank=True, null=True, default=None)

class Bot(models.Model):
    year = models.IntegerField(default=52)
    ob = models.IntegerField(default=0)
    oba = models.IntegerField(default=300)

class botattack(models.Model):
    user1 = models.CharField(max_length=50, blank=True, null=True, default=None)
    user2 = models.CharField(max_length=50, blank=True, null=True, default=None)
    at_type = models.CharField(max_length=10, blank=True, null=True, default=None)
    time = models.IntegerField(default=15)

class Relations(models.Model):
    # When an empire declares a relation, its id number goes to the empire1 field, and the
    # other empire's id goes to empire2 field
    empire1 = models.ForeignKey(Empire, related_name='empire1r', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    empire2 = models.ForeignKey(Empire, related_name='empire2r', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    class RelationTypes(models.TextChoices):
        AO = 'AO', _('Alliance offered')
        W = 'W', _('War declared')
        A = 'A', _('Alliance')
        NO = 'NO', _('Non agression pact offered')
        NC = 'NC', _('Non agression pact cancelled')
        PC = 'PC', _('Permanent non agression pact cancelled')
        N = 'N', _('Non agression pact')
        C = 'C', _('Ceasefire')
        CO = 'CO', _('Ceasefire offered')
    relation_type = models.CharField(max_length=2, choices=RelationTypes.choices)
    relation_length = models.IntegerField(blank=True, null=True, default=None)
    relation_creation_tick = models.IntegerField(default=0)
    relation_cancel_tick = models.IntegerField(default=0)
    relation_remaining_time = models.IntegerField(default=0)


class Messages(models.Model):
    user1 = models.ForeignKey(UserStatus, related_name='user1m', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    user2 = models.ForeignKey(UserStatus, related_name='user2m', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    message = models.CharField(max_length=5000, blank=True, null=True, default=None)
    date_and_time = models.DateTimeField(blank=True)
    user1_deleted = models.BooleanField(default=False)
    user2_deleted = models.BooleanField(default=False)


class MapSettings(models.Model):
    user = models.ForeignKey(User, related_name='user1ms', on_delete=models.CASCADE)
    faction = models.ForeignKey(UserStatus, related_name='factionms', on_delete=models.CASCADE, blank=True, null=True, default=None)
    empire = models.ForeignKey(Empire, on_delete=models.CASCADE, blank=True, null=True, default=None)
    class MapSetting(models.TextChoices):
        UE = 'UE', _('Unexplored planets')
        PE = 'PE', _('Planets of empire')
        PF = 'PF', _('Planets of faction ')
        YE = 'YE', _('Your empire')
        YR = 'YR', _('Your portals')
        YP = 'YP', _('Your planets')
        SC = 'SC', _('Scouted Planets')
        SS = 'SS', _('Sensed Systems')
    map_setting = models.CharField(max_length=2, choices=MapSetting.choices, default='UE')
    class ColorSettings(models.TextChoices):
        R = 'R', _('Red')
        B = 'B', _('Blue')
        G = 'G', _('Green')
        O = 'O', _('Orange')
        Y = 'Y', _('Yellow')
        I = 'I', _('Indigo')
        V = 'V', _('Violet')
        W = 'W', _('White')
        P = 'P', _('Pink')
        N = 'N', _('Brown')
        C = 'C', _('Cyan')
        A = 'A', _('Navy')
    color_settings = models.CharField(max_length=1, choices=ColorSettings.choices, default='G')

class Scouting(models.Model):
    user = models.ForeignKey(User, related_name='galtwousersc', on_delete=models.CASCADE)
    planet = models.ForeignKey(Planets, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    scout = models.FloatField(default=0)
    empire = models.ForeignKey(Empire, on_delete=models.SET_NULL, blank=True, null=True, default=None)


class HallOfFame(models.Model):
    round = models.IntegerField(default=0)
    userid = models.IntegerField(default=0)
    user = models.CharField(max_length=30) # Display name
    empire = models.CharField(max_length=35) #empire name with id
    artefacts = models.IntegerField(default=0)
    planets = models.IntegerField(default=0)
    networth = models.BigIntegerField(default=0)
    race = models.CharField(max_length=30)


class Specops(models.Model):
    user_to = models.ForeignKey(User, related_name='Souser1', on_delete=models.CASCADE)
    user_from = models.ForeignKey(User, related_name='Souser2', blank=True, null=True,
                                  default=None, on_delete=models.SET_DEFAULT)
    class SpecopType(models.TextChoices):
        O = 'O', _('Agent operation')
        S = 'S', _('Psychic spell')
        G = 'G', _('Ghost incantation')
    specop_type = models.CharField(max_length=1, choices=SpecopType.choices, default='O')
    name = models.CharField(max_length=50, blank=True, null=True, default=None)
    specop_strength = models.FloatField(default=0)
    specop_strength2 = models.FloatField(default=0)
    # for spells like enlightment
    extra_effect = models.CharField(max_length=50, blank=True, null=True, default=None)
    ticks_left = models.IntegerField(default=0)
    stealth = models.BooleanField(default=False)
    planet = models.ForeignKey(Planets, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    date_and_time = models.DateTimeField(blank=True, null=True, default=None)

class System(models.Model):
    x = models.IntegerField()
    y = models.IntegerField()
    img = models.CharField(max_length=50, blank=True, null=True, default=None)
    home = models.BooleanField(default=False)
    
class Sensing(models.Model):
    scout = models.FloatField(default=0)
    system = models.ForeignKey(System, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    empire = models.ForeignKey(Empire, on_delete=models.SET_NULL, blank=True, null=True, default=None)
    
class Ticks_log(models.Model):
    round = models.IntegerField()
    calc_time_ms = models.DecimalField(max_digits=12, decimal_places=6)
    dt = models.DateTimeField()
    error = models.TextField(null=True)

class Ops(models.Model):
    class SpecopType(models.TextChoices):
        O = 'O', _('Agent operation')
        S = 'S', _('Psychic spell')
        G = 'G', _('Ghost incantation')
    specop_type = models.CharField(max_length=1, choices=SpecopType.choices, default='O')
    name = models.CharField(max_length=50, blank=True, null=True, default=None)
    ident = models.CharField(max_length=2)
    tech = models.IntegerField()
    readiness = models.IntegerField()
    difficulty = models.DecimalField(max_digits=2, decimal_places=1)
    selfsp = models.BooleanField(default=False)
    stealth = models.BooleanField(default=False)
    description = models.CharField(max_length=255, default=None)