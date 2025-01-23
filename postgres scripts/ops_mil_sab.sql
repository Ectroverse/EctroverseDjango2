CREATE OR REPLACE function ops_sab
(gal_nr integer, unit varchar, d_id int, success float)
returns int
LANGUAGE plpgsql AS
$$
declare
	_per int;
	_userstatus_table varchar;
	_fleet_table varchar;
	_sql varchar;
	_num int;
BEGIN

	if gal_nr = 1 then
		_userstatus_table := 'app_userstatus';
		_fleet_table := 'app_fleet';
	else 
		_userstatus_table := 'galtwo_userstatus';
		_fleet_table := 'galtwo_fleet';
	end if;
		
	if success >= 1.0 then 
		_per := 8;
	else 
		_per := (8.0 / 0.5) * (success - 0.5);
	end if;

	_sql = '
	select least('||unit||', floor('||unit||' * (0.01 * ('|| _per ||' + cast(random()*(3-1)+1 as int)))))
	from '||_fleet_table ||' 
	where owner_id = '|| d_id ||' and main_fleet = true
	';
	
	execute _sql into _num;

	return _num;
end 
$$;