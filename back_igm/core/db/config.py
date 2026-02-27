#this file contains coneccions and configs for the databases


import psycopg

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="appdatabase",
    user="backend",
    password="chimichangas"
)

#docker volume create pgdata && docker run -d --name app-postgres -e POSTGRES_DB=appdatabase -e POSTGRES_USER=backend -e POSTGRES_PASSWORD=chimichangas -p 5432:5432 -v pgdata:/var/lib/postgresql/data postgres:16

import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True  # devuelve strings en vez de bytes
)

# Test conexión
print(r.ping())