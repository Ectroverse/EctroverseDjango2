 lock table "PLANET";
	 lock table app_userstatus;
	 lock table app_fleet;
	 lock table app_scouting;
	 lock table app_news;
	 lock table app_specops;

	--gen random
		update app_fleet
		set random = random()*(2147483647-0)
		where main_fleet = FALSE
		and command_order = 7 --perform 
		and ticks_remaining = 0;

	--operations
	with recursive operation as (
		select a.id id, owner_id, a.ghost ghosts, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from app_ops o where o.name = specop) base_cost,
		ops_penalty(1, specop, owner_id) penalty,
		(select owner_id from "PLANET" where id = target_planet_id) defid,
		(select stealth from app_ops o where o.name = a.specop) stealth,
		u.empire_id
		from app_fleet a 
		join app_userstatus u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order = 7 --perform 
		and a.ticks_remaining = 0
		and u.psychic_readiness >= 0
		and a.id = case when 0 = 0 then a.id else 0 end
		and (a.specop in ('Survey System', 'Sense Artefact', 'Vortex Portal') or (select owner_id from "PLANET" where id = target_planet_id) is not null)
	),
	-- cant op empty planets
	
	not_empty as (
		select a.id id, target_planet_id p_id, specop, owner_id oid
		from app_fleet a 
		where a.specop not in ('Survey System', 'Sense Artefact', 'Vortex Portal') 
		and (select owner_id from "PLANET" where id = target_planet_id) is null
		and a.main_fleet = false
		and a.command_order = 7 --perform 
		and a.ticks_remaining = 0
	),
	success as (
		-- success
		select op.id s_id, p.id p_id, op.owner_id, op.specop, ops_Attack(1, op.id, op.owner_id, op.specop) attack,
		greatest((ops_Attack(1, op.id, op.owner_id, op.specop) / 
		--defence
		(case when op.specop in ('Survey System', 'Sense Artefact') then 
			(select networth from app_userstatus where id = op.owner_id) / op.ghosts
		when p.owner_id is null or p.owner_id = op.owner_id then 50 else
		1.0 + (select ((dc.num_val * (COALESCE(df.wizard,0)) * (1.0 + 0.005 * def.research_percent_culture)) / 7)
		from app_userstatus def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = 'psychic_coeff'
		join app_fleet df on df.main_fleet = true and df.owner_id = op.defid
		where def.id = df.owner_id) end)),0) success,
		-- ghost defence
		greatest(least((ops_Attack(1, op.id, op.owner_id, op.specop) / 
		--defence
		(case when p.owner_id is null then 50 else
		1.0 + (select dc.num_val * (COALESCE(df.ghost,0)) * (1.0 + 0.005 * def.research_percent_culture)
		from app_userstatus def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = 'ghost_coeff'
		join app_fleet df on df.main_fleet = true and df.owner_id = op.defid
		where def.id = df.owner_id) end)),3.0),0) g_def
		
		from operation op
		join "PLANET" p on (case when op.specop != 'Survey System' then p.id = op.p_id else 
		p.x = (select x from "PLANET" where id = op.p_id) AND
		p.y = (select y from "PLANET" where id = op.p_id) end)
		where op.penalty < 150
	),
	--losses
	attloss as (
		select s.s_id al_id, (case when p.owner_id is null or op.specop in ('Survey System', 'Sense Artefact', 'Vortex Portal') 
		or p.owner_id = op.owner_id then 0 
		else 
			round(case when s.success < 2.0 
			then greatest(0, least(coalesce(op.ghosts,0), (1.0 - (0.5 * power((0.5 * s.success ), 1.1))) *
			(1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) * (op.random & 255)) * coalesce(op.ghosts,0))) 
			else 0 end) 
		end) losses
		from success s
		join operation op on op.id = s.s_id
		join "PLANET" p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, op.defid, op.c_o, 
		case when op.specop not in ('Survey System', 'Sense Artefact', 'Vortex Portal') then
			(case when p.owner_id is null or p.owner_id = op.owner_id then 0 else round(case 
			when s.success < 2.0 then greatest(0, least(coalesce((select wizard from app_fleet where main_fleet=true and owner_id = p.owner_id),0), 
			(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
			* (op.random & 255))) * coalesce((select wizard from app_fleet where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
			end) end losses,
		case when op.specop not in ('Survey System', 'Sense Artefact', 'Vortex Portal') then		
			(case when p.owner_id is null or p.owner_id = op.owner_id then 0 else round(case 
			when s.success < 2.0 then greatest(0, least(coalesce((select ghost from app_fleet where main_fleet=true and owner_id = p.owner_id),0), 
			(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
			* (op.random & 255))) * coalesce((select ghost from app_fleet where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
			end) end g_losses
		from success s
		join operation op on op.id = s.s_id
		join "PLANET" p on p.id = op.p_id
		where s.p_id = op.p_id
	),
	

	--readiness
	p_cost as (
		select op.id id, u.empire_id atemp, op.penalty, op.base_cost, op.specop, op.owner_id,
		(case when p.owner_id is null then 1 else
		(select empire_id from app_userstatus d where d.user_id = p.owner_id) end) demp,
		(greatest((case when op.specop in ('Survey System', 'Sense Artefact', 'Vortex Portal') or p.owner_id is null then 1 else 
		(0.5*(power(((1.0+u.num_planets)/(1.0+(select num_planets from app_userstatus d where d.user_id = p.owner_id))), 1.8)+
		(power(((1.0+(select planets from app_empire where id = u.empire_id))/
		(1.0+(select planets from app_empire where id =(select empire_id from app_userstatus d where d.user_id = p.owner_id)))), 1.2))))
		end), 0.75)) fa
		from operation op
		join "PLANET" p on p.id = op.p_id
		join app_userstatus u on u.id = op.owner_id
	),
	
	fa_cost as (
		select pc.id id, pc.atemp, pc.demp, pc.specop, pc.owner_id,(
		select ((1.0 + 0.01 * penalty) * pc.base_cost * pc.fa)) fa
		from p_cost pc
	),
	
	w_cost as (
		select c.id id, c.atemp, c.demp, c.specop, c.owner_id,(
		select case when exists (select c.fa from app_relations
		where empire1_id in (c.atemp, c.demp) and empire2_id in (c.atemp, c.demp)
		and relation_type in ('A', 'W'))
		then c.fa/3
		else c.fa end) fa
		from fa_cost c
	),
	
	r_cost as (
		select c.id id, c.specop, c.owner_id,(
		select case when exists (select c.fa from app_relations
		where empire1_id in (c.atemp, c.demp) and empire2_id in (c.atemp, c.demp)
		and relation_type in ('NC', 'PC', 'N', 'C'))
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
		chr(10) ||'Planet: ' || p.i || chr(10) ||
		case when p.owner_id is not null then 
			 'Owned by: ' || (select user_name from app_userstatus where id = p.owner_id) || chr(10) || 
			 '' 
		else '' end ||
		case when s.success >= 0.4 then 
			'Size: ' || p.size ||
			 case when s.success >= 0.9 then 
				 case when p.bonus_solar > 0 then chr(10) || 'Solar Bonus: ' || p.bonus_solar || '%' 
				 when p.bonus_fission > 0 then chr(10) || 'Fission Bonus: ' || p.bonus_fission || '%' 
				 when p.bonus_mineral > 0 then chr(10) || 'Mineral Bonus: ' || p.bonus_mineral || '%' 
				 when p.bonus_crystal > 0 then chr(10) || 'Crystal Bonus: ' || p.bonus_crystal || '%' 
				 when p.bonus_ectrolium > 0 then chr(10) || 'Ectrolium Bonus: ' || p.bonus_mineral || '%' 
				 else '' end 
			else '' end ||
			case when p.owner_id is not null then
				case when s.success >= 0.5 then
					chr(10) || 'Current population: ' || p.current_population
				else '' end ||
				case when s.success >= 0.6 then
					chr(10) || 'Max population: ' || p.max_population
				else '' end ||
				case when s.success >= 0.7 then
					chr(10) || 'Portal protection: ' || p.protection 
				else '' end ||
				case when s.success >= 0.8 then 
					 chr(10) || 'Solar Collectors: ' || p.solar_collectors ||
					 chr(10) || 'Fission Reactors: ' || p.fission_reactors  ||
					 chr(10) || 'Mineral Plants: ' || p.mineral_plants ||
					 chr(10) || 'Crystal Labs: ' || p.crystal_labs || 
					 chr(10) || 'Refinement Stations: ' || p.refinement_stations ||
					 chr(10) || 'Cities: ' || p.cities ||
					 chr(10) || 'Research Centers: ' || p.research_centers ||
					 chr(10) || 'Defense Sats: ' || p.defense_sats ||
					 chr(10) || 'Shield Networks: ' || p.shield_networks 
				else '' end ||
				case when s.success >= 1.0 then
					chr(10) || 'Portal: ' || 
						case when p.portal = true then 'Present' 
							when p.portal_under_construction = true then 'Under construction' 
						else 'Absent' end
				else '' end
			else '' end ||
			case when s.success >= 1.0 and p.artefact_id is not null then
				chr(10) || 'Artefact: ' ||
				(select name from app_artefacts a where a.id = p.artefact_id)
			else '' end
		 else 'No information was gathered about this planet!' || '' end
		 ) news_info
		from operation op
		join "PLANET" p on p.x = (select x from "PLANET" where id = op.p_id) AND
		p.y = (select y from "PLANET" where id = op.p_id)
		join success s on s.s_id = op.id and s.p_id = p.id
		join prevent_neg n on n.id = op.id
		where op.specop = 'Survey System'
		order by p.i
	),
	-- pff, ps and vp
	
	ticks as (
		select op.p_id pid, op.id,
			(case when op.specop = 'Planetary Shielding' then cast(random()*(100-10)+10 as int)
			when op.specop = 'Portal Force Field' then cast(random()*(47-16)+16 as int)
			when op.specop = 'Vortex Portal' then 
				round(least(144, (3 + (120 * ((ops_Attack(1, op.id, op.owner_id, op.specop) * 7) / 
					(select networth from app_userstatus where id = op.owner_id))))))
			else 0 end) ticks
		from operation op 
		where specop in ('Planetary Shielding', 'Portal Force Field', 'Vortex Portal')
	),
	strength as (
		select op.p_id pid, op.id,
			(case when op.specop = 'Planetary Shielding' then
			round(ops_Attack(1, op.id, op.owner_id, op.specop) * cast(random()*(500-250)+250 as int))
			when op.specop = 'Portal Force Field' then round(200 * ((select success from success where s_id = op.id) - 0.5))
			else (select success from success where s_id = op.id) end) strength
		from operation op 
		where specop in ('Planetary Shielding', 'Portal Force Field', 'Vortex Portal')
	),
	create_op as(
		insert into app_specops 
		(user_to_id, user_from_id, specop_type, stealth, name, ticks_left, specop_strength, specop_strength2, planet_id)
		select (case when op.specop = 'Vortex Portal' then s.owner_id ELSE
		(select owner_id from "PLANET" where id = op.p_id) end), s.owner_id, 'G', 
		(case when s.success >= 2.0 then true else false end), s.specop, t.ticks, 
		(select strength from strength where id = op.id), 0, op.p_id
		from operation op
		join success s on s.s_id = op.id
		join ticks t on t.id = s.s_id
		join prevent_neg n on n.id = op.id
		where (select strength from strength where id = op.id) > 0 and t.ticks > 0
		and op.specop in ('Planetary Shielding', 'Portal Force Field', 'Vortex Portal')
	),
	-- other incas
	call as (
		select op.id cid, ((case when s.success >= 1.0 then 
			0.8 else 2 * (s.success - 0.6) end)  * cast(random()*(110-90)+90 as int) / 100) fa,
			sqrt(power(abs(p.x-(select x from "PLANET" where id = op.p_id)), 2) + 
			power(abs(p.y-(select y from "PLANET" where id = op.p_id)), 2)) dist, p.id pid, op.defid
		from operation op
		join "PLANET" p on p.owner_id = op.defid
		join success s on s.s_id = op.id
		where op.specop = 'Call to Arms'
	),
	kill_pop as (
		select c.cid, least(p.current_population,round(p.current_population * c.fa * (1.0 - (c.dist / 16.0)))) pop_killed, c.pid, c.defid
		from call c
		join "PLANET" p on p.id = c.pid
		where c.dist < 16.0
	),
	gained_sols as (
		select round((c.pop_killed/100 * (1.0 + 0.01 * (select research_percent_military from app_userstatus where id = c.defid)))
		/ 2 ) sols_gained, c.cid, c.defid
		from kill_pop c
	),
	upd_call as (
		update "PLANET" p
		set current_population = current_population - b.pop_killed
		from kill_pop b where pid = p.id 
	),
	add_sols as (
		update "PLANET" p
		set current_population = current_population - b.pop_killed
		from kill_pop b where pid = p.id 
	),
	mind_c as (
		update "PLANET" p
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
		where op.specop = 'Mind Control' and s.success >= 1.0 and p.id = op.p_id
	),
	mind_arti as (
		update app_artefacts p
		set empire_holding_id = op.empire_id
		from operation op
		join success s on s.s_id = op.id
		where op.specop = 'Mind Control' and s.success >= 1.0 and p.on_planet_id = op.p_id
	),
	merge_mind_scout as (
		merge into app_scouting a
		using (select op.empire_id, op.owner_id, op.p_id
		from operation op 
		join success s on s.s_id = op.id
		where op.specop = 'Mind Control' and s.success >= 1.0 
		) s
		on a.empire_id = s.empire_id and a.user_id = s.owner_id and a.planet_id = s.p_id
		WHEN MATCHED THEN
			UPDATE SET scout = 1.0
		WHEN NOT MATCHED THEN
		  INSERT (scout, empire_id, user_id, planet_id)
		  VALUES (1, s.empire_id, s.owner_id, s.p_id)
	),
	--sense
	sense as (
		select empire_id, user_id, fleet_id, p_id, system_id, x, y		
		from(
		select op.id fleet_id, op.empire_id, op.owner_id user_id, op.p_id,
			greatest((2*random(0.2,0.8)*log10(10 * s.attack)), 1) strength,
			 sqrt(1+ pow(p.x-p2.x,2) + pow(p.y-p2.y,2) ) dist,
			 s.success,
			 p2.id system_id, p2.x, p2.y
			from operation op
			join prevent_neg n on n.id = op.id
			join success s on s.s_id = op.id and s.success >= 1
			join "PLANET" p on p.id = op.p_id
			join app_system p2 on 1=1
			where op.specop = 'Sense Artefact'
		) where strength >= dist
		group by empire_id, user_id, fleet_id, p_id, system_id, x, y
		),
	ins_sense as 
		(
		merge into app_sensing a
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
		'Your Ghost Ships have located an Artefact at Planet:' || p.x ||','|| p.y || ':' || p.i news_info
		from app_artefacts  a
		join "PLANET" p on p.id = a.on_planet_id
		join sense s on s.x = p.x and s.y = p.y
	),
	merge_arti_scout as 
	(
		merge into app_scouting a
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
				join app_userstatus u on u.id = op.defid
				where op.specop = 'Energy Surge'
	),
	energy_surge_recursive AS (
	
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
				' ' as news,
				0 as attid,
				op.defid as defid
				from operation op 
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				join app_userstatus u on u.id = op.defid
				where op.specop = 'Energy Surge'
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
				where op.specop = 'Energy Surge'
				and op.id > e.min_op_id
				and op.defid = e.defid
			) min_op_id,
			e.min_op_id last_op_id,
			'Energy lost: ' || e.energy || ' '
			|| 'Minerals lost: ' || cast(least(e.minerals*0.3, e.total_damage/30) as bigint) || ' '
			|| 'Crystals lost: ' || cast(least(e.crystals*0.3, e.total_damage/60) as bigint) || ' '
			|| 'Ectrolium lost: ' || cast(least(e.ectrolium*0.3, e.total_damage/50) as bigint) || ' '
			|| 'Solars lost: ' || cast(least(total_solar_collectors*0.25, total_damage/3000) as bigint) || ' '
			|| 'Fissions lost: ' || cast(least(total_fission_reactors*0.25, total_damage/4000) as bigint) || ' '
			|| 'Research lost: ' || cast(least(total_rc_points*0.2, total_damage/2) as bigint) || ' '
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
	esurge_update1 as (
		update app_userstatus u
		set energy = b.energy,
		minerals =b.minerals,
		crystals = b.crystals,
		ectrolium = b.ectrolium,
		research_percent_operations = research_percent_operations * rc_points_loss,
		research_points_military = research_points_military * rc_points_loss,
		research_points_construction = research_points_construction * rc_points_loss,
		research_points_tech = research_points_tech * rc_points_loss,
		research_points_energy = research_points_energy * rc_points_loss,
		research_points_population = research_points_population * rc_points_loss,
		research_points_culture = research_points_culture * rc_points_loss,
		research_points_operations = research_points_operations * rc_points_loss,
		research_points_portals = research_points_portals * rc_points_loss
		from esurge_losses b
		where u.id = b.defid
	),
	esurge_update2 as (
		update "PLANET" p
		set fission_reactors = fission_reactors * fissions_loss,
		solar_collectors = solar_collectors * solars_loss
		from esurge_losses e
		where p.owner_id = e.defid
	)

		
	select * from esurge_losses;*/

--	select id, energy from app_userstatus
	


	--select * from esurge_losses
	/*
		    select 
				min(op.id) op_id, 
				op.owner_id attacker_user_id, 
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
				op.defid defender_user_id,
				0 n,
				count(*) total_ops,
				greatest(max(u.networth), max(u.energy)) as total_damage,  
				max(u.networth) networth,
				min(op.id) min_op_id
				from operation op
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				join app_userstatus u on u.id = op.defid
				where op.specop = 'Energy Surge'
				group by op.defid, op.owner_id
*/
				/*
	
	,	
   energy_surge AS (
	    select 
				max(op.id) op_id, 
				max(op.owner_id )attacker_user_id, 
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
				max(u.id) defender_user_id,
				0 n,
				count(*) total_ops,
				greatest(max(u.networth), max(u.energy)) as total_damage,  
				max(u.networth) networth,
				min(op.id) min_op_id
				from operation op
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				join app_userstatus u on u.id = op.defid
				where op.specop = 'Energy Surge'
				group by op.defid
  			UNION ALL
		    SELECT 
			e.op_id, e.attacker_user_id, 
			0 as energy ,
			e.minerals - cast(least(e.minerals*0.3, e.total_damage/30) as bigint) as minerals, 
			e.crystals - cast(least(e.crystals*0.3, e.total_damage/60) as bigint) as crystals, 
			e.ectrolium - cast(least(e.ectrolium*0.3, e.total_damage/50) as bigint) as ectrolium, 
			e.total_solar_collectors - cast(least(total_solar_collectors*0.25, total_damage/3000) as int) as total_solar_collectors,
			e.total_fission_reactors - cast(least(total_fission_reactors*0.25, total_damage/4000) as int) as total_fission_reactors,
			e.total_rc_points - cast(least(total_rc_points*0.2, total_damage/2) as bigint) as total_rc_points,
			e.defender_user_id, n+1, total_ops,
			greatest(e.networth, 0) as total_damage, networth,
			(select min(op.id)
				from operation op
				join prevent_neg n on n.id = op.id
				join success s on s.s_id = op.id and s.success >= 1
				where op.specop = 'Energy Surge'
				and op.id > e.min_op_id
				and op.defid = e.defender_user_id
			) min_op_id
			FROM energy_surge e
			WHERE min_op_id is not null
		)

		select * from energy_surge 
		--where n > 0
*/	