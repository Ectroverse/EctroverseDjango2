CREATE EXTENSION IF NOT EXISTS tablefunc; -- for crosstab

drop table if exists classes cascade;

create table classes
(id serial primary key, name varchar(255), dt timestamp);

insert into classes
(name, dt)
values
('general', current_timestamp),
('upkeep', current_timestamp),
('building production', current_timestamp),
('building names', current_timestamp),
('research names', current_timestamp),
('unit upkeep costs', current_timestamp),
('units nw', current_timestamp),
('other nw', current_timestamp),
('unit names', current_timestamp),
('unit labels', current_timestamp),
('building names', current_timestamp),
('HK', current_timestamp), --harks
('MT', current_timestamp),
('FH', current_timestamp),
('SB', current_timestamp),
('DW', current_timestamp),
('WK', current_timestamp),
('JK', current_timestamp);


select * from classes;

drop table if exists constants;

create table constants
(id serial primary key, class int references classes(id) not null, 
name varchar(255), num_val numeric, text_val varchar(255), dt timestamp, UNIQUE(class, name) );


insert into constants (class, name, num_val, dt)
values 

((select id from classes where name = 'general'),'total_units', 13,current_timestamp),
((select id from classes where name = 'general'),'population_size_factor', 200,current_timestamp),
((select id from classes where name = 'general'),'energy_decay_factor', 0.005,current_timestamp),
((select id from classes where name = 'general'),'crystal_decay_factor', 0.02,current_timestamp),
((select id from classes where name = 'general'),'networth_per_building', 8,current_timestamp),

((select id from classes where name = 'upkeep'),'upkeep_solar_collectors', 0,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_fission_reactors', 20,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_mineral_plants', 2,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_crystal_labs', 2,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_refinement_stations', 2,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_cities', 4,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_research_centers', 1,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_defense_sats', 4,current_timestamp),
((select id from classes where name = 'upkeep'),'upkeep_shield_networks', 16,current_timestamp),

((select id from classes where name = 'building production'),'building_production_solar', 12,current_timestamp),
((select id from classes where name = 'building production'),'building_production_fission', 40,current_timestamp),
((select id from classes where name = 'building production'),'building_production_mineral', 1,current_timestamp),
((select id from classes where name = 'building production'),'building_production_crystal', 1,current_timestamp),
((select id from classes where name = 'building production'),'building_production_ectrolium', 1,current_timestamp),
((select id from classes where name = 'building production'),'building_production_cities', 10000,current_timestamp),
((select id from classes where name = 'building production'),'building_production_research', 6,current_timestamp),

((select id from classes where name = 'unit upkeep costs'),'bomber', 2.0,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'fighter', 1.6,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'transport', 3.2,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'cruiser', 12.0,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'carrier', 18.0,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'soldier', 0.4,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'droid', 0.6,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'goliath', 2.8,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'phantom', 0.0,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'wizard', 0.8,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'agent', 0.8,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'ghost', 2.4,current_timestamp),
((select id from classes where name = 'unit upkeep costs'),'exploration', 60.0,current_timestamp),

((select id from classes where name = 'units nw'),'bomber', 4,current_timestamp),
((select id from classes where name = 'units nw'),'fighter', 3,current_timestamp),
((select id from classes where name = 'units nw'),'transport', 5,current_timestamp),
((select id from classes where name = 'units nw'),'cruiser', 12,current_timestamp),
((select id from classes where name = 'units nw'),'carrier', 14,current_timestamp),
((select id from classes where name = 'units nw'),'soldier', 1,current_timestamp),
((select id from classes where name = 'units nw'),'droid', 1,current_timestamp),
((select id from classes where name = 'units nw'),'goliath', 4,current_timestamp),
((select id from classes where name = 'units nw'),'phantom', 7,current_timestamp),
((select id from classes where name = 'units nw'),'wizard', 2,current_timestamp),
((select id from classes where name = 'units nw'),'agent', 2,current_timestamp),
((select id from classes where name = 'units nw'),'ghost', 6,current_timestamp),
((select id from classes where name = 'units nw'),'exploration', 30,current_timestamp),

((select id from classes where name = 'other nw'),'population nw', 0.0005, current_timestamp),
((select id from classes where name = 'other nw'),'research nw', 0.001, current_timestamp),

	/* HK = 'HK', _('Harks')
        MT = 'MT', _('Manticarias')
        FH = 'FH', _('Foohons')
        SB = 'SB', _('Spacebornes')
        DW = 'DW', _('Dreamweavers')
        WK = 'WK', _('Wookiees')*/

((select id from classes where name = 'HK'),'pop_growth', (0.8*0.02),current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_military', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_construction', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_tech', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_energy', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_population', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_culture', 0.6,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_operations', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'research_bonus_portals', 1.2,current_timestamp),
((select id from classes where name = 'HK'),'energy_production', 0.9,current_timestamp),
((select id from classes where name = 'HK'),'mineral_production', 1.0,current_timestamp),
((select id from classes where name = 'HK'),'crystal_production', 1.25,current_timestamp),
((select id from classes where name = 'HK'),'ectrolium_production', 1.0,current_timestamp),
((select id from classes where name = 'HK'),'travel_speed', (1.4*2.0),current_timestamp),
((select id from classes where name = 'HK'),'research_max_military', 250.0,current_timestamp),

((select id from classes where name = 'MT'),'pop_growth', (0.9*0.02),current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_military', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_construction', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_tech', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_energy', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_population', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_culture', 1.8,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_operations', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'research_bonus_portals', 0.9,current_timestamp),
((select id from classes where name = 'MT'),'energy_production', 1.4,current_timestamp),
((select id from classes where name = 'MT'),'mineral_production', 1.0,current_timestamp),
((select id from classes where name = 'MT'),'crystal_production', 1.0,current_timestamp),
((select id from classes where name = 'MT'),'ectrolium_production', 1.0,current_timestamp),
((select id from classes where name = 'MT'),'race_special_solar_15', 1.15,current_timestamp),
((select id from classes where name = 'MT'),'research_max_military', (1.0*2.0),current_timestamp),

((select id from classes where name = 'FH'),'pop_growth', (0.8*0.02),current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_military', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_construction', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_tech', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_energy', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_population', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_culture', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_operations', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'research_bonus_portals', 1.5,current_timestamp),
((select id from classes where name = 'FH'),'energy_production', 0.8,current_timestamp),
((select id from classes where name = 'FH'),'mineral_production', 1.0,current_timestamp),
((select id from classes where name = 'FH'),'crystal_production', 1.0,current_timestamp),
((select id from classes where name = 'FH'),'ectrolium_production', 1.2,current_timestamp),
((select id from classes where name = 'FH'),'travel_speed', (1.0*2.0),current_timestamp),
((select id from classes where name = 'MT'),'race_special_pop_research', 6000 ,current_timestamp),

((select id from classes where name = 'SB'),'pop_growth', (1.2*0.02),current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_military', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_construction', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_tech', 0.6,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_energy', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_population', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_culture', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_operations', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'research_bonus_portals', 1.1,current_timestamp),
((select id from classes where name = 'SB'),'energy_production', 1.3,current_timestamp),
((select id from classes where name = 'SB'),'mineral_production', 1.0,current_timestamp),
((select id from classes where name = 'SB'),'crystal_production', 1.0,current_timestamp),
((select id from classes where name = 'SB'),'ectrolium_production', 1.0,current_timestamp),
((select id from classes where name = 'SB'),'travel_speed', (1.8*2.0),current_timestamp),
((select id from classes where name = 'SB'),'research_max_energy', 250.0,current_timestamp),

((select id from classes where name = 'DW'),'pop_growth', (1.1*0.02),current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_military', 1.0,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_construction', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_tech', 2.8,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_energy', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_population', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_culture', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_operations', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'research_bonus_portals', 1.4,current_timestamp),
((select id from classes where name = 'DW'),'energy_production', 0.8,current_timestamp),
((select id from classes where name = 'DW'),'mineral_production', 1.0,current_timestamp),
((select id from classes where name = 'DW'),'crystal_production', 1.25,current_timestamp),
((select id from classes where name = 'DW'),'ectrolium_production', 1.0,current_timestamp),
((select id from classes where name = 'DW'),'travel_speed', (1.0*2.0),current_timestamp),
((select id from classes where name = 'DW'),'research_max_military', 100.0,current_timestamp),
((select id from classes where name = 'DW'),'research_max_construction', 250.0,current_timestamp),

((select id from classes where name = 'WK'),'pop_growth', (1.2*0.02),current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_military', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_construction', 2.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_tech', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_energy', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_population', 2.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_culture', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_operations', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'research_bonus_portals', 2.0,current_timestamp),
((select id from classes where name = 'WK'),'energy_production', 0.7,current_timestamp),
((select id from classes where name = 'WK'),'mineral_production', 1.25,current_timestamp),
((select id from classes where name = 'WK'),'crystal_production', 1.25,current_timestamp),
((select id from classes where name = 'WK'),'ectrolium_production', 1.0,current_timestamp),
((select id from classes where name = 'WK'),'race_special_resource_interest', 0.005,current_timestamp),
((select id from classes where name = 'WK'),'travel_speed', (1.6*2.0),current_timestamp),
((select id from classes where name = 'WK'),'research_max_population', 250.0,current_timestamp);


select * from  constants;
drop table if exists ticks_log;

create table ticks_log
(id serial primary key, round varchar(255), calc_time_ms numeric, dt timestamp);


drop table if exists unit_stats;

create table unit_stats
as 
select * from crosstab (
'select c1.name class_name, t.name, t.num_val
	from constants t
	join classes c1 on c1.id = t.class 
	where c1.name in (''unit upkeep costs'', ''units nw'')
	order by 1,2'
) as ct
( 
class_name varchar,	
agent numeric,
bomber numeric,
carrier numeric,
cruiser numeric,
droid numeric,
exploration numeric,
fighter numeric,
ghost numeric,
goliath numeric,
phantom numeric,
soldier numeric,
transport numeric,
wizard numeric
);