import { Category, Product, Variant, Attribute, AttributeSet } from "./models.js";
import { Handler } from "./Handler.js";
import { CHART_TYPE } from "./charts.js";

// Gestor mantiene un árbol espejo de objetos de dominio y valida/analiza
// cada operación visual antes de que llegue al Handler.
//
// Cada método analyze* devuelve:
//   { ok, blocked, reason?, flow, inputs?, deletions? }
//
//   flow: "none" | "additive" | "destructive" | "mixed" | "blocked"
//   inputs:    [{ attr, label, dataType, options, hint, productId? }]
//   deletions: [{ label }]

export class Gestor {
  constructor(handler) {
    this.handler = handler;
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // MIRROR — construye instancias de dominio desde el árbol de charts
  // ═══════════════════════════════════════════════════════════════════════════

  buildMirror() {
    const cats     = new Map(); // chartId → Category
    const prods    = new Map(); // chartId → Product
    const vars     = new Map(); // chartId → Variant
    const catToId  = new Map(); // Category instance → chartId
    const prodToId = new Map(); // Product  instance → chartId

    const toAttr = (a) => {
      if (a instanceof Attribute) return a;
      const attr = new Attribute({ key: a.key, name: a.name, data_type: a.data_type, is_static: a.is_static ?? false, id: a.id ?? null });
      attr.enum_values = [...(a.enum_values ?? [])];
      return attr;
    };

    const walk = (chart, parentCat, parentProd) => {
      if (chart.chartType === "root") {
        chart.listaHijos.forEach(c => walk(c, null, null));
        return;
      }

      if (chart.chartType === CHART_TYPE.CATEGORY) {
        const attrs = (chart.model?.attributes ?? []).map(toAttr);
        const cat   = new Category({ name: chart.model?.name ?? "", id: chart.model?.id ?? null, attributes: attrs });
        if (parentCat) { cat.father_categorie = parentCat; parentCat.subcategories.push(cat); }
        cats.set(chart.id, cat);
        catToId.set(cat, chart.id);
        chart.listaHijos.forEach(c => walk(c, cat, null));

      } else if (chart.chartType === CHART_TYPE.PRODUCT) {
        if (!parentCat) return;
        const m    = chart.model ?? {};
        const prod = new Product({
          code:                       m.code        ?? `SKU-${chart.id}`,
          title:                      m.title       ?? "",
          price:                      m.price       ?? 0,
          description:                m.description ?? "",
          brand:                      m.brand       ?? "",
          id:                         m.id          ?? null,
          category:                   parentCat,
          attributes_implementations: m.attributes_implementations ?? [],
        });
        prods.set(chart.id, prod);
        prodToId.set(prod, chart.id);
        parentCat.products.push(prod);
        chart.listaHijos.forEach(c => walk(c, parentCat, prod));

      } else if (chart.chartType === CHART_TYPE.VARIANT) {
        if (!parentProd) return;
        const m    = chart.model ?? {};
        const vart = new Variant({ id: m.id ?? null, attribute_implementations: m.attribute_implementations ?? [] });
        vars.set(chart.id, vart);
        parentProd.variants.push(vart);
      }
    };

    walk(this.handler.root, null, null);
    return { cats, prods, vars, catToId, prodToId };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // VALIDACIÓN ESTRUCTURAL
  // ═══════════════════════════════════════════════════════════════════════════

  checkAdd(parentChartId, chartType) {
    const parent = Handler.findNode(this.handler.root, parentChartId);
    if (!parent) return { ok: false, blocked: true, reason: "Nodo padre no encontrado." };

    // Topología del árbol visual (reglas de estructura, no de negocio)
    if (chartType === CHART_TYPE.CATEGORY) {
      if (parent.chartType !== "root" && parent.chartType !== CHART_TYPE.CATEGORY)
        return { ok: false, blocked: true, reason: "Una categoría solo puede ser hija de otra categoría." };
    }
    if (chartType === CHART_TYPE.PRODUCT) {
      if (parent.chartType !== CHART_TYPE.CATEGORY)
        return { ok: false, blocked: true, reason: "Un producto solo puede ser hijo de una categoría." };
    }
    if (chartType === CHART_TYPE.VARIANT) {
      if (parent.chartType !== CHART_TYPE.PRODUCT)
        return { ok: false, blocked: true, reason: "Una variante solo puede ser hija de un producto." };
    }

    // Hijos exclusivos — delegado al dominio
    if (parent.chartType === CHART_TYPE.CATEGORY) {
      const { cats } = this.buildMirror();
      const cat = cats.get(parent.id);
      if (cat) {
        const reason = chartType === CHART_TYPE.CATEGORY ? cat.can_add_subcategory()
                     : chartType === CHART_TYPE.PRODUCT  ? cat.can_add_product()
                     : null;
        if (reason) return { ok: false, blocked: true, reason };
      }
    }

    return { ok: true, blocked: false };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // ANÁLISIS DE IMPACTO
  // ═══════════════════════════════════════════════════════════════════════════

  // Analiza agregar un producto a una categoría.
  // Retorna los atributos estáticos heredados que el producto debe implementar.
  analyzeAddProduct(parentCategoryChartId) {
    const structural = this.checkAdd(parentCategoryChartId, CHART_TYPE.PRODUCT);
    if (!structural.ok) return { ...structural, flow: "blocked" };

    const { cats } = this.buildMirror();
    const cat = cats.get(parentCategoryChartId);
    if (!cat) return { ok: true, blocked: false, flow: "none", inputs: [] };

    const staticAttrs = [...cat.get_full_attr_set().values()].filter(a => a.is_static);
    if (staticAttrs.length === 0) return { ok: true, blocked: false, flow: "none", inputs: [] };

    const inputs = staticAttrs.map(a => ({
      attr:     a,
      label:    a.name,
      dataType: a.data_type,
      options:  a.enum_values ?? [],
      hint:     a.key,
    }));
    return { ok: true, blocked: false, flow: "additive", inputs };
  }

  // Analiza agregar una variante a un producto.
  // Retorna los atributos dinámicos heredados que la variante debe implementar.
  analyzeAddVariant(parentProductChartId) {
    const structural = this.checkAdd(parentProductChartId, CHART_TYPE.VARIANT);
    if (!structural.ok) return { ...structural, flow: "blocked" };

    const { prods } = this.buildMirror();
    const prod = prods.get(parentProductChartId);
    if (!prod) return { ok: true, blocked: false, flow: "none", inputs: [] };

    const dynAttrs = [...prod.category.get_full_attr_set().values()].filter(a => !a.is_static);
    if (dynAttrs.length === 0) return {
      ok:      false,
      blocked: true,
      reason:  "No hay atributos de variante en la familia de este producto. Agregá un atributo de variante a alguna categoría ancestral antes de crear una variante.",
      flow:    "blocked",
    };

    const inputs = dynAttrs.map(a => ({
      attr:     a,
      label:    a.name,
      dataType: a.data_type,
      options:  a.enum_values ?? [],
      hint:     a.key,
    }));
    return { ok: true, blocked: false, flow: "additive", inputs };
  }

  // Analiza agregar un atributo a una categoría (desde el modal).
  // Retorna qué productos en el subárbol necesitan implementarlo.
  analyzeAddAttribute(categoryChartId, attrPlain) {
    const { cats, prodToId } = this.buildMirror();
    const cat = cats.get(categoryChartId);
    if (!cat) return { ok: true, blocked: false, flow: "none", affected: [], inputs: [] };

    const attr = new Attribute({
      key:       attrPlain.key,
      name:      attrPlain.name,
      data_type: attrPlain.data_type,
      is_static: attrPlain.is_static ?? false,
      id:        attrPlain.id ?? null,
    });
    attr.enum_values = [...(attrPlain.enum_values ?? [])];

    // Atributos dinámicos: impactan variantes ya existentes, pero solo las de
    // productos que no estén cubiertos por una categoría intermedia que ya defina el attr.
    if (!attr.is_static) {
      const impacts = cat.compute_impact(new AttributeSet([attr]));
      const variantInputs = [];
      for (const [, products] of impacts) {
        for (const prod of products) {
          const cid = prodToId.get(prod);
          if (cid == null) continue;
          const prodChart = Handler.findNode(this.handler.root, cid);
          if (!prodChart) continue;
          for (const varChart of prodChart.listaHijos) {
            if (varChart.chartType !== CHART_TYPE.VARIANT) continue;
            variantInputs.push({
              attr,
              label:     `Variante #${varChart.id} (${prodChart.label}): ${attr.name}`,
              dataType:  attr.data_type,
              options:   attr.enum_values ?? [],
              hint:      attr.key,
              variantId: varChart.id,
            });
          }
        }
      }
      if (variantInputs.length === 0) return { ok: true, blocked: false, flow: "none", affected: [], inputs: [] };
      return { ok: true, blocked: false, flow: "additive", affected: [], inputs: variantInputs };
    }

    const impacts = cat.impact_on_add_attribute(attr);
    if (impacts.length === 0) return { ok: true, blocked: false, flow: "none", affected: [], inputs: [] };

    const affected = [];
    const inputs   = [];
    for (const [, products] of impacts) {
      for (const prod of products) {
        const cid   = prodToId.get(prod);
        const chart = cid != null ? Handler.findNode(this.handler.root, cid) : null;
        const label = chart?.label ?? prod.title ?? prod.code;
        affected.push({ chartId: cid, label });
        inputs.push({ attr, label: `${label}: ${attr.name}`, dataType: attr.data_type, options: attr.enum_values ?? [], hint: attr.key, productId: cid });
      }
    }

    if (affected.length === 0) return { ok: true, blocked: false, flow: "none", affected: [], inputs: [] };
    return { ok: true, blocked: false, flow: "additive", affected, inputs };
  }

  // Analiza quitar un atributo de una categoría (desde el modal).
  // Retorna qué productos y variantes perderán su implementación,
  // respetando el shielding de categorías intermedias que definan el mismo attr.
  analyzeRemoveAttribute(categoryChartId, attrPlain) {
    const attrKey  = attrPlain.key;
    const catChart = Handler.findNode(this.handler.root, categoryChartId);
    if (!catChart) return { ok: true, blocked: false, flow: "none", affected: [], affectedVariants: [], deletions: [] };

    const { cats, prodToId } = this.buildMirror();
    const cat = cats.get(categoryChartId);

    const affectedProds   = [];
    const affectedVars    = [];
    const variantsToDelete = [];

    const checkProd = (prodChart) => {
      const impls = prodChart.model?.attributes_implementations ?? [];
      if (impls.some(i => (i.attribute?.key ?? i.key) === attrKey))
        affectedProds.push({ id: prodChart.id, label: prodChart.label });

      for (const varChart of prodChart.listaHijos) {
        if (varChart.chartType !== CHART_TYPE.VARIANT) continue;
        const varImpls = varChart.model?.attribute_implementations ?? [];
        if (!varImpls.some(i => (i.attribute?.key ?? i.key) === attrKey)) continue;
        const label = `Variante #${varChart.id} (${prodChart.label})`;
        if (varImpls.length === 1) {
          variantsToDelete.push({ id: varChart.id, label });
        } else {
          affectedVars.push({ id: varChart.id, label });
        }
      }
    };

    if (cat) {
      const attr = new Attribute({
        key: attrKey, name: attrPlain.name ?? attrKey,
        data_type: attrPlain.data_type ?? "text",
        is_static: attrPlain.is_static ?? false,
        id: attrPlain.id ?? null,
      });
      const impacts = cat.compute_impact(new AttributeSet([attr]));
      for (const [, products] of impacts) {
        for (const prod of products) {
          const cid = prodToId.get(prod);
          if (cid == null) continue;
          const prodChart = Handler.findNode(this.handler.root, cid);
          if (prodChart) checkProd(prodChart);
        }
      }
    } else {
      this._walkProductCharts(catChart, checkProd);
    }

    const deletions = [
      ...affectedProds   .map(p => ({ label: `Implementación de "${attrPlain.name}" en ${p.label}`, attrKey, productId: p.id })),
      ...affectedVars    .map(v => ({ label: `Implementación de "${attrPlain.name}" en ${v.label}`, attrKey, variantId: v.id })),
      ...variantsToDelete.map(v => ({ label: `${v.label} — eliminada (quedaría sin implementaciones)` })),
    ];

    const total = affectedProds.length + affectedVars.length + variantsToDelete.length;
    return {
      ok:               true,
      blocked:          false,
      flow:             total > 0 ? "destructive" : "none",
      affected:         affectedProds,
      affectedVariants: affectedVars,
      variantsToDelete,
      deletions,
    };
  }

  // Verifica que una combinación de implementaciones no duplique una variante existente.
  // implementations: [{ attribute: { key } | key, value }]
  // Retorna { ok: true } o { ok: false, reason: string }.
  checkVariantUnique(parentProductChartId, implementations) {
    const sig = (impls) =>
      impls.map(i => `${i.attribute?.key ?? i.key}:${i.value}`).sort().join("|");

    const newSig    = sig(implementations);
    const prodChart = Handler.findNode(this.handler.root, parentProductChartId);
    if (!prodChart) return { ok: true };

    for (const varChart of prodChart.listaHijos) {
      if (varChart.chartType !== CHART_TYPE.VARIANT) continue;
      const existing = varChart.model?.attribute_implementations ?? [];
      if (sig(existing) === newSig)
        return { ok: false, reason: "Ya existe una variante con la misma combinación de valores." };
    }
    return { ok: true };
  }

  // Analiza eliminar un nodo: retorna todo lo que se borrará en cascada.
  analyzeDelete(chartId) {
    const chart = Handler.findNode(this.handler.root, chartId);
    if (!chart) return { ok: false, blocked: true, reason: "Nodo no encontrado." };

    const deletions = [];
    this._collectDeletions(chart, deletions);
    return { ok: true, blocked: false, flow: "destructive", deletions };
  }

  // Analiza mover un nodo: chequea estructura y calcula delta de atributos.
  analyzeMove(fromChartId, toChartId, mode) {
    const fromChart = Handler.findNode(this.handler.root, fromChartId);
    const toChart   = Handler.findNode(this.handler.root, toChartId);
    if (!fromChart || !toChart) return { ok: false, blocked: true, reason: "Nodo no encontrado." };

    if (mode === "child" && Handler.findNode(fromChart, toChartId))
      return { ok: false, blocked: true, reason: "No se puede mover una carta dentro de sí misma o de uno de sus descendientes." };

    const effectiveParentId = mode === "child" ? toChartId : toChart.idParent;
    const structural = this.checkAdd(effectiveParentId, fromChart.chartType);
    if (!structural.ok) return { ...structural, flow: "blocked" };

    if (fromChart.chartType === CHART_TYPE.CATEGORY)
      return this._analyzeMoveCategory(fromChartId, effectiveParentId);

    if (fromChart.chartType === CHART_TYPE.PRODUCT)
      return this._analyzeMoveProduct(fromChartId, effectiveParentId);

    return { ok: true, blocked: false, flow: "none" };
  }

  // ═══════════════════════════════════════════════════════════════════════════
  // PRIVADOS
  // ═══════════════════════════════════════════════════════════════════════════

  _walkProductCharts(chart, cb) {
    if (chart.chartType === CHART_TYPE.PRODUCT) { cb(chart); return; }
    chart.listaHijos.forEach(c => this._walkProductCharts(c, cb));
  }

  _collectDeletions(chart, list) {
    if (chart.chartType !== "root")
      list.push({ label: chart.label, type: chart.chartType, id: chart.id });
    chart.listaHijos.forEach(c => this._collectDeletions(c, list));
  }

  _analyzeMoveCategory(fromChartId, newParentChartId) {
    const { cats, prodToId } = this.buildMirror();
    const cat       = cats.get(fromChartId);
    if (!cat) return { ok: true, blocked: false, flow: "none" };
    const newParent = cats.get(newParentChartId) ?? null;

    let rawAdd = [], rawRem = [];
    try {
      if (!cat.father_categorie && newParent) {
        rawAdd = cat.impact_on_add_father(newParent);
      } else if (cat.father_categorie && !newParent) {
        rawRem = cat.impact_on_remove_father();
      } else if (cat.father_categorie && newParent) {
        [rawRem, rawAdd] = cat.impact_on_change_father(newParent);
      }
    } catch (e) {
      return { ok: false, blocked: true, reason: e.message };
    }

    const flatten = (raw) => raw.flatMap(([attrs, products]) =>
      [...attrs.values()].flatMap(attr =>
        products.map(prod => {
          const cid   = prodToId.get(prod);
          const chart = cid != null ? Handler.findNode(this.handler.root, cid) : null;
          return { attr, productLabel: chart?.label ?? prod.title, productId: cid };
        })
      )
    );

    const gains  = flatten(rawAdd);
    const losses = flatten(rawRem);

    const inputs    = gains.map(x => ({ attr: x.attr, label: `${x.productLabel}: ${x.attr.name}`, dataType: x.attr.data_type, options: x.attr.enum_values ?? [], hint: x.attr.key, productId: x.productId }));
    const deletions = losses.map(x => ({ label: `"${x.attr.name}" en ${x.productLabel}`, productId: x.productId, attrKey: x.attr.key }));

    const flow = inputs.length > 0 && deletions.length > 0 ? "mixed"
               : inputs.length > 0                         ? "additive"
               : deletions.length > 0                      ? "destructive"
               : "none";

    return { ok: true, blocked: false, flow, inputs, deletions };
  }

  _analyzeMoveProduct(fromChartId, newParentCatChartId) {
    const { cats, prods } = this.buildMirror();
    const prod   = prods.get(fromChartId);
    const newCat = cats.get(newParentCatChartId);
    if (!prod || !newCat) return { ok: true, blocked: false, flow: "none" };

    // ── Atributos estáticos (implementaciones a nivel de producto) ────────────
    const [toAdd, toRemove] = prod.impact_on_change_category(newCat);
    const inputs    = [...toAdd.values()].map(a => ({
      attr: a, label: a.name, dataType: a.data_type, options: a.enum_values ?? [], hint: a.key,
    }));
    const deletions = [...toRemove.values()].map(a => ({
      label: `Implementación de "${a.name}" eliminada del producto`, attrKey: a.key,
    }));

    // ── Atributos dinámicos (implementaciones a nivel de variante) ────────────
    // Comparamos por key porque las instancias de Attribute vienen de mirrors distintos.
    const currentDynKeys = new Set(
      [...prod.category.get_full_attr_set().values()].filter(a => !a.is_static).map(a => a.key)
    );
    const newDynAttrs = [...newCat.get_full_attr_set().values()].filter(a => !a.is_static);
    const newDynKeys  = new Set(newDynAttrs.map(a => a.key));

    const dynKeysLost   = [...currentDynKeys].filter(k => !newDynKeys.has(k));
    const dynAttrsGained = newDynAttrs.filter(a => !currentDynKeys.has(a.key));

    const prodChart = Handler.findNode(this.handler.root, fromChartId);
    if (prodChart) {
      const variantCharts = prodChart.listaHijos.filter(c => c.chartType === CHART_TYPE.VARIANT);

      // Destructivo: implementaciones de variante que quedan huérfanas en la nueva categoría
      for (const varChart of variantCharts) {
        const impls = varChart.model?.attribute_implementations ?? [];
        for (const key of dynKeysLost) {
          if (impls.some(i => (i.attribute?.key ?? i.key) === key)) {
            const name = impls.find(i => (i.attribute?.key ?? i.key) === key)?.attribute?.name ?? key;
            deletions.push({
              label:     `Implementación de "${name}" en Variante #${varChart.id}`,
              variantId: varChart.id,
              attrKey:   key,
            });
          }
        }
      }

      // Aditivo: variantes existentes que quedan incompletas por attrs nuevos requeridos
      for (const varChart of variantCharts) {
        for (const attr of dynAttrsGained) {
          inputs.push({
            attr,
            label:     `Variante #${varChart.id} — ${attr.name}`,
            dataType:  attr.data_type,
            options:   attr.enum_values ?? [],
            hint:      attr.key,
            variantId: varChart.id,
          });
        }
      }
    }

    const flow = inputs.length > 0 && deletions.length > 0 ? "mixed"
               : inputs.length > 0                         ? "additive"
               : deletions.length > 0                      ? "destructive"
               : "none";

    return { ok: true, blocked: false, flow, inputs, deletions };
  }
}
