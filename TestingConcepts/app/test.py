from models import Category
from category_repo import CategoryRepo


def main():
    print("1. crear")
    category = Category(
        id=None,
        name="Ropa",
        attributes=[],
    )

    saved = CategoryRepo.save(category)
    print("guardado:", saved.id, saved.name, saved.attributes)

    print("\n2. leer")
    found = CategoryRepo.read(saved.id)
    if found is not None:
        print("leido:", found.id, found.name, found.attributes)
    else:
        print("no encontrado")

    print("\n3. actualizar con save")
    found.name = "Ropa deportiva"
    updated = CategoryRepo.save(found)
    print("actualizado:", updated.id, updated.name, updated.attributes)

    input("cualquier letra para seguir")

    print("\n4. borrar")
    deleted = CategoryRepo.delete(updated.id)
    print("borrado:", deleted)

    print("\n5. comprobar que ya no existe")
    again = CategoryRepo.read(updated.id)
    print("resultado:", again)


if __name__ == "__main__":
    main()