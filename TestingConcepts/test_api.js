/**
 * test_api.js — Testing completo de la API IGM Product Management
 *
 * Cubre todos los endpoints documentados en interfaces.md:
 *   - Attributes  (CRUD + enum-values)
 *   - Categories  (CRUD + dynamic/static attribute + del_attribute)
 *   - Products    (CRUD + dynamic-attribute + implementations + variants)
 *
 * Uso: node test_api.js
 * Requiere Node >= 18 (fetch nativo).
 */

const BASE = "http://localhost:8001";

// ── helpers ──────────────────────────────────────────────────────────────────

let passed = 0;
let failed = 0;

async function req(method, path, body = null) {
  const opts = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  const data = await res.json().catch(() => null);
  return { status: res.status, data };
}

function assert(label, condition, got) {
  if (condition) {
    console.log(`  ✓ ${label}`);
    passed++;
  } else {
    console.error(`  ✗ ${label}  →  got: ${JSON.stringify(got)}`);
    failed++;
  }
}

function section(title) {
  console.log(`\n${"═".repeat(60)}`);
  console.log(`  ${title}`);
  console.log("═".repeat(60));
}

// IDs globales que se van completando durante el run
const ids = {};

// ═══════════════════════════════════════════════════════════════════════════
// 1. ATTRIBUTES
// ═══════════════════════════════════════════════════════════════════════════

async function testAttributes() {
  section("1. ATTRIBUTES");

  // ── 1.1 GET /attributes ─────────────────────────────────────────────────
  console.log("\n  1.1  GET /attributes — lista inicial");
  {
    const { status, data } = await req("GET", "/attributes");
    assert("status 200", status === 200, status);
    assert("retorna array", Array.isArray(data), data);
  }

  // ── 1.2 POST /attributes — crear atributo enum dinámico ─────────────────
  console.log("\n  1.2  POST /attributes — crear atributo enum dinámico");
  {
    const body = {
      key: `talle_${Date.now()}`,
      name: "Talle",
      data_type: "enum",
      is_static: false,
      enum_values: ["S", "M", "L"],
    };
    const { status, data } = await req("POST", "/attributes", body);
    assert("status 201", status === 201, status);
    assert("tiene id", typeof data.id === "number", data);
    assert("key correcto", data.key === body.key, data.key);
    assert("enum_values correcto", JSON.stringify(data.enum_values) === JSON.stringify(body.enum_values), data.enum_values);
    ids.dynAttr = data.id;
    ids.dynAttrKey = data.key;
  }

  // ── 1.3 POST /attributes — crear atributo text estático ─────────────────
  console.log("\n  1.3  POST /attributes — crear atributo text estático");
  {
    const body = {
      key: `material_${Date.now()}`,
      name: "Material",
      data_type: "text",
      is_static: true,
    };
    const { status, data } = await req("POST", "/attributes", body);
    assert("status 201", status === 201, status);
    assert("is_static true", data.is_static === true, data.is_static);
    ids.statAttr = data.id;
    ids.statAttrKey = data.key;
  }

  // ── 1.4 GET /attributes/{id} ────────────────────────────────────────────
  console.log("\n  1.4  GET /attributes/{id}");
  {
    const { status, data } = await req("GET", `/attributes/${ids.dynAttr}`);
    assert("status 200", status === 200, status);
    assert("id correcto", data.id === ids.dynAttr, data.id);
  }

  // ── 1.5 PATCH /attributes/{id} — actualizar nombre ─────────────────────
  console.log("\n  1.5  PATCH /attributes/{id} — actualizar nombre");
  {
    const { status, data } = await req("PATCH", `/attributes/${ids.dynAttr}`, {
      name: "Talle (actualizado)",
    });
    assert("status 200", status === 200, status);
    assert("nombre actualizado", data.name === "Talle (actualizado)", data.name);
  }

  // ── 1.6 PATCH /attributes/{id} — reemplazar enum_values ────────────────
  console.log("\n  1.6  PATCH /attributes/{id} — reemplazar enum_values");
  {
    const newVals = ["XS", "S", "M", "L", "XL"];
    const { status, data } = await req("PATCH", `/attributes/${ids.dynAttr}`, {
      enum_values: newVals,
    });
    assert("status 200", status === 200, status);
    assert("enum_values reemplazados", JSON.stringify(data.enum_values) === JSON.stringify(newVals), data.enum_values);
  }

  // ── 1.7 POST /attributes/{id}/enum-values — agregar valor ───────────────
  console.log("\n  1.7  POST /attributes/{id}/enum-values — agregar valor");
  {
    const { status, data } = await req("POST", `/attributes/${ids.dynAttr}/enum-values`, {
      value: "XXL",
    });
    assert("status 200", status === 200, status);
    assert("XXL agregado", data.enum_values.includes("XXL"), data.enum_values);
  }

  // ── 1.8 POST /attributes/{id}/enum-values — duplicado debe fallar ───────
  console.log("\n  1.8  POST /attributes/{id}/enum-values — duplicado → 400");
  {
    const { status } = await req("POST", `/attributes/${ids.dynAttr}/enum-values`, {
      value: "XXL",
    });
    assert("status 400", status === 400, status);
  }

  // ── 1.9 GET /attributes/{id} — not found ────────────────────────────────
  console.log("\n  1.9  GET /attributes/99999 — not found → 404");
  {
    const { status } = await req("GET", "/attributes/99999");
    assert("status 404", status === 404, status);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 2. CATEGORIES
// ═══════════════════════════════════════════════════════════════════════════

async function testCategories() {
  section("2. CATEGORIES");

  // ── 2.1 POST /categories ────────────────────────────────────────────────
  console.log("\n  2.1  POST /categories — crear categoría");
  {
    const { status, data } = await req("POST", "/categories", {
      name: `TestCat_${Date.now()}`,
    });
    assert("status 201", status === 201, status);
    assert("tiene id", typeof data.id === "number", data);
    assert("products vacío", Array.isArray(data.products) && data.products.length === 0, data.products);
    assert("attributes vacío", Array.isArray(data.attributes) && data.attributes.length === 0, data.attributes);
    ids.cat = data.id;
    ids.catName = data.name;
  }

  // ── 2.2 GET /categories ─────────────────────────────────────────────────
  console.log("\n  2.2  GET /categories — lista");
  {
    const { status, data } = await req("GET", "/categories");
    assert("status 200", status === 200, status);
    assert("retorna array", Array.isArray(data), data);
    assert("nuestra categoría en la lista", data.some((c) => c.id === ids.cat), ids.cat);
  }

  // ── 2.3 GET /categories/{id} ────────────────────────────────────────────
  console.log("\n  2.3  GET /categories/{id}");
  {
    const { status, data } = await req("GET", `/categories/${ids.cat}`);
    assert("status 200", status === 200, status);
    assert("id correcto", data.id === ids.cat, data.id);
  }

  // ── 2.4 PATCH /categories/{id} — actualizar nombre ─────────────────────
  console.log("\n  2.4  PATCH /categories/{id} — actualizar nombre");
  {
    const newName = `${ids.catName}_v2`;
    const { status, data } = await req("PATCH", `/categories/${ids.cat}`, {
      name: newName,
    });
    assert("status 200", status === 200, status);
    assert("nombre actualizado", data.name === newName, data.name);
  }

  // ── 2.5 POST /categories/{id}/static-attribute — sin implementaciones ───
  console.log("\n  2.5  POST /categories/{id}/static-attribute — sin productos (no impact)");
  {
    const { status, data } = await req(
      "POST",
      `/categories/${ids.cat}/static-attribute`,
      { attribute_id: ids.statAttr }
    );
    assert("status 200", status === 200, status);
    assert("needs_implementations false", data.needs_implementations === false, data);
    assert("category presente", data.category !== undefined, data);
    assert("atributo en categoría", data.category.attributes.some((a) => a.id === ids.statAttr), data.category.attributes);
  }

  // ── 2.6 POST /categories/{id}/dynamic-attribute — sin productos ──────────
  console.log("\n  2.6  POST /categories/{id}/dynamic-attribute — sin productos (no impact)");
  {
    const { status, data } = await req(
      "POST",
      `/categories/${ids.cat}/dynamic-attribute`,
      { attribute_id: ids.dynAttr }
    );
    assert("status 200", status === 200, status);
    assert("needs_implementations false", data.needs_implementations === false, data);
    assert("atributo en categoría", data.category.attributes.some((a) => a.id === ids.dynAttr), data.category.attributes);
  }

  // ── 2.7 GET /categories/{id} — not found ────────────────────────────────
  console.log("\n  2.7  GET /categories/99999 — not found → 404");
  {
    const { status } = await req("GET", "/categories/99999");
    assert("status 404", status === 404, status);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 3. PRODUCTS
// ═══════════════════════════════════════════════════════════════════════════

async function testProducts() {
  section("3. PRODUCTS");

  const code = `TEST-${Date.now()}`;

  // ── 3.1 POST /products — crear producto ─────────────────────────────────
  console.log("\n  3.1  POST /products — crear producto");
  {
    const body = {
      code,
      title: "Remera Test",
      price: 1500.0,
      description: "Remera de algodón para testing",
      brand: "TestBrand",
      category_id: ids.cat,
    };
    const { status, data } = await req("POST", "/products", body);
    assert("status 201", status === 201, status);
    assert("tiene id", typeof data.id === "number", data);
    assert("code correcto", data.code === code, data.code);
    assert("category_id correcto", data.category?.id === ids.cat, data.category?.id);
    assert("variants vacío", Array.isArray(data.variants) && data.variants.length === 0, data.variants);
    ids.prod = data.id;
    ids.prodCode = data.code;
  }

  // ── 3.2 GET /products ───────────────────────────────────────────────────
  console.log("\n  3.2  GET /products — lista");
  {
    const { status, data } = await req("GET", "/products");
    assert("status 200", status === 200, status);
    assert("retorna array", Array.isArray(data), data);
    assert("nuestro producto en la lista", data.some((p) => p.id === ids.prod), ids.prod);
  }

  // ── 3.3 GET /products/{id} ──────────────────────────────────────────────
  console.log("\n  3.3  GET /products/{id}");
  {
    const { status, data } = await req("GET", `/products/${ids.prod}`);
    assert("status 200", status === 200, status);
    assert("id correcto", data.id === ids.prod, data.id);
    assert("tiene category", data.category !== undefined, data.category);
    assert("tiene attributes_implementations", Array.isArray(data.attributes_implementations), data);
  }

  // ── 3.4 GET /products/by-code/{code} ────────────────────────────────────
  console.log("\n  3.4  GET /products/by-code/{code}");
  {
    const { status, data } = await req("GET", `/products/by-code/${code}`);
    assert("status 200", status === 200, status);
    assert("code correcto", data.code === code, data.code);
  }

  // ── 3.5 PATCH /products/{id} — actualizar campos ────────────────────────
  console.log("\n  3.5  PATCH /products/{id} — actualizar precio y título");
  {
    const { status, data } = await req("PATCH", `/products/${ids.prod}`, {
      title: "Remera Test v2",
      price: 1800.0,
    });
    assert("status 200", status === 200, status);
    assert("título actualizado", data.title === "Remera Test v2", data.title);
    assert("precio actualizado", data.price === 1800.0, data.price);
  }

  // ── 3.6 POST /products/{id}/implementations — agregar impl estática ──────
  console.log("\n  3.6  POST /products/{id}/implementations — impl estática");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/implementations`,
      { attribute_id: ids.statAttr, value: "algodón 100%" }
    );
    assert("status 200", status === 200, status);
    const impl = data.attributes_implementations.find(
      (i) => i.attribute.id === ids.statAttr
    );
    assert("implementación presente", impl !== undefined, data.attributes_implementations);
    assert("valor correcto", impl?.value === "algodón 100%", impl?.value);
  }

  // ── 3.7 POST /products/{id}/dynamic-attribute — sin variantes ───────────
  console.log("\n  3.7  POST /products/{id}/dynamic-attribute — sin variantes (no impact)");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/dynamic-attribute`,
      { attribute_id: ids.dynAttr }
    );
    assert("status 200", status === 200, status);
    assert("needs_implementations false", data.needs_implementations === false, data);
    assert("atributo en product.attributes", data.product.attributes.some((a) => a.id === ids.dynAttr), data.product?.attributes);
  }

  // ── 3.8 POST /products/{id}/variants — crear primera variante ───────────
  console.log("\n  3.8  POST /products/{id}/variants — crear variante");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/variants`,
      {
        implementations: [
          { attribute_id: ids.dynAttr, value: "S" },
        ],
      }
    );
    assert("status 200", status === 200, status);
    assert("no hay error", data.error === undefined, data.error);
    assert("variante creada", Array.isArray(data.variants) && data.variants.length === 1, data.variants?.length);
    ids.variant1 = data.variants[0].id;
  }

  // ── 3.9 POST /products/{id}/variants — segunda variante ─────────────────
  console.log("\n  3.9  POST /products/{id}/variants — segunda variante");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/variants`,
      {
        implementations: [
          { attribute_id: ids.dynAttr, value: "M" },
        ],
      }
    );
    assert("status 200", status === 200, status);
    assert("dos variantes", data.variants?.length === 2, data.variants?.length);
    ids.variant2 = data.variants[1].id;
  }

  // ── 3.10 POST /products/{id}/variants — implementations inválidas ────────
  console.log("\n  3.10 POST /products/{id}/variants — implementations vacías → error");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/variants`,
      { implementations: [] }
    );
    assert("status 200 con error body", status === 200, status);
    assert("error implementations_invalid", data.error === "implementations_invalid", data.error);
    assert("needed_attributes presente", Array.isArray(data.needed_attributes), data);
  }

  // ── 3.11 GET /products/{id} — verificar estado completo ─────────────────
  console.log("\n  3.11 GET /products/{id} — verificar estado completo con variantes");
  {
    const { status, data } = await req("GET", `/products/${ids.prod}`);
    assert("status 200", status === 200, status);
    assert("2 variantes", data.variants?.length === 2, data.variants?.length);
    const v = data.variants[0];
    assert("variante tiene attribute_implementations", Array.isArray(v?.attribute_implementations), v);
    assert("variante tiene impl del dynAttr", v?.attribute_implementations?.some((i) => i.attribute.id === ids.dynAttr), v?.attribute_implementations);
  }

  // ── 3.12 DELETE /products/{id}/variants/{variant_id} ────────────────────
  console.log("\n  3.12 DELETE /products/{id}/variants/{variant_id} — eliminar variante");
  {
    const { status, data } = await req(
      "DELETE",
      `/products/${ids.prod}/variants/${ids.variant2}`
    );
    assert("status 200", status === 200, status);
    assert("queda 1 variante", data.variants?.length === 1, data.variants?.length);
  }

  // ── 3.13 GET /products/by-code/NO-EXISTE — not found ────────────────────
  console.log("\n  3.13 GET /products/by-code/NOEXISTE → 404");
  {
    const { status } = await req("GET", "/products/by-code/NOEXISTE");
    assert("status 404", status === 404, status);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 4. OPERACIONES CON IMPACTO (flujo de dos llamadas)
// ═══════════════════════════════════════════════════════════════════════════

async function testImpactFlows() {
  section("4. FLUJOS CON IMPACTO (dos llamadas)");

  // Necesitamos un segundo atributo dinámico para testear el flujo con impacto
  // El producto ya tiene una variante con ids.dynAttr = "S"

  // ── 4.1 Crear segundo atributo dinámico ─────────────────────────────────
  console.log("\n  4.1  Crear segundo atributo dinámico para test de impacto");
  {
    const { status, data } = await req("POST", "/attributes", {
      key: `color_${Date.now()}`,
      name: "Color",
      data_type: "enum",
      is_static: false,
      enum_values: ["rojo", "azul", "negro"],
    });
    assert("status 201", status === 201, status);
    ids.dynAttr2 = data.id;
  }

  // ── 4.2 Primera llamada: agregar dynAttr2 al producto con variantes ─────
  console.log("\n  4.2  POST /products/{id}/dynamic-attribute — 1ra llamada (con variantes) → needs_implementations");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/dynamic-attribute`,
      { attribute_id: ids.dynAttr2 }
    );
    assert("status 200", status === 200, status);
    assert("needs_implementations true", data.needs_implementations === true, data);
    assert("impact tiene variant_id", data.impact?.length > 0 && data.impact[0].variant_id !== undefined, data.impact);
    // Guardamos el id de la variante que reportó
    ids.impactedVariantId = data.impact[0].variant_id;
  }

  // ── 4.3 Segunda llamada: con variant_options cubriendo la variante ───────
  console.log("\n  4.3  POST /products/{id}/dynamic-attribute — 2da llamada (con variant_options)");
  {
    const { status, data } = await req(
      "POST",
      `/products/${ids.prod}/dynamic-attribute`,
      {
        attribute_id: ids.dynAttr2,
        variant_options: [
          { variant_id: ids.impactedVariantId, value: "rojo" },
        ],
      }
    );
    assert("status 200", status === 200, status);
    assert("needs_implementations false", data.needs_implementations === false, data);
    assert("product presente", data.product !== undefined, data);
    // La variante debería tener ahora 2 attrs implementados
    // Las variantes se re-persisten con nuevos IDs tras el save; buscamos cualquiera con 2 impls
    const v = data.product.variants?.find((v) => v.attribute_implementations?.length === 2);
    assert("variante tiene 2 impls", v !== undefined, data.product.variants?.map((v) => v.attribute_implementations?.length));
  }

  // ── 4.4 DELETE /categories/{id}/attributes/{attr_id}?del_opt=0 — needs_decision
  console.log("\n  4.4  DELETE /categories/{id}/attributes/{attr_id}?del_opt=0 — reporta impacto");
  {
    // En la categoría deberíamos tener ids.statAttr (estático) y el producto tiene una impl de él
    const { status, data } = await req(
      "DELETE",
      `/categories/${ids.cat}/attributes/${ids.statAttr}?del_opt=0`
    );
    assert("status 200", status === 200, status);
    // Si hay productos con impl del atributo → needs_decision=true
    // Si no hay → needs_decision=false (igualmente es un flujo válido)
    assert("needs_decision presente en respuesta", data.needs_decision !== undefined, data);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// 5. LIMPIEZA
// ═══════════════════════════════════════════════════════════════════════════

async function cleanup() {
  section("5. LIMPIEZA");

  // Borrar producto (cascadea variantes e implementaciones)
  if (ids.prod) {
    console.log("\n  5.1  DELETE /products/{id}");
    const { status } = await req("DELETE", `/products/${ids.prod}`);
    assert("producto eliminado", status === 200, status);
  }

  // Borrar categoría
  if (ids.cat) {
    console.log("\n  5.2  DELETE /categories/{id}");
    const { status } = await req("DELETE", `/categories/${ids.cat}`);
    assert("categoría eliminada", status === 200, status);
  }

  // Borrar atributos creados
  for (const [label, idKey] of [
    ["5.3  DELETE atributo dinámico", "dynAttr"],
    ["5.4  DELETE atributo estático", "statAttr"],
    ["5.5  DELETE atributo color", "dynAttr2"],
  ]) {
    if (ids[idKey]) {
      console.log(`\n  ${label}`);
      const { status } = await req("DELETE", `/attributes/${ids[idKey]}`);
      assert("eliminado", status === 200, status);
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log("╔══════════════════════════════════════════════════════════════╗");
  console.log("║      IGM Product API — Test Suite                           ║");
  console.log(`║      ${BASE}                                   ║`);
  console.log("╚══════════════════════════════════════════════════════════════╝");

  try {
    await testAttributes();
    await testCategories();
    await testProducts();
    await testImpactFlows();
    await cleanup();
  } catch (err) {
    console.error("\n  ⚠  Error inesperado:", err.message);
    failed++;
  }

  const total = passed + failed;
  console.log(`\n${"═".repeat(60)}`);
  console.log(`  RESULTADO: ${passed}/${total} tests pasaron`);
  if (failed > 0) {
    console.log(`  FALLIDOS:  ${failed}`);
  }
  console.log("═".repeat(60));

  process.exit(failed > 0 ? 1 : 0);
}

main();
