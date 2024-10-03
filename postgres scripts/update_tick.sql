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
 
 release lock table "PLANET";
										 
   
  _end_ts   := clock_timestamp();

  RAISE NOTICE 'Execution time in ms = %' , 1000 * (extract(epoch FROM _end_ts - _start_ts));
  
  insert into ticks_log (round, calc_time, dt)
  values ((select max(round_number) from app_roundstatus), 
		  1000 * extract(epoch FROM _end_ts - _start_ts), current_timestamp);
  
END
$$;
