from app import start_oauth

#print(start_oauth())  # redirigis a esa URL

# despues del callback OK:
from app import enqueue_email

print(enqueue_email("juanseguzzardilopez@hotmail.com", "test", "hola"))

