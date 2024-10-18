CREATE OR REPLACE PROCEDURE calc_tick()
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
   _tmp numeric;
BEGIN 
   _start_ts := clock_timestamp();
 
 -- population  
 lock table "PLANET";
  
 UPDATE "PLANET" p
 SET max_population = ((select num_val from constants where name = 'building_production_cities') 
					   * cities +  size * 
					  (select num_val from constants where name = 'population_size_factor') 
					  )* (1.00 + 0.01 * u.research_percent_population)
 from app_userstatus u
 where u.id = p.owner_id
 and p.owner_id is not null;
 
 UPDATE "PLANET" as p
 SET current_population = greatest(least(p.current_population + p.current_population
										 * (1.00 + 0.01 * u.research_percent_population) * 
										   t.num_val , p.max_population),100)
 from app_userstatus as u 
 join classes c on c.name = u.race
 join constants t on t.class = c.id and t.name = 'pop_growth'
 where u.id = p.owner_id
 and p.owner_id is not null;
 
  -- buildings   
 lock table app_construction;
 
 update app_construction
 set ticks_remaining = ticks_remaining - 1;

 update "PLANET" p
 set solar_collectors = solar_collectors + case when a.building_type = 'SC' then a.n else 0 end,
 fission_reactors =fission_reactors + case when a.building_type = 'FR' then a.n else 0 end,
 mineral_plants = mineral_plants + case when a.building_type = 'MP' then a.n else 0 end,
 crystal_labs = crystal_labs + case when a.building_type = 'CL' then a.n else 0 end,
 refinement_stations = refinement_stations + case when a.building_type = 'RS' then a.n else 0 end,
 cities = cities + case when a.building_type = 'CT' then a.n else 0 end,
 research_centers = research_centers + case when a.building_type = 'RC' then a.n else 0 end,
 defense_sats = defense_sats + case when a.building_type = 'DS' then a.n else 0 end,
 shield_networks = shield_networks + case when a.building_type = 'SN' then a.n else 0 end,
 portal = case when a.building_type = 'PL' then true else portal end,
 buildings_under_construction = buildings_under_construction - a.n,
 portal_under_construction = case when a.building_type = 'PL' then false else portal_under_construction end
 from app_construction a
 where p.id = a.planet_id and a.ticks_remaining = 0
 and p.owner_id is not null;
 
 update "PLANET" p
 set total_buildings = solar_collectors + fission_reactors + mineral_plants + crystal_labs + refinement_stations + 
 cities + research_centers + defense_sats + shield_networks + case when portal = true then 1 else 0 end
 where p.owner_id is not null;
 -- portal coverage
 
 update "PLANET" p
 set protection = p4.protection
  from 
 (select p1.id, 
  LEAST(100, 100 * GREATEST(0, 1.0 - sqrt(min(sqrt(power(p1.x-p2.x,2) + 
												  power(p1.y-p2.y,2)))/ (7 + (1.0 + 0.01 * u.research_percent_portals))) )) 
   protection
  from "PLANET" p1
  join "PLANET" p2 on p1.owner_id = p2.owner_id and p2.portal = true
  join app_userstatus u on u.id = p1.owner_id
  where p1.owner_id is not null
  group by p1.id, u.research_percent_portals
  ) p4
 where p.id = p4.id;
 
								
 -- user eco  		
lock table app_userstatus;

update app_userstatus u
set population = cur_pop,
num_planets = total_pl,
energy_production = 
-- solar
r.race_energy_production* (1 + u.research_percent_energy/100)* 
				(SC_prod * r.solar_bonus * a.dark_mist_effect + FR_prod ) * 
				case when b.extra_effect = 'Energy' then b.Enlightenment_effect else 1 end,


energy_decay = greatest(0, u.energy * (select num_val from constants c where c.name = 'energy_decay_factor')), 
energy_interest =  least(u.energy_production, u.energy * r.race_special_resource_interest), 

--energy_specop_effect =, 
mineral_production = MP_prod * r.race_mineral_production * case when b.extra_effect = 'Mineral' then b.Enlightenment_effect else 1 end, 
mineral_decay = 0, 
mineral_interest = least(u.mineral_production, u.minerals * r.race_special_resource_interest), 

crystal_production = CL_prod * r.race_crystal_production * case when b.extra_effect = 'Crystal' then b.Enlightenment_effect else 1 end ,  
crystal_decay = greatest(0, u.crystals * (select num_val from constants c  where c.name = 'crystal_decay_factor')), 
crystal_interest =  least(u.crystal_production, u.crystals * r.race_special_resource_interest), 
 
ectrolium_production = RS_prod * r.race_ectrolium_production  * case when b.extra_effect = 'Ectrolium' then b.Enlightenment_effect else 1 end ,
ectrolium_decay = 0, 
ectrolium_interest = least(u.ectrolium_production, u.ectrolium * r.race_special_resource_interest),

buildings_upkeep = SC * (select num_val from constants where name = 'upkeep_solar_collectors')
 + FR * (select num_val from constants where name = 'upkeep_fission_reactors')
 + MP * (select num_val from constants where name = 'upkeep_mineral_plants')
 + CL * (select num_val from constants where name = 'upkeep_crystal_labs')
 + RS * (select num_val from constants where name = 'upkeep_refinement_stations')
 + CT * (select num_val from constants where name = 'upkeep_cities')
 + RC * (select num_val from constants where name = 'upkeep_research_centers')
 + DS * (select num_val from constants where name = 'upkeep_defense_sats')
 + SN * (select num_val from constants where name = 'upkeep_shield_networks'),

portals_upkeep = greatest(0 , pow(greatest(1, PL - 1), 1.2736) * 10000 / (1 + u.research_percent_portals/100)), 
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
 from app_userstatus u2
 join (select owner_id, sum(current_population) cur_pop, count(*) total_pl,
	   ((select num_val from constants where name = 'building_production_solar') * sum(solar_collectors* (1 + bonus_solar/100 ))
	    ) SC_prod,
	   sum(solar_collectors) SC,
	   ((select num_val from constants where name = 'building_production_fission') * sum(fission_reactors* (1 + bonus_fission/100 ))
	    ) FR_prod,
	   sum(fission_reactors) FR,
	   sum(mineral_plants * (1 + bonus_mineral/100 )) MP_prod, 
	   sum(mineral_plants) MP,
	   sum(crystal_labs* (1 + bonus_crystal/100 )) CL_prod,
	   sum(crystal_labs) CL,
	   sum(refinement_stations* (1 + bonus_ectrolium/100 )) RS_prod,
	   sum(refinement_stations) RS,
	   sum(cities) CT,
	   sum(research_centers) RC,
	   sum(defense_sats) DS , 
	   sum(shield_networks) SN , 
	   sum(case when portal = true then 1 else 0 end) PL ,
	   sum(population) pop
	   from "PLANET" p1
	   join app_userstatus u1 on u1.id = p1.owner_id
	   where p1.owner_id is not null
	   group by owner_id) p on p.owner_id = u2.id  
  left join (select user_to_id, 
		 (specop_strength / 100.0) Enlightenment_effect,
		 extra_effect
		 from app_specops  a
		 where a.name in ('Enlightenment') and specop_strength > 0
		) b on u2.id = b.user_to_id

  join (select u3.id, 
		 max(case when c.name = 'race_special_solar_15' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 solar_bonus,
		 max(case when c.name = 'energy_production' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_energy_production,
		 max(case when c.name = 'mineral_production' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_mineral_production,
		 max(case when c.name = 'crystal_production' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_crystal_production,
		 max(case when c.name = 'ectrolium_production' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_ectrolium_production,
		 max(case when c.name = 'race_special_resource_interest' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_special_resource_interest
		 from app_userstatus u3
		 join classes l on l.name = u3.race
		 left join constants c on c.class = l.id --and c.name in('race_special_solar_15', 'energy_production')
		 group by u3.id
		 ) r on r.id = u2.id
 left join 		(select user_to_id, 
		 1*  EXP (SUM (LN (100 / (specop_strength + 100.0)))) dark_mist_effect  --EXP (SUM (LN )) is just multiplication
		 from app_specops  a
		 where a.name in ('Black Mist', 'Dark Web') and specop_strength > 0
		 group by user_to_id
		)  a on u2.id = a.user_to_id
  left join (select owner_id, sum(bomber) bomber, sum(fighter) fighter, sum(transport) transport,
			 sum(cruiser) cruiser, sum(soldier) soldier, sum(droid) droid, sum(goliath) goliath,
			 sum(phantom) phantom, sum(wizard) wizard, sum(agent) agent, sum(ghost) ghost,
			 sum(exploration) exploration
			 from app_fleet
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
	from app_fleet a1
	join unit_stats u1 on u1.class_name = 'unit upkeep costs'
	group by owner_id) fs on fs.owner_id =  u2.id 
;

update app_userstatus u
set population_upkeep_reduction = least(population_upkeep_reduction, (portals_upkeep + buildings_upkeep + units_upkeep));

update app_userstatus u
set 
ectrolium_income = ectrolium_production + ectrolium_interest - ectrolium_decay, 
crystal_income = crystal_production + crystal_interest - crystal_decay,
mineral_income = mineral_production + mineral_interest - mineral_decay, 
energy_income =  energy_production + population_upkeep_reduction +  energy_interest - energy_decay + energy_specop_effect
		- buildings_upkeep - portals_upkeep - units_upkeep,
networth = a.total_nw 
 from (
 select n.owner_id, n.nw + fs.fleet_nw as total_nw from
	 (select owner_id, (sum(total_buildings)*(select num_val from constants where name = 'networth_per_building') +
	 sum(bonus_solar)* 1.25 + sum(bonus_mineral)* 1.45 + sum(bonus_crystal)* 2.25 + sum(bonus_ectrolium) * 1.65  +
	 sum(bonus_fission)* 5.0 +  sum(size)* 1.75) nw
	 from "PLANET" p
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
		from app_fleet a1
		join unit_stats u2 on u2.class_name = 'units nw'
		group by owner_id) fs on fs.owner_id =  n.owner_id
 ) as a
 where u.id = a.owner_id;
 
update app_userstatus u
set energy = energy + energy_income,
minerals = crystals + mineral_income,
crystals = crystals + crystal_income,
ectrolium = ectrolium + ectrolium_income;
 
 delete from app_construction
 where ticks_remaining = 0;
   
  _end_ts   := clock_timestamp();

  RAISE NOTICE 'Execution time in ms = %' , 1000 * (extract(epoch FROM _end_ts - _start_ts));
  
  insert into ticks_log (round, calc_time_ms, dt)
  values ((select max(round_number) from app_roundstatus), 
		  1000 * extract(epoch FROM _end_ts - _start_ts), current_timestamp);
  
END
$$;
 
 