# Generated by Django 3.1 on 2024-03-21 15:45

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Artefacts',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('description', models.CharField(blank=True, default=None, max_length=300, null=True)),
                ('effect1', models.IntegerField(default=0)),
                ('effect2', models.IntegerField(default=0)),
                ('effect3', models.IntegerField(default=0)),
                ('ticks_left', models.IntegerField(default=0)),
                ('extra_effect', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('date_and_time', models.DateTimeField(blank=True, default=None, null=True)),
                ('image', models.CharField(blank=True, default=None, max_length=50, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Bot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField(default=52)),
                ('ob', models.IntegerField(default=0)),
                ('oba', models.IntegerField(default=300)),
            ],
        ),
        migrations.CreateModel(
            name='botattack',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user1', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('user2', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('at_type', models.CharField(blank=True, default=None, max_length=10, null=True)),
                ('time', models.IntegerField(default=15)),
            ],
        ),
        migrations.CreateModel(
            name='Empire',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField(default=0)),
                ('x', models.IntegerField(default=0)),
                ('y', models.IntegerField(default=0)),
                ('rank', models.IntegerField(default=0)),
                ('numplayers', models.IntegerField(default=0)),
                ('planets', models.IntegerField(default=0)),
                ('taxation', models.FloatField(default=0.0)),
                ('networth', models.BigIntegerField(default=0)),
                ('name', models.CharField(default='', max_length=30)),
                ('name_with_id', models.CharField(default='', max_length=35)),
                ('password', models.CharField(blank=True, default='', max_length=30)),
                ('fund_energy', models.IntegerField(default=0)),
                ('fund_minerals', models.IntegerField(default=0)),
                ('fund_crystals', models.IntegerField(default=0)),
                ('fund_ectrolium', models.IntegerField(default=0)),
                ('pm_message', models.CharField(default='', max_length=300)),
                ('relations_message', models.CharField(default='No relations message.', max_length=300)),
                ('empire_image', models.ImageField(blank=True, upload_to='empire_images/')),
                ('artefacts', models.ManyToManyField(to='galtwo.Artefacts')),
            ],
        ),
        migrations.CreateModel(
            name='HallOfFame',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('round', models.IntegerField(default=0)),
                ('userid', models.IntegerField(default=0)),
                ('user', models.CharField(max_length=30)),
                ('empire', models.CharField(max_length=35)),
                ('artefacts', models.IntegerField(default=0)),
                ('planets', models.IntegerField(default=0)),
                ('networth', models.BigIntegerField(default=0)),
                ('race', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='Planets',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('i', models.IntegerField()),
                ('home_planet', models.BooleanField(default=False)),
                ('pos_in_system', models.IntegerField(default=0)),
                ('size', models.IntegerField()),
                ('current_population', models.IntegerField(default=0)),
                ('max_population', models.IntegerField(default=0)),
                ('protection', models.IntegerField(default=0)),
                ('overbuilt', models.FloatField(default=0.0)),
                ('overbuilt_percent', models.FloatField(default=0.0)),
                ('bonus_solar', models.IntegerField(default=0)),
                ('bonus_mineral', models.IntegerField(default=0)),
                ('bonus_crystal', models.IntegerField(default=0)),
                ('bonus_ectrolium', models.IntegerField(default=0)),
                ('bonus_fission', models.IntegerField(default=0)),
                ('solar_collectors', models.IntegerField(default=0)),
                ('fission_reactors', models.IntegerField(default=0)),
                ('mineral_plants', models.IntegerField(default=0)),
                ('crystal_labs', models.IntegerField(default=0)),
                ('refinement_stations', models.IntegerField(default=0)),
                ('cities', models.IntegerField(default=0)),
                ('research_centers', models.IntegerField(default=0)),
                ('defense_sats', models.IntegerField(default=0)),
                ('shield_networks', models.IntegerField(default=0)),
                ('portal', models.BooleanField(default=False)),
                ('portal_under_construction', models.BooleanField(default=False)),
                ('total_buildings', models.IntegerField(default=0)),
                ('buildings_under_construction', models.IntegerField(default=0)),
                ('artefact', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.artefacts')),
                ('owner', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'PLANETS',
            },
        ),
        migrations.CreateModel(
            name='RoundStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('galaxy_size', models.IntegerField(default=100)),
                ('tick_number', models.IntegerField(default=0)),
                ('is_running', models.BooleanField(default=False)),
                ('round_number', models.IntegerField(default=0)),
                ('artetimer', models.IntegerField(default=1440)),
                ('round_start', models.DateTimeField(blank=True, default=None, null=True)),
                ('artedelay', models.IntegerField(default=59)),
            ],
        ),
        migrations.CreateModel(
            name='System',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('x', models.IntegerField()),
                ('y', models.IntegerField()),
                ('img', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('home', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='UserStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user_name', models.CharField(default='user-display-name', max_length=30)),
                ('mail_flag', models.IntegerField(default=0)),
                ('construction_flag', models.IntegerField(default=0)),
                ('economy_flag', models.IntegerField(default=0)),
                ('military_flag', models.IntegerField(default=0)),
                ('empire_role', models.CharField(choices=[('PM', 'Prime Minister'), ('VM', 'Vice Minister'), ('P', ''), ('I', 'Independent')], default='P', max_length=2)),
                ('votes', models.IntegerField(default=0)),
                ('request_aid', models.CharField(choices=[('PM', 'Prime minister'), ('VM', 'Prime minister and vice ministers'), ('A', 'All players'), ('N', 'Nobody')], default='N', max_length=2)),
                ('race', models.CharField(blank=True, choices=[('HK', 'Harks'), ('MT', 'Manticarias'), ('FH', 'Foohons'), ('SB', 'Spacebornes'), ('DW', 'Dreamweavers'), ('WK', 'Wookiees'), ('JK', 'Jackos')], default=None, max_length=2, null=True)),
                ('energy', models.BigIntegerField(default=120000, validators=[django.core.validators.MinValueValidator(0)])),
                ('minerals', models.BigIntegerField(default=10000, validators=[django.core.validators.MinValueValidator(0)])),
                ('crystals', models.BigIntegerField(default=5000, validators=[django.core.validators.MinValueValidator(0)])),
                ('ectrolium', models.BigIntegerField(default=5000, validators=[django.core.validators.MinValueValidator(0)])),
                ('energy_production', models.BigIntegerField(default=0)),
                ('energy_decay', models.BigIntegerField(default=0)),
                ('energy_interest', models.BigIntegerField(default=0)),
                ('energy_income', models.BigIntegerField(default=0)),
                ('energy_specop_effect', models.BigIntegerField(default=0)),
                ('mineral_production', models.IntegerField(default=0)),
                ('mineral_decay', models.IntegerField(default=0)),
                ('mineral_interest', models.IntegerField(default=0)),
                ('mineral_income', models.IntegerField(default=0)),
                ('crystal_production', models.IntegerField(default=0)),
                ('crystal_decay', models.IntegerField(default=0)),
                ('crystal_interest', models.IntegerField(default=0)),
                ('crystal_income', models.IntegerField(default=0)),
                ('ectrolium_production', models.IntegerField(default=0)),
                ('ectrolium_decay', models.IntegerField(default=0)),
                ('ectrolium_interest', models.IntegerField(default=0)),
                ('ectrolium_income', models.IntegerField(default=0)),
                ('num_planets', models.IntegerField(default=1)),
                ('population', models.BigIntegerField(default=0)),
                ('networth', models.BigIntegerField(default=1)),
                ('buildings_upkeep', models.BigIntegerField(default=0)),
                ('units_upkeep', models.BigIntegerField(default=0)),
                ('portals_upkeep', models.IntegerField(default=0)),
                ('population_upkeep_reduction', models.BigIntegerField(default=0)),
                ('total_solar_collectors', models.IntegerField(default=100)),
                ('total_fission_reactors', models.IntegerField(default=0)),
                ('total_mineral_plants', models.IntegerField(default=50)),
                ('total_crystal_labs', models.IntegerField(default=25)),
                ('total_refinement_stations', models.IntegerField(default=25)),
                ('total_cities', models.IntegerField(default=0)),
                ('total_research_centers', models.IntegerField(default=0)),
                ('total_defense_sats', models.IntegerField(default=0)),
                ('total_shield_networks', models.IntegerField(default=0)),
                ('total_portals', models.IntegerField(default=1)),
                ('total_buildings', models.IntegerField(default=200)),
                ('fleet_readiness', models.IntegerField(default=100)),
                ('psychic_readiness', models.IntegerField(default=100)),
                ('agent_readiness', models.IntegerField(default=100)),
                ('fleet_readiness_max', models.IntegerField(default=100)),
                ('psychic_readiness_max', models.IntegerField(default=100)),
                ('agent_readiness_max', models.IntegerField(default=100)),
                ('research_percent_military', models.IntegerField(default=0)),
                ('research_percent_construction', models.IntegerField(default=0)),
                ('research_percent_tech', models.IntegerField(default=0)),
                ('research_percent_energy', models.IntegerField(default=0)),
                ('research_percent_population', models.IntegerField(default=0)),
                ('research_percent_culture', models.IntegerField(default=0)),
                ('research_percent_operations', models.IntegerField(default=0)),
                ('research_percent_portals', models.IntegerField(default=0)),
                ('research_points_military', models.BigIntegerField(default=0)),
                ('research_points_construction', models.BigIntegerField(default=0)),
                ('research_points_tech', models.BigIntegerField(default=0)),
                ('research_points_energy', models.BigIntegerField(default=0)),
                ('research_points_population', models.BigIntegerField(default=0)),
                ('research_points_culture', models.BigIntegerField(default=0)),
                ('research_points_operations', models.BigIntegerField(default=0)),
                ('research_points_portals', models.BigIntegerField(default=0)),
                ('alloc_research_military', models.IntegerField(default=16)),
                ('alloc_research_construction', models.IntegerField(default=12)),
                ('alloc_research_tech', models.IntegerField(default=12)),
                ('alloc_research_energy', models.IntegerField(default=12)),
                ('alloc_research_population', models.IntegerField(default=12)),
                ('alloc_research_culture', models.IntegerField(default=12)),
                ('alloc_research_operations', models.IntegerField(default=12)),
                ('alloc_research_portals', models.IntegerField(default=12)),
                ('current_research_funding', models.BigIntegerField(default=0)),
                ('long_range_attack_percent', models.IntegerField(default=200)),
                ('air_vs_air_percent', models.IntegerField(default=200)),
                ('ground_vs_air_percent', models.IntegerField(default=200)),
                ('ground_vs_ground_percent', models.IntegerField(default=200)),
                ('post_attack_order', models.IntegerField(choices=[(1, 'Station On Planet'), (2, 'Wait In System'), (5, 'Recall To Main')], default=2)),
                ('tag_points', models.IntegerField(default=0)),
                ('tag', models.CharField(blank=True, default='Player', max_length=50, null=True)),
                ('galsel', models.IntegerField(default=1)),
                ('last_active', models.DateTimeField(blank=True, default=None, null=True)),
                ('empire', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.empire')),
                ('home_planet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='galtwouser', to=settings.AUTH_USER_MODEL)),
                ('voting_for', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.userstatus')),
            ],
        ),
        migrations.CreateModel(
            name='UnitConstruction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n', models.IntegerField()),
                ('ticks_remaining', models.IntegerField()),
                ('unit_type', models.CharField(choices=[('bomber', 'Bombers'), ('fighter', 'Fighters'), ('transport', 'Transports'), ('cruiser', 'Cruisers'), ('carrier', 'Carriers'), ('soldier', 'Soldiers'), ('droid', 'Droids'), ('goliath', 'Goliaths'), ('phantom', 'Phantoms'), ('wizard', 'Psychics'), ('agent', 'Agents'), ('ghost', 'Ghost Ships'), ('exploration', 'Exploration Ships')], max_length=11)),
                ('energy_cost', models.BigIntegerField(default=0)),
                ('mineral_cost', models.BigIntegerField(default=0)),
                ('crystal_cost', models.BigIntegerField(default=0)),
                ('ectrolium_cost', models.BigIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='galtwoucon', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Specops',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('specop_type', models.CharField(choices=[('O', 'Agent operation'), ('S', 'Psychic spell'), ('G', 'Ghost incantation')], default='O', max_length=1)),
                ('name', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('specop_strength', models.FloatField(default=0)),
                ('specop_strength2', models.FloatField(default=0)),
                ('extra_effect', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('ticks_left', models.IntegerField(default=0)),
                ('stealth', models.BooleanField(default=False)),
                ('date_and_time', models.DateTimeField(blank=True, default=None, null=True)),
                ('planet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets')),
                ('user_from', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='Souser2', to=settings.AUTH_USER_MODEL)),
                ('user_to', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='Souser1', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Scouting',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scout', models.FloatField(default=0)),
                ('planet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='galtwousersc', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Relations',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('relation_type', models.CharField(choices=[('AO', 'Alliance offered'), ('W', 'War declared'), ('A', 'Alliance'), ('NO', 'Non agression pact offered'), ('NC', 'Non agression pact cancelled'), ('PC', 'Permanent non agression pact cancelled'), ('N', 'Non agression pact')], max_length=2)),
                ('relation_length', models.IntegerField(blank=True, default=None, null=True)),
                ('relation_creation_tick', models.IntegerField(default=0)),
                ('relation_cancel_tick', models.IntegerField(default=0)),
                ('relation_remaining_time', models.IntegerField(default=0)),
                ('empire1', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='empire1r', to='galtwo.empire')),
                ('empire2', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='empire2r', to='galtwo.empire')),
            ],
        ),
        migrations.CreateModel(
            name='News',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('news_type', models.CharField(choices=[('SA', 'Successfull Attack'), ('UA', 'Unsuccessfull Attack'), ('SD', 'Successfull Defence'), ('UD', 'Unsuccessfull Defence'), ('SE', 'Successfull Exploration'), ('UE', 'Unsuccessfull Exploration'), ('PA', 'Psychic Attack'), ('PD', 'Psychic Defence'), ('AA', 'Agent Attack'), ('AD', 'Agent Defence'), ('GA', 'Ghost Attack'), ('GD', 'Ghost Defence'), ('SI', 'Sent aid'), ('RA', 'Requested aid'), ('M', 'Market operation'), ('N', 'None'), ('BB', 'Buildings Built'), ('UB', 'Units Built'), ('MS', 'Message Sent'), ('MR', 'Message Reseived'), ('RWD', 'Relation War Declared'), ('RWE', 'Relation War Ended'), ('RNP', 'Relation Nap Proposed'), ('RND', 'Relation Nap Declared'), ('RNE', 'Relation Nap Ended'), ('RAP', 'Relation Alliance Proposed'), ('RAD', 'Relation Alliance Declared'), ('RAE', 'Relation Alliance Ended'), ('FS', 'Fleet Stationed'), ('FU', 'Fleet Station Unsuccessful'), ('FM', 'Fleet Merged'), ('FJ', 'Fleet Joined Main'), ('E', 'Something Extra')], default='N', max_length=3)),
                ('tick_number', models.IntegerField(default=0)),
                ('date_and_time', models.DateTimeField(blank=True, default=None, null=True)),
                ('is_read', models.BooleanField(default=False)),
                ('is_personal_news', models.BooleanField(default=False)),
                ('is_empire_news', models.BooleanField(default=False)),
                ('fleet1', models.TextField(blank=True, default=None, null=True)),
                ('fleet2', models.TextField(blank=True, default=None, null=True)),
                ('extra_info', models.TextField(blank=True, default=None, null=True)),
                ('empire1', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Empire1', to='galtwo.empire')),
                ('empire2', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='Empire2', to='galtwo.empire')),
                ('planet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets')),
                ('user1', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user1n', to=settings.AUTH_USER_MODEL)),
                ('user2', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user2n', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Messages',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.CharField(blank=True, default=None, max_length=5000, null=True)),
                ('date_and_time', models.DateTimeField(blank=True)),
                ('user1_deleted', models.BooleanField(default=False)),
                ('user2_deleted', models.BooleanField(default=False)),
                ('user1', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user1m', to='galtwo.userstatus')),
                ('user2', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user2m', to='galtwo.userstatus')),
            ],
        ),
        migrations.CreateModel(
            name='MapSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('map_setting', models.CharField(choices=[('UE', 'Unexplored planets'), ('PE', 'Planets of empire'), ('PF', 'Planets of faction '), ('YE', 'Your empire'), ('YR', 'Your portals'), ('YP', 'Your planets'), ('SC', 'Scouted Planets')], default='UE', max_length=2)),
                ('color_settings', models.CharField(choices=[('R', 'Red'), ('B', 'Blue'), ('G', 'Green'), ('O', 'Orange'), ('Y', 'Yellow'), ('I', 'Indigo'), ('V', 'Violet'), ('W', 'White'), ('P', 'Pink')], default='G', max_length=1)),
                ('empire', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, to='galtwo.empire')),
                ('faction', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='factionms', to='galtwo.userstatus')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user1ms', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Fleet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('main_fleet', models.BooleanField(default=False)),
                ('ticks_remaining', models.IntegerField(default=0)),
                ('current_position_x', models.FloatField(default=0.0)),
                ('current_position_y', models.FloatField(default=0.0)),
                ('command_order', models.IntegerField(choices=[(0, 'Attack Planet'), (1, 'Station On Planet'), (2, 'Move To System'), (3, 'Merge In System'), (4, 'Merge In System A'), (5, 'Join Main Fleet'), (6, 'Perform Operation'), (7, 'Perform Incantation'), (8, 'Stationed'), (10, 'Explore Planet')], default=0)),
                ('x', models.IntegerField(blank=True, default=None, null=True)),
                ('y', models.IntegerField(blank=True, default=None, null=True)),
                ('i', models.IntegerField(blank=True, default=None, null=True)),
                ('bomber', models.BigIntegerField(default=0, verbose_name='Bombers')),
                ('fighter', models.BigIntegerField(default=0, verbose_name='Fighters')),
                ('transport', models.BigIntegerField(default=0, verbose_name='Transports')),
                ('cruiser', models.BigIntegerField(default=0, verbose_name='Cruisers')),
                ('carrier', models.BigIntegerField(default=0, verbose_name='Carriers')),
                ('soldier', models.BigIntegerField(default=0, verbose_name='Soldiers')),
                ('droid', models.BigIntegerField(default=0, verbose_name='Droids')),
                ('goliath', models.BigIntegerField(default=0, verbose_name='Goliaths')),
                ('phantom', models.BigIntegerField(default=0, verbose_name='Phantoms')),
                ('wizard', models.BigIntegerField(default=0, verbose_name='Psychics')),
                ('agent', models.BigIntegerField(default=0, verbose_name='Agents')),
                ('ghost', models.BigIntegerField(default=0, verbose_name='Ghost Ships')),
                ('exploration', models.BigIntegerField(default=0, verbose_name='Exploration Ships')),
                ('specop', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('on_planet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets')),
                ('owner', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='galtwofleet', to=settings.AUTH_USER_MODEL)),
                ('target_planet', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='target', to='galtwo.planets')),
            ],
        ),
        migrations.CreateModel(
            name='Construction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('n', models.IntegerField()),
                ('ticks_remaining', models.IntegerField()),
                ('building_type', models.CharField(choices=[('SC', 'Solar Collectors'), ('FR', 'Fission Reactors'), ('MP', 'Mineral Plants'), ('CL', 'Crystal Laboratories'), ('RS', 'Refinement Stations'), ('CT', 'Cities'), ('RC', 'Research Centers'), ('DS', 'Defense Satellites'), ('SN', 'Shield Networks'), ('PL', 'Portal')], max_length=2)),
                ('energy_cost', models.BigIntegerField(default=0)),
                ('mineral_cost', models.BigIntegerField(default=0)),
                ('crystal_cost', models.BigIntegerField(default=0)),
                ('ectrolium_cost', models.BigIntegerField(default=0)),
                ('planet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='galtwo.planets')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='galtwocon', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='artefacts',
            name='empire_holding',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='arteempire', to='galtwo.empire'),
        ),
        migrations.AddField(
            model_name='artefacts',
            name='on_planet',
            field=models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='galtwo.planets'),
        ),
    ]