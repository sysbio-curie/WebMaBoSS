#!/bin/bash
#
# Runs the tests of a WebMaBoSS docker image, in throwaway containers and with an empty database :
#   - the unit tests (manage.py test api),
#   - the API smoke test (tests/smoke/api_smoke.py),
#   - the browser smoke test (tests/smoke/browser_smoke.py),
# The smoke tests are compared with the reference snapshots of tests/smoke/reference.
#
# usage: tests/run_ci.sh IMAGE [--record]
#
#   --record : records the reference snapshots with IMAGE, instead of comparing with them
#              (the unit tests are skipped). References are recorded with the last release.
#
# Snapshots, screenshots and logs (app.log, and error_log with the tracebacks of the server errors)
# are written in $OUT (default: tests-output).
# It is used by .github/workflows/tests.yml, and can be run locally.

set -uo pipefail

IMAGE=${1:?usage: $0 IMAGE [--record]}
RECORD=${2:-}
OUT=$(realpath -m "${OUT:-tests-output}")
SRC=$(realpath "$(dirname "$0")/..")
REF=tests/smoke/reference
MARIADB=mariadb:12.3.3
NAME=webmaboss-ci-$$
DB_PASSWORD=ci-$$

# Memory limits (without swap) : the java of GINsim and the MaBoSS threads would otherwise size themselves
# on the whole machine. At most app + database + browser run at the same time : 6GB.
limit() { echo "--memory $1 --memory-swap $1"; }

FAILED=()

cleanup() {
	docker logs $NAME-app > "$OUT/app.log" 2>&1
	docker cp $NAME-app:/var/webmaboss/server/error_log "$OUT/error_log" > /dev/null 2>&1
	docker rm -f -v $NAME-db $NAME-app > /dev/null 2>&1
	docker volume rm $NAME-data > /dev/null 2>&1
	docker network rm $NAME > /dev/null 2>&1
}
trap cleanup EXIT

step() {
	echo
	echo "======== $1"
}

mkdir -p "$OUT" && chmod 777 "$OUT"
docker network create $NAME > /dev/null

step "Starting $MARIADB"
docker run -d --name $NAME-db --network $NAME $(limit 1g) \
	-e MARIADB_ROOT_PASSWORD=$DB_PASSWORD -e MARIADB_DATABASE=webmaboss \
	-e MARIADB_USER=webmaboss -e MARIADB_PASSWORD=$DB_PASSWORD \
	$MARIADB --max_allowed_packet=268435456 > /dev/null
until docker exec $NAME-db healthcheck.sh --connect --innodb_initialized > /dev/null 2>&1; do sleep 2; done

DB=(-e DB_HOST=$NAME-db -e DB_PORT=3306 -e DB_PASSWORD=$DB_PASSWORD)
PYTHON=/opt/conda/bin/python3

if [ "$RECORD" != "--record" ]; then
	step "Unit tests"
	# On their own database. The application checks the guest account at startup, so it must be migrated first
	docker exec $NAME-db mariadb -uroot -p$DB_PASSWORD -e "CREATE DATABASE unit"
	docker run --rm --network $NAME $(limit 2g) "${DB[@]}" -e DB_NAME=unit -e DB_USER=root --user root --entrypoint bash $IMAGE -c "
		mkdir -p data/settings && printf 'secret_key: ci\nallowed_hosts: [\"*\"]\n' > data/settings/config.yml &&
		$PYTHON manage.py migrate --settings=settings.test_settings > /dev/null &&
		printf 'admin: admin\n' >> data/settings/config.yml &&
		$PYTHON manage.py test api --settings=settings.test_settings --noinput
	" || FAILED+=("unit tests")
fi

step "Starting the application"
# Installed as the installation page would do : migrations first, then the admin is declared.
# allowed_hosts is a string, as older installations wrote it (the unit tests use a list)
docker run --rm -v $NAME-data:/var/webmaboss/data --network $NAME $(limit 2g) "${DB[@]}" -e DB_NAME=webmaboss -e DB_USER=webmaboss \
	--entrypoint bash $IMAGE -c "
	mkdir -p data/settings data/media && printf \"secret_key: ci\nallowed_hosts: '*'\n\" > data/settings/config.yml &&
	$PYTHON manage.py migrate --settings=settings.prod_settings > /dev/null &&
	printf 'admin: admin\n' >> data/settings/config.yml
" || { echo "Installation failed"; exit 1; }

start_app() {
	# Without the hourly maintenance (tested by the unit tests) : it would run during the smoke tests
	docker run -d --name $NAME-app --network $NAME $(limit 3g) -v $NAME-data:/var/webmaboss/data \
		"${DB[@]}" -e DB_NAME=webmaboss -e DB_USER=webmaboss -e MAINTENANCE_EVERY=0 $IMAGE > /dev/null
	wait_app
}

wait_app() {
	for i in $(seq 1 100); do
		[ "$(docker exec $NAME-app curl -s -o /dev/null -w '%{http_code}' localhost:8000/)" = 200 ] && return
		sleep 3
	done
	echo "The application did not start"; exit 1
}

start_app

api_smoke() {
	docker run --rm --user $(id -u):$(id -g) --network $NAME $(limit 512m) -v "$SRC":/src:ro -v "$OUT":/out \
		--entrypoint $PYTHON $IMAGE -I /src/tests/smoke/api_smoke.py --url http://$NAME-app:8000 "$@"
}

browser_smoke() {
	docker build -q -f "$SRC/tests/smoke/Dockerfile.browser" -t webmaboss-browser-test "$SRC/tests/smoke" > /dev/null
	docker run --rm --user $(id -u):$(id -g) -e HOME=/tmp $(limit 2g) --shm-size 512m --network $NAME \
		-v "$SRC":/src:ro -v "$OUT":/out \
		webmaboss-browser-test python3 /src/tests/smoke/browser_smoke.py --url http://$NAME-app:8000 --screenshots /out/screenshots "$@"
}

if [ "$RECORD" = "--record" ]; then
	step "Recording the API smoke test references"
	# Twice, with a restart in between, to find out what changes from one run to the other
	api_smoke --out /out/api1.json || FAILED+=("api smoke test (1)")
	docker restart $NAME-app > /dev/null && wait_app
	api_smoke --out /out/api2.json || FAILED+=("api smoke test (2)")

	step "Recording the browser smoke test reference"
	browser_smoke --out /out/browser.json || FAILED+=("browser smoke test")

	if [ ${#FAILED[@]} -eq 0 ]; then
		mkdir -p "$SRC/$REF" && cp "$OUT"/api1.json "$OUT"/api2.json "$OUT"/browser.json "$SRC/$REF/"
		echo "References written in $REF"
	fi
else
	step "API smoke test"
	api_smoke --out /out/api.json --compare /src/$REF/api1.json /src/$REF/api2.json || FAILED+=("api smoke test")

	step "Browser smoke test"
	browser_smoke --out /out/browser.json --compare /src/$REF/browser.json || FAILED+=("browser smoke test")
fi

echo
if [ ${#FAILED[@]} -gt 0 ]; then
	echo "FAILED: ${FAILED[*]}"
	exit 1
fi
echo "SUCCESS"
