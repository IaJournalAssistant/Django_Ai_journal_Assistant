#!/bin/bash

echo "Initializing Django database..."

# Check if there are any changes that need migrations
echo "Checking for migration changes..."
if docker-compose exec web python manage.py makemigrations --dry-run --check; then
  echo "No new migrations needed."
else
  echo "Creating new migrations..."
  docker-compose exec web python manage.py makemigrations
fi

# Run migrations
echo "Applying migrations..."
docker-compose exec web python manage.py migrate

# Create cache table
echo "Creating cache table if it doesn't exist..."
docker-compose exec web python manage.py createcachetable

# Collect static files
echo "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput

# Create superuser (interactive)
echo "Creating superuser..."
docker-compose exec web python manage.py createsuperuser

echo "Database initialization complete!"