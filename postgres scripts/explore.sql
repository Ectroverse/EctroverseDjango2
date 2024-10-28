CREATE OR REPLACE PROCEDURE explore(ArrayPlanets integer[])
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
   _tmp numeric;
BEGIN 
   _start_ts := clock_timestamp();
   
   
   -- lock planet
   
   
  _end_ts   := clock_timestamp();
  RAISE NOTICE 'Execution time in ms = %' , 1000 * (extract(epoch FROM _end_ts - _start_ts));
end
$$;
   