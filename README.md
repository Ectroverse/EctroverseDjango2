## TODO

Put your name after an item if you want to reserve it for yourself, not all items need assignments though

#### v0.1 Remaining Items
left to do:
- any bugs?
- email password recovery
- new player tutorial
- add device fingerprinting to prevent double accounts

## Getting it setup on a new machine:

(you'll need docker and docker-compose installed, google how to do it for your OS)

0. Copy .env.template to .env (`cp .env.template .env`) and change the secret key if you care about security
1. `docker-compose up -d`
2. `docker exec -it ectroversedjango_python_1 /bin/bash`
3. `python manage.py makemigrations app` (if you are loading an older db, check below in readme, don't do later steps)
4. `python manage.py migrate`
5. `python manage.py createsuperuser` create a user named admin, with whatever pass you want, you can skip email
6. `python manage.py collectstatic --noinput`
7. go to http://127.0.0.1:8000, log in as admin, and choose a race
8. Check roundstatus, if no entries create entry
9. `python manage.py generate_planets` (can take a while if its a big galaxy with a lot of planets)
10. `cd java`
11. `javac *.java -d .` - if wasnt allready compiled into bytecode
12. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTick >> log.txt &`
13. Set the `Round statuss` object's `Is running` to True whenever you want the tick time to start running

to kill the java process tick:
1. `ps -aux` - get the list of currently running jobs
2. ` kill PID` ,replacing the PID with the process ID of the Main.java

## Starting up server once its setup

1. `docker-compose up -d`

that's it!  without docker this would be a dozen steps

## To rebuild the containers, like if a config setting changed (in project/requirements)
First
`docker-compose down`
then
`docker-compose up -d --no-deps --build`

To rebuild only the python container:
`docker-compose up -d --no-deps --build python`

## To extract the db (for backing up for example)
If you are loading an old db on a new server, don't go through steps 3-7 
Go to python container first: `docker exec -it ectroversedjango_python_1 /bin/bash`

to extract:
`python manage.py dumpdata --natural-foreign \
   --exclude auth.permission --exclude contenttypes \
   --indent 4 > db.json`

to load extracted:
Delete the existing db first:
``python manage.py flush`
then:
`python manage.py loaddata db.json`

## Check it's running

`docker ps` should list all three containers as Up

## Shut it down

`docker-compose down`

## Look at logs

Watch Django's console (i.e. the uwsgi log) with
1. `docker exec -it ectroversedjango_python_1 /bin/bash`
2. `tail -f /tmp/mylog.log`

Nginx log:
`docker logs -f ectroversedjango_nginx_1`

Database log:
`docker logs -f ectroversedjango_db_1`

Restart all docker containers:
`docker restart $(docker ps -q)`

## Console into the python container (which runs the Django app) to poke around or debug something

`docker exec -it ectroversedjango_python_1 /bin/bash`

## Console into the potgres container psql
1. `docker exec -it ectroversedjango_db_1 bash`
2. `psql -U dbadmin djangodatabase`

the user name and db name are set in the db: -> environment: in the docker-compose.yml

## To run the java tick process:
1. `docker exec -it ectroversedjango_python_1 /bin/bash`
2. `cd java`
3. `javac *.java -d .` - if wasnt allready compiled into bytecode
4. `java -cp postgresql-42.2.19.jar: org.ectroverse.processtick.ProcessTick >> log.txt &`

to kill it:
1. `ps -aux` - get the list of currently running jobs
2. ` kill PID` ,replacing the PID with the process ID of the Main.java

##Django shell
`python manage.py shell`

