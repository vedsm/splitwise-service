LOCAL_VARIABLES := RUN_ENV=DEV \
	LOGGING_LEVEL=DEBUG \
	MONGO_CONNECTION_STRING=mongodb://root:example_pwd@localhost:27017/my_service?authSource=admin \

create_env:
	virtualenv venv
	echo "now call: source ./venv/bin/activate"

activate_env:
	source ./venv/bin/activate

install:
	pip3 install -r ./requirements.txt

test:
	echo "testing"
	$(LOCAL_VARIABLES) python -m pytest

run:
	$(LOCAL_VARIABLES) uvicorn --host 0.0.0.0 --port 5000 src.main:app --reload

package:
	echo "to create a docker build/ python package/code artefacts"
	docker-compose -f ./docker-compose.yml build

publish:
	echo "to publish a created docker image / code artefacts to a cental repository"
	docker-compose -f ./docker-compose.yml push

run_package:
	docker-compose -f docker-compose.yml up --remove-orphans

deploy:
	echo "deploying"

lint:
	black --check .

test-ci:
	echo "testing"
	$(LOCAL_VARIABLES) pytest --cov=src --cov-report=html --no-coverage-upload
	echo "Running CSS JS Hack utility since Microsoft did an awesome job on CSP security settings." 
	css_js_inliner