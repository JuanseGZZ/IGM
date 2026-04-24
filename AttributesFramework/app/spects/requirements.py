# ============================================================
# STACK
# ============================================================
# psycopg[binary]   -> driver postgres
# fastapi           -> framework HTTP / routing
# uvicorn[standard] -> ASGI server
# pydantic          -> validacion y DTOs
# python-dotenv     -> variables de entorno desde .env


# ============================================================
# APIs - DASHBOARD DE GESTION
# ============================================================

# --- ATTRIBUTES ---
# GET    /attributes                              listar todos
# POST   /attributes                              crear atributo
# GET    /attributes/{id}                         obtener uno
# PUT    /attributes/{id}                         editar atributo
# DELETE /attributes/{id}                         eliminar
# POST   /attributes/{id}/enum-values             agregar valor enum
# DELETE /attributes/{id}/enum-values/{value}     quitar valor enum

# --- CATEGORIES ---
# GET    /categories                              listar todas
# POST   /categories                              crear categoria
# GET    /categories/{id}                         obtener una
# PUT    /categories/{id}                         editar nombre
# DELETE /categories/{id}                         eliminar
# POST   /categories/{id}/attributes/{attr_id}    suscribir atributo
# DELETE /categories/{id}/attributes/{attr_id}    desuscribir atributo

# --- PRODUCTS ---
# GET    /products                                listar todos
# POST   /products                                crear producto
# GET    /products/{id}                           obtener uno
# GET    /products/code/{code}                    obtener por codigo
# PUT    /products/{id}                           editar producto
# DELETE /products/{id}                           eliminar
# POST   /products/{id}/attributes/{attr_id}      suscribir atributo al producto
# DELETE /products/{id}/attributes/{attr_id}      desuscribir atributo
# POST   /products/{id}/implementations           agregar implementacion estatica
# DELETE /products/{id}/implementations/{impl_id} quitar implementacion estatica
# GET    /products/{id}/needed-attributes         atributos necesarios para crear variante

# --- VARIANTS (bajo producto) ---
# GET    /products/{id}/variants                  listar variantes
# POST   /products/{id}/variants                  crear variante
# DELETE /products/{id}/variants/{variant_id}     eliminar variante


# ============================================================
# DTOs
# ============================================================

# --- ATTRIBUTE ---
# AttributeCreateDTO
#   key: str
#   name: str
#   data_type: str          # "text" | "number" | "boolean" | "enum"
#   is_static: bool

# AttributeUpdateDTO
#   name: str
#   is_static: bool

# AttributeResponseDTO
#   id: int
#   key: str
#   name: str
#   data_type: str
#   is_static: bool
#   enum_values: list[str]

# EnumValueAddDTO
#   value: str


# --- CATEGORY ---
# CategoryCreateDTO
#   name: str

# CategoryUpdateDTO
#   name: str

# CategoryResponseDTO
#   id: int
#   name: str
#   attributes: list[AttributeResponseDTO]


# --- ATTRIBUTE IMPLEMENTATION ---
# AttributeImplementationCreateDTO
#   attribute_id: int
#   value: str | int | float | bool

# AttributeImplementationResponseDTO
#   id: int
#   attribute: AttributeResponseDTO
#   value: str


# --- VARIANT ---
# VariantCreateDTO
#   implementations: list[AttributeImplementationCreateDTO]

# VariantResponseDTO
#   id: int
#   attribute_implementations: list[AttributeImplementationResponseDTO]


# --- PRODUCT ---
# ProductCreateDTO
#   code: str
#   title: str
#   price: float
#   description: str
#   brand: str
#   category_id: int

# ProductUpdateDTO
#   title: str
#   price: float
#   description: str
#   brand: str

# ProductResponseDTO
#   id: int
#   code: str
#   title: str
#   price: float
#   description: str
#   brand: str
#   category: CategoryResponseDTO
#   attributes: list[AttributeResponseDTO]
#   attributes_implementations: list[AttributeImplementationResponseDTO]
#   variants: list[VariantResponseDTO]
