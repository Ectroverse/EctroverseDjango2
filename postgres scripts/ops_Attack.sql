CREATE OR REPLACE function ops_Attack
(gal_nr integer, fleet_id integer, u_id int, specop varchar)
returns double PRECISION
LANGUAGE plpgsql AS
$$
declare
	_op_penalty int;
	_attack double PRECISION;
	_op_type varchar;
	_diff numeric;
	_fleet_table varchar;
	_userstatus_table varchar;
	_ops_table varchar;
	_sql varchar;
BEGIN

	if gal_nr = 1 then
		_userstatus_table := 'app_userstatus';
		_fleet_table := 'app_fleet';
		
		select into _op_type, _diff
		o.specop_type, o.difficulty
		from app_ops o
		where o.name = specop;
	else 
		_userstatus_table := 'galtwo_userstatus';
		_fleet_table := 'galtwo_fleet';
		
		select into _op_type, _diff
		o.specop_type, o.difficulty
		from galtwo_ops o
		where o.name = specop;
	end if;
	
	select ops_penalty(gal_nr, specop, u_id) into _op_penalty;
	
	if _op_penalty >= 150 then
	 	return 0;
	end if;

	_sql = '
	select 
		(0.6 + (0.8/ 255.0) * (cast(random()*255 as int) & 255)) * 
		att.num_val 
		* (case when '''||_op_type||''' = ''O'' then coalesce(f.agent,0) 
				when '''||_op_type||'''= ''G'' then coalesce(f.ghost,0) end)  
		* (1.0 + 0.01 * case when '''||_op_type||''' = ''O'' then a.research_percent_operations  
							 when '''||_op_type||''' = ''G'' then a.research_percent_culture end)
		/ '||_diff||' 
		/ (case when '||_op_penalty||' > 0 then 1 + (0.01 * '||_op_penalty||') else 1 end) 
	from app_fleet f
	join app_userstatus a on a.user_id = f.owner_id
	join classes c on c.name = a.race
	join constants att on att.class = c.id and att.name = case when '''||_op_type||''' = ''O'' then ''agent_coeff''
																when '''||_op_type||''' = ''G'' then ''ghost_coeff'' end
	where f.id = '||fleet_id||';';
	
	execute _sql into _attack;

	return _attack;
end 
$$;