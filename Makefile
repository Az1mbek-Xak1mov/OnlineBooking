mig:
	python manage.py makemigrations
	python manage.py migrate

admin:
	python3 manage.py createsuperuser

flake8:
	flake8 .

isort:
	isort .
