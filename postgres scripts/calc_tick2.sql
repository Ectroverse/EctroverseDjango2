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

 update '|| _planets_table ||' p
 set solar_collectors = solar_collectors + case when a.building_type = ''SC'' then a.n else 0 end,
 fission_reactors =fission_reactors + case when a.building_type = ''FR'' then a.n else 0 end,
 mineral_plants = mineral_plants + case when a.building_type = ''MP'' then a.n else 0 end,
 crystal_labs = crystal_labs + case when a.building_type = ''CL'' then a.n else 0 end,
 refinement_stations = refinement_stations + case when a.building_type = ''RS'' then a.n else 0 end,
 cities = cities + case when a.building_type = ''CT'' then a.n else 0 end,
 research_centers = research_centers + case when a.building_type = ''RC'' then a.n else 0 end,
 defense_sats = defense_sats + case when a.building_type = ''DS'' then a.n else 0 end,
 shield_networks = shield_networks + case when a.building_type = ''SN'' then a.n else 0 end,
 portal = case when a.building_type = ''PL'' then true else portal end,
 buildings_under_construction = buildings_under_construction - a.n,
 portal_under_construction = case when a.building_type = ''PL'' then false else portal_under_construction end
 from '|| _construction_table||' a
 where p.id = a.planet_id and a.ticks_remaining = 0
 and p.owner_id is not null;

 with news_buildings as 
(select user_id
	  from '|| _construction_table||' a 
	  where a.ticks_remaining = 0
	  group by user_id)
,      
ins_news_success as (
    insert into '|| _news_table||' ( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, extra_info)
    select n.user_id, u.empire_id, ''BB'', current_timestamp, true, false, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'),
        ''These building constructions were finished: '' ||
            ( select STRING_AGG(''
			'',
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
			) extra_info
     from '|| _construction_table||'
     where ticks_remaining = 0
     group by user_id

    )     
    as extra_info
    from news_buildings n
    join '|| _userstatus_table ||' u on u.id = n.user_id
)

update '|| _userstatus_table ||' u
set construction_flag = 1 
from (select user_id from news_buildings group by user_id) c 
where u.id = c.user_id;
 
 delete from '|| _construction_table||'
 where ticks_remaining = 0;
 
 update '|| _planets_table ||' p
 set total_buildings = solar_collectors + fission_reactors + mineral_plants + crystal_labs + refinement_stations + 
 cities + research_centers + defense_sats + shield_networks + case when portal = true then 1 else 0 end
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

research_points_military = u.research_points_military + 1.2 * u.alloc_research_military * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100 
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_military ,

research_points_construction = u.research_points_construction + 1.2 * u.alloc_research_construction * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
  + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_construction ,


research_points_tech = u.research_points_tech + 1.2 * u.alloc_research_tech * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus 
research_bonus_tech ,


research_points_energy = u.research_points_energy + 1.2 * u.alloc_research_energy * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_energy ,


research_points_population = u.research_points_population + 1.2 * u.alloc_research_population * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_population ,


research_points_culture = u.research_points_culture + 1.2 * u.alloc_research_culture * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_culture ,


research_points_operations = u.research_points_operations + 1.2 * u.alloc_research_operations * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus 
research_bonus_operations ,


research_points_portals = u.research_points_portals + 1.2 * u.alloc_research_portals * 
case when b.extra_effect = ''Research'' then ( 1 + b.Enlightenment_effect/100.0) else 1 end
* (RC * (select num_val from constants where name = ''building_production_research'') + u.current_research_funding/100.0
 + case when race_special_pop_research != 0 then cur_pop / race_special_pop_research else 0 end) * -- foohon bonus
research_bonus_portals ,


population = cur_pop,
num_planets = total_pl,
energy_production = 
-- solar
r.race_energy_production* (1 + u.research_percent_energy/100.0)* 
				(SC_prod * r.race_special_solar_15 * COALESCE(a.dark_mist_effect,1) + FR_prod ) * 
				case when b.extra_effect = ''Energy'' then (1 + b.Enlightenment_effect/100.0) else 1 end
				* coalesce((select (1 + effect1/100.0) from app_Artefacts f where name = ''Ether Gardens'' and f.empire_holding_id = u.empire_id),1),


energy_decay = greatest(0, u.energy * (select num_val from constants c where c.name = ''energy_decay_factor'')), 
energy_interest =  least(u.energy_production, u.energy * r.race_special_resource_interest), 

--energy_specop_effect =, 
mineral_production = MP_prod * r.race_mineral_production * case when b.extra_effect = ''Mineral'' then (1 + b.Enlightenment_effect/100.0) else 1 end, 
mineral_decay = 0, 
mineral_interest = least(u.mineral_production, u.minerals * r.race_special_resource_interest), 

crystal_production = CL_prod * r.race_crystal_production * case when b.extra_effect = ''Crystal'' then (1 + b.Enlightenment_effect/100.0) else 1 end ,  
crystal_decay = greatest(0, u.crystals * (select num_val from constants c  where c.name = ''crystal_decay_factor'')), 
crystal_interest =  least(u.crystal_production, u.crystals * r.race_special_resource_interest), 
 
ectrolium_production = RS_prod * r.race_ectrolium_production  * case when b.extra_effect = ''Ectrolium'' then (1 + b.Enlightenment_effect/100.0) else 1 end ,
ectrolium_decay = 0, 
ectrolium_interest = least(u.ectrolium_production, u.ectrolium * r.race_special_resource_interest),

buildings_upkeep = SC * (select num_val from constants where name = ''upkeep_solar_collectors'')
 + FR * (select num_val from constants where name = ''upkeep_fission_reactors'')
 + MP * (select num_val from constants where name = ''upkeep_mineral_plants'')
 + CL * (select num_val from constants where name = ''upkeep_crystal_labs'')
 + RS * (select num_val from constants where name = ''upkeep_refinement_stations'')
 + CT * (select num_val from constants where name = ''upkeep_cities'')
 + RC * (select num_val from constants where name = ''upkeep_research_centers'')
 + DS * (select num_val from constants where name = ''upkeep_defense_sats'')
 + SN * (select num_val from constants where name = ''upkeep_shield_networks''),

portals_upkeep = pow(greatest(0, PL - 1), 1.2736) * 100.0 / (1 + u.research_percent_portals/100.0), 
units_upkeep = COALESCE(fs.fleet_cost, 0),

total_solar_collectors = SC, 
total_fission_reactors = FR , 
total_mineral_plants = MP, 
total_crystal_labs = CL,
total_refinement_stations = RS, 
total_cities = CT,
total_research_centers = RC,
total_defense_sats = DS, 
total_shield_networks = SN,
total_portals = PL,
total_buildings = SC + FR + MP + CL + RS + CT + RC + DS + SN + PL

-- select  SC, r.solar_bonus, a.dark_mist_effect
 from '|| _userstatus_table ||' u2
 join (select owner_id, sum(current_population) cur_pop, count(*) total_pl,
	   ((select num_val from constants where name = ''building_production_solar'') * sum(solar_collectors* (1 + bonus_solar/100.0 ))
	    ) SC_prod,
	   sum(solar_collectors) SC,
	   ((select num_val from constants where name = ''building_production_fission'') * sum(fission_reactors* (1 + bonus_fission/100.0 ))
	    ) FR_prod,
	   sum(fission_reactors) FR,
	   sum(mineral_plants * (1 + bonus_mineral/100.0 )) MP_prod, 
	   sum(mineral_plants) MP,
	   sum(crystal_labs* (1 + bonus_crystal/100.0 )) CL_prod,
	   sum(crystal_labs) CL,
	   sum(refinement_stations* (1 + bonus_ectrolium/100.0 )) RS_prod,
	   sum(refinement_stations) RS,
	   sum(cities) CT,
	   sum(research_centers) RC,
	   sum(defense_sats) DS , 
	   sum(shield_networks) SN , 
	   sum(case when portal = true then 1 else 0 end) PL ,
	   sum(population) pop
	   from '|| _planets_table ||' p1
	   join '|| _userstatus_table ||' u1 on u1.id = p1.owner_id
	   where p1.owner_id is not null
	   group by owner_id) p on p.owner_id = u2.id  
  left join (select user_to_id, 
		 (specop_strength / 100.0) Enlightenment_effect,
		 extra_effect
		 from app_specops  a
		 where a.name in (''Enlightenment'') and specop_strength > 0
		) b on u2.id = b.user_to_id

  join (select id, race_special_pop_research,
		 
		case when race_special_solar_15 = 0 then 1 else race_special_solar_15 end,
		case when race_special_resource_interest = 0 then 1 else race_special_resource_interest end,
		
		case when race_energy_production = 0 then 1 else race_energy_production end,
		case when race_mineral_production = 0 then 1 else race_mineral_production end,
		case when race_crystal_production = 0 then 1 else race_crystal_production end,
		case when race_ectrolium_production = 0 then 1 else race_ectrolium_production end,
		
		case when research_bonus_military = 0 then 1 else research_bonus_military end,
		case when research_bonus_construction = 0 then 1 else research_bonus_construction end,
		case when research_bonus_tech = 0 then 1 else research_bonus_tech end,
		case when research_bonus_energy = 0 then 1 else research_bonus_energy end,
		case when research_bonus_population = 0 then 1 else research_bonus_population end,
		case when research_bonus_culture = 0 then 1 else research_bonus_culture end,
		case when research_bonus_operations = 0 then 1 else research_bonus_operations end,
		case when research_bonus_portals = 0 then 1 else research_bonus_portals end
		from (
		
			 select u3.id, 
			 max(case when c.name = ''race_special_pop_research'' then c.num_val else 0 end ) race_special_pop_research,
			 max(case when c.name = ''race_special_solar_15'' then c.num_val else 0 end ) race_special_solar_15,
			 max(case when c.name = ''energy_production'' then c.num_val else 0 end ) race_energy_production,
			 max(case when c.name = ''mineral_production'' then c.num_val  else 0 end ) race_mineral_production,
			 max(case when c.name = ''crystal_production'' then c.num_val else 0 end ) race_crystal_production,
			 max(case when c.name = ''ectrolium_production'' then	c.num_val else 0 end ) race_ectrolium_production,
			 max(case when c.name = ''race_special_resource_interest'' then c.num_val else 0 end ) race_special_resource_interest,
			 max(case when c.name = ''research_bonus_military'' then c.num_val else 0 end ) research_bonus_military,
			 max(case when c.name = ''research_bonus_construction'' then c.num_val else 0 end ) research_bonus_construction,
			 max(case when c.name = ''research_bonus_tech'' then c.num_val else 0 end ) research_bonus_tech,
			 max(case when c.name = ''research_bonus_energy'' then c.num_val else 0 end ) research_bonus_energy,
			 max(case when c.name = ''research_bonus_population'' then c.num_val else 0 end ) research_bonus_population,
			 max(case when c.name = ''research_bonus_culture'' then c.num_val else 0 end ) research_bonus_culture,
			 max(case when c.name = ''research_bonus_operations'' then c.num_val else 0 end ) research_bonus_operations,
			 max(case when c.name = ''research_bonus_portals'' then c.num_val else 0 end ) research_bonus_portals
			 
			 from '|| _userstatus_table ||' u3
			 join classes l on l.name = u3.race
			 left join constants c on c.class = l.id --and c.name in(''race_special_solar_15'', ''energy_production'')
			 group by u3.id
			 ) g
		 ) r on r.id = u2.id
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
  left join 
  (select 
	owner_id, 
	sum(a1.bomber  * u1.bomber) +
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
	sum(a1.exploration  * u1.exploration) as fleet_cost
	from '|| _fleet_table ||' a1
	join unit_stats u1 on u1.class_name = ''unit upkeep costs''
	group by owner_id) fs on fs.owner_id =  u2.id 
where u2.id = u.id
;


update '|| _userstatus_table ||' u
set population_upkeep_reduction = least(population_upkeep_reduction, (portals_upkeep + buildings_upkeep + units_upkeep));


update '|| _unitconstruction_table||'
set ticks_remaining = ticks_remaining -1;



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
set fleet_readiness = greatest(-100, least(fleet_readiness_max ,fleet_readiness + case when u.energy <= 0 then -3 else 2 end)) ,
psychic_readiness = greatest(-100, least(psychic_readiness_max ,psychic_readiness + case when u.energy <= 0 then -3 else 2 end)),
agent_readiness = greatest(-100, least(agent_readiness_max ,agent_readiness + case when u.energy <= 0 then -3 else 2 end));

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
and u.energy <= 0;



-- research percentages update after nw and research points calucaltion

update '|| _userstatus_table ||' u
set 
research_percent_military = u.research_percent_military + case when u.research_percent_military < (
	case when research_max_military < 200 
	then least(research_max_military, floor(200 * (1 - exp(u.research_points_military/(-10 * u.networth)))))
	else least(research_max_military, floor(research_max_military * (1 - exp(u.research_points_military/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_military > (
	case when research_max_military < 200 
	then least(research_max_military, floor(200 * (1 - exp(u.research_points_military/(-10 * u.networth)))))
	else least(research_max_military, floor(research_max_military * (1 - exp(u.research_points_military/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,
research_percent_construction = u.research_percent_construction + case when u.research_percent_construction < (
	case when research_max_construction < 200 
	then least(research_max_construction, floor(200 * (1 - exp(u.research_points_construction/(-10 * u.networth)))))
	else least(research_max_construction, floor(research_max_construction * (1 - exp(u.research_points_construction/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_construction > (
	case when research_max_construction < 200 
	then least(research_max_construction, floor(200 * (1 - exp(u.research_points_construction/(-10 * u.networth)))))
	else least(research_max_construction, floor(research_max_construction * (1 - exp(u.research_points_construction/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,
research_percent_tech = u.research_percent_tech + case when u.research_percent_tech < (
	case when research_max_tech < 200 
	then least(research_max_tech, floor(200 * (1 - exp(u.research_points_tech/(-10 * u.networth)))))
	else least(research_max_tech, floor(research_max_tech * (1 - exp(u.research_points_tech/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_tech > (
	case when research_max_tech < 200 
	then least(research_max_tech, floor(200 * (1 - exp(u.research_points_tech/(-10 * u.networth)))))
	else least(research_max_tech, floor(research_max_tech * (1 - exp(u.research_points_tech/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,	
research_percent_energy = u.research_percent_energy + case when u.research_percent_energy < (
	case when research_max_energy < 200 
	then least(research_max_energy, floor(200 * (1 - exp(u.research_points_energy/(-10 * u.networth)))))
	else least(research_max_energy, floor(research_max_energy * (1 - exp(u.research_points_energy/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_energy > (
	case when research_max_energy < 200 
	then least(research_max_energy, floor(200 * (1 - exp(u.research_points_energy/(-10 * u.networth)))))
	else least(research_max_energy, floor(research_max_energy * (1 - exp(u.research_points_energy/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,	
research_percent_population = u.research_percent_population + case when u.research_percent_population < (
	case when research_max_population < 200 
	then least(research_max_population, floor(200 * (1 - exp(u.research_points_population/(-10 * u.networth)))))
	else least(research_max_population, floor(research_max_population * (1 - exp(u.research_points_population/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_population > (
	case when research_max_population < 200 
	then least(research_max_population, floor(200 * (1 - exp(u.research_points_population/(-10 * u.networth)))))
	else least(research_max_population, floor(research_max_population * (1 - exp(u.research_points_population/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,	
research_percent_culture = u.research_percent_culture + case when u.research_percent_culture < (
	case when research_max_culture < 200 
	then least(research_max_culture, floor(200 * (1 - exp(u.research_points_culture/(-10 * u.networth)))))
	else least(research_max_culture, floor(research_max_culture * (1 - exp(u.research_points_culture/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_culture > (
	case when research_max_culture < 200 
	then least(research_max_culture, floor(200 * (1 - exp(u.research_points_culture/(-10 * u.networth)))))
	else least(research_max_culture, floor(research_max_culture * (1 - exp(u.research_points_culture/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,	
research_percent_operations = u.research_percent_operations + case when u.research_percent_operations < (
	case when research_max_operations < 200 
	then least(research_max_operations, floor(200 * (1 - exp(u.research_points_operations/(-10 * u.networth)))))
	else least(research_max_operations, floor(research_max_operations * (1 - exp(u.research_points_operations/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_operations > (
	case when research_max_operations < 200 
	then least(research_max_operations, floor(200 * (1 - exp(u.research_points_operations/(-10 * u.networth)))))
	else least(research_max_operations, floor(research_max_operations * (1 - exp(u.research_points_operations/(-10 * u.networth)))))
	end
	) then -1 
	else 0 end,	
research_percent_portals = u.research_percent_portals + case when u.research_percent_portals < (
	case when research_max_portals < 200 
	then least(research_max_portals, floor(200 * (1 - exp(u.research_points_portals/(-10 * u.networth)))))
	else least(research_max_portals, floor(research_max_portals * (1 - exp(u.research_points_portals/(-10 * u.networth)))))
	end
	) then 1 
	when 
	u.research_percent_portals > (
	case when research_max_portals < 200 
	then least(research_max_portals, floor(200 * (1 - exp(u.research_points_portals/(-10 * u.networth)))))
	else least(research_max_portals, floor(research_max_portals * (1 - exp(u.research_points_portals/(-10 * u.networth)))))
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
	update app_artefacts r
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

select to_char(100 * extract(epoch FROM _end_ts - _start_ts), 'FM9999999999.99999999') into _retstr;

--RAISE NOTICE 'Execution time in ms = %' , _retstr;

_sql := 
'insert into '|| _ticks_log_table||' (round, calc_time_ms, dt)
values ('|| _round_number||' , '|| _retstr|| ', current_timestamp);
';

execute _sql;

EXCEPTION WHEN OTHERS THEN
_end_ts   := clock_timestamp();
select to_char(100 * extract(epoch FROM _end_ts - _start_ts), 'FM9999999999.99999999') into _retstr;
--RAISE NOTICE 'error msg is %', SQLERRM;
_sql := 
'insert into '|| _ticks_log_table||' (round, calc_time_ms, dt, error)
values ('|| _round_number||' , '|| _retstr|| ', current_timestamp, '''|| 'SQLSTATE: ' || SQLSTATE || ' SQLERRM: ' || SQLERRM ||''');
';
execute _sql;
  
END
$$;
