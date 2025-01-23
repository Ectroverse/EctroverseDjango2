--gen random
		update app_fleet
		set random = random()*(2147483647-0)
		where main_fleet = FALSE
		and command_order = 6 --perform 
		and ticks_remaining = 0;

	--operations
	with operation as (
		select a.id id, owner_id, a.agent agents, specop, target_planet_id p_id, random, command_order c_o, 
		(select readiness from app_ops o where o.name = specop) base_cost,
		case when (select tech from app_ops o where o.name = specop) = 0 then 0 else 
		(case when greatest(0,pow(((select tech from app_ops o where o.name = specop) - u.research_percent_operations),1.2),0) < 0 then 0
		else greatest(0,pow(((select tech from app_ops o where o.name = specop) - u.research_percent_operations),1.2),0) end) end penalty,
		(select owner_id from "PLANET" where id = target_planet_id) defid,
		(select stealth from app_ops o where o.name = a.specop) stealth
		from app_fleet a 
		join app_userstatus u on u.user_id = a.owner_id
		where a.main_fleet = FALSE
		and a.command_order = 6 --perform 
		and a.ticks_remaining = 0
		and u.agent_readiness >= 0
		and a.id = case when 0 = 0 then a.id else 0 end
	),
	attack as (
	 select op.id a_id, (((0.6 + (0.8/ 255.0) * (op.random & 255))) * att.num_val * coalesce(op.agents,0) *
		(select (1.0 + 0.01 * u.research_percent_operations) from app_userstatus u where u.user_id = op.owner_id)/
		(select difficulty from app_ops o where o.name = op.specop) / 
		(case when op.penalty > 0 then 1 + (0.01 * op.penalty) else 1 end)) attack
		from operation op
		join app_userstatus a on a.id = op.owner_id
		join classes c on c.name = a.race
		join constants att on att.class = c.id and att.name = 'agent_coeff'
		where op.penalty < 150
	),
	success as (
		-- success
		select op.id s_id, p.id p_id, op.owner_id, op.specop,COALESCE((atac.attack / 
		--defence
		(case when p.owner_id is null then 50 else
		1.0 + (select dc.num_val * (COALESCE(df.agent,0)) * (1.0 + 0.005 * def.research_percent_operations)
		from app_userstatus def
		join classes d_c on d_c.name = def.race
		join constants dc on dc.class = d_c.id and dc.name = 'agent_coeff'
		join app_fleet df on df.main_fleet = true and df.owner_id = op.defid) end)),0) success
		from operation op
		join "PLANET" p on p.id = op.p_id
		join attack atac on op.id = atac.a_id
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
		join "PLANET" p on p.id = op.p_id 
		where s.p_id = op.p_id
	),
	defloss as (
		select s.s_id dl_id, op.defid, op.c_o, 
		case when p.owner_id is null then 0 else round(case 
		when s.success < 2.0 then greatest(0, least(coalesce((select agent from app_fleet where main_fleet=true and owner_id = p.owner_id),0), 
		(0.5 * power((0.5 * s.success ), 1.1)) * (1.0 - power((0.5 * s.success), 0.2)) * (0.75 + (0.5 / 255.0) 
		* (op.random & 255))) * coalesce((select agent from app_fleet where main_fleet=true and owner_id = p.owner_id),0))else 0 end)
		end losses
		from success s
		join operation op on op.id = s.s_id
		join "PLANET" p on p.id = op.p_id
		where s.p_id = op.p_id
	),
	
	deflosses as (
		update app_fleet f
		set agent = agent - l.lost
		from (select sum(losses) lost , defid from defloss group by defid) l
		where f.owner_id=l.defid and main_fleet=true
	),
	--readiness
	p_cost as (
		select op.id id, u.empire_id atemp, op.penalty, op.base_cost, op.specop, op.owner_id,
		(case when p.owner_id is null then 1 else
		(select empire_id from app_userstatus d where d.user_id = p.owner_id) end) demp,
		(greatest((case when p.owner_id is null then 1 else 
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
	)
	select * from (
	select b.*, lag(c_sum, 1, 100) over(partition by owner_id order by id) lag_sum from (
	select r.* , u.agent_readiness - sum(fa )
	OVER (PARTITION BY u.id
    ORDER BY r.id) c_sum
	from r_cost r
	join app_userstatus u on u.id = r.owner_id
	where u.agent_readiness >= 0 --the the first op always completes
	)b  
	) c where lag_sum >= 0

	