

// modelado de la misma

// base
producto                                m-1     categoria
productosAtributos                      m-1     producto
productosAtributos                      m-1     atributos
atributosImplementacion                 m-1     producto
variante                                m-1     producto
atributosImplementacion                 m-1     variante
atributosImplementacion                 m-1     atributos
enumValues                              m-1     atributos
categoriaAtributos                      m-1     categoria     
categoriaAtributos                      m-1     atributos

// expandida, hago un adaptador en implementacion asi no pongo 3 variables en inmplementacion, y renombre la tabla a atrImplementacion btw
producto                                m-1     categoria
productosAtributos                      m-1     producto
productosAtributos                      m-1     atributos
productoImplementacion                  m-1     producto
productoImplementacion                  1-1     atrImplementacion
variante                                m-1     producto
varianteImplementacion                  m-1     variante
varianteImplementacion                  1-1     atrImplementacion
atrImplementacion                       m-1     atributos
enumValues                              m-1     atributos
categoriaAtributos                      m-1     categoria     
categoriaAtributos                      m-1     atributos

// puntualizada
category{
    id              :int
    name            :str
}
categoryAtributes{
    id:int
    atributes_id    :int
    category_id     :int
}
product{
    id              :int
    code            :str
    title           :str
    price           :float
    description     :str
    brand           :str
    category        :FK
}
productImplementation{
    id              :int
    product_id      :FK
    atrImp_id       :FK
}
atrImplementation{
    id              :int
    atribute_id     :FK
    value           :str // es str para poner cualquier valor, luego se transforma con el typo que esta en atribute
}
productsAtributes{
    id:int
    product_id      :FK
    atribute_id     :FK
}
atribute{
    id              :int
    key             :str
    name            :str
    data_type       :str
    is_static       :bool
}
enum_values{
    id              :int
    atribute_id     :FK
    value           :str
}
variant{
    id              :int
    code            :str
    product_id      :FK
}
variantImplementation{
    id              :int
    variant_id      :FK
    atrImp_id       :FK
}



