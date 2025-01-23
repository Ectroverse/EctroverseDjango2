CREATE OR REPLACE function ops_network
(gal_nr integer, u_id int, d_id int, success float)
returns double PRECISION
LANGUAGE plpgsql AS
$$
declare
	_r_per double PRECISION;
	_userstatus_table varchar;
	_sql varchar;
BEGIN

	if gal_nr = 1 then
		_userstatus_table := 'app_userstatus';
	else 
		_userstatus_table := 'galtwo_userstatus';
	end if;
		
	if success >= 1.0 then 
		_r_per := 3;
	else 
		_r_per := least(3.0, (3.0 / 0.6) * (success - 0.4));
	end if;

	_sql = '
	with r_points as (
		select u.research_points_military * (0.01 * '|| _r_per ||') mil,
			u.research_points_construction * (0.01 * '|| _r_per ||') con,
			u.research_points_tech * (0.01 * '|| _r_per ||') tec,
			u.research_points_energy * (0.01 * '|| _r_per ||') eng,
			u.research_points_population * (0.01 * '|| _r_per ||') pop,
			u.research_points_culture * (0.01 * '|| _r_per ||') cul,
			u.research_points_operations * (0.01 * '|| _r_per ||') ops,
			u.research_points_portals * (0.01 * '|| _r_per ||') por
		from '|| _userstatus_table ||' u
		where id = '|| d_id ||'
	),
	defender as (
		update '|| _userstatus_table ||' 
		set research_points_military = research_points_military - rp.mil,
			research_points_construction = research_points_construction - rp.con,
			research_points_tech = research_points_tech - rp.tec,
			research_points_energy = research_points_energy - rp.eng,
			research_points_population = research_points_population - rp.pop,
			research_points_culture = research_points_culture - rp.cul,
			research_points_operations = research_points_operations - rp.ops,
			research_points_portals = research_points_portals - rp.por
		from r_points rp
		where id = '|| d_id ||'
	)
	update '|| _userstatus_table ||' 
		set research_points_military = research_points_military + rp.mil,
			research_points_construction = research_points_construction + rp.con,
			research_points_tech = research_points_tech + rp.tec,
			research_points_energy = research_points_energy + rp.eng,
			research_points_population = research_points_population + rp.pop,
			research_points_culture = research_points_culture + rp.cul,
			research_points_operations = research_points_operations + rp.ops,
			research_points_portals = research_points_portals + rp.por
		from r_points rp
		where id = '|| u_id ||'
	';
	
	execute _sql;

	return _r_per;
end 
$$;