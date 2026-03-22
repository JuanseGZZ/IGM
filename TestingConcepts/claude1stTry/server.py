from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from dtos import (
    AttributeCreate, AttributeUpdate, AttributeOut,
    CategoryCreate, CategoryUpdate, CategoryOut,
    ProductCreate, ProductUpdate, ProductOut, ProductSummary,
    VariantIn,
    ImplementationOut, VariantOut,
)
from services import AttributeService, CategoryService, ProductService

app = FastAPI(title="IGM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Mappers dominio → DTO ─────────────────────────────────────────────────────

def _attr_out(attr) -> AttributeOut:
    return AttributeOut(
        id=attr.id,
        key=attr.key,
        name=attr.name,
        data_type=attr.data_type,
        is_static=attr.is_static,
        enum_values=attr.enum_values,
    )

def _cat_out(cat) -> CategoryOut:
    return CategoryOut(
        id=cat.id,
        name=cat.name,
        attributes=[_attr_out(a) for a in cat.attributes],
    )

def _impl_out(impl) -> ImplementationOut:
    return ImplementationOut(
        id=impl.id,
        attribute=_attr_out(impl.attribute),
        value=impl.value,
    )

def _variant_out(variant) -> VariantOut:
    return VariantOut(
        id=variant.id,
        attribute_implementations=[_impl_out(i) for i in variant.attribute_implementations],
    )

def _product_out(product) -> ProductOut:
    return ProductOut(
        id=product.id,
        code=product.code,
        title=product.title,
        price=product.price,
        description=product.description,
        brand=product.brand,
        category=_cat_out(product.category),
        attributes=[_attr_out(a) for a in product.attributes],
        attributes_implementations=[_impl_out(i) for i in product.attributes_implementations],
        variants=[_variant_out(v) for v in product.variants],
    )

def _product_summary(product) -> ProductSummary:
    return ProductSummary(
        id=product.id,
        code=product.code,
        title=product.title,
        price=product.price,
        brand=product.brand,
        category_id=product.category.id,
        category_name=product.category.name,
        variant_count=len(product.variants),
    )


# ── Attributes ────────────────────────────────────────────────────────────────

@app.get("/attributes", response_model=list[AttributeOut])
def list_attributes():
    return [_attr_out(a) for a in AttributeService.get_all()]


@app.get("/attributes/{attr_id}", response_model=AttributeOut)
def get_attribute(attr_id: int):
    try:
        return _attr_out(AttributeService.get(attr_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/attributes", response_model=AttributeOut, status_code=201)
def create_attribute(body: AttributeCreate):
    try:
        return _attr_out(AttributeService.create(body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/attributes/{attr_id}", response_model=AttributeOut)
def update_attribute(attr_id: int, body: AttributeUpdate):
    try:
        return _attr_out(AttributeService.update(attr_id, body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/attributes/{attr_id}", status_code=204)
def delete_attribute(attr_id: int):
    if not AttributeService.delete(attr_id):
        raise HTTPException(status_code=404, detail="Atributo no encontrado")


# ── Categories ────────────────────────────────────────────────────────────────

@app.get("/categories", response_model=list[CategoryOut])
def list_categories():
    return [_cat_out(c) for c in CategoryService.get_all()]


@app.get("/categories/{cat_id}", response_model=CategoryOut)
def get_category(cat_id: int):
    try:
        return _cat_out(CategoryService.get(cat_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/categories", response_model=CategoryOut, status_code=201)
def create_category(body: CategoryCreate):
    try:
        return _cat_out(CategoryService.create(body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/categories/{cat_id}", response_model=CategoryOut)
def update_category(cat_id: int, body: CategoryUpdate):
    try:
        return _cat_out(CategoryService.update(cat_id, body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/categories/{cat_id}", status_code=204)
def delete_category(cat_id: int):
    if not CategoryService.delete(cat_id):
        raise HTTPException(status_code=404, detail="Categoría no encontrada")


# ── Products ──────────────────────────────────────────────────────────────────

@app.get("/products", response_model=list[ProductSummary])
def list_products():
    return [_product_summary(p) for p in ProductService.get_all()]


@app.get("/products/{prod_id}", response_model=ProductOut)
def get_product(prod_id: int):
    try:
        return _product_out(ProductService.get(prod_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(body: ProductCreate):
    try:
        return _product_out(ProductService.create(body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/products/{prod_id}", response_model=ProductOut)
def update_product(prod_id: int, body: ProductUpdate):
    try:
        return _product_out(ProductService.update(prod_id, body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/products/{prod_id}", status_code=204)
def delete_product(prod_id: int):
    if not ProductService.delete(prod_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")


# ── Variants ──────────────────────────────────────────────────────────────────

@app.post("/products/{prod_id}/variants", response_model=ProductOut, status_code=201)
def add_variant(prod_id: int, body: VariantIn):
    try:
        return _product_out(ProductService.add_variant(prod_id, body))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/products/{prod_id}/variants/{variant_id}", response_model=ProductOut)
def delete_variant(prod_id: int, variant_id: int):
    try:
        return _product_out(ProductService.delete_variant(prod_id, variant_id))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
