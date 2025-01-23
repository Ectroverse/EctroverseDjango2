CREATE OR REPLACE function ops_hack
(gal_nr integer, u_id int, d_id int, success float)
returns double PRECISION
LANGUAGE plpgsql AS
$$
declare
	_e_per double PRECISION;
	_userstatus_table varchar;
	_specops_table varchar;
	_sql varchar;
BEGIN

	if gal_nr = 1 then
		_userstatus_table := 'app_userstatus';
		_specops_table := 'app_specops';
	else 
		_userstatus_table := 'galtwo_userstatus';
		_specops_table := 'galtwo_specops';
	end if;
		
	if success >= 1.0 then 
		_e_per := 20;
	else 
		_e_per := least(20.0, (20.0 / 0.6) * (success - 0.4));
	end if;

	_sql = '
	insert into '|| _specops_table ||'
		(user_to_id, user_from_id, specop_type, stealth, extra_effect, name, ticks_left, specop_strength, specop_strength2)
		select '|| d_id ||', '|| u_id ||', ''O'', false, ''None'', ''Hack mainframe'', 
		(case when '|| _e_per ||' > 0 then least(32, round(pow(6,'|| success ||'+0.6))) else 0 end),
		'|| _e_per ||', '|| _e_per ||'
	';
	
	execute _sql;

	return _e_per;
end 
$$;