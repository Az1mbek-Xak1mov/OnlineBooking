mig:
	python manage.py makemigrations
	python manage.py migrate
admin:
	python3 manage.py createsuperuser

fake-datas:
	python manage.py loaddata authen/fixtures/users.json
