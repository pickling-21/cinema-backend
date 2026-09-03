# Запуск


1. Проверить postgres контейнер запущен. 
SQL_HOST=127.0.0.1 на время 

2. psql -h 127.0.0.1 -U app -d movies_database -f docker_compose/simple_project/database_dump.sql

`admin` и пароль `123123`

3. uv run python manage.py createsuperuser

4. uv run manage.py runserver  


cd /root/practicum/new_admin_panel_sprint_2/docker_compose/simple_project

docker compose up -d



