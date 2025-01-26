	CREATE OR REPLACE PROCEDURE incantations(gal_nr integer default null, fleet_id integer default 0)
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
		_construction_table varchar(255);
		_ticks_log_table varchar(255);
		_system_table varchar(255);
		_sensing_table varchar(255);
		
		_roundstatus varchar(255);
		_sql varchar;
	BEGIN 
	   _start_ts := clock_timestamp();
	   
	   -- for each type of round (slow/fast) we chose the tables accordingly
		
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
			_construction_table := 'app_construction';
			_ticks_log_table := 'app_ticks_log';
			_ops_table := 'app_ops';
			_system_table := 'app_system';
			_sensing_table := 'app_sensing';
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
			_construction_table := 'galtwo_construction';
			_ticks_log_table := 'galtwo_ticks_log';
			_ops_table := 'galtwo_ops';
			_system_table := 'galtwo_system';
			_sensing_table := 'galtwo_sensing';
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
		and command_order = 7 --perform 
		and ticks_remaining = 0;

	--operations
	with recursive operation as (
		select a.id id, owner_id, a.ghost ghosts, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from '|| _ops_table||' o where o.name = specop) base_cost,
		ops_penalty('||gal_nr||', specop, owner_id) penalty,
		(select owner_id from '|| _planets_table ||' where id = target_planet_id) defid,
		(select stealth from '|| _ops_table||' o where o.name = a.specop) stealth,
		ops_Attack('||gal_nr||', a.id, a.owner_id, a.specop) attack,
		u.empire_id
		from '|| _fleet_table ||' a 
		join '|| _userstatus_table ||' u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order = 7 --perform 
		and a.ticks_remaining = 0
		and a.id = case when '|| fleet_id ||' = 0 then a.id else '|| fleet_id ||' end
		and (a.specop in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') or (select owner_id from '|| _planets_table ||' where id = target_planet_id) is not null)
	),
	-- cant op empty planets
	
	empty_planets as (
		select a.id id, target_planet_id p_id, specop, owner_id oid
		from '|| _fleet_table ||' a 
		where a.specop not in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') 
		and (select owner_id from '|| _planets_table ||' where id = target_planet_id) is null
		and a.main_fleet = false
		and a.command_order = 7 --perform 
		and a.ticks_remaining = 0
	),
	success as (
		-- success
		select op.id s_id, p.id p_id, op.owner_id, op.specop,
		greatest(op.attack / 
		(case when op.specop in (''Survey System'', ''Sense Artefact'') then 
			(select networth from '|| _userstatus_table ||' where id = op.owner_id) / op.ghosts
		when p.owner_id is null or p.owner_id = op.owner_id then 50 else
		1.0 + (select ((dc.num_val * (COALESCE(df.wizard,0)) * (1.0 + 0.005 * def.research_percent_culture)) / 7)
		from '|| _userstatus_table ||' def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = ''psychic_coeff''
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = op.defid
		where def.id = df.owner_id) end),0) success,
		-- ghost defence
		greatest(op.attack / 
		(case when p.owner_id is null then 50 else
		1.0 + (select dc.num_val * (COALESCE(df.ghost,0)) * (1.0 + 0.005 * def.research_percent_culture)
		from '|| _userstatus_table ||' def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = ''ghost_coeff''
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = op.defid
		where def.id = df.owner_id) end),0) g_def
		
		from operation op
		join '|| _planets_table ||' p on (case when op.specop != ''Survey System'' then p.id = op.p_id else 
		p.x = (select x from '|| _planets_table ||' where id = op.p_id) AND
		p.y = (select y from '|| _planets_table ||' where id = op.p_id) end)
		where op.penalty < 150
	),
	--losses
	attloss as (
		select s.s_id al_id, (case when p.owner_id is null or op.specop in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') 
		or p.owner_id = op.owner_id then 0 
		else 
			round(case when s.success < 2.0 
			then greatest(0, least(coalesce(op.ghosts,0), (1.0 - (0.5 * power((0.5 * s.success ), 1.1))) *
			(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.ghosts,0))) 
			else 0 end) 
		end) losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, op.defid, op.c_o, 
		case when op.specop not in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') then
			(case when p.owner_id is null or p.owner_id = op.owner_id then 0 else round(case 
			when s.success < 2.0 then greatest(0, least(coalesce((select wizard from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0), 
			(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
			* (op.random & 255))) * coalesce((select wizard from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
			end) end losses,
		case when op.specop not in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') then		
			(case when p.owner_id is null or p.owner_id = op.owner_id then 0 else round(case 
			when s.success < 2.0 then greatest(0, least(coalesce((select ghost from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0), 
			(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
			* (op.random & 255))) * coalesce((select ghost from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
			end) end g_losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id
		where s.p_id = op.p_id
	),
	

	--readiness
	p_cost as (
		select op.id id, u.empire_id atemp, op.penalty, op.base_cost, op.specop, op.owner_id,
		(case when p.owner_id is null then 1 else
		(select empire_id from '|| _userstatus_table ||' d where d.user_id = p.owner_id) end) demp,
		(greatest((case when op.specop in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'') or p.owner_id is null then 1 else 
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
		then greatest(50.0, c.fa)
		else c.fa end) fa
		from w_cost c
	),
	
	prevent_neg as (
		select id from (
		select b.*, lag(c_sum, 1, 100) over(partition by owner_id order by id) lag_sum from (
		select r.* , u.agent_readiness - sum(fa )
		OVER (PARTITION BY u.id
		ORDER BY r.id) c_sum
		from r_cost r
		join app_userstatus u on u.id = r.owner_id
		where u.agent_readiness >= 0 --the the first op always completes
		)b  
		) c where lag_sum >= 0
	),
	
	-- incas
	
	survey as (
		select s.s_id i_id, (
		chr(10) ||''Planet: '' || p.i || chr(10) ||
		case when p.owner_id is not null then 
			 ''Owned by: '' || (select user_name from '|| _userstatus_table ||' where id = p.owner_id) || chr(10) || 
			 '''' 
		else '''' end ||
		case when s.success >= 0.4 then 
			''Size: '' || p.size ||
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
		join '|| _planets_table ||' p on p.x = (select x from '|| _planets_table ||' where id = op.p_id) AND
		p.y = (select y from '|| _planets_table ||' where id = op.p_id)
		join success s on s.s_id = op.id and s.p_id = p.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Survey System''
		order by p.i
	),
	-- pff, ps and vp
	
	ticks as (
		select op.p_id pid, op.id,
			(case when op.specop = ''Planetary Shielding'' then cast(random()*(100-10)+10 as int)
			when op.specop = ''Portal Force Field'' then cast(random()*(47-16)+16 as int)
			when op.specop = ''Vortex Portal'' then 
				round(least(144, (3 + (120 * ((ops_Attack('||gal_nr||', op.id, op.owner_id, op.specop) * 7) / 
					(select networth from '|| _userstatus_table ||' where id = op.owner_id))))))
			else 0 end) ticks
		from operation op 
		where specop in (''Planetary Shielding'', ''Portal Force Field'', ''Vortex Portal'')
	),
	strength as (
		select op.p_id pid, op.id,
			(case when op.specop = ''Planetary Shielding'' then
			round(ops_Attack('||gal_nr||', op.id, op.owner_id, op.specop) * cast(random()*(500-250)+250 as int))
			when op.specop = ''Portal Force Field'' then round(200 * ((select success from success where s_id = op.id) - 0.5))
			else (select success from success where s_id = op.id) end) strength
		from operation op 
		where specop in (''Planetary Shielding'', ''Portal Force Field'', ''Vortex Portal'')
	),
	create_op as(
		insert into '|| _specops_table ||' 
		(user_to_id, user_from_id, specop_type, stealth, name, ticks_left, specop_strength, specop_strength2, planet_id)
		select (case when op.specop = ''Vortex Portal'' then s.owner_id ELSE
		(select owner_id from '|| _planets_table ||' where id = op.p_id) end), s.owner_id, ''G'', 
		(case when s.success >= 2.0 then true else false end), s.specop, t.ticks, 
		(select strength from strength where id = op.id), 0, op.p_id
		from operation op
		join success s on s.s_id = op.id
		join ticks t on t.id = s.s_id
		join prevent_neg n on n.id = op.id
		where (select strength from strength where id = op.id) > 0 and t.ticks > 0
		and op.specop in (''Planetary Shielding'', ''Portal Force Field'', ''Vortex Portal'')
	),
	-- other incas
	call as (
		select op.id cid, ((case when s.success >= 1.0 then 
			0.8 else 2 * (s.success - 0.6) end)  * cast(random()*(110-90)+90 as int) / 100) fa,
			sqrt(power(abs(p.x-(select x from '|| _planets_table ||' where id = op.p_id)), 2) + 
			power(abs(p.y-(select y from '|| _planets_table ||' where id = op.p_id)), 2)) dist, p.id pid, op.defid
		from operation op
		join '|| _planets_table ||' p on p.owner_id = op.defid
		join success s on s.s_id = op.id
		where op.specop = ''Call to Arms''
	),
	kill_pop as (
		select c.cid, least(p.current_population,round(p.current_population * c.fa * (1.0 - (c.dist / 16.0)))) pop_killed, c.pid, c.defid
		from call c
		join '|| _planets_table ||' p on p.id = c.pid
		where c.dist < 16.0
	),
	gained_sols as (
		select round((c.pop_killed/100 * (1.0 + 0.01 * (select research_percent_military from '|| _userstatus_table ||' where id = c.defid)))
		/ 2 ) sols_gained, c.cid, c.defid
		from kill_pop c
	),
	upd_call as (
		update '|| _planets_table ||' p
		set current_population = current_population - b.pop_killed
		from kill_pop b where pid = p.id 
	),
	mind_c as (
		update '|| _planets_table ||' p
		set owner_id = op.owner_id,
		current_population = p.size * 20,
		protection = 0,
		buildings_under_construction = 0,
		portal = false,
		portal_under_construction = false,
		solar_collectors = (case when s.success >= 2.0 then p.solar_collectors else 0 end),
		fission_reactors = (case when s.success >= 2.0 then p.fission_reactors else 0 end),
		mineral_plants = (case when s.success >= 2.0 then p.mineral_plants else 0 end),
		crystal_labs = (case when s.success >= 2.0 then p.crystal_labs else 0 end),
		refinement_stations = (case when s.success >= 2.0 then p.refinement_stations else 0 end),
		cities = (case when s.success >= 2.0 then p.cities else 0 end),
		research_centers = (case when s.success >= 2.0 then p.research_centers else 0 end),
		defense_sats = (case when s.success >= 2.0 then p.defense_sats else 0 end),
		shield_networks = (case when s.success >= 2.0 then p.shield_networks else 0 end),
		total_buildings = (case when s.success >= 2.0 then p.total_buildings else 0 end)
		from operation op
		join success s on s.s_id = op.id
		where op.specop = ''Mind Control'' and s.success >= 1.0 and p.id = op.p_id
	),
	mind_arti as (
		update '|| _artefacts_table ||' p
		set empire_holding_id = op.empire_id
		from operation op
		join success s on s.s_id = op.id
		where op.specop = ''Mind Control'' and s.success >= 1.0 and p.on_planet_id = op.p_id
	),
	merge_mind_scout as (
		merge into '|| _scouting_table ||' a
		using (select op.empire_id, op.owner_id, op.p_id
		from operation op 
		join success s on s.s_id = op.id
		where op.specop = ''Mind Control'' and s.success >= 1.0 
		) s
		on a.empire_id = s.empire_id and a.user_id = s.owner_id and a.planet_id = s.p_id
		WHEN MATCHED THEN
			UPDATE SET scout = 1.0
		WHEN NOT MATCHED THEN
		  INSERT (scout, empire_id, user_id, planet_id)
		  VALUES (1, s.empire_id, s.owner_id, s.p_id)
	),
	mind_constr as (
		delete from '|| _construction_table ||' 
		where planet_id in ( 
		select op.p_id from operation op
		join success s on s.s_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Mind Control'' and s.success >= 1.0)
	),
	--sense
	sense as (
		select empire_id, user_id, fleet_id, p_id, system_id, x, y		
		from(
		select op.id fleet_id, op.empire_id, op.owner_id user_id, op.p_id,
			greatest((2*random(0.2,0.8)*log10(10 * op.attack)), 1) strength,
			 sqrt(1+ pow(p.x-p2.x,2) + pow(p.y-p2.y,2) ) dist,
			 s.success,
			 p2.id system_id, p2.x, p2.y
			from operation op
			join prevent_neg n on n.id = op.id
			join success s on s.s_id = op.id and s.success >= 1
			join '|| _planets_table ||' p on p.id = op.p_id
			join '|| _system_table ||' p2 on 1=1
			where op.specop = ''Sense Artefact''
		) where strength >= dist
		group by empire_id, user_id, fleet_id, p_id, system_id, x, y
		),
	ins_sense as 
		(
		merge into '|| _sensing_table ||' a
		using (select empire_id, system_id 
		from sense
		group by empire_id, system_id
		) s
		on a.empire_id = s.empire_id and a.system_id = s.system_id
		WHEN MATCHED THEN
			UPDATE SET scout = 1.0
		WHEN NOT MATCHED THEN
		  INSERT (scout, empire_id, system_id)
		  VALUES (1, s.empire_id, s.system_id)
	), 
	sense_arti as 
	(
		select a.id arti_id, p.id planet_id, s.fleet_id, s.empire_id, s.user_id,
		''Your Ghost Ships have located an Artefact at Planet:'' || p.x ||'',''|| p.y || '':'' || p.i news_info
		from '|| _artefacts_table ||'  a
		join '|| _planets_table ||' p on p.id = a.on_planet_id
		join sense s on s.x = p.x and s.y = p.y
	),
	merge_arti_scout as 
	(
		merge into '|| _scouting_table ||' a
		using (select empire_id, user_id, planet_id
		from sense_arti
		) s
		on a.empire_id = s.empire_id and a.user_id = s.user_id and a.planet_id = s.planet_id 
		WHEN MATCHED THEN
			UPDATE SET scout = 1.0
		WHEN NOT MATCHED THEN
		  INSERT (scout, empire_id, user_id, planet_id)
		  VALUES (1, s.empire_id, s.user_id, s.planet_id)
	),
	energy_surges as (
				select op.id as op_id, op.defid 
				from operation op
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				join '|| _userstatus_table ||' u on u.id = op.defid
				where op.specop = ''Energy Surge''
	),
	energy_surge_recursive as (
	
	--1/2 of energy loss damages rc, 1 rc point per 1 energy, max 20% of total
	--1/10 of energy loss damages minerals, 1 mineral per 3 energy, max 30% of total
	--1/10 of energy loss damages crystals, 1 crystal per 6 energy, max 30% of total
	--1/10 of energy loss damages ectrolium, 1 ectrolium per 5 energy, max 30% of total
	--1/10 of energy loss damages solars, 1 solar per 300 energy, max 25% of total
	--1/10 of energy loss damages fissions, 1 fission per 400 energy, max 25% of total

	    select 
				max(u.energy) energy,
				max(u.minerals) minerals,
				max(u.crystals) crystals, 
				max(u.ectrolium) ectrolium, 
				max(u.total_solar_collectors) total_solar_collectors, 
				max(u.total_fission_reactors) total_fission_reactors,
				max(u.research_percent_operations +	
				u.research_points_military +		
				u.research_points_construction +	
				u.research_points_tech +		
				u.research_points_energy +	
				u.research_points_population +	
				u.research_points_culture +	
				u.research_points_operations +
				u.research_points_portals) total_rc_points,
				0 n,
				count(*) total_ops,
				greatest(max(u.networth), max(u.energy)) as total_damage,  
				max(u.networth) networth,
				min(op.id) min_op_id,
				0 last_op_id,
				'' '' as news,
				0 as attid,
				op.defid as defid
				from operation op 
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				join '|| _userstatus_table ||' u on u.id = op.defid
				where op.specop = ''Energy Surge''
				and (op.defid, op.id) in (select defid, min(op_id) from energy_surges group by defid)
				group by op.defid
  			UNION ALL
		    SELECT 
			0 as energy ,
			e.minerals - cast(least(e.minerals*0.3, e.total_damage/30) as bigint) as minerals, 
			e.crystals - cast(least(e.crystals*0.3, e.total_damage/60) as bigint) as crystals, 
			e.ectrolium - cast(least(e.ectrolium*0.3, e.total_damage/50) as bigint) as ectrolium, 
			e.total_solar_collectors - cast(least(total_solar_collectors*0.25, total_damage/3000) as int) as total_solar_collectors,
			e.total_fission_reactors - cast(least(total_fission_reactors*0.25, total_damage/4000) as int) as total_fission_reactors,
			e.total_rc_points - cast(least(total_rc_points*0.2, total_damage/2) as bigint) as total_rc_points,
			 n+1, total_ops,
			greatest(e.networth, 0) as total_damage, networth,
			(select min(op.id)
				from operation op
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				where op.specop = ''Energy Surge''
				and op.id > e.min_op_id
				and op.defid = e.defid
			) min_op_id,
			e.min_op_id last_op_id,
			''Energy lost: '' || e.energy || '' ''
			|| ''Minerals lost: '' || cast(least(e.minerals*0.3, e.total_damage/30) as bigint) || '' ''
			|| ''Crystals lost: '' || cast(least(e.crystals*0.3, e.total_damage/60) as bigint) || '' ''
			|| ''Ectrolium lost: '' || cast(least(e.ectrolium*0.3, e.total_damage/50) as bigint) || '' ''
			|| ''Solars lost: '' || cast(least(total_solar_collectors*0.25, total_damage/3000) as bigint) || '' ''
			|| ''Fissions lost: '' || cast(least(total_fission_reactors*0.25, total_damage/4000) as bigint) || '' ''
			|| ''Research lost: '' || cast(least(total_rc_points*0.2, total_damage/2) as bigint) || '' ''
			as news,
			o.owner_id attid,
			o.defid defid 
			FROM energy_surge_recursive e
			join operation o on e.min_op_id = o.id
			WHERE min_op_id is not null
		),
	esurge_losses as (
		select defid,
		greatest(0, min(r.energy)) energy,
		greatest(0, min(r.minerals)) minerals,
		greatest(0, min(r.crystals)) crystals,
		greatest(0, min(r.ectrolium)) ectrolium,
		least(1.0, (1 - (max(total_solar_collectors::float)-min(total_solar_collectors::float))/(max(total_solar_collectors::float)+1))) solars_loss,
		least(1.0, (1 - (max(total_fission_reactors::float)-min(total_fission_reactors::float))/(max(total_fission_reactors::float)+1))) fissions_loss,
		least(1.0, (1 - (max(total_rc_points::float)-min(total_rc_points::float))/(max(total_rc_points::float)+1))) rc_points_loss
		from energy_surge_recursive r 
		where n = 0 or (defid,n) in (select defid, max(n) from energy_surge_recursive group by defid)
		group by defid
	),
	esurge_update2 as (
		update '|| _planets_table ||' p
		set fission_reactors = fission_reactors * fissions_loss,
		solar_collectors = solar_collectors * solars_loss
		from esurge_losses e
		where p.owner_id = e.defid
	),
	-- news
	ins_news_success as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''GA'', current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' ghost ships'' || chr(10) || '''' 
		else '''' end || 
		case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' ghost ships'' || chr(10) || '''' 
		else '''' end ||
		case when dl.g_losses > 0 then ''Defender Lost: '' || dl.g_losses || '' psychics'' || chr(10) || '''' 
		else '''' end ||
		case when e.specop = ''Survey System'' then (select string_agg(i.news_info, ''
        '') from survey i where i.i_id = e.id)
		when e.specop = ''Vortex Portal'' then
			''Vortex Portal created at '' || (select x from '|| _planets_table ||' where id = e.p_id) || '','' 
			|| (select y from '|| _planets_table ||' where id = e.p_id) || '' for a duration of '' || 
			(select ticks from ticks where id = e.id) || '' weeks!''
		when e.specop = ''Planetary Shielding'' then
			case when (select strength from strength where id = e.id) > 0 and (select ticks from ticks where id = e.id) > 0 then 
				''Your Ghost Ships managed to create a shield lasting '' || (select ticks from ticks where id = e.id) ||
				'' weeks, able to withstand '' || (select strength from strength where id = e.id) ||  '' damage!''
			else ''Your Ghost Ships failed!'' end
		when e.specop = ''Portal Force Field'' then
			case when (select strength from strength where id = e.id) > 0 and (select ticks from ticks where id = e.id) > 0 then 
				''Your Ghost Ships managed to create a force field lasting '' || (select ticks from ticks where id = e.id) ||
				'' weeks, reducing portal capability by '' || (select strength from strength where id = e.id) ||  ''%!''
			else ''Your Ghost Ships failed!'' end
		when e.specop = ''Sense Artefact'' then 
			case when (select count(*) from sense_arti) > 0 then
			(select string_agg(i.news_info, '''|| chr(10) || ''') from sense_arti i where i.fleet_id = e.id)
			else ''Your ghost ships searched thoughrally through out the galaxy, but no presence of any artefacts was felt!''
			end
		when e.specop = ''Call to Arms'' then
			case when (select sum(pop_killed) from kill_pop where cid = e.id) > 0 then 
				(select sum(pop_killed) from kill_pop where cid = e.id) || '' population has been recruited, training '' ||
				(select sum(sols_gained) from gained_sols where cid = e.id)	 || '' soldiers!''
			else
				''Your Ghost Ships failed!''
			end
		when e.specop = ''Mind Control'' then
			case when (select success from success where s_id = e.id) >= 1.0 then 
				''Your Ghost Ships took control of the planet!''
			else
				''Your Ghost Ships failed!''
			end
		when e.specop = ''Energy Surge'' then
			case when (select success from success where s_id = e.id) >= 1.0 then 
				''Your Ghost Ships managed to launch a destructive wave of energy killing everything on its path! ''|| chr(10) || '' '' 
				''Results: '' || (select news from energy_surge_recursive r where r.last_op_id = e.id)
			else
				''Your Ghost Ships failed!''
			end
		end )
		from operation e
		join prevent_neg n on n.id = e.id
		join attloss al on al.al_id = e.id
		join defloss dl on dl.dl_id = e.id
		where n.id = e.id
	),
	ins_no_pr_news as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''GA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Not enough Psychic Readiness, Ghost Ships returning!''
		from operation e
		join success s on s.s_id =e.id
		where e.id not in (select id from prevent_neg)
	),
	penalty_to_high_news as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select id from '|| _userstatus_table ||' u where u.user_id = e.defid),
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''GA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Culture technology not high enough to perform '' || e.specop || chr(10) || ''Ghost Ships returning!''
		from operation e
		where penalty >= 150
	),
	empty_planets_news as (
		insert into '|| _news_table||' 
		( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.oid, (select empire_id from '|| _userstatus_table ||' u where u.user_id = e.oid), 
		''GA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Your Ghost Ships cannot perform '' || e.specop || '' on an empty planet!'' || chr(10) || ''Ghost Ships returning!''
		from empty_planets e
	),
	ins_news_defence as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select (select owner_id from '|| _planets_table ||' where id = e.p_id), 
		(case when s.success > 2.0 then e.owner_id else null end),
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.defid), 
		''GD'', 
		current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' ghost ships'' || chr(10) || '''' 
		else '''' end || 
		case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' ghost ships'' || chr(10) || '''' 
		else '''' end ||
		case when dl.g_losses > 0 then ''Defender Lost: '' || dl.g_losses || '' psychics'' || chr(10) || '''' 
		else '''' end ||
		case when e.specop = ''Planetary Shielding'' then
			case when (select strength from strength where id = e.id) > 0 and (select ticks from ticks where id = e.id) > 0 then 
				''Enemy Ghost Ships managed to create a shield lasting '' || (select ticks from ticks where id = e.id) ||
				'' weeks, able to withstand '' || (select strength from strength where id = e.id) ||  '' damage!''
			else ''Your Psychics managed to defend!'' end
		when e.specop = ''Portal Force Field'' then
			case when (select strength from strength where id = e.id) > 0 and (select ticks from ticks where id = e.id) > 0 then 
				''Enemy Ghost Ships managed to create a force field lasting '' || (select ticks from ticks where id = e.id) ||
				'' weeks, reducing portal capability by '' || (select strength from strength where id = e.id) ||  ''%!''
			else ''Your Psychics managed to defend!'' end
		when e.specop = ''Call to Arms'' then
			case when (select sum(pop_killed) from kill_pop where cid = e.id) > 0 then 
				(select sum(pop_killed) from kill_pop where cid = e.id) || '' population has been recruited, training '' ||
				(select sum(sols_gained) from gained_sols where cid = e.id)	 || '' soldiers!''
			else
				''Your Psychics managed to defend!''
			end
		when e.specop = ''Mind Control'' then
			case when s.success >= 1.0 then 
				''The planet was lost!''
			else
				''Your Psychics managed to defend!''
			end
		when e.specop = ''Energy Surge'' then
			case when (select success from success where s_id = e.id) >= 1.0 then 
				''Enemy Ghost Ships managed to launch a destructive wave of energy killing everything on its path! ''|| chr(10) || '' '' 
				''Results: '' || (select news from energy_surge_recursive r where r.last_op_id = e.id)
			else
				''Your Psychics managed to defend!''
			end
		end )
		from operation e 
		join success s on s.s_id = e.id
		join attloss al on al.al_id = e.id
		join defloss dl on dl.dl_id = e.id
		join prevent_neg n on n.id = e.id
		where e.defid is not null and e.defid != e.owner_id
		and (s.success < 2.0 or e.stealth = false) and e.specop not in (''Survey System'', ''Sense Artefact'', ''Vortex Portal'')
	),
	--scouting
	merge_scout as (
		merge into '|| _scouting_table ||' a
		using (select op.owner_id, op.p_id, max(op.success) success
		from success op
		where op.specop in (''Survey System'')
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
		ghost = ghost - COALESCE((select losses from attloss where al_id = a.id), 0),
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
	where a.id = s.a_id
	and a.command_order = 7 and a.ticks_remaining = 0
	),
	deflosses as (
		update '|| _fleet_table ||' f
		set wizard = wizard - COALESCE((select sum(losses) from defloss where defid = f.owner_id),0),
		ghost = ghost - COALESCE((select sum(g_losses) from defloss where defid = f.owner_id),0),
		soldier = soldier + COALESCE((select sum(sols_gained) from gained_sols where defid = f.owner_id),0) -- call
		from (select defid from operation group by defid) o
		where f.owner_id=o.defid and f.main_fleet=true
	)
	update '|| _userstatus_table ||' u
	set military_flag = case when f.id is not null then 1 when c.owner_id is not null and u2.military_flag != 1 then 2 else 1 end,
	psychic_readiness = u.psychic_readiness - case when d.owner_id is not null then d.sm else 0 end,
	-- e-surge part, cant have multiple updates of the same table inside 1 CTE
	    energy = case when b.defid is not null then b.energy else u.energy end,
		minerals =case when b.defid is not null then b.minerals else u.minerals end,
		crystals = case when b.defid is not null then b.crystals else u.crystals end,
		ectrolium = case when b.defid is not null then b.ectrolium else u.ectrolium end,
		research_percent_operations = case when b.defid is not null then u.research_percent_operations * b.rc_points_loss else u.research_percent_operations end,
		research_points_military = case when b.defid is not null then u.research_points_military * b.rc_points_loss else u.research_points_military end,
		research_points_construction = case when b.defid is not null then u.research_points_construction * b.rc_points_loss else u.research_points_construction end,
		research_points_tech = case when b.defid is not null then u.research_points_tech * b.rc_points_loss else u.research_points_tech end,
		research_points_energy = case when b.defid is not null then u.research_points_energy * b.rc_points_loss else u.research_points_energy end,
		research_points_population = case when b.defid is not null then u.research_points_population * b.rc_points_loss else u.research_points_population end,
		research_points_culture = case when b.defid is not null then u.research_points_culture * b.rc_points_loss else u.research_points_culture end,
		research_points_operations = case when b.defid is not null then u.research_points_operations * b.rc_points_loss else u.research_points_operations end,
		research_points_portals = case when b.defid is not null then u.research_points_portals * b.rc_points_loss else u.research_points_portals end
	-- e-surge part
	from '|| _userstatus_table ||' u2
	left join (select oid id from empty_planets group by oid) f on u2.id = f.id
	left join (select owner_id from operation group by owner_id) c on c.owner_id = u2.id
	left join (select owner_id, sum(r.fa) sm from r_cost r join prevent_neg n on n.id = r.id group by owner_id) d on d.owner_id = u2.id
	left join esurge_losses b on u2.id = b.defid -- e-surge part
	where u.id = u2.id;
	
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
	--raise notice '%', _sql;
	execute _sql;
	
_end_ts   := clock_timestamp();
  
select to_char(100 * extract(epoch FROM _end_ts - _start_ts), 'FM9999999999.99999999') into _retstr;

--RAISE NOTICE 'Execution time in ms = %' , _retstr;

_sql := 
'insert into '|| _ticks_log_table||' (round, calc_time_ms, dt, logtype)
values ('|| _round_number||' , '|| _retstr|| ', current_timestamp, ''i'');
';

execute _sql;

EXCEPTION WHEN OTHERS THEN
_end_ts   := clock_timestamp();
select to_char(100 * extract(epoch FROM _end_ts - _start_ts), 'FM9999999999.99999999') into _retstr;
--RAISE NOTICE 'error msg is %', SQLERRM;
_sql := 
'insert into '|| _ticks_log_table||' (round, calc_time_ms, dt, error, logtype)
values ('|| _round_number||' , '|| _retstr|| ', current_timestamp, '''|| 'SQLSTATE: ' || SQLSTATE || ' SQLERRM: ' || SQLERRM ||''', ''i'');
';
execute _sql;    
 
	END
	$$;
	 
	 
