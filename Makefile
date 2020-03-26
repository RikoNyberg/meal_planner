APP_NAME = meal_plan

run:
	docker build -t $(APP_NAME) .
	docker run --rm -p 5000:5000 --name meal_plan_website $(APP_NAME)

server:
	docker build -t $(APP_NAME) .
	docker-compose up -d