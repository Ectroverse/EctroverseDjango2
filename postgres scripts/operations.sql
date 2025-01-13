CREATE OR REPLACE PROCEDURE operations(gal_nr varchar)
LANGUAGE plpgsql AS
$$
declare
   _start_ts timestamptz;
   _end_ts   timestamptz;
   _timest timestamptz;
   _tmp numeric;
   _round_number int;
   _retstr varchar(255);
   _retnum numeric;
   _retbool boolean;
   
	_ops_table varchar(255);
	_planets_table varchar(255);
	_userstatus_table varchar(255);
    _fleet_table varchar(255);
	_scouting_table varchar(255);
	_news_table varchar(255);
	_artefacts_table varchar(255);
	_specops_table varchar(255);
	
	_roundstatus varchar(255);
	_sql varchar;
BEGIN 
   _start_ts := clock_timestamp();
   
   -- for each type of round (slow/fast) we chose the tables accordingly
	_ops_table := 'app_ops';
	if gal_nr = 'slow' then
		_planets_table := '"PLANET"';
		_userstatus_table := 'app_userstatus';
		_fleet_table := 'app_fleet';
		_scouting_table := 'app_scouting';
		_news_table := 'app_news';
		_roundstatus := 'app_roundstatus';
		_artefacts_table := 'app_artefacts';
		_specops_table := 'app_specops';
	else 
		_planets_table := '"PLANETS"';
		_userstatus_table := 'galtwo_userstatus';
		_fleet_table := 'galtwo_fleet';
		_scouting_table := 'galtwo_scouting';
		_news_table := 'galtwo_news';
		_roundstatus := 'galtwo_roundstatus';
		_artefacts_table := 'galtwo_artefacts';
		_specops_table := 'galtwo_specops';
	end if;

	EXECUTE format('select max(round_number) from  %s ;', _roundstatus)
	INTO _round_number; 


	EXECUTE 'select is_running from '|| _roundstatus || ' where round_number = ' || _round_number
	INTO _retbool; 

	-- do not calc tick if the round timer is stopped	
	IF _retbool = false THEN
	  return;
	END IF;

 _sql :=
 ' 
 lock table '|| _planets_table ||';
 lock table '|| _userstatus_table ||';
 lock table '|| _fleet_table ||';
 lock table '|| _scouting_table||';
 lock table '|| _news_table||';
 lock table '|| _specops_table||';

--operations
	update '|| _fleet_table ||'
	set random = random()*(2147483647-0)
	where main_fleet = FALSE
	and command_order = 6 --perform operation
	and ticks_remaining = 0;

with operation as (
	select id, owner_id, agent, specop, target_planet_id p_id, random,
		(case when (select tech from '|| _ops_table||' o where o.name = specop)-
		(select research_percent_operations from '|| _userstatus_table ||' u where u.user_id = owner_id) < 0 then 0
		else (select tech from '|| _ops_table||' o where o.name = specop) -
		(select research_percent_operations from '|| _userstatus_table ||' u where u.user_id = owner_id) end) penalty
	from '|| _fleet_table ||' a where a.main_fleet = FALSE
	and command_order = 6 --perform operation
	and a.ticks_remaining = 0
),
success as (
	select op.id s_id, (((0.6 + (0.8/ 255.0) * (op.random & 255)) * 
	1 -- agents_coeff 
	* op.agent *
	(select (1.0 + 0.01 * research_percent_operations) from '|| _userstatus_table ||' u where u.user_id = op.owner_id))/
	(select difficulty from '|| _ops_table||' o where o.name = op.specop)) / (case when p.owner_id is null then 50 end)
	success
	from operation op
	join '|| _planets_table ||' p on p.id = op.p_id
	where op.penalty < 150
),
information as (
	select s.s_id i_id, (case when op.specop = ''Observe Planet'' THEN
	( case when s.success > 0.4 then 
	 (case when p.owner_id is null then ''Planet Size: '' || p.size end) else ''No information was gathered about this planet!'' end) end) news_info
	from operation op
	join '|| _planets_table ||' p on p.id = op.p_id
	join success s on s.s_id = op.id
),	 
ins_news_success as (
	insert into '|| _news_table||' 
	( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, planet_id, fleet1, extra_info)
	select e.owner_id, 
	(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
	''AA'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
	(select (i.news_info) from information i where i.i_id = e.id)
	from operation e
)
update '|| _userstatus_table ||' u
set military_flag = case when military_flag != 1 then 2 else 1 end -- red flag overrides green
from (select owner_id from operation group by owner_id) c 
where u.id = c.owner_id;
 
';

execute _sql;
   
_end_ts   := clock_timestamp();
  
END
$$;
 
 
