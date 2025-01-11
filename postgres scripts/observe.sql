CREATE OR REPLACE PROCEDURE observe_planets(fleet_id integer default null)
LANGUAGE plpgsql
AS $$
BEGIN

	select * from app_fleet a
	where a.main_fleet = FALSE
	and a.ticks_remaining = 0
	and command_order = 6 --perfrom operation
	and specop = 'Observe Planet'
	and a.id = case when fleet_id is null then a.id else fleet_id end;

END;
$$;