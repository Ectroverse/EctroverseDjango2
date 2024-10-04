CREATE OR REPLACE PROCEDURE calc_tick()
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
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
				(SC_prod * r.solar_bonus * a.dark_mist_effect + FR_prod ),


/*energy_decay =, 
energy_interest =,
energy_income= , 
energy_specop_effect =, 
mineral_production =,
mineral_decay =, 
mineral_interest = , 
mineral_income = ,
crystal_production = , 
crystal_decay = , 
crystal_interest = , 
crystal_income = , 
ectrolium_production = ,
ectrolium_decay = , 
ectrolium_interest = ,
ectrolium_income = , 
buildings_upkeep = ,
portals_upkeep = , 
population_upkeep_reduction =, */
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
 from (select owner_id, sum(current_population) cur_pop, count(*) total_pl,
	   ((select num_val from constants where name = 'building_production_solar') * sum(solar_collectors* (1 + bonus_solar/100 ))
	    ) SC_prod,
	   sum(solar_collectors) SC,
	   ((select num_val from constants where name = 'building_production_fission') * sum(fission_reactors* (1 + bonus_fission/100 ))
	    ) FR_prod,
	   sum(fission_reactors) FR,
	   
	   sum(mineral_plants) MP,
	   sum(crystal_labs) CL,
	   sum(refinement_stations) RS,
	   sum(cities) CT,
	   sum(research_centers) RC,
	   sum(defense_sats) DS , 
	   sum(shield_networks) SN , 
	   sum(case when portal = true then 1 else 0 end) PL  
	   from "PLANET" p1
	   join app_userstatus u1 on u1.id = p1.owner_id
	   where p1.owner_id is not null
	   group by owner_id) p,
	   
		(select user_to_id, 
		 1*  EXP (SUM (LN (100 / (specop_strength + 100.0)))) dark_mist_effect  --EXP (SUM (LN )) is just multiplication
		 from app_specops  a
		 where a.name in ('Black Mist', 'Dark Web') and specop_strength > 0
		 group by user_to_id
		)  a ,
		
		(select u.id, 
		 max(case when c.name = 'race_special_solar_15' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 solar_bonus,

		 max(case when c.name = 'energy_production' then
		 case when c.num_val is not null then c.num_val else 1 end 
		 else 0 end )
		 race_energy_production
		 
		 from app_userstatus u
		 join classes l on l.name = u.race
		 left join constants c on c.class = l.id and c.name in('race_special_solar_15', 'energy_production')
		 group by u.id
		 ) r
 /*where p.owner_id = a.user_to_id
 and p.owner_id = r.id */
 
 where p.owner_id = u.id   
 and u.id = a.user_to_id
 and r.id = p.owner_id
 and p.owner_id is not null;

 -- networth
 update app_userstatus u
 set networth = n.nw
 from (select owner_id, (sum(total_buildings)*(select num_val from constants where name = 'networth_per_building') +
 sum(bonus_solar)* 1.25 + sum(bonus_mineral)* 1.45 + sum(bonus_crystal)* 2.25 + sum(bonus_ectrolium) * 1.65  +
 sum(bonus_fission)* 5.0 +  sum(size)* 1.75) nw
 from "PLANET" p
 group by owner_id) n
 where n.owner_id  = u.id;
 
 	/*population = 0;
		networth = 0;
		num_planets = 0;
		cmdTickProduction_solar = 0;
		cmdTickProduction_fission = 0;
		cmdTickProduction_mineral = 0;
		cmdTickProduction_crystal = 0;
		cmdTickProduction_ectrolium = 0;
		cmdTickProduction_research = 0;*/
 
 delete from app_construction
 where ticks_remaining = 0;
   
  _end_ts   := clock_timestamp();

  RAISE NOTICE 'Execution time in ms = %' , 1000 * (extract(epoch FROM _end_ts - _start_ts));
  
  insert into ticks_log (round, calc_time_ms, dt)
  values ((select max(round_number) from app_roundstatus), 
		  1000 * extract(epoch FROM _end_ts - _start_ts), current_timestamp);
  
END
$$;

 