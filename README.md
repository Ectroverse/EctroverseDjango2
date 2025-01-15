#### v0.2 Remaining Items

- new player tutorial
- finish Guide
- add device fingerprinting to prevent double accounts

## Note

Change "ectroversedjango" to folder name on local machine for bash etc

## Getting it setup on a new machine:

(you'll need docker and docker-compose installed, google how to do it for your OS)

0. Copy .env.template to .env (`cp .env.template .env`) and change the secret key if you care about security
1. `docker-compose up -d`
2. `docker exec -it ectroversedjango-python-1 /bin/bash` depending on machine may have to replace _ with -
3. `python manage.py makemigrations` (if you are loading an older db, check below in readme, don't do later steps)
4. `python manage.py migrate`
5. `python manage.py createsuperuser` create a user named admin, with whatever pass you want, you can skip email
6. `python manage.py collectstatic --noinput`
7. `python manage.py gen_ops_app'
8. `python manage.py gen_ops_galtwo'
9. go to project/settings and # line 63
10. http://127.0.0.1:8000/admin, in both Round Status create new entry and save
11. `python manage.py generate_planets` (can take a while if its a big galaxy with a lot of planets)
12. `python manage.py generate_galtwo` (can take a while if its a big galaxy with a lot of planets)
13. remove # from line 63 in project/settings
14. go to http://127.0.0.1:8000, log in as admin, and choose a race
15. `cd java`
16. set regular round tick time in java/settings
17. `javac *.java -d .` - if wasnt allready compiled into bytecode
18. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTickSlow >> log.txt &`
19. Set the `Round status` object's `Is running` to True whenever you want the tick time to start running
20. set fast round tick time in java/settings
21. `javac *.java -d .` - if wasnt allready compiled into bytecode
22. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTickFast >> log.txt &`
23. Set the `Round status` object's `Is running` to True whenever you want the tick time to start running

## Activating accounts

to kill the java process tick:
1. `ps -aux` - get the list of currently running jobs
2. ` kill PID` ,replacing the PID with the process ID of the Main.java

## To rebuild the containers, like if a config setting changed (in project/requirements)
First
`docker-compose down`
then
`docker-compose up -d --no-deps --build`

To rebuild only the python container:
`docker-compose up -d --no-deps --build python`

## To extract the db (for backing up for example)
If you are loading an old db on a new server, don't go through steps 3-7 
Go to python container first: `docker exec -it ectroversedjango-python-1 /bin/bash`

to extract:
`python manage.py dumpdata --natural-foreign --exclude auth.permission --exclude contenttypes --indent 4 > db.json`

to load extracted:
Delete the existing db first:
`python manage.py flush`
then:
`python manage.py loaddata db.json`

## Check it's running

`docker ps` should list all three containers as Up

## Shut it down

`docker-compose down`

## Look at logs

Watch Django's console (i.e. the uwsgi log) with
1. `docker exec -it ectroversedjango-python-1 /bin/bash`
2. `tail -f /tmp/mylog.log`

Nginx log:
`docker logs -f ectroversedjango-nginx-1`

Database log:
`docker logs -f ectroversedjango-db-1`

Restart all docker containers:
`docker restart $(docker ps -q)`

## Console into the python container (which runs the Django app) to poke around or debug something

`docker exec -it ectroversedjango-python-1 /bin/bash`

## Console into the potgres container psql
1. `docker exec -it ectroversedjango-db-1 bash`
2. `psql -U dbadmin djangodatabase`

the user name and db name are set in the db: -> environment: in the docker-compose.yml

## To run the java tick process:
1. `docker exec -it ectroversedjango-java-1 /bin/bash`
2. `cd java`
3. `javac *.java -d .` - if wasnt allready compiled into bytecode
4. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTickSlow >> log.txt &` for app tick
5. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTickSlow >> log.txt &` for galtwo tick

to kill it:
1. `ps -aux` - get the list of currently running jobs
2. ` kill PID` ,replacing the PID with the process ID of the Main.java

##Django shell
`python manage.py shell`
