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
		_empire_table varchar(255);
		_rel_table varchar(255);
		
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
			_empire_table := 'app_empire';
			_rel_table := 'app_relations';
		else 
			_planets_table := '"PLANETS"';
			_userstatus_table := 'galtwo_userstatus';
			_fleet_table := 'galtwo_fleet';
			_scouting_table := 'galtwo_scouting';
			_news_table := 'galtwo_news';
			_roundstatus := 'galtwo_roundstatus';
			_artefacts_table := 'galtwo_artefacts';
			_specops_table := 'galtwo_specops';
			_empire_table := 'galtwo_empire';
			_rel_table := 'galtwo_relations';
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
		select a.id id, owner_id, a.agent agents, a.ghost ghosts, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from '|| _ops_table||' o where o.name = specop) base_cost,
			(case when (select tech from '|| _ops_table||' o where o.name = specop)-
			(case when a.command_order = 6 then u. research_percent_operations 
			else u.research_percent_culture end) < 0 then 0
			else (select tech from '|| _ops_table||' o where o.name = specop) -
			(case when a.command_order = 6 then u. research_percent_operations 
			else u.research_percent_culture end) end) penalty,
			(select owner_id from '|| _planets_table ||' where id = target_planet_id) defid,
			(select stealth from '|| _ops_table||' o where o.name = a.specop) stealth
		from '|| _fleet_table ||' a 
		join '|| _userstatus_table ||' u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order in (6,7) --perform 
		and a.ticks_remaining = 0
		and (case when a.command_order = 6 then u.agent_readiness >= 0 else u.psychic_readiness >= 0 end)
		and a.id = case when '|| fleet_id ||' = 0 then a.id else '|| fleet_id ||' end
	),
	/*attack as (
	 select op.id a_id, (((0.6 + (0.8/ 255.0) * (op.random & 255)) * 
		att.num_val * (case when op.c_o = 6 then coalesce(op.agents,0) else coalesce(op.ghosts,0) end) *
		(select (1.0 + 0.01 * (case when op.c_o = 6 then u.research_percent_operations 
			else u.research_percent_culture end)) from '|| _userstatus_table ||' u where u.user_id = op.owner_id))/
		(select difficulty from '|| _ops_table||' o where o.name = op.specop)) / (case when op.penalty > 0 then 1 + (0.01 * op.penalty) else 1 end) attack
		from operation op
		join '|| _userstatus_table ||' a on a.id = op.owner_id
		join classes c on c.name = a.race
		join constants att on att.class = c.id and att.name = case when op.c_o = 6 then ''agent_coeff'' else ''ghost_coeff'' end
		where op.penalty < 150
	),*/
	success as (
		-- success
		select op.id s_id, p.id p_id, op.owner_id, op.specop, COALESCE((ops_Attack('||gal_nr||', op.id, op.owner_id, op.specop)  / 
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
		end / case when op.c_o = 6 then 1 else 7 end )),0)
		success,
		-- ghost defence
		case when op.c_o = 7 then COALESCE((ops_Attack('||gal_nr||', op.id, op.owner_id, op.specop) / 
		(case when p.owner_id is null then 50 else
		1.0 + (select  dcc.num_val * coalesce(df.ghost,0) * 
        (1.0 + 0.005 * defc.research_percent_culture)
		from '|| _userstatus_table ||' defc
		join classes d_cc on d_cc.name = defc.race
		join constants dcc on dcc.class = d_cc.id and dcc.name = ''ghost_coeff''
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = 
		(select owner_id from '|| _planets_table ||' where id = op.p_id)) end)),0)
		else 0 end
		g_def
		
		from operation op
		join '|| _planets_table ||' p on (case when op.specop != ''Survey System'' then p.id = op.p_id else 
		p.x = (select x from '|| _planets_table ||' where id = op.p_id) AND
		p.y = (select y from '|| _planets_table ||' where id = op.p_id) end)
		--join attack atac on op.id = atac.a_id
		where op.penalty < 150
	),
	--losses
	attloss as (
		select s.s_id al_id, case when p.owner_id is null then 0 else round(case when op.c_o = 6 then case 
		when s.success < 2.0 then greatest(0, least(coalesce(op.agents,0), (1.0 - (0.5 * power((0.5 * s.success ), 1.1))) *
		(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.agents,0))) else 0 end
		else case when s.g_def < 2.0 then greatest(0, least(coalesce(op.ghosts,0), (1.0 - (0.5 * power((0.5 * s.g_def ), 1.1))) *
		(1.0 - power((0.5 * s.g_def), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.ghosts,0))) else 0 end
		end) end losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, op.defid, op.c_o,
		case when p.owner_id is null then 0 else round(case when op.c_o = 6 then case 
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
	
	defagentloss as (
		update '|| _fleet_table ||' f
		set agent = agent - l.lost
		from (select sum(losses) lost , defid from defloss where c_o = 6 group by defid) l
		where f.owner_id=l.defid and main_fleet=true
	),
	--readiness
	p_cost as (
		select op.id id, u.empire_id atemp, op.penalty, op.base_cost, op.specop, op.owner_id,
		(case when p.owner_id is null then 1 else
		(select empire_id from '|| _userstatus_table ||' d where d.user_id = p.owner_id) end) demp,
		(greatest((case when op.specop=''Survey System'' or p.owner_id is null then 1 else 
		(0.5*(power(((1.0+u.num_planets)/(1.0+(select num_planets from '|| _userstatus_table ||' d where d.user_id = p.owner_id))), 1.8)+
		(power(((1.0+(select planets from '|| _empire_table ||' where id = u.empire_id))/
		(1.0+(select planets from '|| _empire_table ||' where id =(select empire_id from '|| _userstatus_table ||' d where d.user_id = p.owner_id)))), 1.2))))
		end), 0.75)) fa
		from operation op
		join '|| _planets_table ||' p on p.id = op.p_id
		join '|| _userstatus_table ||' u on u.id = op.owner_id
	),
	
	fa_cost as (
		select pc.id id, pc.atemp, pc.demp, pc.specop, pc.owner_id,(
		select ((1.0 + 0.01 * penalty) * pc.base_cost * pc.fa)) fa
		from p_cost pc
	),
	
	w_cost as (
		select c.id id, c.atemp, c.demp, c.specop, c.owner_id,(
		select case when exists (select c.fa from '|| _rel_table ||'
		where empire1_id in (c.atemp, c.demp) and empire2_id in (c.atemp, c.demp)
		and relation_type in (''A'', ''W''))
		then c.fa/3
		else c.fa end) fa
		from fa_cost c
	),
	
	r_cost as (
		select c.id id, c.specop, c.owner_id,(
		select case when exists (select c.fa from '|| _rel_table ||'
		where empire1_id in (c.atemp, c.demp) and empire2_id in (c.atemp, c.demp)
		and relation_type in (''NC'', ''PC'', ''N'', ''C''))
		then 50.0
		else c.fa end) fa
		from w_cost c
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
	
	op_information as (
		select s.s_id i_id, (case when op.specop = ''Spy Target'' then
		case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
		else '''' end || 
		case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
		else '''' end ||
		case when s.success >= 0.4 then
			case when s.success >= 0.5 then 
					chr(10) || ''Fleet readiness: '' || u.fleet_readiness
			else '''' end ||
			case when s.success >= 0.7 then
					chr(10) || ''Psychic readiness: '' || u.psychic_readiness
			else '''' end ||
			case when s.success >= 0.9 then
					chr(10) || ''Agent readiness: '' || u.Agent_readiness
			else '''' end ||
			case when s.success >= 1.0 then
					chr(10) || ''Energy: '' || u.energy
			else '''' end ||
			case when s.success >= 0.6 then
					chr(10) || ''Minerals: '' || u.minerals
			else '''' end ||
				chr(10) || ''Crystals: '' || u.crystals ||
			case when s.success >= 0.8 then
					chr(10) || ''Ectrolium: '' || u.ectrolium
			else '''' end ||
			case when s.success >= 0.9 then
					chr(10) || ''Population: '' || u.population
			else '''' end 
		else ''Your Agents failed'' end 
		end) news_info
		from operation op
		join '|| _userstatus_table ||' u on u.id = op.defid
		join success s on s.s_id = op.id
		join attloss al on al.al_id = op.id
		join defloss dl on dl.dl_id = op.id
		where op.c_o = 6 and op.defid is not null
	),
	--news
	ins_news_success as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		(case when e.c_o = 6 then ''AA'' else ''GA'' end), 
		current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when e.specop in (''Observe Planet'', ''Survey System'') then (select string_agg(i.news_info, ''
        '') from  p_information i where i.i_id = e.id)else 
		(select i.news_info from  op_information i where i.i_id = e.id)end)
		from operation e
	),
	ins_news_defence as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select (select owner_id from '|| _planets_table ||' where id = e.p_id), 
		(case when s.success > 2.0 then e.owner_id else null end),
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.defid), 
		(case when e.c_o = 6 then ''AD'' else ''GD'' end), 
		current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when e.c_o = 6 then 
			case when s.success >= 1 then ''Their agents were successful!''
			when s.success >= 0.4 then ''Our agents managed to stop the attackers before all damage was done!''
			else ''Our agents managed to defend'' end
		end)
		from operation e 
		join success s on s.s_id = e.id
		where e.defid is not null
		and (s.success < 2.0 or e.stealth = false)
	),
	--scouting
	merge_scout as (
		merge into '|| _scouting_table ||' a
		using (select op.owner_id, op.p_id, max(op.success) success
		from success op
		where op.specop in (''Observe Planet'', ''Survey System'')
		group by op.p_id, op.owner_id
		) o
		on a.empire_id = (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.owner_id) and 
		a.planet_id = o.p_id
		WHEN MATCHED THEN
			UPDATE SET scout = case when o.success >= a.scout then o.success else a.scout end
		WHEN NOT MATCHED THEN
		  INSERT (planet_id, empire_id, user_id, scout)
		  VALUES (o.p_id, (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.owner_id), o.owner_id, o.success)
	),
	send_home as (
		update '|| _fleet_table ||' a
		set i = s.i,
		x = s.x,
		y = s.y,
		agent = agent - (case when a.command_order = 6 then at.losses else 0 end),
		command_order = 5,
		ticks_remaining = case when a.x = s.x and a.y = s.y then ticks_remaining 
						  else floor((sqrt(pow((a.current_position_x - s.x),2) + pow((a.current_position_y - s.y),2))/
						  c.num_val) * coalesce((select (1+(effect1/100)) from '|| _artefacts_table ||' where name = ''Blackhole'' and
						  empire_holding_id = s.owner_id),1)--num_val is speed 
						  ) end
	from 
		(select * from
		(select a.id a_id, a.owner_id, p.id p_id, p.x, p.y, p.i,
		rank() over(partition by a.owner_id, a.id order by (pow((p.x - a.current_position_x),2) + pow((p.y - a.current_position_y),2)) asc) rn
		from '|| _fleet_table ||' a, '|| _planets_table ||' p
		where p.owner_id = a.owner_id
		and p.portal = true
		) g where g.rn = 1) s 
	join '|| _userstatus_table ||' u on u.id = s.owner_id
	join classes l on l.name = u.race
	join constants c on c.class = l.id and c.name = ''travel_speed''
	join operation op on op.id= s.a_id
	join attloss at on at.al_id = op.id
	where a.id = s.a_id
	and a.command_order in (6,7) and a.ticks_remaining = 0
	)
	update '|| _userstatus_table ||' u
	set military_flag = case when military_flag != 1 then 2 else 1 end,
	agent_readiness = agent_readiness - COALESCE((select sum(fa) from r_cost where specop=''Observe Planet'' and owner_id=u.id group by owner_id),0),
	psychic_readiness = psychic_readiness - COALESCE((select sum(fa) from r_cost where specop=''Survey System'' and owner_id=u.id group by owner_id),0)
	from (select owner_id from operation group by owner_id) c 
	where u.id = c.owner_id;
	
	-- join main fleet
	with recalled_fleets as 
	(select owner_id, 
		sum(bomber) bomber ,
		sum(fighter ) fighter  ,
		sum(transport ) transport  ,
		sum(cruiser ) cruiser  ,
		sum(carrier ) carrier  ,
		sum(soldier ) soldier  ,
		sum(droid ) droid  ,
		sum(goliath ) goliath  ,
		sum(phantom ) phantom  ,
		sum(agent ) agent  ,
		sum(ghost ) ghost  ,
		sum(exploration) exploration 
	  from '|| _fleet_table ||' a 
	  where a.main_fleet = false
	  and a.command_order = 5
	  and a.ticks_remaining = 0
	  group by owner_id)
      
	, join_main_fleet as (
	update '|| _fleet_table ||' a1
	set
	bomber = a1.bomber + b.bomber,
	fighter  = a1.fighter  + b.fighter ,
	transport  = a1.transport  + b.transport ,
	cruiser  = a1.cruiser  + b.cruiser ,
	carrier  = a1.carrier  + b.carrier ,
	soldier  = a1.soldier  + b.soldier ,
	droid  = a1.droid  + b.droid ,
	goliath  = a1.goliath  + b.goliath ,
	phantom  = a1.phantom  + b.phantom ,
	agent  = a1.agent  + b.agent ,
	ghost  = a1.ghost  + b.ghost ,
	exploration = a1.exploration + b.exploration
	from recalled_fleets b
	where a1.main_fleet = true and
	a1.owner_id = b.owner_id
	)
	
	delete from '|| _fleet_table ||' a
	where 
	a.main_fleet = false
	and a.command_order = 5
	and a.ticks_remaining = 0;
	
	';

	execute _sql;
	   
	_end_ts   := clock_timestamp();
	  
	END
	$$;
	 
	 
