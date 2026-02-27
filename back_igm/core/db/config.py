#this file contains coneccions and configs for the databases


import psycopg

conn = psycopg.connect(
    host="localhost",
    port=5432,
    dbname="mi_base",
    user="mi_usuario",
    password="mi_password"
)

import redis

r = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True  # devuelve strings en vez de bytes
)

# Test conexión
print(r.ping())