/**
 * test_framework.js — Tests de integración para frontFW
 *
 * Prerrequisitos:
 *   - Servidor corriendo en http://localhost:8001
 *   - PostgreSQL con DB "productos"
 *
 * Ejecución (desde la raíz del repo):
 *   node TestingConcepts/test_framework.js
 *
 * Secciones:
 *   1. DTOs  — unit tests sin servidor (fromJSON, métodos, toJSON)
 *   2. AttributeService — CRUD completo
 *   3. CategoryService  — CRUD + addProduct
 *   4. ProductService   — CRUD + addImplementation + createVariant
 *   5. Two-call pattern — flujos de impacto a nivel API (sin DOM)
 *   6. Cleanup
 */

import { AttributeDTO }               from "./frontFW/interfaceModels/AttributeDTO.js";
import { AttributeImplementationDTO } from "./frontFW/interfaceModels/AttributeImplementationDTO.js";
import { VariantDTO }                 from "./frontFW/interfaceModels/VariantDTO.js";
import { CategoryDTO }                from "./frontFW/interfaceModels/CategoryDTO.js";
import { ProductDTO }                 from "./frontFW/interfaceModels/ProductDTO.js";
import { AttributeService }           from "./frontFW/service/attributeService.js";
import { CategoryService }            from "./frontFW/service/categoryService.js";
import { ProductService }             from "./frontFW/service/productService.js";
import { AttributeApi }               from "./frontFW/api/attributeApi.js";
import { CategoryApi }                from "./frontFW/api/categoryApi.js";
import { ProductApi }                 from "./frontFW/api/productApi.js";

// ── colores ───────────────────────────────────────────────────────────────────
const G = "\x1b[32m✓\x1b[0m";   // verde
const R = "\x1b[31m✗\x1b[0m";   // rojo
const Y = "\x1b[33m●\x1b[0m";   // amarillo (skip)
const B = (t) => `\x1b[1m${t}\x1b[0m`;

let passed = 0, failed = 0, skipped = 0;

function ok(label, condition, got) {
  if (condition) {
    console.log(`  ${G} ${label}`);
    passed++;
  } else {
    console.log(`  ${R} ${label}`);
    if (got !== undefined) console.log(`      got: ${JSON.stringify(got)}`);
    failed++;
  }
}

function skip(label, reason) {
  console.log(`  ${Y} ${label}  — ${reason}`);
  skipped++;
}

function section(title) {
  console.log(`\n${B("══ " + title + " ══")}`);
}

// Sufijo único por ejecución para evitar conflictos de key en DB
const TS = Date.now().toString(36).toUpperCase();

// IDs creados durante los tests, para cleanup final
const ids = {
  attrEnum: null,    // attribute "enum"  dynamic
  attrDyn:  null,    // dynamic attribute text
  attrStat: null,    // static attribute text
  attrTmp:  null,    // atributo temporal del two-call 5.3
  cat:      null,    // category de prueba
  prod:     null,    // product de prueba
  prodCode: `TFW-${TS}`,
};

// ─────────────────────────────────────────────────────────────────────────────
// 1. DTOs — unit tests sin servidor
// ─────────────────────────────────────────────────────────────────────────────
section("1. DTOs — unit tests");

// ── 1.1 AttributeDTO ──────────────────────────────────────────────────────────
console.log("\n  [1.1 AttributeDTO]");
{
  const raw = { id: 5, key: "color", name: "Color", data_type: "enum",
                is_static: false, enum_values: ["rojo", "azul"] };
  const a = AttributeDTO.fromJSON(raw);

  ok("fromJSON asigna campos", a.id === 5 && a.key === "color" && a.name === "Color");
  ok("isEnum()", a.isEnum() === true);
  ok("isDynamic()", a.isDynamic() === true);
  ok("isStatic()", a.isStatic() === false);
  ok("enum_values correcto", Array.isArray(a.enum_values) && a.enum_values[1] === "azul");

  const j = a.toJSON();
  ok("toJSON retorna objeto plano con id", j.id === 5 && j.key === "color");

  const aText = AttributeDTO.fromJSON({ key: "peso", name: "Peso", data_type: "number", is_static: true });
  ok("is_static text", aText.isStatic() === true && !aText.isEnum());
}

// ── 1.2 AttributeImplementationDTO ───────────────────────────────────────────
console.log("\n  [1.2 AttributeImplementationDTO]");
{
  const raw = {
    id: 1,
    attribute: { id: 5, key: "color", name: "Color", data_type: "enum",
                 is_static: false, enum_values: ["rojo"] },
    value: "rojo",
  };
  const impl = AttributeImplementationDTO.fromJSON(raw);

  ok("fromJSON", impl.id === 1 && impl.value === "rojo");
  ok("attribute es AttributeDTO", impl.attribute instanceof AttributeDTO);
  ok("castValue enum → string", impl.castValue() === "rojo");

  const implNum = AttributeImplementationDTO.fromJSON({
    id: 2,
    attribute: { key: "precio", name: "Precio", data_type: "number", is_static: true, enum_values: [] },
    value: "3.14",
  });
  ok("castValue number → float", implNum.castValue() === 3.14);

  const implBool = AttributeImplementationDTO.fromJSON({
    id: 3,
    attribute: { key: "activo", name: "Activo", data_type: "boolean", is_static: true, enum_values: [] },
    value: "true",
  });
  ok("castValue boolean → true", implBool.castValue() === true);
}

// ── 1.3 VariantDTO ────────────────────────────────────────────────────────────
console.log("\n  [1.3 VariantDTO]");
{
  const raw = {
    id: 10,
    attribute_implementations: [
      { id: 1,
        attribute: { key: "color", name: "Color", data_type: "enum",
                     is_static: false, enum_values: ["rojo"] },
        value: "rojo" },
      { id: 2,
        attribute: { key: "talle", name: "Talle", data_type: "text",
                     is_static: false, enum_values: [] },
        value: "M" },
    ],
  };
  const v = VariantDTO.fromJSON(raw);

  ok("fromJSON id", v.id === 10);
  ok("implementations mapeadas", v.attribute_implementations.length === 2);
  ok("getValue('color')", v.getValue("color") === "rojo");
  ok("getValue('talle')", v.getValue("talle") === "M");
  ok("getValue key inexistente → null", v.getValue("marca") === null);

  const j = v.toJSON();
  ok("toJSON incluye attribute_implementations", Array.isArray(j.attribute_implementations));
}

// ── 1.4 CategoryDTO ───────────────────────────────────────────────────────────
console.log("\n  [1.4 CategoryDTO]");
{
  const raw = {
    id: 1, name: "Ropa",
    attributes: [
      { id: 3, key: "talle", name: "Talle", data_type: "text", is_static: false, enum_values: [] },
      { id: 4, key: "material", name: "Material", data_type: "text", is_static: true, enum_values: [] },
    ],
    products: [{ id: 10, code: "R001" }],
  };
  const c = CategoryDTO.fromJSON(raw);

  ok("fromJSON nombre", c.name === "Ropa" && c.id === 1);
  ok("attributes mapeados", c.attributes.length === 2 && c.attributes[0] instanceof AttributeDTO);
  ok("getDynamicAttributes()", c.getDynamicAttributes().length === 1);
  ok("getStaticAttributes()", c.getStaticAttributes().length === 1);
  ok("products se guarda raw", Array.isArray(c.products) && c.products[0].code === "R001");
  ok("null → null", CategoryDTO.fromJSON(null) === null);
}

// ── 1.5 ProductDTO ────────────────────────────────────────────────────────────
console.log("\n  [1.5 ProductDTO]");
{
  const raw = {
    id: 99, code: "REMERA-001", title: "Remera", price: 999,
    description: "desc", brand: "Nike",
    category: {
      id: 1, name: "Ropa",
      attributes: [
        { id: 3, key: "talle", name: "Talle", data_type: "text", is_static: false, enum_values: [] },
        { id: 4, key: "material", name: "Material", data_type: "text", is_static: true, enum_values: [] },
      ],
      products: [],
    },
    attributes: [
      { id: 7, key: "coleccion", name: "Colección", data_type: "text", is_static: false, enum_values: [] },
    ],
    attributes_implementations: [
      { id: 1,
        attribute: { id: 4, key: "material", name: "Material", data_type: "text", is_static: true, enum_values: [] },
        value: "algodón" },
    ],
    variants: [
      {
        id: 10,
        attribute_implementations: [
          { id: 1,
            attribute: { key: "talle", name: "Talle", data_type: "text", is_static: false, enum_values: [] },
            value: "M" },
        ],
      },
    ],
  };
  const p = ProductDTO.fromJSON(raw);

  ok("fromJSON campos base", p.id === 99 && p.code === "REMERA-001" && p.price === 999);
  ok("category es CategoryDTO", p.category instanceof CategoryDTO);
  ok("category.id accesible", p.category.id === 1);
  ok("variants mapeadas", p.variants.length === 1 && p.variants[0] instanceof VariantDTO);
  ok("getAllDynamicAttributes() deduplica cat+own", p.getAllDynamicAttributes().length === 2);
  ok("getAllStaticAttributes()", p.getAllStaticAttributes().length === 1);
  ok("getImplementation('material')", p.getImplementation("material")?.value === "algodón");
  ok("getImplementation clave inexistente → null", p.getImplementation("xxx") === null);
  ok("variant.getValue('talle')", p.variants[0].getValue("talle") === "M");

  const j = p.toJSON();
  ok("toJSON tiene todos los campos", "code" in j && "category" in j && "variants" in j);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. AttributeService
// ─────────────────────────────────────────────────────────────────────────────
section("2. AttributeService");

// ── 2.1 create text ──────────────────────────────────────────────────────────
console.log("\n  [2.1 create — text, is_static=true]");
try {
  const attr = await AttributeService.create({
    key: `tfw_mat_${TS}`, name: "TFW Material", data_type: "text",
    is_static: true, enum_values: [],
  });
  ids.attrStat = attr.id;
  ok("retorna AttributeDTO", attr instanceof AttributeDTO);
  ok("id asignado", attr.id > 0);
  ok("key correcto", attr.key === `tfw_mat_${TS}`);
  ok("isStatic()", attr.isStatic());
} catch (e) {
  ok("create text", false, e.message);
}

// ── 2.2 create enum ──────────────────────────────────────────────────────────
console.log("\n  [2.2 create — enum, is_static=false]");
try {
  const attr = await AttributeService.create({
    key: `tfw_col_${TS}`, name: "TFW Color", data_type: "enum",
    is_static: false, enum_values: ["rojo", "azul"],
  });
  ids.attrEnum = attr.id;
  ok("retorna AttributeDTO", attr instanceof AttributeDTO);
  ok("isEnum()", attr.isEnum());
  ok("isDynamic()", attr.isDynamic());
  ok("enum_values", attr.enum_values.length === 2);
} catch (e) {
  ok("create enum", false, e.message);
}

// ── 2.3 create dyn (para variantes) ──────────────────────────────────────────
console.log("\n  [2.3 create — dynamic text (para variantes)]");
try {
  const attr = await AttributeService.create({
    key: `tfw_tal_${TS}`, name: "TFW Talle", data_type: "text",
    is_static: false, enum_values: [],
  });
  ids.attrDyn = attr.id;
  ok("retorna AttributeDTO", attr instanceof AttributeDTO);
  ok("isDynamic()", attr.isDynamic());
} catch (e) {
  ok("create dyn", false, e.message);
}

// ── 2.4 getAll ────────────────────────────────────────────────────────────────
console.log("\n  [2.4 getAll]");
try {
  const list = await AttributeService.getAll();
  ok("retorna array", Array.isArray(list));
  ok("elementos son AttributeDTO", list.length > 0 && list[0] instanceof AttributeDTO);
  ok("contiene el creado", list.some((a) => a.key === `tfw_mat_${TS}`));
} catch (e) {
  ok("getAll", false, e.message);
}

// ── 2.5 getById ───────────────────────────────────────────────────────────────
console.log("\n  [2.5 getById]");
try {
  const attr = await AttributeService.getById(ids.attrStat);
  ok("retorna AttributeDTO", attr instanceof AttributeDTO);
  ok("mismo id", attr.id === ids.attrStat);
  const missing = await AttributeService.getById(999999);
  ok("id inexistente → null", missing === null);
} catch (e) {
  ok("getById", false, e.message);
}

// ── 2.6 update ────────────────────────────────────────────────────────────────
console.log("\n  [2.6 update]");
try {
  const updated = await AttributeService.update(ids.attrStat, { name: "TFW Material v2" });
  ok("retorna AttributeDTO", updated instanceof AttributeDTO);
  ok("name actualizado", updated.name === "TFW Material v2");
} catch (e) {
  ok("update", false, e.message);
}

// ── 2.7 addEnumValue ──────────────────────────────────────────────────────────
console.log("\n  [2.7 addEnumValue]");
try {
  const updated = await AttributeService.addEnumValue(ids.attrEnum, "verde");
  ok("retorna AttributeDTO", updated instanceof AttributeDTO);
  ok("enum_values incluye 'verde'", updated.enum_values.includes("verde"));
} catch (e) {
  ok("addEnumValue", false, e.message);
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. CategoryService
// ─────────────────────────────────────────────────────────────────────────────
section("3. CategoryService");

// ── 3.1 create ────────────────────────────────────────────────────────────────
console.log("\n  [3.1 create]");
try {
  const cat = await CategoryService.create("TFW Categoría Test");
  ids.cat = cat.id;
  ok("retorna CategoryDTO", cat instanceof CategoryDTO);
  ok("id asignado", cat.id > 0);
  ok("name correcto", cat.name === "TFW Categoría Test");
} catch (e) {
  ok("create", false, e.message);
}

// ── 3.2 getAll ────────────────────────────────────────────────────────────────
console.log("\n  [3.2 getAll]");
try {
  const list = await CategoryService.getAll();
  ok("retorna array", Array.isArray(list));
  ok("elementos son CategoryDTO", list.length > 0 && list[0] instanceof CategoryDTO);
  ok("contiene la creada", list.some((c) => c.id === ids.cat));
} catch (e) {
  ok("getAll", false, e.message);
}

// ── 3.3 getById ───────────────────────────────────────────────────────────────
console.log("\n  [3.3 getById]");
try {
  const cat = await CategoryService.getById(ids.cat);
  ok("retorna CategoryDTO", cat instanceof CategoryDTO);
  ok("mismo id", cat.id === ids.cat);
  const missing = await CategoryService.getById(999999);
  ok("id inexistente → null", missing === null);
} catch (e) {
  ok("getById", false, e.message);
}

// ── 3.4 updateName ────────────────────────────────────────────────────────────
console.log("\n  [3.4 updateName]");
try {
  const updated = await CategoryService.updateName(ids.cat, "TFW Cat Actualizada");
  ok("retorna CategoryDTO", updated instanceof CategoryDTO);
  ok("name actualizado", updated.name === "TFW Cat Actualizada");
} catch (e) {
  ok("updateName", false, e.message);
}

// ── 3.5 addDynamicAttribute (sin productos → sin impacto) ────────────────────
console.log("\n  [3.5 addDynamicAttribute — sin impacto]");
try {
  if (!ids.cat || !ids.attrEnum) {
    skip("addDynamicAttribute", "falta cat o attrEnum");
  } else {
    const cat = await CategoryService.addDynamicAttribute(ids.cat, ids.attrEnum, null);
    ok("retorna CategoryDTO", cat instanceof CategoryDTO);
    ok("atributo agregado", cat.attributes.some((a) => a.id === ids.attrEnum));
    ok("atributo es dinámico", cat.getDynamicAttributes().some((a) => a.id === ids.attrEnum));
  }
} catch (e) {
  ok("addDynamicAttribute", false, e.message);
}

// ── 3.6 addStaticAttribute (sin productos → sin impacto) ─────────────────────
console.log("\n  [3.6 addStaticAttribute — sin impacto]");
try {
  if (!ids.cat || !ids.attrStat) {
    skip("addStaticAttribute", "falta cat o attrStat");
  } else {
    const cat = await CategoryService.addStaticAttribute(ids.cat, ids.attrStat, null);
    ok("retorna CategoryDTO", cat instanceof CategoryDTO);
    ok("atributo estático agregado", cat.attributes.some((a) => a.id === ids.attrStat));
  }
} catch (e) {
  ok("addStaticAttribute", false, e.message);
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. ProductService
// ─────────────────────────────────────────────────────────────────────────────
section("4. ProductService");

// ── 4.1 create ────────────────────────────────────────────────────────────────
console.log("\n  [4.1 create]");
try {
  if (!ids.cat) {
    skip("create product", "falta ids.cat");
  } else {
    const prod = await ProductService.create({
      code: ids.prodCode, title: "TFW Producto Test",
      price: 1234, description: "Test framework producto",
      brand: "TestBrand", category_id: ids.cat,
    });
    ids.prod = prod.id;
    ok("retorna ProductDTO", prod instanceof ProductDTO);
    ok("id asignado", prod.id > 0);
    ok("code correcto", prod.code === ids.prodCode);
    ok("price correcto", prod.price === 1234);
    ok("category es objeto (no category_id)", prod.category instanceof CategoryDTO);
    ok("category.id correcto", prod.category.id === ids.cat);
  }
} catch (e) {
  ok("create", false, e.message);
}

// ── 4.2 getAll ────────────────────────────────────────────────────────────────
console.log("\n  [4.2 getAll]");
try {
  const list = await ProductService.getAll();
  ok("retorna array", Array.isArray(list));
  ok("elementos son ProductDTO", list.length > 0 && list[0] instanceof ProductDTO);
  ok("contiene el creado", list.some((p) => p.id === ids.prod));
} catch (e) {
  ok("getAll", false, e.message);
}

// ── 4.3 getById ───────────────────────────────────────────────────────────────
console.log("\n  [4.3 getById]");
try {
  const prod = await ProductService.getById(ids.prod);
  ok("retorna ProductDTO", prod instanceof ProductDTO);
  ok("mismo id", prod.id === ids.prod);
  ok("variants es array", Array.isArray(prod.variants));
  const missing = await ProductService.getById(999999);
  ok("id inexistente → null", missing === null);
} catch (e) {
  ok("getById", false, e.message);
}

// ── 4.4 getByCode ─────────────────────────────────────────────────────────────
console.log("\n  [4.4 getByCode]");
try {
  const prod = await ProductService.getByCode(ids.prodCode);
  ok("retorna ProductDTO", prod instanceof ProductDTO);
  ok("code correcto", prod.code === ids.prodCode);
  const missing = await ProductService.getByCode("CODIGO-QUE-NO-EXISTE-9999");
  ok("code inexistente → null", missing === null);
} catch (e) {
  ok("getByCode", false, e.message);
}

// ── 4.5 update ────────────────────────────────────────────────────────────────
console.log("\n  [4.5 update]");
try {
  if (!ids.prod) { skip("update", "falta ids.prod"); }
  else {
    const updated = await ProductService.update(ids.prod, { title: "TFW Producto Actualizado", price: 9999 });
    ok("retorna ProductDTO", updated instanceof ProductDTO);
    ok("title actualizado", updated.title === "TFW Producto Actualizado");
    ok("price actualizado", updated.price === 9999);
  }
} catch (e) {
  ok("update", false, e.message);
}

// ── 4.6 addImplementation (atributo estático de la categoría) ─────────────────
console.log("\n  [4.6 addImplementation — atributo estático]");
try {
  if (!ids.prod || !ids.attrStat) { skip("addImplementation", "falta prod o attrStat"); }
  else {
    const prod = await ProductService.addImplementation(ids.prod, ids.attrStat, "algodón");
    ok("retorna ProductDTO", prod instanceof ProductDTO);
    ok("implementación guardada", prod.attributes_implementations.length > 0);
    ok("getImplementation funciona", prod.getImplementation(`tfw_mat_${TS}`) !== null);
    ok("castValue correcto", prod.getImplementation(`tfw_mat_${TS}`)?.castValue() === "algodón");
  }
} catch (e) {
  ok("addImplementation", false, e.message);
}

// ── 4.7 addDynamicAttribute al producto (sin variantes → sin impacto) ────────
console.log("\n  [4.7 addDynamicAttribute al producto — sin impacto]");
try {
  if (!ids.prod || !ids.attrDyn) { skip("addDynamicAttribute prod", "falta prod o attrDyn"); }
  else {
    const prod = await ProductService.addDynamicAttribute(ids.prod, ids.attrDyn, null);
    ok("retorna ProductDTO", prod instanceof ProductDTO);
    ok("atributo propio agregado", prod.attributes.some((a) => a.id === ids.attrDyn));
  }
} catch (e) {
  ok("addDynamicAttribute prod", false, e.message);
}

// ── 4.8 createVariant — con implementations directas ─────────────────────────
console.log("\n  [4.8 createVariant — con implementations]");
try {
  if (!ids.prod || !ids.attrDyn) { skip("createVariant", "falta prod o attrDyn"); }
  else {
    // El producto tiene attrDyn (tfw_talle, text) y attrEnum (tfw_color, enum)
    // Primero necesitamos agregar attrEnum al producto si no está
    // Usamos solo attrDyn para simplificar
    const implementations = [
      { attribute_id: ids.attrDyn,  value: "L" },
      { attribute_id: ids.attrEnum, value: "rojo" },
    ];
    const prod = await ProductService.createVariant(ids.prod, implementations, null);
    ok("retorna ProductDTO", prod instanceof ProductDTO);
    ok("tiene variantes", prod.variants.length > 0);
    const v = prod.variants.find((vt) =>
      vt.attribute_implementations.some(
        (i) => i.attribute?.id === ids.attrDyn && i.value === "L"
      )
    );
    ok("variante creada con attrDyn=L", v !== undefined);
    if (v) {
      ok("getValue('tfw_tal_TS')", v.getValue(`tfw_tal_${TS}`) === "L");
    }
  }
} catch (e) {
  ok("createVariant", false, e.message);
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. Two-call pattern — a nivel API (sin DOM)
// ─────────────────────────────────────────────────────────────────────────────
section("5. Two-call pattern — flujos de impacto (nivel API)");

// El servicio maneja este flujo internamente con buildDynamicImplForm (DOM).
// Aquí lo probamos haciendo las dos llamadas manualmente a nivel API
// para verificar que el servidor responde correctamente a cada paso.

// ── 5.1 Categoría con producto → addStaticAttribute con impacto ───────────────
console.log("\n  [5.1 Category addStaticAttribute con impacto]");
let impactCatId = null, impactAttrId = null;
try {
  // Crear una categoría nueva
  const { data: catData } = await CategoryApi.create("TFW Impact Cat");
  impactCatId = catData.id;
  ok("categoría de impacto creada", impactCatId > 0, catData);

  // Crear un atributo text estático nuevo
  const { data: aData } = await AttributeApi.create({
    key: `tfw_imp_${TS}`, name: "TFW Impacto", data_type: "text",
    is_static: true, enum_values: [],
  });
  impactAttrId = aData.id;
  ok("atributo de impacto creado", impactAttrId > 0, aData);

  // Agregar un producto a la categoría (para que haya impacto)
  if (ids.prod) {
    // Reasignar el producto de prueba a la nueva categoría
    const { status: ps } = await CategoryApi.addProduct(impactCatId, ids.prod);
    ok("producto reasignado a categoría de impacto", ps === 200, ps);
  }

  // Primera llamada: detectar impacto
  const { status: s1, data: d1 } = await CategoryApi.addStaticAttribute(impactCatId, {
    attribute_id: impactAttrId,
  });
  ok("primera llamada → 200", s1 === 200, s1);
  ok("needs_implementations = true", d1.needs_implementations === true, d1);
  ok("impact contiene productos afectados", Array.isArray(d1.impact) && d1.impact.length > 0, d1.impact);

  if (d1.needs_implementations && d1.impact?.length > 0) {
    const affectedProductId = d1.impact[0].product_id;
    ok("impact tiene product_id", affectedProductId > 0, d1.impact[0]);

    // Segunda llamada: proveer los valores
    const implementations = d1.impact.map((p) => ({ product_id: p.product_id, value: "valor-test" }));
    const { status: s2, data: d2 } = await CategoryApi.addStaticAttribute(impactCatId, {
      attribute_id: impactAttrId,
      implementations,
    });
    ok("segunda llamada → 200", s2 === 200, s2);
    ok("categoría devuelta", d2.category?.id === impactCatId, d2);
    ok("atributo en categoría", d2.category?.attributes?.some((a) => a.id === impactAttrId), d2.category);
  }
} catch (e) {
  ok("two-call static", false, e.message);
}

// ── 5.2 Categoría removeAttribute con needs_decision ─────────────────────────
console.log("\n  [5.2 Category removeAttribute — needs_decision]");
try {
  if (!impactCatId || !impactAttrId) {
    skip("removeAttribute impact", "falta impactCatId o impactAttrId");
  } else {
    // Primera llamada: del_opt=0 → detectar impacto
    const { status: s1, data: d1 } = await CategoryApi.removeAttribute(impactCatId, impactAttrId, 0);
    ok("primera llamada → 200", s1 === 200, s1);
    ok("needs_decision = true (hay impl huérfanas)", d1.needs_decision === true, d1);
    ok("impact tiene productos", Array.isArray(d1.impact) && d1.impact.length > 0, d1.impact);

    // Segunda llamada: del_opt=1 → eliminar impls huérfanas
    const { status: s2, data: d2 } = await CategoryApi.removeAttribute(impactCatId, impactAttrId, 1);
    ok("segunda llamada (del_opt=1) → 200", s2 === 200, s2);
    ok("atributo eliminado de categoría", !d2.category?.attributes?.some((a) => a.id === impactAttrId), d2);
  }
} catch (e) {
  ok("removeAttribute impact", false, e.message);
}

// ── 5.3 Product addDynamicAttribute con variantes (impacto) ──────────────────
console.log("\n  [5.3 Product addDynamicAttribute — con variantes (two-call)]");
try {
  if (!ids.prod || !ids.attrEnum) {
    skip("prod addDynamic con variantes", "falta prod o attrEnum");
  } else {
    // El producto ya tiene una variante (del test 4.8) y attrDyn (tfw_talle)
    // Crear un atributo dinámico nuevo para el producto
    const { data: nAttrData } = await AttributeApi.create({
      key: `tfw_tmp_${TS}`, name: "TFW Temporada", data_type: "text",
      is_static: false, enum_values: [],
    });
    const nAttrId = nAttrData.id;
    ids.attrTmp = nAttrId;
    ok("atributo temporada creado", nAttrId > 0);

    // Refresh: verificar cuántas variantes tiene el producto
    const { data: prodData } = await ProductApi.getById(ids.prod);
    const variantCount = prodData.variants?.length ?? 0;

    if (variantCount === 0) {
      skip("two-call con variantes", "el producto no tiene variantes actualmente");
    } else {
      // Primera llamada al PRODUCT endpoint
      const { status: s1, data: d1 } = await ProductApi.addDynamicAttribute(ids.prod, {
        attribute_id: nAttrId,
      });
      ok("primera llamada → 200", s1 === 200, s1);
      ok("needs_implementations = true", d1.needs_implementations === true, d1);
      ok("impact contiene variantes", Array.isArray(d1.impact) && d1.impact.length > 0, d1.impact);

      // Segunda llamada con variant_options
      const variant_options = d1.impact.map((v) => ({ variant_id: v.variant_id, value: "verano" }));
      const { status: s2, data: d2 } = await ProductApi.addDynamicAttribute(ids.prod, {
        attribute_id: nAttrId,
        variant_options,
      });
      ok("segunda llamada → 200", s2 === 200, s2);
      ok("producto retornado", d2.product?.id === ids.prod, d2);
    }

    // No se elimina aquí — el cleanup principal lo borra DESPUÉS de eliminar el producto
  }
} catch (e) {
  ok("prod addDynamic two-call", false, e.message);
}

// ── 5.4 Product createVariant — implementations_invalid flow ─────────────────
console.log("\n  [5.4 Product createVariant — implementations_invalid]");
// Usar un producto fresco sin variantes para no arrastrar estado del test 4.8
{
  let freshProd = null;
  try {
    // Crear producto limpio en la misma categoría de test
    const catId = ids.cat ?? (await CategoryService.create("TFW Cat 54")).id;
    const { data: fpData } = await ProductApi.create({
      code: `TFW-F54-${TS}`, title: "Fresh Prod 54", price: 1,
      description: "-", brand: "-", category_id: catId,
    });
    freshProd = fpData.id;

    // Agregar atributo dinámico al producto (sin variantes → sin impacto)
    if (ids.attrDyn) {
      await ProductApi.addDynamicAttribute(freshProd, { attribute_id: ids.attrDyn });
    }

    // Llamar createVariant con [] → server debe retornar implementations_invalid
    const { status, data } = await ProductApi.createVariant(freshProd, []);

    if (data?.error === "implementations_invalid") {
      ok("status 200 con error implementations_invalid", status === 200, status);
      ok("needed_attributes es array", Array.isArray(data.needed_attributes), data);
      ok("needed_attributes tiene atributos", data.needed_attributes.length > 0, data.needed_attributes);
      const neededAttrs = data.needed_attributes.map(AttributeDTO.fromJSON);
      ok("mapeo a AttributeDTO[]", neededAttrs.every((a) => a instanceof AttributeDTO));
    } else {
      // Sin atributos dinámicos requeridos → variante vacía creada
      ok("sin atributos requeridos → variante creada directamente", !data?.error, data);
    }
  } catch (e) {
    ok("createVariant invalid flow", false, e.message);
  } finally {
    if (freshProd) {
      try {
        const p = await ProductService.getById(freshProd);
        for (const v of p?.variants ?? []) {
          await ProductApi.deleteVariant(freshProd, v.id);
        }
        await ProductApi.delete(freshProd);
      } catch (_) {}
    }
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. Cleanup
// ─────────────────────────────────────────────────────────────────────────────
section("6. Cleanup");

// Las funciones se ejecutan secuencialmente (no eager) para respetar FK constraints.
// Orden: primero variantes → producto → categorías → atributos
const cleanups = [
  // 1. Eliminar variantes del producto antes de eliminar el producto
  ["Variantes de producto", async () => {
    if (!ids.prod) return true;
    const prod = await ProductService.getById(ids.prod);
    for (const v of prod?.variants ?? []) {
      await ProductApi.deleteVariant(ids.prod, v.id);
    }
    return true;
  }],
  // 2. Eliminar el producto (ahora en impactCatId, puede estar en cualquier cat)
  ["Producto",         () => ids.prod      ? ProductService.delete(ids.prod)          : Promise.resolve(true)],
  // 3. Eliminar categorías (ya sin productos)
  ["Categoría test",   () => ids.cat       ? CategoryService.delete(ids.cat)          : Promise.resolve(true)],
  ["Categoría impact", () => impactCatId   ? CategoryService.delete(impactCatId)      : Promise.resolve(true)],
  // 4. Eliminar atributos (FK libre después de borrar el producto)
  ["Attr estático",    () => ids.attrStat  ? AttributeService.delete(ids.attrStat)    : Promise.resolve(true)],
  ["Attr enum",        () => ids.attrEnum  ? AttributeService.delete(ids.attrEnum)    : Promise.resolve(true)],
  ["Attr dinámico",    () => ids.attrDyn   ? AttributeService.delete(ids.attrDyn)     : Promise.resolve(true)],
  ["Attr temporal",    () => ids.attrTmp   ? AttributeService.delete(ids.attrTmp)     : Promise.resolve(true)],
];

for (const [label, fn] of cleanups) {
  try {
    const result = await fn();
    ok(`delete ${label}`, result !== false);
  } catch (e) {
    ok(`delete ${label}`, false, e.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Resumen
// ─────────────────────────────────────────────────────────────────────────────
console.log(`\n${"─".repeat(50)}`);
console.log(`${B("Resultado:")}  ${G} ${passed} ok   ${R} ${failed} fail   ${Y} ${skipped} skip`);
if (failed > 0) process.exit(1);
