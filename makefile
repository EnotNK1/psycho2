up:
	docker compose up -d

build:
	docker compose up --build -d

stop:
	docker compose stop redis nginx app backup db celery_worker celery_beat
