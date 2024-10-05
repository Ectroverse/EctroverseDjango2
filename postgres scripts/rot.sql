
### Arti timer + delay on loss ###

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