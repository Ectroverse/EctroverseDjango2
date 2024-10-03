CREATE OR REPLACE PROCEDURE calc_tick()
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
BEGIN 
   _start_ts := clock_timestamp();
   
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
 shield_networks =shield_networks + case when a.building_type = 'SN' then a.n else 0 end,
 portal = case when a.building_type = 'PL' then true else portal end,
 total_buildings = total_buildings + a.n,
 buildings_under_construction = buildings_under_construction - a.n,
 portal_under_construction = case when a.building_type = 'PL' then false else portal_under_construction end
 from app_construction a
 where p.id = a.planet_id and a.ticks_remaining = 0;
 
 lock table app_userstatus;
 
 
 update app_userstatus u
 set population = cp
 from (select owner_id, sum(current_population) cp
	   from "PLANET"
	   group by owner_id) p
 where p.owner_id = u.id;
 
 
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
  
  insert into ticks_log (round, calc_time, dt)
  values ((select max(round_number) from app_roundstatus), 
		  1000 * extract(epoch FROM _end_ts - _start_ts), current_timestamp);
  
END
$$;
