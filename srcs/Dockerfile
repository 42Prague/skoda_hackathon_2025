FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    graphviz \
    graphviz-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/Matteralmar/AI_skill_coach.git /app

COPY .env /app/.env

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]
