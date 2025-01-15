	CREATE OR REPLACE PROCEDURE operations(gal_nr integer default null, fleet_id integer default null)
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
		if gal_nr = 1 then
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

	--gen random
		update '|| _fleet_table ||'
		set random = random()*(2147483647-0)
		where main_fleet = FALSE
		and command_order in (6,7) --perform 
		and ticks_remaining = 0;

	--operations
	with operation as (
		select a.id id, owner_id, agent, ghost, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from '|| _ops_table||' o where o.name = specop) base_cost,
			(case when (select tech from '|| _ops_table||' o where o.name = specop)-
			(case when a.command_order = 6 then u. research_percent_operations 
			else u.research_percent_culture end) < 0 then 0
			else (select tech from '|| _ops_table||' o where o.name = specop) -
			(case when a.command_order = 6 then u. research_percent_operations 
			else u.research_percent_culture end) end) penalty
		from '|| _fleet_table ||' a 
		join '|| _userstatus_table ||' u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order in (6,7) --perform 
		and a.ticks_remaining = 0
		and (case when a.command_order = 6 then u.agent_readiness >= 0 else u.psychic_readiness >= 0 end)
		and a.id = case when '|| fleet_id ||' = 0 then a.id else '|| fleet_id ||' end
	),
	attack as (
	 select op.id a_id, (((0.6 + (0.8/ 255.0) * (op.random & 255)) * 
		att.num_val * (case when op.c_o = 6 then coalesce(op.agent,0) else coalesce(op.ghost,0) end) *
		(select (1.0 + 0.01 * (case when op.c_o = 6 then u.research_percent_operations 
			else u.research_percent_culture end)) from '|| _userstatus_table ||' u where u.user_id = op.owner_id))/
		(select difficulty from '|| _ops_table||' o where o.name = op.specop)) / (case when op.penalty > 0 then 1 + (0.01 * op.penalty) else 1 end) attack
		from operation op
		join '|| _userstatus_table ||' a on a.id = op.owner_id
		join classes c on c.name = a.race
		join constants att on att.class = c.id and att.name = case when op.c_o = 6 then ''agent_coeff'' else ''ghost_coeff'' end
		where op.penalty < 150
	),
	success as (
		-- success
		select op.id s_id, p.id p_id, COALESCE(atac.attack / 
		--defence
		(case when p.owner_id is null then 50 else
		1.0 + (select  dc.num_val * (select case when op.c_o = 6 then coalesce(df.agent,0) else coalesce(df.wizard,0) end) * 
        (1.0 + 0.005 * (select case when op.c_o = 6 then def.research_percent_operations else def.research_percent_culture end))
		from '|| _userstatus_table ||' def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = case when op.c_o = 6 then ''agent_coeff'' else ''psychic_coeff'' end
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = 
		(select owner_id from '|| _planets_table ||' where id = p.id)
		where def.id = df.owner_id)
		end / case when op.c_o = 6 then 1 else 7 end ),0)
		success,
		-- ghost defence
		case when op.c_o = 7 then COALESCE(atac.attack / (case when p.owner_id is null then 50 else
		1.0 + (select  dcc.num_val * coalesce(df.ghost,0) * 
        (1.0 + 0.005 * defc.research_percent_culture)
		from '|| _userstatus_table ||' defc
		join classes d_cc on d_cc.name = defc.race
		join constants dcc on dcc.class = d_cc.id and dcc.name = ''ghost_coeff''
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = 
		(select owner_id from '|| _planets_table ||' where id = op.p_id)) end),0)
		else 0 end
		g_def
		
		from operation op
		join '|| _planets_table ||' p on (case when op.specop != ''Survey System'' then p.id = op.p_id else 
		p.x = (select x from '|| _planets_table ||' where id = op.p_id) AND
		p.y = (select y from '|| _planets_table ||' where id = op.p_id) end)
		join attack atac on op.id = atac.a_id
		where op.penalty < 150
	),
	attloss as (
		select s.s_id al_id, case when p.owner_id is null then 0 else round(case when op.c_o = 6 then case 
		when s.success < 2.0 then greatest(0, least(coalesce(op.agent,0), (1.0 - (0.5 * power((0.5 * s.success ), 1.1))) *
		(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.agent,0))) else 0 end
		else case when s.g_def < 2.0 then greatest(0, least(coalesce(op.ghost,0), (1.0 - (0.5 * power((0.5 * s.g_def ), 1.1))) *
		(1.0 - power((0.5 * s.g_def), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.ghost,0))) else 0 end
		end) end losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, case when p.owner_id is null then 0 else round(case when op.c_o = 6 then case 
		when s.success < 2.0 then greatest(0, least(coalesce(
		(select agent from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0), 
		(0.5 * power((0.5 * s.success ), 1.1)) *
		(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * 
		coalesce((select agent from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0))) else 0 end
		else case when s.g_def < 2.0 then greatest(0, least(coalesce(
		(select ghost from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0), 
		(0.5 * power((0.5 * s.g_def ), 1.1)) *
		(1.0 - power((0.5 * s.g_def), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * 
		coalesce((select ghost from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0))) else 0 end
		end) end losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id
		where s.p_id = op.p_id
	),
	
	-- observe/ survey
	
	p_information as (
		select s.s_id i_id, (
		 case when p.owner_id is not null then 
					 case when op.specop = ''Survey System'' then ''Planet: '' || p.i || chr(10) || '''' 
					 else '''' end ||
		 ''Owned by: '' || (select user_name from '|| _userstatus_table ||' where id = p.owner_id) || chr(10) || 
					 case when al.losses > 0 and op.c_o = 6 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
					 else '''' end || 
					 case when dl.losses > 0 and op.c_o = 6 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
					 else '''' end ||
		 '''' else '''' end ||
		case when s.success >= 0.4 then ''Planet'' || 
			case when op.specop = ''Survey System'' then 
			'': '' || p.i || chr(10) || 
			'''' else '''' end || '' Size: '' || p.size ||
			 case when s.success >= 0.9 then 
				 case when p.bonus_solar > 0 then chr(10) || ''Solar Bonus: '' || p.bonus_solar || ''%'' 
				 when p.bonus_fission > 0 then chr(10) || ''Fission Bonus: '' || p.bonus_fission || ''%'' 
				 when p.bonus_mineral > 0 then chr(10) || ''Mineral Bonus: '' || p.bonus_mineral || ''%'' 
				 when p.bonus_crystal > 0 then chr(10) || ''Crystal Bonus: '' || p.bonus_crystal || ''%'' 
				 when p.bonus_ectrolium > 0 then chr(10) || ''Ectrolium Bonus: '' || p.bonus_mineral || ''%'' 
				 else '''' end 
			 else '''' end ||
			case when p.owner_id is not null then
				case when s.success >= 0.5 then
					chr(10) || ''Current population: '' || p.current_population
				else '''' end ||
				case when s.success >= 0.6 then
					chr(10) || ''Max population: '' || p.max_population
				else '''' end ||
				case when s.success >= 0.7 then
					chr(10) || ''Portal protection: '' || p.protection 
				else '''' end ||
				case when s.success >= 0.8 then 
					 chr(10) || ''Solar Collectors: '' || p.solar_collectors ||
					 chr(10) || ''Fission Reactors: '' || p.fission_reactors  ||
					 chr(10) || ''Mineral Plants: '' || p.mineral_plants ||
					 chr(10) || ''Crystal Labs: '' || p.crystal_labs || 
					 chr(10) || ''Refinement Stations: '' || p.refinement_stations ||
					 chr(10) || ''Cities: '' || p.cities ||
					 chr(10) || ''Research Centers: '' || p.research_centers ||
					 chr(10) || ''Defense Sats: '' || p.defense_sats ||
					 chr(10) || ''Shield Networks: '' || p.shield_networks 
				else '''' end ||
				case when s.success >= 1.0 then
					chr(10) || ''Portal: '' || 
						case when p.portal = true then ''Present'' 
							when p.portal_under_construction = true then ''Under construction'' 
						else ''Absent'' end
				else '''' end
			else '''' end ||
			case when s.success >= 1.0 and p.artefact_id is not null then
				chr(10) || ''Artefact: '' ||
				(select name from '|| _artefacts_table||' a where a.id = p.artefact_id)
			else '''' end
		 else ''No information was gathered about this planet!'' || '''' end
		 ) news_info
		from operation op
		join '|| _planets_table ||' p on (case when op.specop = ''Observe Planet'' then p.id = op.p_id else 
		p.x = (select x from '|| _planets_table ||' where id = op.p_id) AND
		p.y = (select y from '|| _planets_table ||' where id = op.p_id) 
		 end) 
		join success s on s.s_id = op.id and s.p_id = p.id
		join attloss al on al.al_id = op.id
		join defloss dl on dl.dl_id = op.id
		order by p.i
	),	

	-- other ops
	
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
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news, is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''AA'', current_timestamp, true, true, false, (select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when e.specop in (''Observe Planet'', ''Survey System'') then (select string_agg(i.news_info, ''
        '') from  p_information i where i.i_id = e.id) end)
		from operation e
	),
	merge_scout as (
		merge into '|| _scouting_table ||' a
		using (select op.owner_id, op.p_id, s.success, op.specop
		from operation op 
		join success s on s.p_id = op.p_id) o
		on a.empire_id = (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.owner_id) and a.planet_id = o.p_id 
		and o.specop in (''Observe Planet'', ''Survey System'')
		WHEN MATCHED THEN
			UPDATE SET scout = case when o.success >= a.scout then o.success else a.scout end
		WHEN NOT MATCHED THEN
		  INSERT (planet_id, empire_id, user_id, scout)
		  VALUES (o.p_id, (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.owner_id), o.owner_id, o.success)
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
	 
	 
