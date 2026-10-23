# WebMaboSS : a web interface for simulating Boolean models stochastically
[![Docker image](https://img.shields.io/docker/v/sysbiocurie/webmaboss?logo=docker&sort=date)](https://hub.docker.com/repository/docker/sysbiocurie/webmaboss/general)
<img align="right" height="100" src="https://maboss.curie.fr/images/maboss_logo.jpg">


WebMaBoSS is a web interface for the MaBoSS, the Markovian Boolean Stochastic Simulator. MaBoSS is a C++ software for simulating continuous/discrete time Markov processes, applied on a Boolean network.

WebMaBoSS allows you to store, modify, and simulate MaBoSS models. You can also import/export models in other compatible formats (SBML-qual, GINsim, BNet). Models can also be imported from public repositories (BioModels, Cell Collective, and the model repository of GINsim).

WebMaBoSS is available as a docker container that can quickly be deployed locally. You will need [Docker](https://docs.docker.com/get-docker/), with its [Compose](https://docs.docker.com/compose/install/) plugin if you want to use it.
A live version is deployed at [https://webmaboss.vincent-noel.fr](https://webmaboss.vincent-noel.fr).

### Reference

Noël, V., Ruscone, M., Stoll, G., Viara, E., Zinovyev, A., Barillot, E., & Calzone, L. (2021). WebMaBoSS: A Web Interface for Simulating Boolean Models Stochastically. *Frontiers in molecular biosciences, 8.*. DOI : [10.3389/fmolb.2021.754444](https://www.frontiersin.org/articles/10.3389/fmolb.2021.754444/full)

### Use live version

To try the version available at [https://webmaboss.vincent-noel.fr](https://webmaboss.vincent-noel.fr) without an account, click on Demo : the demo models can be browsed and simulated, but not modified. To upload, edit and keep your own models, create a user account. Once created, you can immediately login and start discovering the default project, which contains copies of the demo models.

For more information, consult the tutorials. 


### Run locally with Docker and Docker-compose
Launch WebMaBoSS's container using :

```
git clone https://github.com/sysbio-curie/WebMaBoSS
cd WebMaBoSS
docker pull sysbiocurie/webmaboss:1.1.0
docker compose up -d webmaboss
```
	
And then open your browser to this url : http://localhost:8000/


This will use the docker image from sysbiocurie/webmaboss on [DockerHub](https://hub.docker.com/repository/docker/sysbiocurie/webmaboss/general). If you want to build your image locally, remove the docker pull command.
### Run locally with Docker
If you don't want to build the image (this can take 10-20 min), you can first download it from [DockerHub](https://hub.docker.com/repository/docker/sysbiocurie/webmaboss/general) : 

```
docker pull sysbiocurie/webmaboss:1.1.0
```

Otherwise :
```
docker build -f docker/Dockerfile -t sysbiocurie/webmaboss:1.1.0 .
```

Then launch the container of the database. Note that you should modify the password. 
```
docker run -d --name webmaboss-db \
	--restart=always \
	-v webmaboss_db:/var/lib/mysql \
	-e MYSQL_RANDOM_ROOT_PASSWORD=yes \
	-e MYSQL_DATABASE=webmaboss \
	-e MYSQL_USER=webmaboss \
	-e MYSQL_PASSWORD=InsertAPassWordForTheDatabase \
	mariadb:12.3.3 \
	--max_allowed_packet=268435456 
```
Then launch WebMaBoSS' container
```
docker run -d --name webmaboss \
	--restart=always \
	-v webmaboss_data:/var/webmaboss/data \
	-p 8000:8000 \
	--link webmaboss-db \
	-u www-data \
	-e DB_HOST=webmaboss-db \
	-e DB_PORT=3306 \
	-e DB_NAME=webmaboss \
	-e DB_USER=webmaboss \
	-e DB_PASSWORD=InsertAPassWordForTheDatabase \
	sysbiocurie/webmaboss:1.1.0
```
And finally open your browser to this url : http://localhost:8000/

### Behind a reverse proxy serving https
The server of the container only speaks http. If it is published in https through a reverse proxy, add its public address to `settings/config.yml` in the data volume, and restart the container. Otherwise the forms of the administration pages are refused (403, CSRF verification failed) :
```
csrf_trusted_origins: ['https://maboss.curie.fr']
```

### Monitoring
Administrators (accounts with the staff status, given in the administration pages at `/admin/`) have a Monitoring page in their profile : the number of active users in time, the space used by the database and the data, the list of the users with the space they use, and the cleanup of old or failed simulations, of the simulations of anonymous users, and of inactive accounts.

### Maintenance
`manage.py maintenance` deletes the simulations of anonymous users after a day, marks as interrupted the simulations a restart of the server stopped, cleans the expired sessions and the old imports of models, lists again the models of the repositories (BioModels, Cell Collective, GINsim) and computes the statistics of the users shown on the Monitoring page. The container runs it every hour, in the background (its output is in `docker logs webmaboss`). The environment variable `MAINTENANCE_EVERY` changes the period, in seconds, and `MAINTENANCE_EVERY=0` disables it, for instance to run it from the cron of the host instead :
```
docker exec webmaboss /opt/conda/bin/python3 manage.py maintenance --settings=settings.prod_settings
```
`--only demo stalled ...` runs some of the tasks.

### Upgrading an installation from 1.0.x
The data volumes are kept : the database is migrated when the container starts. Then :
- behind a reverse proxy serving https, add `csrf_trusted_origins` to `settings/config.yml` (see above), as the administration pages would refuse their forms.
- `allowed_hosts` in `settings/config.yml` can stay as older versions wrote it (`allowed_hosts: '*'`, a single string instead of a list) : it is read as a list.
- Anonymous users can't modify the demo project anymore. Restore the demo models once, in case they were modified : `docker exec webmaboss /opt/conda/bin/python3 manage.py reset_demo --settings=settings.prod_settings`
- The email addresses of the accounts are converted to lower case. Users log in with their username, so it changes nothing for them.

### Tests

The tests run against a docker image, in throwaway containers with an empty database : the unit tests, a smoke test of the API, and a smoke test of the web interface in a browser. The smoke tests are compared with reference snapshots, recorded with the last release, or when the behaviour is changed on purpose. They run on GitHub for every push, and can be run locally :
```
docker build -f docker/Dockerfile -t webmaboss:test .
tests/run_ci.sh webmaboss:test
```
Snapshots, screenshots and logs are written in `tests-output`. To record new references, after checking that all the differences are expected : `tests/run_ci.sh webmaboss:test --record`.

The versions of all dependencies are fixed : conda packages in `docker/conda-linux-64.lock`, python packages in `docker/constraints.txt` and javascript packages in `yarn.lock`, so that rebuilding the image always gives the same environment.

### Tutorials

Three tutorials are based on the demo models, which are in the Demo and in the default project of the accounts :

- [Tutorial on Cohen 2015 : Tumor Cell Invasion and Migration](https://github.com/sysbio-curie/WebMaBoSS/raw/master/tutorials/Tutorial_Cohen.pdf)
- [Tutorial on Corral 2020 : Interplay between SMAD2 and STAT5A regulating IL-17A/F expression in Th cells](https://github.com/sysbio-curie/WebMaBoSS/raw/master/tutorials/Tutorial_Corral.pdf)
- Tutorial on Sizek 2019 : following the cell cycle and the entry into apoptosis with observed graphs, in the Tutorials page of the interface (`/tutorials/sizek/`). It reproduces the section 3.9 of the [CoLoMoTo tutorial](https://doi.org/10.1098/rsfs.2025.0002).

The Cohen and Corral tutorials are also available in the Tutorials page.

### License

[GNU Lesser General Public License v3](https://github.com/sysbio-curie/WebMaBoSS/blob/master/LICENSE.md)

### Acknowledgements

The development was supported by European Union's Horizon 2020 Programme under agreement no. 668858 (PrECISE project) and agreement no. 951773 (PerMedCoE project). It was also partially funded by Agence Nationale de la Recherche in the program Investissements d’Avenir (project No. ANR-19-P3IA-0001; PRAIRIE 3IA Institute).
