CREATE OR REPLACE PROCEDURE test()
LANGUAGE plpgsql AS
$$

DECLARE 
	tb int;
	tp int;
	ts varchar;
	_start_ts timestamptz;
	v int;
BEGIN
_start_ts := clock_timestamp();


-- Arti timer + delay on loss 

UPDATE app_roundstatus rs
SET artedelay =
(CASE
WHEN 
(SELECT COUNT (*) FROM app_artefacts art WHERE art.on_planet_id is not null) != 
(SELECT MAX(emparts) as max_emp
FROM 
(SELECT COUNT(art.empire_holding_id) AS emparts 
FROM app_artefacts art WHERE art.empire_holding_id is not null
GROUP BY art.empire_holding_id ) as emp_max)
AND rs.artetimer < 144
THEN artedelay - 1
WHEN artedelay = 0
THEN 5
ELSE artedelay
END);
UPDATE app_roundstatus rs
SET artetimer = 
(CASE
WHEN 
rs.artedelay = 0
THEN
144
WHEN (SELECT COUNT (*) FROM app_artefacts art WHERE art.on_planet_id is not null) = 
(SELECT MAX(emparts) as max_emp
FROM 
(SELECT COUNT(art.empire_holding_id) AS emparts 
FROM app_artefacts art WHERE art.empire_holding_id is not null
GROUP BY art.empire_holding_id ) as emp_max)
THEN artetimer - 1
ELSE artetimer
END);

-- terraformer arti with news

tb:=(SELECT (RANDOM()*(100-10)+10));
tp:=(SELECT id from "PLANET" p WHERE home_planet = False AND bonus_solar=0 AND bonus_mineral=0 
AND bonus_crystal=0 and bonus_ectrolium = 0 and bonus_fission = 0 AND p.owner_id = 
(SELECT id FROM app_userstatus u WHERE u.empire_id = 
(SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer'))
ORDER BY RANDOM() LIMIT 1);
v:= (SELECT (RANDOM()*(5-1)+1));


UPDATE "PLANET" P
SET bonus_fission = case 
    when v = 1
        then tb else bonus_fission
    end ,
  bonus_solar = case
    when  v = 2 
		then tb else bonus_solar
    end ,
  bonus_mineral = case
    when  v = 3 
		then tb else bonus_mineral
    end ,
  bonus_crystal = case
    when  v = 4
		then tb else bonus_crystal
    end ,
  bonus_ectrolium = case
    when  v = 5 
		then tb else bonus_ectrolium
    end 
WHERE p.id = tp
AND (SELECT ticks_left FROM app_artefacts WHERE name = 'Terraformer' ) = 0
and tp is not null;

insert into app_news
select 
(select id from app_news ORDER BY id DESC LIMIT 1) + 1, 'TE', (select tick_number from app_roundstatus), _start_ts, False, True, True, 'Terraformer', v, tb,
(SELECT empire_id FROM app_userstatus u WHERE u.empire_id = (SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer')), 
(SELECT empire_id FROM app_userstatus u WHERE u.empire_id = (SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer')),
tp, (SELECT id FROM app_userstatus u WHERE u.empire_id = (SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer')), 
(SELECT id FROM app_userstatus u WHERE u.empire_id = (SELECT empire_holding_id FROM app_artefacts WHERE name = 'Terraformer'))
where (SELECT ticks_left FROM app_artefacts WHERE name = 'Terraformer' ) = 0 and tp is not null
	;

--arti timers

UPDATE app_artefacts
SET ticks_left = case
	when ticks_left = 0 and name = 'Terraformer'
	then (SELECT Cast(RANDOM()*(59-10)+10 as int))
	when ticks_left = 0 and name = 'Flying Dutchman'
	then (SELECT Cast(RANDOM()*(59-10)+10 as int))
	else greatest(0,ticks_left - 1)
	end;

END
$$;
