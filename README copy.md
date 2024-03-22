# Introduction 
AppServer Codebase for RB-AMC Project


# Setup Steps

## Prerequesites 
- Docker Desktop
- Backend codebase checked out


### Run Below commands in one terminal
   1. run with build (dev purpose only)  
      `$ docker-compose -f docker-compose-dev.yaml up -d --build`
      
   2. create database in db container (one-time)

      `$ docker-compose -f docker-compose-dev.yaml exec db sh` 

      `# psql -U postgres -c "CREATE DATABASE amc ENCODING 'LATIN1' TEMPLATE template0 LC_COLLATE 'C' LC_CTYPE 'C';"`  

      `# exit`
      
   3. create all tables in database for first time (one-time)

      `$ docker-compose -f docker-compose-dev.yaml exec api sh`  

      `# flask createdb`  

      `# exit`

### Run below command in another terminal for logs
   `$ docker-compose -f docker-compose-dev.yaml logs -f`

# OTHER IMPORTANT COMMANDS

1. Command to start the dev environment
   `$ docker-compose -f docker-compose-dev.yaml up -d --build`
2. Command to stop the environment
   `$ docker-compose -f docker-compose-dev.yaml down`
3. Command to stop the enviorment and data cleanup
   `$ docker-compose -f docker-compose-dev.yaml down -v`


