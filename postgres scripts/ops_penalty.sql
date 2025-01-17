CREATE OR REPLACE function ops_penalty
(gal_nr integer, specop varchar, u_id int)
returns int
LANGUAGE plpgsql AS
$$
declare
	_penalty int;
	_op_type varchar;
	_op_tech int;
	_sql varchar;
	_userstatus_table varchar;
BEGIN
	if gal_nr = 1 then
		_userstatus_table := 'app_userstatus';
	else 
		_userstatus_table := 'galtwo_userstatus';
	end if;
	
	select into _op_type, _op_tech
	o.specop_type, o.tech
	from app_ops o
	where o.name = specop;
	
	_sql = '
	select 
	cast (greatest(0,pow('||_op_tech||' - case when '''||_op_type||''' = ''G'' then u.research_percent_culture
				   when '''||_op_type||''' = ''O'' then u.research_percent_operations
				   end, 1.2)) as int)
	from '||_userstatus_table||' u
	where u.user_id = '||u_id||';
	
	';
	
	execute _sql into _penalty;
	return _penalty;
end 
$$;