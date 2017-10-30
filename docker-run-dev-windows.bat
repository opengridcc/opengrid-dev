@echo off

REM Test if docker-machine exists
echo.
echo [STARTING OPENGRID DOCKER] checking if docker-machine is installed
where docker-machine 1>nul 2>nul
if %ERRORLEVEL%==1 (
	echo [STARTING OPENGRID DOCKER] docker-machine not installed. Please install docker-machine.
	pause
	exit
) else (
	echo [STARTING OPENGRID DOCKER] SUCCESS: docker-machine installed
)

REM Test if jupyter notebook exists
echo [STARTING OPENGRID DOCKER] checking if jupyter notebook is installed
where jupyter 1>nul 2>nul
if %ERRORLEVEL%==1 (
	echo [STARTING OPENGRID DOCKER] FAILURE: jupyter notebook not installed. Please install jupyter notebook.
	pause
	exit
) else (
	echo [STARTING OPENGRID DOCKER] SUCCESS: jupyter notebook installed
)

REM Test if default machine exists.
REM If not, create it.
REM After creation, make sure it runs
docker-machine status default 1>nul 2>nul
if %ERRORLEVEL%==1 (
	echo [STARTING OPENGRID DOCKER] default does not exist and will be created. This could take a while
	REM docker-machine create -d hyperv --hyperv-virtual-switch "DockerSwitch" default
	docker-machine create -d hyperv default
)
echo [STARTING OPENGRID DOCKER] starting default. This could take a while.
docker-machine start default 1>nul 2>nul
docker-machine env --shell powershell 1>nul 2>nul
echo [STARTING OPENGRID DOCKER] default running.

REM Stop and/or remove existing opengrid-dev container, if any
docker ps -a | findstr opengrid-dev 1>nul 2>nul
if %ERRORLEVEL%==1 (
	echo [STARTING OPENGRID DOCKER] opengrid-dev container does not exist
) else (
	echo [STARTING OPENGRID DOCKER] opengrid-dev container exists. Removing.
	docker stop opengrid-dev 1>nul 2>nul
	docker rm opengrid-dev 1>nul 2>nul
)

REM Start the docker, publish port 8888 to host 
REM mount current folder to /usr/local/opengrid in the container
REM for data persistence, mount ./data to the /data folder
REM if you want to store the data in a different location, modify the command below
echo [STARTING OPENGRID DOCKER] Start a new instance on localhost:8899.
echo [STARTING OPENGRID DOCKER] When prompted, share your drives with docker to run the script succesfully.
docker run -d -p 8899:8888 -v "%CD%:/usr/local/opengrid"  -v "%CD%/data:/data" --name opengrid-dev opengrid/dev 1>nul 2>nul
if %ERRORLEVEL%==1 (
	echo [STARTING OPENGRID DOCKER] failed to start opengrid-dev container
) else (
	echo [STARTING OPENGRID DOCKER] succesfully started opengrid-dev container
)

echo [STARTING OPENGRID DOCKER] launching Jupyter Notebook
timeout 3 1>nul 2>nul

start "" http://localhost:8899/tree/notebooks 1>nul 2>nul
