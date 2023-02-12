FROM python:3.9.0-alpine

WORKDIR /app

COPY bot.py /app
COPY requirements.txt /app

RUN apk add --no-cache build-base
RUN pip install -r requirements.txt

CMD ["python","-u", "bot.py"]