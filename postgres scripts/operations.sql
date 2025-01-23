	CREATE OR REPLACE PROCEDURE operations(gal_nr integer default null, fleet_id integer default 0)
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
		and command_order = 6 --perform 
		and ticks_remaining = 0;

	--operations
	with operation as (
		select a.id id, owner_id, a.agent agents, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from '|| _ops_table||' o where o.name = specop) base_cost,
		ops_penalty('||gal_nr||', specop, owner_id) penalty,
		(select owner_id from '|| _planets_table ||' where id = target_planet_id) defid,
		(select stealth from '|| _ops_table||' o where o.name = a.specop) stealth
		from '|| _fleet_table ||' a 
		join '|| _userstatus_table ||' u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order = 6 --perform 
		and a.ticks_remaining = 0
		and u.agent_readiness >= 0
		and a.id = case when '|| fleet_id ||' = 0 then a.id else '|| fleet_id ||' end
		and (a.specop in (''Observe Planet'', ''Nuke Planet'') or (select owner_id from '|| _planets_table ||' where id = target_planet_id) is not null)
	),
	
	-- cant op empty planets
	
	not_empty as (
		select a.id id, target_planet_id p_id, specop, owner_id oid
		from '|| _fleet_table ||' a 
		where a.specop not in (''Observe Planet'', ''Nuke Planet'') 
		and (select owner_id from '|| _planets_table ||' where id = target_planet_id) is null
		and a.main_fleet = false
		and a.command_order = 6 --perform 
		and a.ticks_remaining = 0
	),

	--success
	

	success as (
		-- success
		select op.id s_id, p.id p_id, op.owner_id, op.specop, greatest(least((ops_Attack('||gal_nr||', op.id, op.owner_id, op.specop) / 
		--defence
		(case when p.owner_id is null then 50 else
		1.0 + (select dc.num_val * (COALESCE(df.agent,0)) * (1.0 + 0.005 * def.research_percent_operations)
		from '|| _userstatus_table ||' def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = ''agent_coeff''
		join '|| _fleet_table ||' df on df.main_fleet = true and df.owner_id = op.defid
		where def.id = df.owner_id) end)),3.0),0) success
		from operation op
		join '|| _planets_table ||' p on p.id = op.p_id
		where op.penalty < 150
	),
	--losses
	attloss as (
		select s.s_id al_id, (case when p.owner_id is null then 0 
		else 
			round(case when s.success < 2.0 
			then greatest(0, least(coalesce(op.agents,0), (1.0 - (0.5 * power((0.5 * s.success ), 1.1))) *
			(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.agents,0))) 
			else 0 end) 
		end) losses
		from success s
		join operation op on op.id = s.s_id
		join '|| _planets_table ||' p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, op.defid, op.c_o, 
		case when p.owner_id is null then 0 else round(case 
		when s.success < 2.0 then greatest(0, least(coalesce((select agent from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0), 
		(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
		* (op.random & 255))) * coalesce((select agent from '|| _fleet_table ||' where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
		end losses
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
		(greatest((case when p.owner_id is null then 1 else 
		(0.5*(power(((1.0+u.num_planets)/(1.0+(select num_planets from '|| _userstatus_table ||' d where d.user_id = p.owner_id))), 1.8)+
		(power(((1.0+(select planets from '|| _empire_table ||' where id = u.empire_id))/
		(1.0+(select planets from '|| _empire_table ||' where id =(select empire_id from '|| _userstatus_table ||' d where d.user_id = p.owner_id)))), 1.2))))
		end), 0.75)) fa
		from operation op
		join '|| _planets_table ||' p on p.id = op.p_id
		join '|| _userstatus_table ||' u on u.id = op.owner_id
		where op.penalty < 150
	),
	
	fa_cost as (
		select pc.id id, pc.atemp, pc.demp, pc.specop, pc.owner_id,(
		select case when penalty >= 150 then 0 else ((1.0 + 0.01 * penalty) * pc.base_cost * pc.fa) end) fa
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
	
<<<<<<< HEAD
	
=======
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
>>>>>>> af673816ef45ee0fa17f8cbf0913ae1cabcb01fa
	
	-- ops
	
	observe as (
		select s.s_id i_id, ( 
		 case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
		 else '''' end || 
		 case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
		 else '''' end ||
		case when s.success >= 0.4 then 
			''Planet Size: '' || p.size ||
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
		join '|| _planets_table ||' p on p.id = op.p_id 
		join success s on s.s_id = op.id and s.p_id = p.id
		join attloss al on al.al_id = op.id
		join defloss dl on dl.dl_id = op.id
		join prevent_neg n on n.id = op.id
	),
	network_i as (
		select op.id ni_id, ops_network('||gal_nr||', op.owner_id, op.defid, CAST(s.success AS NUMERIC(4,2))) r_per
		from operation op
		join success s on s.s_id = op.id
	),
	hack as (
		select op.id h_id, ops_hack('||gal_nr||', op.owner_id, op.defid, CAST(s.success AS NUMERIC(4,2))) hack
		from operation op
		join success s on s.s_id = op.id
	),
	bribe as (
		select op.id b_id, (case when op.random % 2 = 0 then 1 else 2 end) choice, 
			(case when op.random % 2 = 0 then least(300, round( power(s.success, 2) * 33))
			else least(900, round( power(s.success, 2) * 100)) end) per
		from operation op
		join success s on s.s_id = op.id
		where s.success >= 0.6
	),
	steal as (
		select op.id sr_id, op.owner_id u_id, op.defid d_id, (case when op.random % 10 in (0,1,2,3) then 1
			when op.random % 10 in (4,5,6) then 2 else 3 end) choice,
			round(case when op.random % 10 in (0,1,2,3) then (u.minerals *(s.success / 20))
			when op.random % 10 in (4,5,6) then (u.crystals *(s.success / 20)) else (u.ectrolium *(s.success / 20)) end) res
		from operation op
		join success s on s.s_id = op.id
		join '|| _userstatus_table ||' u on u.id = op.defid
		where s.success >= 1.0 and op.specop = ''Steal Resources''
	),
	mil_sab as (
		select op.id ms_id, op.defid defid,
			(ops_sab('||gal_nr||', ''bomber'', op.defid, s.success)) bomb,
			(ops_sab('||gal_nr||', ''fighter'', op.defid, s.success)) figs,
			(ops_sab('||gal_nr||', ''transport'', op.defid, s.success)) tran,
			(ops_sab('||gal_nr||', ''cruiser'', op.defid, s.success)) cru,
			(ops_sab('||gal_nr||', ''carrier'', op.defid, s.success)) car,
			(ops_sab('||gal_nr||', ''soldier'', op.defid, s.success)) sol,
			(ops_sab('||gal_nr||', ''droid'', op.defid, s.success)) dro,
			(ops_sab('||gal_nr||', ''goliath'', op.defid, s.success)) gol,
			(ops_sab('||gal_nr||', ''phantom'', op.defid, s.success)) pha,
			(ops_sab('||gal_nr||', ''wizard'', op.defid, s.success)) chi,
			(ops_sab('||gal_nr||', ''agent'', op.defid, s.success)) age,
			(ops_sab('||gal_nr||', ''ghost'', op.defid, s.success)) gho,
			(ops_sab('||gal_nr||', ''exploration'', op.defid, s.success)) exp
		from operation op
		join success s on s.s_id = op.id
		where op.specop = ''Military Sabotage''
	),
	bio as (
		select op.id bid, (case when s.success >= 1.0 then 0.6 else (0.6 / 0.4) * (s.success - 0.6) end) fa,
			sqrt(power(abs(p.x-(select x from '|| _planets_table ||' where id = op.p_id)), 2) + 
			power(abs(p.y-(select y from '|| _planets_table ||' where id = op.p_id)), 2)) dist, p.id pid
		from operation op
		join '|| _planets_table ||' p on p.owner_id = op.defid
		join success s on s.s_id = op.id
		where op.specop = ''Bio Infection''
	),
	kill_pop as (
		select b.bid bid, round(p.current_population * b.fa * (1.0 - (b.dist / 23.0))) pop_killed, b.pid pid
		from bio b
		join '|| _planets_table ||' p on p.id = b.pid
		where b.dist < 23.0
	),
	upd_bio as (
		update '|| _planets_table ||' p
		set current_population = current_population - b.pop_killed
		from kill_pop b where pid = p.id 
	),
	theft as (
		select op.id tid, least(100, round(pow(s.success,3)*12.5)) fa, p.planet_id pid, op.owner_id oid, p.scout, op.specop, s.success
		from operation op
		join success s on s.s_id = op.id
		join '|| _scouting_table ||' p on user_id = op.defid
		where op.specop = ''Maps theft''
	),
	ops as (
		select s.s_id i_id, (
		case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
		else '''' end || 
		case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
		else '''' end ||
		case when op.specop = ''Spy Target'' then 
			case when s.success >= 0.4 then
				case when s.success >= 0.5 then 
						 ''Fleet readiness: '' || u.fleet_readiness || ''%''
				else '''' end ||
				case when s.success >= 0.7 then
						chr(10) || ''Psychic readiness: '' || u.psychic_readiness || ''%''
				else '''' end ||
				case when s.success >= 0.9 then
						chr(10) || ''Agent readiness: '' || u.agent_readiness || ''%''
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
		when op.specop = ''Infiltration'' then
			case when s.success >= 0.4 then
				case when s.success >= 0.5 then
					 ''Energy: '' || u.energy
				else '''' end ||
				case when s.success >= 0.6 then
						chr(10) || ''Minerals: '' || u.minerals
				else '''' end ||
				case when s.success >= 0.4 then
					chr(10) || ''Crystals: '' || u.crystals
				else '''' end ||
				case when s.success >= 0.8 then
						chr(10) || ''Ectrolium: '' || u.ectrolium
				else '''' end ||
				case when s.success >= 0.7 then
						chr(10) || ''Solar Collectors: '' || u.total_solar_collectors
				else '''' end  ||
				case when s.success >= 1.0 then 
						chr(10) || ''Fission Reactors: '' || u.total_fission_reactors 
				else '''' end ||
				case when s.success >= 0.7 then
						chr(10) || ''Crystal Laboratories: '' || u.total_mineral_plants 
				else '''' end ||
				case when s.success >= 0.9 then
						chr(10) || ''Refinement Stations: '' || u.total_refinement_stations 
				else '''' end ||
				case when s.success >= 0.5 then
						chr(10) || ''Cities: '' || u.total_cities 
				else '''' end ||
				case when s.success >= 0.6 then
						chr(10) || ''Research Centers: '' || u.total_research_centers 
				else '''' end ||
				case when s.success >= 0.4 then
					chr(10) || ''Defense Satellites: '' || u.total_defense_sats
				else '''' end ||
				case when s.success >= 0.9 then
						chr(10) || ''Shield Networks: '' || u.total_shield_networks 
				else '''' end ||
				case when s.success >= 1.0 then
						chr(10) || ''Military Research: '' || u.research_percent_military || ''%''
				else '''' end ||
				case when s.success >= 0.9 then
						chr(10) || ''Contruction Research: '' || u.research_percent_construction || ''%'' 
				else '''' end ||
				case when s.success >= 0.8 then
						chr(10) || ''Technology Research: '' || u.research_percent_tech || ''%'' 
				else '''' end ||
				case when s.success >= 0.6 then
						chr(10) || ''Energy Research: '' || u.research_percent_energy || ''%'' 
				else '''' end ||
				case when s.success >= 0.7 then
						chr(10) || ''Population Research: '' || u.research_percent_population || ''%'' 
				else '''' end ||
				case when s.success >= 0.8 then
						chr(10) || ''Culture Research: '' || u.research_percent_culture || ''%'' 
				else '''' end ||
				case when s.success >= 1.0 then
						chr(10) || ''Operations Research: '' || u.research_percent_operations || ''%'' 
						|| chr(10) || ''Portals Research: '' || u.research_percent_portals || ''%'' 
				else '''' end
			else ''Your Agents failed''			
			end
		when op.specop = ''Diplomatic Espionage'' then
			case when s.success >= 1.0 then 
				''Your agents gathered information about all special operations affecting the target faction currently!''
			else
				''Your agents couldnt gather any information!''
			end
		when op.specop = ''High Infiltration'' then
			case when s.success >= 1.0 then 
				''Your agents gathered faction information!''
			else
				''Your agents couldnt gather any information!''
			end
		when op.specop = ''Network Infiltration'' then
			case when (select r_per from network_i where ni_id = op.id) > 0 then 
				(select r_per from network_i where ni_id = op.id) || ''% research was stolen!''
			else
				''No research was stolen!''
			end
		when op.specop = ''Hack mainframe'' then
			case when (select hack from hack where h_id = op.id) > 0 then 
				''Target income lost: '' || (select hack from hack where h_id = op.id) || ''%''
				|| chr(10) ||	''Our income increase: '' || (select hack from hack where h_id = op.id) || ''%''
			else
				''Your agents failed!''
			end
		when op.specop = ''Bribe officials'' then
			case when s.success >= 0.6 then 
				''Building '' || case when (select choice from bribe where b_id = op.id) = 1 then ''costs '' else '' time '' end
				|| ''increased by '' || (select per from bribe where b_id = op.id) || ''%''
			else
				''Your agents failed!''
			end
		when op.specop = ''Planetary Beacon'' then
			case when s.success >= 1.0 then 
				''All dark web effects were removed from the planet, however the planet defenders gained +10% military bonus!''
			else
				''Your agents failed!''
			end
		when op.specop = ''Steal Resources'' then
			case when s.success >= 1.0 then 
				''Our agents manged to steal '' || (select res from steal where sr_id = op.id) ||
					case when (select choice from steal where sr_id = op.id) = 1 then '' minerals!'' 
					when (select choice from steal where sr_id = op.id) = 2 then '' crystals!''
					else '' ectrolium!'' end
			else
				''Your agents failed!''
			end
		when op.specop = ''Military Sabotage'' then
			''Fleet Destroyed:'' ||
			case when (select bomb from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Bombers: '' || (select bomb from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select figs from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Fighters: '' || (select figs from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select tran from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Transports: '' || (select tran from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select cru from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Cruisers: '' || (select cru from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select car from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Carriers: '' || (select car from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select sol from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Soldiers: '' || (select sol from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select dro from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Droids: '' || (select dro from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select gol from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Goliaths: '' || (select gol from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select pha from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Phantoms: '' || (select pha from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select chi from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Psychics: '' || (select chi from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select age from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Agents: '' || (select age from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select gho from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Ghost Ships: '' || (select gho from mil_sab where ms_id = op.id)
			else '''' end ||
			case when (select exp from mil_sab where ms_id = op.id) > 0 then 
				chr(10) || ''Exploration Ships: '' || (select exp from mil_sab where ms_id = op.id)
			else '''' end
		when op.specop = ''Bio Infection'' then
			case when (select sum(pop_killed) from kill_pop where bid = op.id) > 0 then 
				''Your agents have spread a dangerous infection around target planets, killing a total of '' ||
					(select sum(pop_killed) from kill_pop where bid = op.id) || '' citizens!''
			else
				''Your agents failed!''
			end
		when op.specop = ''Maps theft'' then 
			case when s.success >= 1.0 then 
				''Your agents managed to gather scouting informaton about '' ||
				(select max(fa) from theft where tid = op.id) || ''% planets of target faction!''
			else
				''Your agents failed!''
			end
		end) news_info
		from operation op
		join '|| _userstatus_table ||' u on u.id = op.defid
		join success s on s.s_id = op.id
		join attloss al on al.al_id = op.id
		join defloss dl on dl.dl_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop != ''Observe Planet''
	),
	calc_time as (
		select s.s_id cid,
		(case when s.specop = ''Diplomatic Espionage'' then
			case when s.success >= 1.0 then 50.0 else
			least(50, cast(power(7, s.success) as int)) end
			when s.specop = ''High Infiltration'' then
			case when s.success >= 1.0 then 144.0 else 0 end
			when s.specop = ''Bribe officials'' then
			least(72, round(s.success *24))
			when s.specop = ''Planetary Beacon'' then
			case when s.success >= 1.0 then 24 else 0 end
		else 0 end) time
		from operation op
		join success s on s.s_id = op.id
		join prevent_neg n on n.id = op.id
		where s.success >= 1.0
	),
	time_based as (
		insert into '|| _specops_table ||'
		(user_to_id, user_from_id, specop_type, stealth, extra_effect, name, ticks_left, specop_strength, specop_strength2, planet_id)
		select (select owner_id from '|| _planets_table ||' where id = op.p_id), s.owner_id, ''O'', 
		(case when s.success >= 2.0 then true else false end), 
		(case when s.specop = ''Diplomatic Espionage'' then ''show special operations affecting target''
		when s.specop = ''Bribe officials'' then (case when (select choice from bribe where b_id = op.id) = 1 then ''resource_cost''
		else ''building_time'' end)
		when s.specop = ''High Infiltration'' then ''show high infiltration'' else '''' end), s.specop, t.time, 
		(case when s.specop = ''Bribe officials'' then (select per from bribe where b_id = op.id) else s.success end), 0, op.p_id
		from operation op
		join success s on s.s_id = op.id
		join calc_time t on t.cid = s.s_id
		join prevent_neg n on n.id = op.id
		where s.success >= 1.0
		and t.time > 0 and op.specop in (''Diplomatic Espionage'', ''High Infiltration'', ''Bribe officials'', ''Planetary Beacon'')
	),
	nuke_planet as (
		update '|| _planets_table ||' p
		set owner_id = null,
		size = cast(random()*(p.size-(p.size*0.8))+(p.size*0.8) as int),
		current_population = p.size * 20,
		max_population = p.size * 200,
		protection = 0,
		overbuilt = 0,
		overbuilt_percent = 0, 
		bonus_fission = (case when p.bonus_solar=0 and p.bonus_mineral=0 and p.bonus_crystal=0 and p.bonus_ectrolium=0 then
		cast(random()*(100-10)+10 as int) else 0 end),
		solar_collectors = 0,
		fission_reactors = 0,
		mineral_plants = 0,
		crystal_labs = 0,
		refinement_stations = 0,
		cities = 0,
		research_centers = 0,
		defense_sats = 0,
		shield_networks = 0,
		portal = false,
		portal_under_construction = false,
		total_buildings = 0,
		buildings_under_construction = 0
		from operation op
		join success s on s.s_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Nuke Planet'' and s.success >= 1.0 and p.id = op.p_id
	),
	nuke_constr as (
		delete from '|| _construction_table ||' 
		where planet_id in ( 
		select op.p_id from operation op
		join success s on s.s_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Nuke Planet'' and s.success >= 1.0)
	),
	nuke_station as (
		delete from '|| _fleet_table ||' 
		where id in ( 
		select op.id from operation op
		join success s on s.s_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Nuke Planet'' and s.success >= 1.0)
	),	
	nuke_news as (
		select s.s_id i_id, (
		case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
		else '''' end || 
		case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
		else '''' end ||
		case when s.success >= 1.0 then 
			''The planet was nuked! Most of population is dead. Planets building size is reduced.'' ||
			case when exists (select id from '|| _fleet_table ||' where target_planet_id = op.p_id and command_order = 8 and ticks_remaining = 0) then 
			''Stationed fleet was completely destroyed in the blast!''
			else '''' end
		else ''Your Agents failed'' end) news_info
		from operation op
		join success s on s.s_id = op.id
		join attloss al on al.al_id = op.id
		join defloss dl on dl.dl_id = op.id
		join prevent_neg n on n.id = op.id
		where op.specop = ''Nuke Planet''
	),
	--news
	ins_news_success as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''AA'', current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when e.specop = ''Observe Planet'' then (select news_info from observe where i_id = e.id)
		when e.specop = ''Nuke Planet'' then (select i.news_info from nuke_news i where i.i_id = e.id)
		else (select news_info from ops i where i_id = e.id)
		end)
		from operation e
		join success s on s.s_id =e.id
		join prevent_neg n on n.id = e.id
	),
	ins_no_ar_news as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.owner_id, (select owner_id from '|| _planets_table ||' where id = e.p_id),   
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.owner_id), 
		''AA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Not enough Agents Readiness, Agents returning!''
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
		''AA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Operations technology not high enough to perform '' || e.specop || chr(10) || ''Agents returning!''
		from operation e
		where penalty >= 150
	),
	flag_failed_empty as (
		update '|| _userstatus_table ||' u
		set military_flag = 1
		from (select oid id from not_empty group by oid) f 
		where u.id = f.id
	),
	not_empty_news as (
		insert into '|| _news_table||' 
		( user1_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select e.oid, (select empire_id from '|| _userstatus_table ||' u where u.user_id = e.oid), 
		''AA'', current_timestamp, true, false, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		''Your Agents cannot perform '' || e.specop || '' on an empty planet!'' || chr(10) || ''Agents returning!''
		from not_empty e
	),
	ins_news_defence as (
		insert into '|| _news_table||' 
		( user1_id, user2_id, empire1_id, news_type, date_and_time, is_personal_news, is_empire_news,
		is_read, tick_number, planet_id, fleet1, extra_info)
		select (select owner_id from '|| _planets_table ||' where id = e.p_id), 
		(case when s.success > 2.0 then e.owner_id else null end),
		(select empire_id from '|| _userstatus_table ||' u where u.user_id = e.defid), 
		''AD'', current_timestamp, true, true, false, 
		(select tick_number from '|| _roundstatus||' where round_number = '|| _round_number||'), e.p_id, e.specop,
		(case when al.losses > 0 then ''Attacker Lost: '' || al.losses || '' agents'' || chr(10) || '''' 
			else '''' end || 
			case when dl.losses > 0 then ''Defender Lost: '' || dl.losses || '' agents'' || chr(10) || '''' 
			else '''' end ||
		case when e.specop = ''Nuke Planet'' then
			case when s.success >= 1 then ''The planet was destroyed!''
			else ''Our agents managed to defend!'' end
		when e.specop = ''Network Infiltration'' then 
			case when (select r_per from network_i where ni_id = e.id) > 0 then 
			(select r_per from network_i where ni_id = e.id) || ''% research was stolen!'' else '''' end
		when e.specop = ''Hack mainframe'' then
			case when (select hack from hack where h_id = e.id) > 0 then
				''Our income lost: '' || (select hack from hack where h_id = e.id) || ''%''
			else ''Our agents managed to defend!'' end
		when e.specop = ''Bribe officials'' then
			case when s.success >= 0.6 then 
				''Building '' || case when (select choice from bribe where b_id = e.id) = 1 then ''costs '' else '' time '' end
				|| ''increased by '' || (select per from bribe where b_id = e.id) || ''%''
			else
				''Our agents managed to defend!''
			end
		when e.specop = ''Planetary Beacon'' then
			case when s.success >= 1.0 then 
				''All dark web effects were removed from the planet, however the planet defenders gained +10% military bonus!''
			else
				''Our agents managed to defend!''
			end
		when e.specop = ''Steal Resources'' then
			case when s.success >= 1.0 then 
				''Their agents manged to steal '' || (select res from steal where sr_id = e.id) ||
				case when (select choice from steal where sr_id = e.id) = 1 then '' minerals!'' 
				when (select choice from steal where sr_id = e.id) = 2 then '' crystals!''
				else '' ectrolium!'' end
			else
				''Your agents failed!''
			end
		when e.specop = ''Military Sabotage'' then
			''Fleet Destroyed:'' ||
			case when (select bomb from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Bombers: '' || (select bomb from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select figs from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Fighters: '' || (select figs from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select tran from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Transports: '' || (select tran from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select cru from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Cruisers: '' || (select cru from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select car from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Carriers: '' || (select car from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select sol from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Soldiers: '' || (select sol from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select dro from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Droids: '' || (select dro from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select gol from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Goliaths: '' || (select gol from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select pha from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Phantoms: '' || (select pha from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select chi from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Psychics: '' || (select chi from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select age from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Agents: '' || (select age from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select gho from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Ghost Ships: '' || (select gho from mil_sab where ms_id = e.id)
			else '''' end ||
			case when (select exp from mil_sab where ms_id = e.id) > 0 then 
				chr(10) || ''Exploration Ships: '' || (select exp from mil_sab where ms_id = e.id)
			else '''' end
		when e.specop = ''Bio Infection'' then
			case when (select sum(pop_killed) from kill_pop where bid = e.id) > 0 then 
				''A pandemic is causing a lot of deaths around your planets, killing a total of '' ||
					(select sum(pop_killed) from kill_pop where bid = e.id) || '' citizens!''
			else
				''Your agents prevailed!''
			end
		when e.specop = ''Maps theft'' then 
			case when s.success >= 1.0 then 
				''Your scouting maps were stolen! ''
			else
				''Your agents defended your maps information!''
			end
		else
			case when s.success >= 1 then ''Their agents were successful!''
			when s.success >= 0.4 then ''Our agents managed to stop the attackers before all damage was done!''
			else ''Our agents managed to defend!'' end
		end
		)
		from operation e 
		join success s on s.s_id = e.id
		join attloss al on al.al_id = e.id
		join defloss dl on dl.dl_id = e.id
		join prevent_neg n on n.id = e.id
		where e.defid is not null
		and (s.success < 2.0 or e.stealth = false)
	),
	--scouting
	merge_scout as (
		merge into '|| _scouting_table ||' a
		using (select op.owner_id, op.p_id, max(op.success) success
		from success op
		join prevent_neg n on n.id = op.s_id
		where op.specop = ''Observe Planet''
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
	merge_bio as (
		merge into '|| _scouting_table ||' a
		using (select op.oid, op.pid, max(op.scout) success
		from theft op
		join prevent_neg n on n.id = op.tid 
		where op.specop = ''Maps theft'' and op.fa > cast(random()*(100-0)+0 as int) and op.success >= 1.0
		group by op.pid, op.oid
		) o
		on a.empire_id = (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.oid) and 
		a.planet_id = o.pid
		WHEN MATCHED THEN
			UPDATE SET scout = case when o.success >= a.scout then o.success else a.scout end
		WHEN NOT MATCHED THEN
		  INSERT (planet_id, empire_id, user_id, scout)
		  VALUES (o.pid, (select empire_id from '|| _userstatus_table ||' u where u.user_id = o.oid), o.oid, o.success)
	),
	send_home as (
		update '|| _fleet_table ||' a
		set i = s.i,
		x = s.x,
		y = s.y,
		agent = agent - COALESCE((select losses from attloss where al_id = a.id), 0),
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
	and a.command_order = 6 and a.ticks_remaining = 0
	),
	deflosses as (
		update '|| _fleet_table ||' f
		set bomber = bomber - coalesce((select sum(bomb) from mil_sab where defid = f.owner_id),0),
		fighter = fighter - coalesce((select sum(figs) from mil_sab where defid = f.owner_id),0),
		transport = transport - coalesce((select sum(tran) from mil_sab where defid = f.owner_id),0),
		cruiser = cruiser - coalesce((select sum(cru) from mil_sab where defid = f.owner_id),0),
		carrier = carrier - coalesce((select sum(car) from mil_sab where defid = f.owner_id),0),
		soldier = soldier - coalesce((select sum(sol) from mil_sab where defid = f.owner_id),0),
		droid = droid - coalesce((select sum(dro) from mil_sab where defid = f.owner_id),0),
		goliath = goliath - coalesce((select sum(gol) from mil_sab where defid = f.owner_id),0),
		phantom = phantom - coalesce((select sum(pha) from mil_sab where defid = f.owner_id),0),
		wizard = wizard - coalesce((select sum(chi) from mil_sab where defid = f.owner_id),0),
		agent = agent - (coalesce((select sum(age) from mil_sab where defid = f.owner_id),0) + (select sum(losses) from defloss where defid = f.owner_id)),
		ghost = ghost - coalesce((select sum(gho) from mil_sab where defid = f.owner_id),0),
		exploration = exploration - coalesce((select sum(exp) from mil_sab where defid = f.owner_id),0)
		from (select defid from operation group by defid) o
		where f.owner_id=o.defid and f.main_fleet=true
	),
	update_def as (
		update '|| _userstatus_table ||' u
		set military_flag = 1,
		minerals = minerals - coalesce((select sum(res) from steal where d_id = c.defid and choice = 1),0),
		crystals = crystals - coalesce((select sum(res) from steal where d_id = c.defid and choice = 2),0),
		ectrolium = ectrolium - coalesce((select sum(res) from steal where d_id = c.defid and choice = 3),0)
		from (select defid from operation group by defid) c 
		where u.id = c.defid
	)
	update '|| _userstatus_table ||' u
	set military_flag = case when c.penalty >=150 then 1 else case when military_flag != 1 then 2 else 1 end end ,
	agent_readiness = agent_readiness - COALESCE((select sum(r.fa) from r_cost r join prevent_neg n on n.id = r.id where owner_id=u.id group by owner_id),0),
	minerals = minerals + coalesce((select sum(res) from steal where u_id = c.owner_id and choice = 1),0),
	crystals = crystals + coalesce((select sum(res) from steal where u_id = c.owner_id and choice = 2),0),
	ectrolium = ectrolium + coalesce((select sum(res) from steal where u_id = c.owner_id and choice = 3),0)
	from (select owner_id, max(penalty) penalty from operation group by owner_id) c 
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
	 
	 
	END
	$$;
	 
	 