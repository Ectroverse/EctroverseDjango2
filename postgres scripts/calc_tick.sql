CREATE OR REPLACE PROCEDURE calc_tick(gal_nr varchar)
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
   _timest timestamptz;
   _tmp numeric;
   _round_number int;
   _retstr varchar(255);
   _retnum numeric;
   _retbool boolean;
   
	_planets_table varchar(255);
	_userstatus_table varchar(255);
    _fleet_table varchar(255);
	_construction_table varchar(255);
	_unitconstruction_table varchar(255);
	_scouting_table varchar(255);
	_news_table varchar(255);
	_ticks_log_table varchar(255);
	_artefacts_table varchar(255);
	
	_roundstatus varchar(255);
	_sql varchar;
BEGIN 
   _start_ts := clock_timestamp();
   
   -- for each type of round (slow/fast) we chose the tables accordingly
	if gal_nr = 'slow' then
		_planets_table := '"PLANET"';
		_userstatus_table := 'app_userstatus';
		_fleet_table := 'app_fleet';
		_construction_table := 'app_construction';
		_unitconstruction_table := 'app_unitconstruction';
		_scouting_table := 'app_scouting';
		_news_table := 'app_news';
		_roundstatus := 'app_roundstatus';
		_ticks_log_table := 'app_ticks_log';
		_artefacts_table := 'app_artefacts';
	else 
		_planets_table := '"PLANETS"';
		_userstatus_table := 'galtwo_userstatus';
		_fleet_table := 'galtwo_fleet';
		_construction_table := 'galtwo_construction';
		_unitconstruction_table := 'galtwo_unitconstruction';
		_scouting_table := 'galtwo_scouting';
		_news_table := 'galtwo_news';
		_roundstatus := 'galtwo_roundstatus';
		_ticks_log_table := 'galtwo_ticks_log';
		_artefacts_table := 'galtwo_artefacts';
	end if;

	EXECUTE format('select max(round_number) from  %s ;', _roundstatus)
	INTO _round_number; 


	EXECUTE 'select is_running from '|| _roundstatus || ' where round_number = ' || _round_number
	INTO _retbool; 

	-- do not calc tick if the round timer is stopped	
	IF _retbool = false THEN
	  return;
	END IF;

 _sql :=
 '
  update '|| _roundstatus || '
 set tick_number = tick_number + 1
 where is_running = ''true'';
 
  -- population  
 
 lock table '|| _planets_table ||';
 lock table '|| _userstatus_table ||';
 lock table '|| _fleet_table ||';
 lock table '|| _construction_table||';
 lock table '|| _unitconstruction_table||';
 lock table '|| _scouting_table||';
 lock table '|| _news_table||';
 
  
 UPDATE '|| _planets_table ||' p
 SET max_population = ((select num_val from constants where name = ''building_production_cities'') 
					   * cities +  size * 
					  (select num_val from constants where name = ''population_size_factor'') 
					  )* (1.00 + 0.01 * u.research_percent_population)
 from '|| _userstatus_table ||' u
 where u.id = p.owner_id
 and p.owner_id is not null;
 
 UPDATE '|| _planets_table ||' as p
 SET current_population = greatest(least(p.current_population + p.current_population
										 * (1.00 + 0.01 * u.research_percent_population) * 
										   t.num_val , p.max_population),100)
 from '|| _userstatus_table ||' as u 
 join classes c on c.name = u.race
 join constants t on t.class = c.id and t.name = ''pop_growth''
 where u.id = p.owner_id
 and p.owner_id is not null;
 
  -- buildings   
 
 update '|| _construction_table||'
 set ticks_remaining = ticks_remaining - 1;

 with built_buildings as 
(select planet_id
	  from '|| _construction_table||'
	  where ticks_remaining = 0
	  group by planet_id)

 update '|| _planets_table ||' p
 set solar_collectors = solar_collectors + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''SC'' and ticks_remaining = 0),0),
 fission_reactors = fission_reactors + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''FR'' and ticks_remaining = 0),0),
 mineral_plants = mineral_plants + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''MP'' and ticks_remaining = 0),0),
 crystal_labs = crystal_labs + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''CL'' and ticks_remaining = 0),0),
 refinement_stations = refinement_stations + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''RS'' and ticks_remaining = 0),0),
 cities = cities + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''CT'' and ticks_remaining = 0),0),
 research_centers = research_centers + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''RC'' and ticks_remaining = 0),0),
 defense_sats = defense_sats + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''DS'' and ticks_remaining = 0),0),
 shield_networks = shield_networks + coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id and building_type = ''SN'' and ticks_remaining = 0),0),
 portal = coalesce((select true from '|| _construction_table||' where planet_id = p.id and building_type = ''PL'' and ticks_remaining = 0),portal),
 portal_under_construction = coalesce((select true from '|| _construction_table||' where planet_id = p.id and building_type = ''PL'' and ticks_remaining != 0),false)
 from built_buildings a
 where p.id = a.planet_id
 and p.owner_id is not null;

 with news_buildings as 
(select user_id,
		building_type,
		sum(n) n
	  from '|| _construction_table||'
	  where ticks_remaining = 0
	  group by user_id, building_type)
,      
ins_news_success as (
    insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, extra_info)
    select nb.user_id, u.empire_id, ''BB'', current_timestamp, true, false, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'),
        ''These building constructions were finished: '' || chr(10) ||
			case when building_type = ''SC'' then n || '' solar collectors''
			when building_type = ''FR'' then n || '' fission reactors''
			when building_type = ''MP'' then n || '' mineral plants''
			when building_type = ''CL'' then n || '' crystal laboratories''
			when building_type = ''RS'' then n || '' refinement stations''
			when building_type = ''CT'' then n || '' cities''
			when building_type = ''RC'' then n || '' research centers''
			when building_type = ''DS'' then n || '' defense satelites''
			when building_type = ''SN'' then n || '' shield networks''
			when building_type = ''PL'' then n || '' portals'' end
     from news_buildings nb
	join '|| _userstatus_table ||' u on u.id = nb.user_id
    ) 

update '|| _userstatus_table ||' u
set construction_flag = 1 
from (select user_id from news_buildings group by user_id) c 
where u.id = c.user_id;
 
 delete from '|| _construction_table||'
 where ticks_remaining = 0;
 
 update '|| _planets_table ||' p
 set total_buildings = solar_collectors + fission_reactors + mineral_plants + crystal_labs + refinement_stations + 
 cities + research_centers + defense_sats + shield_networks + case when portal = true then 1 else 0 end,
 buildings_under_construction = coalesce((select sum(n) from '|| _construction_table||' where planet_id = p.id),0)
 where p.owner_id is not null;
 
 
 
 -- portal coverage
 
 update '|| _planets_table ||' p
 set protection = p4.protection
  from 
 (select p1.id, 
  LEAST(100, 100 * GREATEST(0, 1.0 - sqrt(min(sqrt(power(p1.x-p2.x,2) + 
												  power(p1.y-p2.y,2)))/ (7 + (1.0 + 0.01 * u.research_percent_portals))) )) 
   protection
  from '|| _planets_table ||' p1
  join '|| _planets_table ||' p2 on p1.owner_id = p2.owner_id and p2.portal = true
  join '|| _userstatus_table ||' u on u.id = p1.owner_id
  where p1.owner_id is not null
  group by p1.id, u.research_percent_portals
  ) p4
 where p.id = p4.id;
 
  -- user eco  		
update '|| _userstatus_table ||' u
set 

total_solar_collectors = (select sum(solar_collectors) from '|| _planets_table ||' where owner_id = u.id), 
total_fission_reactors = (select sum(fission_reactors) from '|| _planets_table ||' where owner_id = u.id) , 
total_mineral_plants = (select sum(mineral_plants) from '|| _planets_table ||' where owner_id = u.id), 
total_crystal_labs = (select sum(crystal_labs) from '|| _planets_table ||' where owner_id = u.id),
total_refinement_stations = (select sum(refinement_stations) from '|| _planets_table ||' where owner_id = u.id), 
total_cities = (select sum(cities) from '|| _planets_table ||' where owner_id = u.id),
total_research_centers = (select sum(research_centers) from '|| _planets_table ||' where owner_id = u.id),
total_defense_sats = (select sum(defense_sats) from '|| _planets_table ||' where owner_id = u.id), 
total_shield_networks = (select sum(shield_networks) from '|| _planets_table ||' where owner_id = u.id),
total_portals = (select sum(case when portal = true then 1 else 0 end) from '|| _planets_table ||' where owner_id = u.id),
total_buildings = u.total_solar_collectors + u.total_fission_reactors + u.total_mineral_plants + u.total_crystal_labs + u.total_refinement_stations + 
u.total_cities + u.total_research_centers + u.total_defense_sats + u.total_shield_networks + u.total_portals,

population = (select sum(current_population) from '|| _planets_table ||' where owner_id = u.id),
num_planets = (select count(*) from '|| _planets_table ||' where owner_id = u.id),

research_points_military = u.research_points_military + 1.2 * u.alloc_research_military/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100 
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_military''),1.0)  
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),

research_points_construction = u.research_points_construction + 1.2 * u.alloc_research_construction/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_construction''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_tech = u.research_points_tech + 1.2 * u.alloc_research_tech/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus 
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_tech''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_energy = u.research_points_energy + 1.2 * u.alloc_research_energy/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_energy''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_population = u.research_points_population + 1.2 * u.alloc_research_population/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select (2) from '|| _artefacts_table ||' f where name = ''Rabbit Theorum'' and f.empire_holding_id = u.empire_id),1) * 
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_population''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_culture = u.research_points_culture + 1.2 * u.alloc_research_culture/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select num_val from constants where name = u.race and text_val = ''research_culture''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_operations = u.research_points_operations + 1.2 * u.alloc_research_operations/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_operations''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


research_points_portals = u.research_points_portals + 1.2 * u.alloc_research_portals/100 * 
coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Research''),1)
* (u.total_research_centers * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100.0
 + (case when coalesce((select num_val from constants where name = u.race and text_val = ''race_special_pop_research''),0) != 0
 then u.population / (select num_val from constants where name = u.race and text_val = ''race_special_pop_research'') else 0 end)) * -- foohon bonus
coalesce((select (1.5) from '|| _artefacts_table ||' f where name = ''Playboy Quantum'' and f.empire_holding_id = u.empire_id),1) * 
coalesce((select num_val from constants where name = u.race and text_val = ''research_bonus_portals''),1.0)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Research Laboratory'' and f.empire_holding_id = u.empire_id),1),


energy_production = 
-- solar
coalesce((select num_val from constants where name = u.race and text_val = ''energy_production''),1.0) * (1 + u.research_percent_energy/100.0)* 
	((select ((select num_val from constants where name = ''building_production_solar'') * sum(solar_collectors* (1 + bonus_solar/100.0))) from '|| _planets_table ||' 
	where owner_id = u.id) * coalesce((select num_val from constants where name = u.race and text_val = ''race_special_solar_15''),1.0) * COALESCE(a.dark_mist_effect,1) + 
	(select ((select num_val from constants where name = ''building_production_fission'') * sum(fission_reactors* (1 + bonus_fission/100.0))) from '|| _planets_table ||' 
	where owner_id = u.id))  
	* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Ether Gardens'' and f.empire_holding_id = u.empire_id),1),


energy_decay = greatest(0, u.energy * (select num_val from constants c where c.name = ''energy_decay_factor'')), 
energy_interest = least(u.energy_production, u.energy * 
coalesce((select num_val from constants where name = u.race and text_val = ''race_special_resource_interest''),0)), 

energy_specop_effect = u.energy_production * coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Energy''),0), 

mineral_production = (select sum(mineral_plants* (1 + bonus_mineral/100.0)) from '|| _planets_table ||' 
	where owner_id = u.id) * coalesce((select num_val from constants where name = u.race and text_val = ''mineral_production''),1.0) * 
	coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Mineral''),1)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Mirny Mine'' and f.empire_holding_id = u.empire_id),1), 
mineral_decay = 0, 
mineral_interest = least(u.mineral_production, u.minerals * 
coalesce((select num_val from constants where name = u.race and text_val = ''race_special_resource_interest''),0)),

crystal_production = (select sum(crystal_labs* (1 + bonus_crystal/100.0)) from '|| _planets_table ||' 
	where owner_id = u.id) * coalesce((select num_val from constants where name = u.race and text_val = ''crystal_production''),1.0) * 
	coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Crystal''),1)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Crystal Synthesis'' and f.empire_holding_id = u.empire_id),1),  
crystal_decay = greatest(0, u.crystals * (select num_val from constants c  where c.name = ''crystal_decay_factor'')) 
* coalesce((select (0.25) from '|| _artefacts_table ||' f where name = ''Crystal Recharger'' and f.empire_holding_id = u.empire_id),1), 
crystal_interest =  least(u.crystal_production, u.crystals * 
coalesce((select num_val from constants where name = u.race and text_val = ''race_special_resource_interest''),0)), 
 
ectrolium_production = (select sum(refinement_stations* (1 + bonus_ectrolium/100.0)) from '|| _planets_table ||' 
	where owner_id = u.id) * 
	coalesce((select num_val from constants where name = u.race and text_val = ''ectrolium_production''),1.0)  * 
	coalesce((select (specop_strength/100.0) from app_specops f where name = ''Enlightenment'' and f.user_to_id = u.id and extra_effect = ''Ectrolium''),1)
* coalesce((select (1 + effect1/100.0) from '|| _artefacts_table ||' f where name = ''Foohon Technology'' and f.empire_holding_id = u.empire_id),1),
ectrolium_decay = 0, 
ectrolium_interest = least(u.ectrolium_production, u.ectrolium * 
coalesce((select num_val from constants where name = u.race and text_val = ''race_special_resource_interest''),0)),

buildings_upkeep = (u.total_fission_reactors * (select num_val from constants where name = ''upkeep_fission_reactors'')
 + u.total_mineral_plants * (select num_val from constants where name = ''upkeep_mineral_plants'')
 + u.total_crystal_labs * (select num_val from constants where name = ''upkeep_crystal_labs'')
 + u.total_refinement_stations * (select num_val from constants where name = ''upkeep_refinement_stations'')
 + u.total_cities * (select num_val from constants where name = ''upkeep_cities'')
 + u.total_research_centers * (select num_val from constants where name = ''upkeep_research_centers'')
 + u.total_defense_sats * (select num_val from constants where name = ''upkeep_defense_sats'')
 + u.total_shield_networks * (select num_val from constants where name = ''upkeep_shield_networks'')) * 
 case when (select empire_holding_id from '|| _artefacts_table ||' where name = ''Engineer'' ) = u.empire_id then
 (case when (select empire_holding_id from '|| _artefacts_table ||' where name = ''Engineers Son'' ) = u.empire_id then 0.8 else 0.9 end)
 else 1 end,

portals_upkeep = pow(greatest(0, u.total_portals - 1), 1.2736) * 100.0 / (1 + u.research_percent_portals/100.0), 
units_upkeep = (select 
	(sum(a1.bomber  * u1.bomber) +
	sum(a1.fighter  * u1.fighter) +
	sum(a1.transport  * u1.transport) +
	sum(a1.cruiser  * u1.cruiser) +
	sum(a1.carrier  * u1.carrier) +
	sum(a1.soldier  * u1.soldier) +
	sum(a1.droid  * u1.droid) +
	sum(a1.goliath  * u1.goliath) +
	sum(a1.phantom  * u1.phantom) +
	sum(a1.wizard  * u1.wizard) +
	sum(a1.agent  * u1.agent) +
	sum(a1.ghost  * u1.ghost) +
	sum(a1.exploration  * u1.exploration))
	from '|| _fleet_table ||' a1
	join unit_stats u1 on u1.class_name = ''unit upkeep costs''
	where a1.owner_id = u.id) 
	* coalesce((select (1 - effect1/100.0) from '|| _artefacts_table ||' f where name = ''Military Might'' and f.empire_holding_id = u.empire_id),1)

-- select  SC, r.solar_bonus, a.dark_mist_effect
 from '|| _userstatus_table ||' u2 
 left join 		(select user_to_id, 
		 1*  EXP (SUM (LN (100.0 / (specop_strength + 100.0)))) dark_mist_effect  --EXP (SUM (LN )) is just multiplication
		 from app_specops  a
		 where a.name in (''Black Mist'', ''Dark Web'') and specop_strength > 0
		 group by user_to_id
		)  a on u2.id = a.user_to_id
  left join (select owner_id, sum(bomber) bomber, sum(fighter) fighter, sum(transport) transport,
			 sum(cruiser) cruiser, sum(soldier) soldier, sum(droid) droid, sum(goliath) goliath,
			 sum(phantom) phantom, sum(wizard) wizard, sum(agent) agent, sum(ghost) ghost,
			 sum(exploration) exploration
			 from '|| _fleet_table ||'
			 --join constants c on c.
			 group by owner_id)
			 f on f.owner_id = u2.id
  where u2.id = u.id
;


update '|| _userstatus_table ||' u
set population_upkeep_reduction = case when (select empire_holding_id from '|| _artefacts_table ||' where name = ''Darwinism'' ) = u.empire_id 
	then u.population/315 else least(u.population/350, (portals_upkeep + buildings_upkeep + units_upkeep)) end,
	current_research_funding = (current_research_funding * 0.9) + 
	case when (select empire_holding_id from '|| _artefacts_table ||' where name = ''The Recycler'' ) = u.empire_id 
	then u.energy_decay * u.research_percent_tech/200 else 0 end;


update '|| _unitconstruction_table||'
set ticks_remaining = ticks_remaining -1;

update app_specops
set ticks_left = ticks_left -1
where ticks_left is not null;

update '|| _fleet_table ||' f
set 
bomber  = f.bomber  + coalesce(a.bomber ,0),
fighter  = f.fighter  + coalesce(a.fighter ,0),
transport = f.transport + coalesce(a.transport,0),
cruiser = f.cruiser + coalesce(a.cruiser,0),
carrier = f.carrier + coalesce(a.carrier,0),
soldier = f.soldier + coalesce(a.soldier,0),
droid = f.droid + coalesce(a.droid,0),
goliath = f.goliath + coalesce(a.goliath,0),
phantom = f.phantom + coalesce(a.phantom,0),
wizard = f.wizard + coalesce(a.wizard,0),
agent = f.agent + coalesce(a.agent,0),
ghost = f.ghost + coalesce(a.ghost,0),
exploration = f.exploration + coalesce(a.exploration,0)

from 
(
	select * from
	crosstab
	(
	''
	select user_id, unit_type, sum(n) n
	 from '|| _unitconstruction_table||'
	 where ticks_remaining = 0
	 group by user_id, unit_type
	 order by user_id, unit_type
	'',
	'' 
        VALUES (''''agent'''') , (''''bomber'''') , (''''carrier'''') , (''''cruiser'''') ,
		(''''droid'''') , (''''exploration'''') , (''''fighter'''') , (''''ghost'''') ,  (''''goliath'''') ,
		(''''phantom'''') , (''''soldier'''') , (''''transport'''') , (''''wizard'''') 
    ''
	)
	 as ct
	 ( user_id integer,
	  agent bigint,
		bomber bigint,
		carrier bigint,
		cruiser bigint,
		droid bigint,
		exploration bigint,
		fighter bigint,
		ghost bigint,
		goliath bigint,
		phantom bigint,
		soldier bigint,
		transport bigint,
		wizard bigint
	 )
) a
where a.user_id = f.owner_id and f.main_fleet = true;

with news_fleets as 
(select user_id
	  from '|| _unitconstruction_table||' a 
	  where a.ticks_remaining = 0
	  group by user_id)
,      
ins_news_success as (
    insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, extra_info)
    select n.user_id, u.empire_id, ''UB'', current_timestamp, true, false, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'),
        ''These units constructions were finished: '' ||
            ( select STRING_AGG('' 
			'',case when unit_type = ''wizard'' then n || ''psychics'' 
			when unit_type = ''ghost'' then n || ''ghost ships''   
			when unit_type = ''exploration'' then n || ''exploration  ships''
			else n || '' ''|| unit_type || ''s''  END ) extra_info
     from '|| _unitconstruction_table||'
     where ticks_remaining = 0
     group by user_id

    )     
    as extra_info
    from news_fleets n
    join '|| _userstatus_table ||' u on u.id = n.user_id
)

update '|| _userstatus_table ||' u
set construction_flag = 1 
from (select user_id from news_fleets group by user_id) c 
where u.id = c.user_id;

delete from '|| _unitconstruction_table||'
where ticks_remaining = 0;


update '|| _userstatus_table ||' u
set 
ectrolium_income = ectrolium_production + ectrolium_interest - ectrolium_decay, 
crystal_income = crystal_production + crystal_interest - crystal_decay,
mineral_income = mineral_production + mineral_interest - mineral_decay, 
energy_income =  energy_production + population_upkeep_reduction +  energy_interest - energy_decay + energy_specop_effect
		- buildings_upkeep - portals_upkeep - units_upkeep,
networth = a.total_nw + u.population * (select num_val from constants where name = ''population nw'') 
+ ( 
research_points_military +
research_points_construction +
research_points_tech +
research_points_energy +
research_points_population +
research_points_culture +
research_points_operations +
research_points_portals  ) * (select num_val from constants where name = ''research nw'') 

 from (
 select n.owner_id, coalesce(n.nw,0) + coalesce(fs.fleet_nw,0) as total_nw from
	 (select owner_id, (sum(total_buildings)*(select num_val from constants where name = ''networth_per_building'') +
	 sum(bonus_solar)* 1.25 + sum(bonus_mineral)* 1.45 + sum(bonus_crystal)* 2.25 + sum(bonus_ectrolium) * 1.65  +
	 sum(bonus_fission)* 5.0 +  sum(size)* 1.75) nw
	 from '|| _planets_table ||' p
	 group by owner_id) n
 left join 
	  (select 
		owner_id, 
		sum(a1.bomber  * u2.bomber) +
		sum(a1.fighter  * u2.fighter) +
		sum(a1.transport  * u2.transport) +
		sum(a1.cruiser  * u2.cruiser) +
		sum(a1.carrier  * u2.carrier) +
		sum(a1.soldier  * u2.soldier) +
		sum(a1.droid  * u2.droid) +
		sum(a1.goliath  * u2.goliath) +
		sum(a1.phantom  * u2.phantom) +
		sum(a1.wizard  * u2.wizard) +
		sum(a1.agent  * u2.agent) +
		sum(a1.ghost  * u2.ghost) +
		sum(a1.exploration  * u2.exploration) as fleet_nw
		from '|| _fleet_table ||' a1
		join unit_stats u2 on u2.class_name = ''units nw''
		group by owner_id) fs on fs.owner_id =  n.owner_id
 ) as a
 where u.id = a.owner_id;
 
update '|| _userstatus_table ||' u
set energy = greatest(0, energy + energy_income),
minerals = greatest(0, minerals + mineral_income),
crystals = greatest(0, crystals + crystal_income),
ectrolium = greatest(0, ectrolium + ectrolium_income);
 
-- readiness update
update '|| _userstatus_table ||' u
set fleet_readiness = case when (select empire_holding_id from '|| _artefacts_table ||' where name = ''Churchills Brandy'' ) = u.empire_id and
(select (tick_number%2) from '|| _roundstatus||' where round_number = '|| _round_number||') = 0 
then greatest(-100, least(fleet_readiness_max ,fleet_readiness + case when u.energy <= 0 and (u.buildings_upkeep + u.units_upkeep + u.portals_upkeep)
> u.population_upkeep_reduction then -3 else 3 end)) 
else greatest(-100, least(fleet_readiness_max ,fleet_readiness + case when u.energy <= 0 and (u.buildings_upkeep + u.units_upkeep + u.portals_upkeep)
> u.population_upkeep_reduction then -3 else 2 end))end,
psychic_readiness = greatest(-100, least(psychic_readiness_max ,psychic_readiness + case when u.energy <= 0 and (u.buildings_upkeep + u.units_upkeep + u.portals_upkeep)
> u.population_upkeep_reduction then -3 else 2 end)),
agent_readiness = greatest(-100, least(agent_readiness_max ,agent_readiness + case when u.energy <= 0 and (u.buildings_upkeep + u.units_upkeep + u.portals_upkeep)
> u.population_upkeep_reduction then -3 else 2 end));

-- fleet decay
update '|| _fleet_table ||' a
set  bomber = 0.98* bomber,
fighter  = 0.98 * fighter,
transport  = 0.98 * transport,
cruiser  = 0.98 * cruiser,
carrier  = 0.98 * carrier,
soldier  = 0.98 * soldier,
droid  = 0.98 * droid,
goliath = 0.98 * goliath,
phantom  = 0.98 * phantom,
wizard = 0.98 * wizard,
agent  = 0.98 * agent,
ghost  = 0.98 * ghost,
exploration  = 0.98 * exploration
from '|| _userstatus_table ||' u
where u.id = a.owner_id
and u.energy <= 0 and (u.buildings_upkeep + u.units_upkeep + u.portals_upkeep)
> u.population_upkeep_reduction;



-- research percentages update after nw and research points calucaltion

update '|| _userstatus_table ||' u
set 
research_percent_military = u.research_percent_military + case when u.research_percent_military < (
	case when research_max_military < 200 
	then least(research_max_military, floor(200 * (1 - exp((u.research_points_military+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_military, floor(research_max_military * (1 - exp((u.research_points_military+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_military > (
	case when research_max_military < 200 
	then least(research_max_military, floor(200 * (1 - exp((u.research_points_military+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_military, floor(research_max_military * (1 - exp((u.research_points_military+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,
research_percent_construction = u.research_percent_construction + case when u.research_percent_construction < (
	case when research_max_construction < 200 
	then least(research_max_construction, floor(200 * (1 - exp((u.research_points_construction+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_construction, floor(research_max_construction * (1 - exp((u.research_points_construction+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_construction > (
	case when research_max_construction < 200 
	then least(research_max_construction, floor(200 * (1 - exp((u.research_points_construction+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_construction, floor(research_max_construction * (1 - exp((u.research_points_construction+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,
research_percent_tech = u.research_percent_tech + case when u.research_percent_tech < (
	case when research_max_tech < 200 
	then least(research_max_tech, floor(200 * (1 - exp((u.research_points_tech+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_tech, floor(research_max_tech * (1 - exp((u.research_points_tech+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_tech > (
	case when research_max_tech < 200 
	then least(research_max_tech, floor(200 * (1 - exp((u.research_points_tech+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_tech, floor(research_max_tech * (1 - exp((u.research_points_tech+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,	
research_percent_energy = u.research_percent_energy + case when u.research_percent_energy < (
	case when research_max_energy < 200 
	then least(research_max_energy, floor(200 * (1 - exp((u.research_points_energy+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_energy, floor(research_max_energy * (1 - exp((u.research_points_energy+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_energy > (
	case when research_max_energy < 200 
	then least(research_max_energy, floor(200 * (1 - exp((u.research_points_energy+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_energy, floor(research_max_energy * (1 - exp((u.research_points_energy+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,	
research_percent_population = u.research_percent_population + case when u.research_percent_population < (
	case when research_max_population < 200 
	then least(research_max_population, floor(200 * (1 - exp((u.research_points_population+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_population, floor(research_max_population * (1 - exp((u.research_points_population+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_population > (
	case when research_max_population < 200 
	then least(research_max_population, floor(200 * (1 - exp((u.research_points_population+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_population, floor(research_max_population * (1 - exp((u.research_points_population+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,	
research_percent_culture = u.research_percent_culture + case when u.research_percent_culture < (
	case when research_max_culture < 200 
	then least(research_max_culture, floor(200 * (1 - exp((u.research_points_culture+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_culture, floor(research_max_culture * (1 - exp((u.research_points_culture+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_culture > (
	case when research_max_culture < 200 
	then least(research_max_culture, floor(200 * (1 - exp((u.research_points_culture+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_culture, floor(research_max_culture * (1 - exp((u.research_points_culture+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,	
research_percent_operations = u.research_percent_operations + case when u.research_percent_operations < (
	case when research_max_operations < 200 
	then least(research_max_operations, floor(200 * (1 - exp((u.research_points_operations+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_operations, floor(research_max_operations * (1 - exp((u.research_points_operations+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_operations > (
	case when research_max_operations < 200 
	then least(research_max_operations, floor(200 * (1 - exp((u.research_points_operations+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_operations, floor(research_max_operations * (1 - exp((u.research_points_operations+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end,	
research_percent_portals = u.research_percent_portals + case when u.research_percent_portals < (
	case when research_max_portals < 200 
	then least(research_max_portals, floor(200 * (1 - exp((u.research_points_portals+0.0)/(-10 * u.networth+0.0)))))
	else least(
 coalesce((select (100) from '|| _artefacts_table ||' f where name = ''Playboy Quantum'' and f.empire_holding_id = u.empire_id),0) +
 research_max_portals, floor(
 coalesce((select (100) from '|| _artefacts_table ||' f where name = ''Playboy Quantum'' and f.empire_holding_id = u.empire_id),0) +
 research_max_portals * (1 - exp((u.research_points_portals+0.0)/(-10 * u.networth+0.0)))))
	end
	) then 1 
	when 
	u.research_percent_portals > (
	case when research_max_portals < 200 
	then least(research_max_portals, floor(200 * (1 - exp((u.research_points_portals+0.0)/(-10 * u.networth+0.0)))))
	else least(research_max_portals, floor(research_max_portals * (1 - exp((u.research_points_portals+0.0)/(-10 * u.networth+0.0)))))
	end
	) then -1 
	else 0 end

from '|| _userstatus_table ||' u2

join (
	select id,
	case when research_max_military = 0 then 200 else research_max_military end research_max_military,
	case when research_max_construction = 0 then 200 else research_max_construction end research_max_construction,
	case when research_max_tech = 0 then 200 else research_max_tech end research_max_tech,
	case when research_max_energy = 0 then 200 else research_max_energy end research_max_energy,
	case when research_max_population = 0 then 200 else research_max_population end research_max_population,
	case when research_max_culture = 0 then 200 else research_max_culture end research_max_culture,
	case when research_max_operations = 0 then 200 else research_max_operations end research_max_operations,
	case when research_max_portals = 0 then 200 else research_max_portals end research_max_portals
	from (
	select u3.id, 
max(case when c.name = ''research_max_military'' then
 case when c.num_val is not null then c.num_val end 
 else 0 end )
 research_max_military,
    max(case when c.name = ''research_max_construction'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_construction,
   max(case when c.name = ''research_max_tech'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_tech,
 max(case when c.name = ''research_max_energy'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_energy,
 max(case when c.name = ''research_max_population'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end ) 
 research_max_population,
  max(case when c.name = ''research_max_culture'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_culture,
   max(case when c.name = ''research_max_operations'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_operations,
    max(case when c.name = ''research_max_portals'' then
 case when c.num_val is not null then c.num_val  end 
 else 0 end )
 research_max_portals 
 
 from '|| _userstatus_table ||' u3
 join classes l on l.name = u3.race
 left join constants c on c.class = l.id --and c.name in(''race_special_solar_15'', ''energy_production'')
 group by u3.id ) v
 ) r on r.id = u2.id;
 
 
-- find new nearest portal
update '|| _fleet_table ||' a
	set i = s.i,
	x = s.x,
	y = s.y,
	ticks_remaining = case when a.x = s.x and a.y = s.y then ticks_remaining 
					  else floor(sqrt(pow((a.current_position_x - s.x),2) + pow((a.current_position_y - s.y),2))/c.num_val --num_val is speed 
					  ) end
from 
	(select * from
	(select a.id a_id, a.owner_id, p.id p_id, p.x, p.y, p.i,
	rank() over(partition by a.owner_id, a.id order by (pow((p.x - a.current_position_x),2) + pow((p.y - a.current_position_y),2)) asc)  rn
	from '|| _fleet_table ||' a, '|| _planets_table ||' p
	where a.command_order = 5 --return to main fleet
	and p.owner_id = a.owner_id
	and p.portal = true
	) g where g.rn = 1) s 
join '|| _userstatus_table ||' u on u.id = s.owner_id
join classes l on l.name = u.race
join constants c on c.class = l.id and c.name = ''travel_speed''
where a.id = s.a_id;


/*update '|| _fleet_table ||' f
where f.
*/

-- move fleets 
update '|| _fleet_table ||' a1
	set 
	current_position_x = case when a1.ticks_remaining - 1 > 0 then a1.current_position_x + (a1.x - a1.current_position_x) / (a1.ticks_remaining )
						 else a1.x end,
	current_position_y = case when a1.ticks_remaining - 1 > 0 then a1.current_position_y + (a1.y - a1.current_position_y) / (a1.ticks_remaining )
						else a1.y end,
	ticks_remaining = greatest(0, a1.ticks_remaining -1)
from '|| _fleet_table ||' a2
join '|| _userstatus_table ||' u1 on u1.id = a2.owner_id
join classes l on l.name = u1.race
join constants c on c.class = l.id and c.name = ''travel_speed''
where a1.main_fleet = false  
and a1.id = a2.id;

-- join main fleet
with recalled_fleets as 
(select owner_id, 
		sum(bomber) bomber ,
		sum(fighter ) fighter  ,
		sum(transport ) transport  ,
		sum(cruiser ) cruiser  ,
		sum(carrier ) carrier  ,
		sum(soldier ) soldier  ,
		sum(droid ) droid  ,
		sum(goliath ) goliath  ,
		sum(phantom ) phantom  ,
		sum(agent ) agent  ,
		sum(ghost ) ghost  ,
		sum(exploration) exploration 
	  from '|| _fleet_table ||' a 
	  where a.main_fleet = false
	  and a.command_order = 5
	  and a.ticks_remaining = 0
	  group by owner_id)
      
, join_main_fleet as (
update '|| _fleet_table ||' a1
set
bomber = a1.bomber + b.bomber,
fighter  = a1.fighter  + b.fighter ,
transport  = a1.transport  + b.transport ,
cruiser  = a1.cruiser  + b.cruiser ,
carrier  = a1.carrier  + b.carrier ,
soldier  = a1.soldier  + b.soldier ,
droid  = a1.droid  + b.droid ,
goliath  = a1.goliath  + b.goliath ,
phantom  = a1.phantom  + b.phantom ,
agent  = a1.agent  + b.agent ,
ghost  = a1.ghost  + b.ghost ,
exploration = a1.exploration + b.exploration
from recalled_fleets b
where a1.main_fleet = true and
a1.owner_id = b.owner_id
)
,
ins_news_success as (
	insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, extra_info)
	select e.owner_id, u.empire_id, ''FJ'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'),
        ''Theese fleets have returned: '' ||
       	 case when bomber = 0 then '''' when bomber = 1 then bomber || ''bomber'' || chr(10) else bomber || ''bombers'' || chr(10) END ||
         case when fighter = 0 then '''' when fighter = 1 then fighter ||  ''fighter'' || chr(10) else fighter ||  ''fighters'' ||chr(10) END ||
         case when transport = 0 then '''' when transport = 1 then transport || ''transport'' || chr(10) else transport || ''transports'' ||chr(10) END ||
         case when cruiser = 0 then '''' when cruiser = 1 then cruiser || ''cruiser'' || chr(10) else cruiser || ''cruisers'' ||chr(10) END  ||
         case when carrier = 0 then '''' when carrier = 1 then carrier || ''carrier'' || chr(10) else carrier || ''carriers'' ||chr(10) END ||
         case when soldier = 0 then '''' when soldier = 1 then soldier || ''soldier'' || chr(10) else soldier || ''soldiers'' ||chr(10) END ||
         case when droid = 0 then '''' when droid = 1 then droid || ''droid'' || chr(10) else droid || ''droids'' ||chr(10) END  ||
         case when goliath = 0 then '''' when goliath = 1 then goliath ||  ''goliath'' || chr(10) else goliath || ''goliaths'' ||chr(10) END  ||
         case when phantom = 0 then '''' when phantom = 1 then phantom || ''phantom'' || chr(10)  else phantom || ''phantoms'' ||chr(10) END ||
         case when agent = 0 then '''' when agent = 1 then agent || ''agent'' || chr(10) else agent || ''agents'' ||chr(10)END  ||
         case when ghost = 0 then '''' when ghost = 1 then ghost || ''ghost'' || chr(10) else ghost || ''ghosts'' ||chr(10)END  ||
         case when exploration = 0 then '''' when exploration = 1 then exploration || ''exploration ship'' || chr(10) else exploration || ''exploration ships'' ||chr(10) END as extra_info
	from recalled_fleets e
    join '|| _userstatus_table ||' u on u.id = e.owner_id
)

update '|| _userstatus_table ||' u
set military_flag = case when military_flag != 1 then 2 else 1 end
from (select owner_id from recalled_fleets group by owner_id) c 
where u.id = c.owner_id;


delete from '|| _fleet_table ||' a
where 
a.main_fleet = false
and a.command_order = 5
and a.ticks_remaining = 0;

-- merge
with merge_fl as (
	select owner_id, 
		min(id) id,
		sum(bomber) bomber ,
		sum(fighter ) fighter  ,
		sum(transport ) transport  ,
		sum(cruiser ) cruiser  ,
		sum(carrier ) carrier  ,
		sum(soldier ) soldier  ,
		sum(droid ) droid  ,
		sum(goliath ) goliath  ,
		sum(phantom ) phantom  ,
		sum(agent ) agent  ,
		sum(ghost ) ghost  ,
		sum(exploration) exploration 
	  from '|| _fleet_table ||' a 
	  where a.main_fleet = false
	  and (a.command_order = 3 or a.command_order = 4)
	  and a.ticks_remaining = 0
	  group by owner_id, x, y
),
upd_planet as (
update '|| _fleet_table ||' a1
set
bomber = b.bomber,
fighter  = b.fighter ,
transport  = b.transport ,
cruiser  = b.cruiser ,
carrier  = b.carrier ,
soldier  = b.soldier ,
droid  = b.droid ,
goliath  = b.goliath ,
phantom  = b.phantom ,
agent  = b.agent ,
ghost  = b.ghost ,
exploration =  b.exploration
from merge_fl b
where a1.main_fleet = false and
a1.owner_id = b.owner_id
and a1.id = b.id
),
ins_news_success as (
	insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, extra_info)
	select e.owner_id, u.empire_id, ''FM'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'),
        ''Theese fleets have merged: '' ||
       	 case when bomber = 0 then '''' when bomber = 1 then bomber || ''bomber'' || chr(10) else bomber || ''bombers'' || chr(10) END ||
         case when fighter = 0 then '''' when fighter = 1 then fighter ||  ''fighter'' || chr(10) else fighter ||  ''fighters'' ||chr(10) END ||
         case when transport = 0 then '''' when transport = 1 then transport || ''transport'' || chr(10) else transport || ''transports'' ||chr(10) END ||
         case when cruiser = 0 then '''' when cruiser = 1 then cruiser || ''cruiser'' || chr(10) else cruiser || ''cruisers'' ||chr(10) END  ||
         case when carrier = 0 then '''' when carrier = 1 then carrier || ''carrier'' || chr(10) else carrier || ''carriers'' ||chr(10) END ||
         case when soldier = 0 then '''' when soldier = 1 then soldier || ''soldier'' || chr(10) else soldier || ''soldiers'' ||chr(10) END ||
         case when droid = 0 then '''' when droid = 1 then droid || ''droid'' || chr(10) else droid || ''droids'' ||chr(10) END  ||
         case when goliath = 0 then '''' when goliath = 1 then goliath ||  ''goliath'' || chr(10) else goliath || ''goliaths'' ||chr(10) END  ||
         case when phantom = 0 then '''' when phantom = 1 then phantom || ''phantom'' || chr(10)  else phantom || ''phantoms'' ||chr(10) END ||
         case when agent = 0 then '''' when agent = 1 then agent || ''agent'' || chr(10) else agent || ''agents'' ||chr(10)END  ||
         case when ghost = 0 then '''' when ghost = 1 then ghost || ''ghost'' || chr(10) else ghost || ''ghosts'' ||chr(10)END  ||
         case when exploration = 0 then '''' when exploration = 1 then exploration || ''exploration ship'' || chr(10) else exploration || ''exploration ships'' ||chr(10) END as extra_info
	from merge_fl e
    join '|| _userstatus_table ||' u on u.id = e.owner_id
)

update '|| _userstatus_table ||' u
set military_flag = case when military_flag != 1 then 2 else 1 end -- red flag overrides green
from (select owner_id from merge_fl group by owner_id) c 
where u.id = c.owner_id;


delete from '|| _fleet_table ||' a1
where a1.id in
(select id from 
 (select a.owner_id, a.id, rank() over(partition by a.owner_id, a.x, a.y order by a.id asc) rn
	  from '|| _fleet_table ||' a 
	  where a.main_fleet = false
	  and (a.command_order = 3 or a.command_order = 4)
	  and a.ticks_remaining = 0
) b
where rn > 1
);


-- station
 
-- explore planets

with explored_planets as(
	select p_id, a_id, owner_id, empire_id from (
		select p.id p_id, a.id a_id, a.owner_id, u.empire_id, rank() over(partition by p.id order by a.id asc) rn
		from '|| _planets_table ||' p
		join '|| _fleet_table ||' a on a.target_planet_id = p.id
		join '|| _userstatus_table ||' u on u.id = a.owner_id
		where p.owner_id is null
		and	a.command_order = 10 --explore
		and ticks_remaining = 0
	) a where a.rn = 1
), 
upd_planet as (
	update '|| _planets_table ||' p
	set owner_id = e.owner_id
	from explored_planets e
	where p.id = e.p_id 
),
del_explo as (
	delete from '|| _fleet_table ||' a
	using explored_planets e 
	where e.a_id = a.id 
),
upd_Arti as (
	update '|| _artefacts_table ||' r
	set empire_holding_id = e.empire_id
	from explored_planets e
	where r.on_planet_id = e.p_id 
),
del_scout as (
	delete from '|| _scouting_table||' a
	using explored_planets e
	where a.empire_id = e.empire_id and a.planet_id = e.p_id 
),
ins_scout as (insert into '|| _scouting_table||' (planet_id, empire_id, user_id, scout)
	select e.p_id, e.empire_id, e.owner_id, 1.0
	from explored_planets e
),
ins_news_success as (
	insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, planet_id)
	select e.owner_id, e.empire_id, ''SE'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id
	from explored_planets e
)
update '|| _userstatus_table ||' u
set military_flag = case when military_flag != 1 then 2 else 1 end -- red flag overrides green
from (select owner_id from explored_planets group by owner_id) c 
where u.id = c.owner_id;


with unsucessfull_explos as 
(
	select p.id p_id, a.id a_id, a.owner_id, u.empire_id
	from '|| _planets_table ||' p
	join '|| _fleet_table ||' a on a.target_planet_id = p.id
	join '|| _userstatus_table ||' u on u.id = a.owner_id
	where p.owner_id is not null
	and	a.command_order = 10 --explore
	and ticks_remaining = 0
),
upd_explos as (
	update '|| _fleet_table ||' a
	set command_order = 2
	from unsucessfull_explos u
	where u.a_id = a.id
),
ins_news_failed as (
	insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, planet_id)
	select e.owner_id, e.empire_id, ''UE'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id
	from unsucessfull_explos e
)
update '|| _userstatus_table ||' u
set military_flag = 1 
from (select owner_id from unsucessfull_explos group by owner_id) c 
where u.id = c.owner_id;

-- countdown artis
update '|| _artefacts_table||'
set ticks_left = ticks_left -1 where name = ''Tyrs Justice'' and ticks_left > 0 and empire_holding_id is not null;
update '|| _artefacts_table||'
set ticks_left = ticks_left -1 where name = ''Flying Dutchman'' and ticks_left > 0 and empire_holding_id is not null;
update '|| _artefacts_table||'
set ticks_left = ticks_left -1 where name = ''Terraformer'' and ticks_left > 0 and empire_holding_id is not null;

update '|| _planets_table||'
set size = size +1 where id = (select on_planet_id from '|| _artefacts_table||' where name = ''You Grow, Girl!'');

-- delete empty fleets
delete from '|| _fleet_table ||' a 
where a.main_fleet = false and
bomber = 0 and
fighter  = 0 and
transport  = 0 and
cruiser  = 0 and
carrier  = 0 and
soldier  = 0 and
droid  = 0 and
goliath  = 0 and
phantom  = 0 and
agent  = 0 and
ghost  = 0 and
exploration = 0;

';

execute _sql;
   
_end_ts   := clock_timestamp();


  
END
$$;
 
 
