from crud_customers import CrudCustomers


def pause(msg: str):
    input(f"\n{msg}\nENTER para continuar...")


def main():
    CrudCustomers.refresh_meta()

    pause("Etapa 1: CREAR customer id=1")
    c = CrudCustomers.create({
        "id": 1,
        "name": "Juan",
        "surname": "Perez",
        "email": "juan.perez@test.com",
        "mp_associated": 123
    })
    print("CREADO:", c)

    pause("Etapa 2: GET por id=1")
    got = CrudCustomers.get(1)
    print("GET:", got)

    pause("Etapa 3: LIST primeros 10")
    items = CrudCustomers.list(limit=10, offset=0)
    print("LIST:", items)

    pause("Etapa 4: UPDATE id=1 (name, mp_associated)")
    upd = CrudCustomers.update(1, {"name": "Juancho", "mp_associated": 999})
    print("UPDATED:", upd)

    pause("Etapa 5: GET post update")
    got2 = CrudCustomers.get(1)
    print("GET2:", got2)

    pause("Etapa 6: DELETE id=1 (limpieza)")
    ok = CrudCustomers.delete(1)
    print("DELETE OK?:", ok)

    pause("Etapa 7: GET post delete (debe ser None)")
    got3 = CrudCustomers.get(1)
    print("GET3:", got3)

    print("\nListo.")


if __name__ == "__main__":
    main()