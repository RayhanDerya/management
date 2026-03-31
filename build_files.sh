# Install dependencies
python3.12 -m pip install -r requirements.txt

# Collect static files for WhiteNoise
python3.12 manage.py collectstatic --noinput --clear

# Run database migrations
python3.12 manage.py migrate --noinput