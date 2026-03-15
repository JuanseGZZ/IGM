from __future__ import annotations

from typing import Optional
from models import Attribute, AttributeImplementation, Category, Product, Variant
from cruds import DB, get_connection
from psycopg2.extensions import connection as Connection


# ============================================================
# BaseRepository
# ============================================================

class BaseRepository:
    def __init__(self, db: DB) -> None:
        self.db = db


# ============================================================
# AttributeRepository
# ============================================================

class AttributeRepository(BaseRepository):

    def _to_model(self, row: dict) -> Attribute:
        attr = Attribute(
            id        = row["id"],
            key       = row["key"],
            name      = row["name"],
            data_type = row["data_type"],
            is_static = row["is_static"],
        )
        # cargar enum_values si corresponde
        if attr.data_type == "enum":
            enum_rows = self.db.enum_values.get_by_atribute(attr.id)
            for ev in enum_rows:
                attr.enum_values.append(ev["value"])
        return attr

    def get_all(self) -> list[Attribute]:
        return [self._to_model(r) for r in self.db.atribute.get_all()]

    def get_by_id(self, attr_id: int) -> Optional[Attribute]:
        row = self.db.atribute.get_by_id(attr_id)
        return self._to_model(row) if row else None

    def get_by_key(self, key: str) -> Optional[Attribute]:
        row = self.db.atribute.get_by_key(key)
        return self._to_model(row) if row else None

    def get_static(self) -> list[Attribute]:
        return [self._to_model(r) for r in self.db.atribute.get_static()]

    def get_dynamic(self) -> list[Attribute]:
        return [self._to_model(r) for r in self.db.atribute.get_dynamic()]

    def save(self, attr: Attribute) -> Attribute:
        data = {
            "key":       attr.key,
            "name":      attr.name,
            "data_type": attr.data_type,
            "is_static": attr.is_static,
        }
        if attr.id is None:
            row = self.db.atribute.create(data)
            attr.id = row["id"]
            # persistir enum_values nuevos
            for value in attr.enum_values:
                self.db.enum_values.create({"atribute_id": attr.id, "value": value})
        else:
            self.db.atribute.update(attr.id, data)
            # sincronizar enum_values: borrar los viejos y reescribir
            existing = self.db.enum_values.get_by_atribute(attr.id)
            existing_values = {ev["value"] for ev in existing}
            for value in attr.enum_values:
                if value not in existing_values:
                    self.db.enum_values.create({"atribute_id": attr.id, "value": value})
        return attr

    def delete(self, attr_id: int) -> bool:
        return self.db.atribute.delete(attr_id)


# ============================================================
# CategoryRepository
# ============================================================

class CategoryRepository(BaseRepository):

    def __init__(self, db: DB, attribute_repo: AttributeRepository) -> None:
        super().__init__(db)
        self.attribute_repo = attribute_repo

    def _to_model(self, row: dict) -> Category:
        attr_rows = self.db.category_atributes.get_atributes_of_category(row["id"])
        attributes = [self.attribute_repo._to_model(a) for a in attr_rows]
        return Category(
            id         = row["id"],
            name       = row["name"],
            attributes = attributes,
        )

    def get_all(self) -> list[Category]:
        return [self._to_model(r) for r in self.db.category.get_all()]

    def get_by_id(self, cat_id: int) -> Optional[Category]:
        row = self.db.category.get_by_id(cat_id)
        return self._to_model(row) if row else None

    def get_by_name(self, name: str) -> Optional[Category]:
        row = self.db.category.get_by_name(name)
        return self._to_model(row) if row else None

    def save(self, category: Category) -> Category:
        data = {"name": category.name}
        if category.id is None:
            row = self.db.category.create(data)
            category.id = row["id"]
        else:
            self.db.category.update(category.id, data)

        # sincronizar atributos de la categoría
        existing_rows = self.db.category_atributes.get_by_category(category.id)
        existing_attr_ids = {r["atribute_id"] for r in existing_rows}
        for attr in category.attributes:
            if attr.id is None:
                self.attribute_repo.save(attr)
            if attr.id not in existing_attr_ids:
                self.db.category_atributes.create({
                    "category_id": category.id,
                    "atribute_id": attr.id,
                })
        return category

    def delete(self, cat_id: int) -> bool:
        return self.db.category.delete(cat_id)


# ============================================================
# AttributeImplementationRepository  (helper interno)
# ============================================================

class AttributeImplementationRepository(BaseRepository):

    def __init__(self, db: DB, attribute_repo: AttributeRepository) -> None:
        super().__init__(db)
        self.attribute_repo = attribute_repo

    def _to_model(self, row: dict) -> AttributeImplementation:
        attr = self.attribute_repo.get_by_id(row["atribute_id"])
        return AttributeImplementation(
            id        = row["id"],
            attribute = attr,
            value     = row["value"],
        )

    def save(self, impl: AttributeImplementation) -> AttributeImplementation:
        data = {
            "atribute_id": impl.attribute.id,
            "value":       str(impl.value),
        }
        if impl.id is None:
            row = self.db.atr_implementation.create(data)
            impl.id = row["id"]
        else:
            self.db.atr_implementation.update(impl.id, data)
        return impl


# ============================================================
# ProductRepository
# ============================================================

class ProductRepository(BaseRepository):

    def __init__(
        self,
        db:           DB,
        attr_repo:    AttributeRepository,
        cat_repo:     CategoryRepository,
        impl_repo:    AttributeImplementationRepository,
    ) -> None:
        super().__init__(db)
        self.attr_repo = attr_repo
        self.cat_repo  = cat_repo
        self.impl_repo = impl_repo

    def _to_model(self, row: dict) -> Product:
        category = self.cat_repo.get_by_id(row["category_id"])

        # atributos propios del producto (no de la categoría)
        attr_rows = self.db.products_atributes.get_atributes_of_product(row["id"])
        attributes = [self.attr_repo._to_model(a) for a in attr_rows]

        # implementaciones de atributos estáticos
        impl_rows = self.db.product_implementation.get_full_implementation(row["id"])
        attr_impls: list[AttributeImplementation] = []
        for ir in impl_rows:
            attr = self.attr_repo.get_by_id(ir["atribute_id"]) if "atribute_id" in ir \
                   else self.attr_repo.get_by_key(ir["atribute_key"])
            # cast del valor según data_type
            value = _cast_value(ir["value"], ir["data_type"])
            attr_impls.append(AttributeImplementation(
                id        = ir["impl_id"],
                attribute = attr,
                value     = value,
            ))

        return Product(
            id                       = row["id"],
            title                    = row["title"],
            price                    = float(row["price"]),
            description              = row.get("description"),
            brand                    = row.get("brand"),
            category                 = category,
            attributes_implementations = attr_impls,
            attributes               = attributes,
            variants                 = [],  # se cargan bajo demanda en VariantRepository
        )

    def get_all(self) -> list[Product]:
        return [self._to_model(r) for r in self.db.product.get_all()]

    def get_by_id(self, product_id: int) -> Optional[Product]:
        row = self.db.product.get_by_id(product_id)
        return self._to_model(row) if row else None

    def get_by_code(self, code: str) -> Optional[Product]:
        row = self.db.product.get_by_code(code)
        return self._to_model(row) if row else None

    def get_by_category(self, category_id: int) -> list[Product]:
        return [self._to_model(r) for r in self.db.product.get_by_category(category_id)]

    def get_by_brand(self, brand: str) -> list[Product]:
        return [self._to_model(r) for r in self.db.product.get_by_brand(brand)]

    def save(self, product: Product, code: str) -> Product:
        data = {
            "code":        code,
            "title":       product.title,
            "price":       product.price,
            "description": product.description,
            "brand":       product.brand,
            "category_id": product.category.id,
        }
        if product.id is None:
            row = self.db.product.create(data)
            product.id = row["id"]
        else:
            self.db.product.update(product.id, data)

        # sincronizar atributos propios
        existing_rows    = self.db.products_atributes.get_by_product(product.id)
        existing_attr_ids = {r["atribute_id"] for r in existing_rows}
        for attr in product.attributes:
            if attr.id is None:
                self.attr_repo.save(attr)
            if attr.id not in existing_attr_ids:
                self.db.products_atributes.create({
                    "product_id":  product.id,
                    "atribute_id": attr.id,
                })

        # sincronizar implementaciones de atributos estáticos
        existing_impls    = self.db.product_implementation.get_by_product(product.id)
        existing_impl_ids = {r["atr_imp_id"] for r in existing_impls}
        for impl in product.attributes_implementations:
            self.impl_repo.save(impl)
            if impl.id not in existing_impl_ids:
                self.db.product_implementation.create({
                    "product_id": product.id,
                    "atr_imp_id": impl.id,
                })
        return product

    def delete(self, product_id: int) -> bool:
        return self.db.product.delete(product_id)


# ============================================================
# VariantRepository
# ============================================================

class VariantRepository(BaseRepository):

    def __init__(
        self,
        db:           DB,
        product_repo: ProductRepository,
        impl_repo:    AttributeImplementationRepository,
    ) -> None:
        super().__init__(db)
        self.product_repo = product_repo
        self.impl_repo    = impl_repo

    def _to_model(self, row: dict) -> Variant:
        product = self.product_repo.get_by_id(row["product_id"])

        impl_rows = self.db.variant_implementation.get_full_implementation(row["id"])
        attr_impls: list[AttributeImplementation] = []
        for ir in impl_rows:
            attr  = self.product_repo.attr_repo.get_by_key(ir["atribute_key"])
            value = _cast_value(ir["value"], ir["data_type"])
            attr_impls.append(AttributeImplementation(
                id        = ir["impl_id"],
                attribute = attr,
                value     = value,
            ))

        return Variant(
            id                       = row["id"],
            product                  = product,
            attribute_implementations = attr_impls,
        )

    def get_all(self) -> list[Variant]:
        return [self._to_model(r) for r in self.db.variant.get_all()]

    def get_by_id(self, variant_id: int) -> Optional[Variant]:
        row = self.db.variant.get_by_id(variant_id)
        return self._to_model(row) if row else None

    def get_by_product(self, product_id: int) -> list[Variant]:
        return [self._to_model(r) for r in self.db.variant.get_by_product(product_id)]

    def save(self, variant: Variant, code: str) -> Variant:
        data = {
            "code":       code,
            "product_id": variant.product.id,
        }
        if variant.id is None:
            row = self.db.variant.create(data)
            variant.id = row["id"]
        else:
            self.db.variant.update(variant.id, data)

        # sincronizar implementaciones de atributos
        existing_impls    = self.db.variant_implementation.get_by_variant(variant.id)
        existing_impl_ids = {r["atr_imp_id"] for r in existing_impls}
        for impl in variant.attribute_implementations:
            self.impl_repo.save(impl)
            if impl.id not in existing_impl_ids:
                self.db.variant_implementation.create({
                    "variant_id": variant.id,
                    "atr_imp_id": impl.id,
                })
        return variant

    def delete(self, variant_id: int) -> bool:
        return self.db.variant.delete(variant_id)


# ============================================================
# Utilidad: cast de valor según data_type
# ============================================================

def _cast_value(raw: str, data_type: str):
    if data_type == "number":
        try:
            return int(raw)
        except ValueError:
            return float(raw)
    elif data_type == "boolean":
        return raw.lower() in ("true", "1", "yes")
    return raw  # text y enum quedan como str


# ============================================================
# Factory de repositorios — punto de entrada desde el service
# ============================================================

class Repositories:
    """Instancia todos los repos con una única conexión.

    Uso:
        with Repositories() as repos:
            cat  = repos.category.get_by_name("Shirts")
            prod = repos.product.get_by_code("SKU-001")
            prod.variants = repos.variant.get_by_product(prod.id)

    O para operaciones que necesiten transacción manual:
        conn = get_connection()
        repos = Repositories(conn=conn)
        repos.product.save(product, code="SKU-001")
        conn.commit()
        conn.close()
    """

    def __init__(self, conn: Optional[Connection] = None) -> None:
        self._db             = DB(conn=conn)
        self._external_conn  = conn is not None

        attr_repo  = AttributeRepository(self._db)
        cat_repo   = CategoryRepository(self._db, attr_repo)
        impl_repo  = AttributeImplementationRepository(self._db, attr_repo)
        prod_repo  = ProductRepository(self._db, attr_repo, cat_repo, impl_repo)
        var_repo   = VariantRepository(self._db, prod_repo, impl_repo)

        self.attribute  = attr_repo
        self.category   = cat_repo
        self.product    = prod_repo
        self.variant    = var_repo

    def __enter__(self) -> "Repositories":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if not self._external_conn:
            self._db.conn.close()