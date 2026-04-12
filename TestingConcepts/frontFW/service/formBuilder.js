/**
 * formBuilder.js — Construcción dinámica de formularios en el DOM
 *
 * Recibe un container (div), un schema de lo que hay que completar,
 * y un callback que se invoca con los datos ya procesados.
 *
 * Funciones exportadas:
 *   buildDynamicImplForm(container, { attribute, impact }, onSubmit)
 *     → para cuando needs_implementations=true en atributo dinámico
 *       impact: [{product_id, product_code, variants:[{variant_id}]}]
 *       onSubmit: (implementations:[{product_id, variants:[{variant_id, value}]}]) => void
 *
 *   buildStaticImplForm(container, { attribute, impact }, onSubmit)
 *     → para cuando needs_implementations=true en atributo estático
 *       impact: [{product_id, product_code}]
 *       onSubmit: (implementations:[{product_id, value}]) => void
 *
 *   buildDecisionForm(container, { impact, hasOptTwo }, onDecision)
 *     → para cuando needs_decision=true (del_attribute)
 *       onDecision: (del_opt: 1|2) => void
 *
 *   buildVariantForm(container, neededAttributes, onSubmit)
 *     → para crear una variante cuando implementations_invalid
 *       onSubmit: (implementations:[{attribute_id, value}]) => void
 *
 *   buildGenericForm(container, schema, defaults, onSubmit)
 *     → formulario genérico iterando un schema de campos
 *       schema: { fieldKey: { label, type, options?, required?, placeholder? } }
 *       onSubmit: (data: Object) => void
 *
 *   buildChangeParentDecisionForm(container, { impact }, onDecision)
 *     → para cuando needs_decision=true al cambiar el padre de una categoría
 *       impact: [{attribute_key, attribute_name, is_static, affected_products:[{product_id, product_code}]}]
 *       onDecision: (del_opt: 1|2) => void
 *
 *   buildChangeParentImplForm(container, impactWithAttrs, onSubmit)
 *     → para cuando needs_implementations=true al cambiar el padre
 *       impactWithAttrs: [{attribute_key, attribute_name, is_static, data_type, enum_values, products}]
 *       products para estáticos: [{product_id, product_code}]
 *       products para dinámicos: [{product_id, product_code, variants:[{variant_id}]}]
 *       onSubmit: (implementations: { attr_key: [...] }) => void
 */

// ── helpers de DOM ────────────────────────────────────────────────────────────

/**
 * Crea un elemento HTML con atributos y children.
 * @param {string}   tag
 * @param {object}   [attrs]    Atributos. "class" → className. "onXxx" → addEventListener.
 * @param {...*}     children   Strings o HTMLElements
 */
function el(tag, attrs = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class")        e.className = v;
    else if (k === "style")   Object.assign(e.style, v);
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else                      e.setAttribute(k, v);
  }
  for (const child of children.flat()) {
    if (typeof child === "string")
      e.appendChild(document.createTextNode(child));
    else if (child instanceof HTMLElement)
      e.appendChild(child);
  }
  return e;
}

/** Limpia el contenido del container */
function clear(container) {
  container.innerHTML = "";
}

/** Crea un <label> */
function lbl(text) {
  return el("label", { class: "igm-label" }, text);
}

/** Crea un <hN> con clase igm-title */
function ttl(text, level = 3) {
  return el(`h${level}`, { class: "igm-title" }, text);
}

/** Crea un div de sección */
function sec(...cls) {
  return el("div", { class: ["igm-section", ...cls].filter(Boolean).join(" ") });
}

/**
 * Crea el input/select adecuado según el data_type del atributo.
 * @param {{ data_type, enum_values, name }} attribute
 * @param {string} name   Valor del atributo name del input
 * @returns {HTMLInputElement|HTMLSelectElement}
 */
function makeInput(attribute, name) {
  switch (attribute.data_type) {
    case "enum": {
      const s = el("select", { name, class: "igm-select" });
      for (const v of attribute.enum_values ?? []) {
        const o = el("option", { value: v }, v);
        s.appendChild(o);
      }
      return s;
    }
    case "boolean": {
      const s = el("select", { name, class: "igm-select" });
      for (const [v, t] of [["true", "Sí (true)"], ["false", "No (false)"]]) {
        s.appendChild(el("option", { value: v }, t));
      }
      return s;
    }
    case "number":
      return el("input", { type: "number", name, class: "igm-input",
        placeholder: `Número para ${attribute.name}`, step: "any" });
    default: // text
      return el("input", { type: "text", name, class: "igm-input",
        placeholder: `Valor de ${attribute.name}` });
  }
}

/** Parsea el valor crudo del input al tipo real. */
function parseValue(data_type, raw) {
  if (data_type === "number")  return parseFloat(raw);
  if (data_type === "boolean") return raw === "true";
  return raw;
}

// ── formularios de implementación ────────────────────────────────────────────

/**
 * Formulario para completar implementaciones de un atributo DINÁMICO
 * sobre las variantes de uno o varios productos.
 *
 * Muestra:
 *   [Título: nombre del atributo]
 *   [Hint: tipo / valores posibles]
 *   Para cada producto:
 *     [Label: Producto REMERA-001]
 *     Para cada variante:
 *       [Label: Variante #10]   [input/select]
 *   [Botón: Confirmar]
 *
 * @param {HTMLElement} container
 * @param {object}      schema
 * @param {object}      schema.attribute    AttributeDTO (con data_type, enum_values, name)
 * @param {Array}       schema.impact       [{product_id, product_code, variants:[{variant_id}]}]
 * @param {Function}    onSubmit
 *   onSubmit(implementations: [{product_id, variants:[{variant_id, value}]}])
 */
export function buildDynamicImplForm(container, { attribute, impact }, onSubmit) {
  clear(container);

  // mapa de inputs: { product_id, variant_id, inputEl }
  const inputMap = [];

  const form = el("form", {
    class: "igm-form igm-form--dynamic",
    onsubmit: (e) => {
      e.preventDefault();
      // agrupar por product_id
      const implementations = inputMap.reduce((acc, { product_id, variant_id, inputEl }) => {
        const value = parseValue(attribute.data_type, inputEl.value);
        let entry = acc.find((a) => a.product_id === product_id);
        if (!entry) { entry = { product_id, variants: [] }; acc.push(entry); }
        entry.variants.push({ variant_id, value });
        return acc;
      }, []);
      onSubmit(implementations);
    },
  });

  form.appendChild(ttl(`Completar: ${attribute.name}`, 3));
  form.appendChild(
    el("p", { class: "igm-hint" },
      `Tipo: ${attribute.data_type}` +
      (attribute.data_type === "enum"
        ? ` — Valores posibles: ${(attribute.enum_values ?? []).join(", ")}`
        : "")
    )
  );

  for (const prod of impact) {
    const prodSec = sec("igm-product-section");
    prodSec.appendChild(
      ttl(`Producto: ${prod.product_code} (id: ${prod.product_id})`, 4)
    );

    for (const variant of prod.variants) {
      const row = sec("igm-variant-row");
      row.appendChild(lbl(`Variante #${variant.variant_id}`));
      const inp = makeInput(attribute, `v_${prod.product_id}_${variant.variant_id}`);
      row.appendChild(inp);
      prodSec.appendChild(row);
      inputMap.push({ product_id: prod.product_id, variant_id: variant.variant_id, inputEl: inp });
    }

    form.appendChild(prodSec);
  }

  form.appendChild(
    el("button", { type: "submit", class: "igm-btn igm-btn--primary" }, "Confirmar")
  );
  container.appendChild(form);
}

/**
 * Formulario para completar implementaciones de un atributo ESTÁTICO
 * sobre productos (no variantes).
 *
 * Muestra:
 *   [Título: nombre del atributo]
 *   [Hint: tipo / valores posibles]
 *   Para cada producto:
 *     [Label: REMERA-001 (id:1)]  [input/select]
 *   [Botón: Confirmar]
 *
 * @param {HTMLElement} container
 * @param {object}      schema
 * @param {object}      schema.attribute    AttributeDTO
 * @param {Array}       schema.impact       [{product_id, product_code}]
 * @param {Function}    onSubmit
 *   onSubmit(implementations: [{product_id, value}])
 */
export function buildStaticImplForm(container, { attribute, impact }, onSubmit) {
  clear(container);

  const inputMap = []; // { product_id, inputEl }

  const form = el("form", {
    class: "igm-form igm-form--static",
    onsubmit: (e) => {
      e.preventDefault();
      const implementations = inputMap.map(({ product_id, inputEl }) => ({
        product_id,
        value: parseValue(attribute.data_type, inputEl.value),
      }));
      onSubmit(implementations);
    },
  });

  form.appendChild(ttl(`Completar: ${attribute.name}`, 3));
  form.appendChild(
    el("p", { class: "igm-hint" },
      `Tipo: ${attribute.data_type}` +
      (attribute.data_type === "enum"
        ? ` — Valores posibles: ${(attribute.enum_values ?? []).join(", ")}`
        : "")
    )
  );

  for (const prod of impact) {
    const row = sec("igm-product-row");
    row.appendChild(lbl(`${prod.product_code} (id: ${prod.product_id})`));
    const inp = makeInput(attribute, `p_${prod.product_id}`);
    row.appendChild(inp);
    form.appendChild(row);
    inputMap.push({ product_id: prod.product_id, inputEl: inp });
  }

  form.appendChild(
    el("button", { type: "submit", class: "igm-btn igm-btn--primary" }, "Confirmar")
  );
  container.appendChild(form);
}

/**
 * Formulario de decisión para cuando needs_decision=true al eliminar un atributo.
 *
 * Muestra la lista de productos afectados y botones:
 *   [ Eliminar implementaciones huérfanas (del_opt=1) ]
 *   [ Migrar atributo al producto         (del_opt=2) ]   ← solo si hasOptTwo
 *
 * @param {HTMLElement} container
 * @param {object}      schema
 * @param {Array}       schema.impact       [{product_id, product_code}]
 * @param {boolean}     [schema.hasOptTwo]  true si del_opt=2 está disponible
 * @param {Function}    onDecision          (del_opt: 1|2) => void
 */
export function buildDecisionForm(container, { impact, hasOptTwo = true }, onDecision) {
  clear(container);

  const wrap = sec("igm-decision");
  wrap.appendChild(ttl("Acción requerida", 3));
  wrap.appendChild(
    el("p", { class: "igm-hint" },
      "Los siguientes productos quedarían sin cobertura del atributo:"
    )
  );

  const list = el("ul", { class: "igm-impact-list" });
  for (const p of impact) {
    list.appendChild(
      el("li", { class: "igm-impact-item" }, `${p.product_code} (id: ${p.product_id})`)
    );
  }
  wrap.appendChild(list);

  const btnRow = sec("igm-btn-row");

  btnRow.appendChild(
    el("button", {
      type: "button",
      class: "igm-btn igm-btn--danger",
      onclick: () => onDecision(1),
    }, "Eliminar implementaciones huérfanas")
  );

  if (hasOptTwo) {
    btnRow.appendChild(
      el("button", {
        type: "button",
        class: "igm-btn igm-btn--warning",
        onclick: () => onDecision(2),
      }, "Migrar atributo al producto")
    );
  }

  wrap.appendChild(btnRow);
  container.appendChild(wrap);
}

/**
 * Formulario para crear una variante dado los atributos que necesita cubrir.
 * Se usa cuando createVariant recibe error "implementations_invalid".
 *
 * Muestra para cada atributo:
 *   [Label: Nombre (tipo)]   [input/select]
 * [Botón: Crear variante]
 *
 * @param {HTMLElement}  container
 * @param {AttributeDTO[]} neededAttributes   Lista de atributos que necesita la variante
 * @param {Function}     onSubmit
 *   onSubmit(implementations: [{attribute_id, value}])
 */
export function buildVariantForm(container, neededAttributes, onSubmit) {
  clear(container);

  const inputMap = []; // { attribute_id, data_type, inputEl }

  const form = el("form", {
    class: "igm-form igm-form--variant",
    onsubmit: (e) => {
      e.preventDefault();
      const implementations = inputMap.map(({ attribute_id, data_type, inputEl }) => ({
        attribute_id,
        value: parseValue(data_type, inputEl.value),
      }));
      onSubmit(implementations);
    },
  });

  form.appendChild(ttl("Nueva variante", 3));
  form.appendChild(
    el("p", { class: "igm-hint" },
      "Completá todos los atributos para crear la variante."
    )
  );

  for (const attr of neededAttributes) {
    const row = sec("igm-attr-row");
    row.appendChild(
      lbl(`${attr.name}${attr.enum_values?.length ? " (" + attr.enum_values.join(", ") + ")" : " (" + attr.data_type + ")"}`)
    );
    const inp = makeInput(attr, `attr_${attr.id}`);
    row.appendChild(inp);
    form.appendChild(row);
    inputMap.push({ attribute_id: attr.id, data_type: attr.data_type, inputEl: inp });
  }

  form.appendChild(
    el("button", { type: "submit", class: "igm-btn igm-btn--primary" }, "Crear variante")
  );
  container.appendChild(form);
}

/**
 * Formulario genérico que itera un schema de campos y construye el form en el container.
 *
 * Útil para formularios de creación/edición de cualquier entidad (Producto, Categoría, etc.)
 *
 * @param {HTMLElement} container
 * @param {object}      schema    Mapa de campos con su configuración:
 *   {
 *     fieldKey: {
 *       label:        string,               // Texto del label
 *       type:         "text"|"number"|"textarea"|"select"|"boolean",
 *       required:     boolean,              // Agrega " *" al label
 *       placeholder:  string,              // Placeholder del input
 *       options:      [{value, label}],    // Para type="select"
 *     }
 *   }
 * @param {object}   defaults   Valores iniciales (para edición). { fieldKey: value }
 * @param {Function} onSubmit   (data: { fieldKey: value }) => void
 *
 * Ejemplo de uso:
 *   buildGenericForm(div, {
 *     code:        { label: "Código",      type: "text",   required: true },
 *     title:       { label: "Título",      type: "text",   required: true },
 *     price:       { label: "Precio",      type: "number", required: true },
 *     description: { label: "Descripción", type: "textarea" },
 *     category_id: { label: "Categoría",   type: "select",
 *                    options: cats.map(c => ({ value: c.id, label: c.name })) },
 *   }, {}, (data) => ProductService.create(data));
 */
export function buildGenericForm(container, schema, defaults = {}, onSubmit) {
  clear(container);

  const inputMap = {}; // { fieldKey: inputEl }

  const form = el("form", {
    class: "igm-form igm-form--generic",
    onsubmit: (e) => {
      e.preventDefault();
      const data = {};
      for (const [key, inputEl] of Object.entries(inputMap)) {
        const def = schema[key];
        const raw = inputEl.value;
        if      (def.type === "number")  data[key] = parseFloat(raw);
        else if (def.type === "boolean") data[key] = raw === "true";
        else                             data[key] = raw;
      }
      onSubmit(data);
    },
  });

  for (const [key, def] of Object.entries(schema)) {
    const row = sec("igm-field-row");

    // label
    row.appendChild(lbl(def.label + (def.required ? " *" : "")));

    // input/textarea/select
    let inp;

    if (def.type === "textarea") {
      inp = el("textarea", {
        name: key,
        class: "igm-textarea",
        placeholder: def.placeholder ?? "",
      });
      if (defaults[key] != null) inp.value = defaults[key];

    } else if (def.type === "select") {
      inp = el("select", { name: key, class: "igm-select" });
      for (const opt of def.options ?? []) {
        const o = el("option", { value: opt.value }, String(opt.label ?? opt.value));
        if (String(defaults[key]) === String(opt.value)) o.selected = true;
        inp.appendChild(o);
      }

    } else if (def.type === "boolean") {
      inp = el("select", { name: key, class: "igm-select" });
      for (const [v, t] of [["true", "Sí (true)"], ["false", "No (false)"]]) {
        const o = el("option", { value: v }, t);
        if (String(defaults[key]) === v) o.selected = true;
        inp.appendChild(o);
      }

    } else {
      inp = el("input", {
        type: def.type ?? "text",
        name: key,
        class: "igm-input",
        placeholder: def.placeholder ?? "",
      });
      if (defaults[key] != null) inp.value = defaults[key];
    }

    row.appendChild(inp);
    form.appendChild(row);
    inputMap[key] = inp;
  }

  form.appendChild(
    el("button", { type: "submit", class: "igm-btn igm-btn--primary" }, "Guardar")
  );
  container.appendChild(form);
}

/**
 * Formulario de decisión para cuando needs_decision=true al cambiar el padre
 * de una categoría. Muestra los atributos que quedarían huérfanos y ofrece:
 *   del_opt=1 → inyectar esos atributos directamente en la categoría
 *   del_opt=2 → eliminar las implementaciones huérfanas de los productos
 *
 * @param {HTMLElement} container
 * @param {object}      schema
 * @param {Array}       schema.impact
 *   [{attribute_key, attribute_name, is_static, affected_products:[{product_id, product_code}]}]
 * @param {Function}    onDecision   (del_opt: 1|2) => void
 */
export function buildChangeParentDecisionForm(container, impact, onDecision) {
  clear(container);

  const wrap = sec("igm-decision");
  wrap.appendChild(ttl("Atributos huérfanos al cambiar padre", 3));
  wrap.appendChild(
    el("p", { class: "igm-hint" },
      "Al cambiar el padre, los siguientes atributos heredados quedarían sin cobertura en los productos:"
    )
  );

  for (const attrInfo of impact) {
    const attrSec = sec("igm-attr-block");
    attrSec.appendChild(
      ttl(`${attrInfo.attribute_name} (${attrInfo.is_static ? "estático" : "dinámico"})`, 4)
    );

    const list = el("ul", { class: "igm-impact-list" });
    for (const p of attrInfo.affected_products ?? []) {
      list.appendChild(
        el("li", { class: "igm-impact-item" }, `${p.product_code} (id: ${p.product_id})`)
      );
    }
    attrSec.appendChild(list);
    wrap.appendChild(attrSec);
  }

  const btnRow = sec("igm-btn-row");
  btnRow.appendChild(
    el("button", {
      type: "button",
      class: "igm-btn igm-btn--warning",
      onclick: () => onDecision(1),
    }, "Inyectar en la categoría")
  );
  btnRow.appendChild(
    el("button", {
      type: "button",
      class: "igm-btn igm-btn--danger",
      onclick: () => onDecision(2),
    }, "Eliminar implementaciones huérfanas")
  );

  wrap.appendChild(btnRow);
  container.appendChild(wrap);
}

/**
 * Formulario para completar implementaciones cuando needs_implementations=true
 * al cambiar el padre. El nuevo padre tiene atributos que los productos
 * descendientes no cubren aún.
 *
 * Muestra cada atributo con sus productos (y variantes si es dinámico).
 *
 * @param {HTMLElement} container
 * @param {Array}       impactWithAttrs
 *   [{attribute_key, attribute_name, is_static, data_type, enum_values, products}]
 *   products para estáticos: [{product_id, product_code}]
 *   products para dinámicos: [{product_id, product_code, variants:[{variant_id}]}]
 * @param {Function}    onSubmit
 *   onSubmit(implementations: { attr_key: [{product_id, value}] | [{product_id, variants:[{variant_id, value}]}] })
 */
export function buildChangeParentImplForm(container, impactWithAttrs, onSubmit) {
  clear(container);

  // { attribute_key, is_static, data_type, product_id, variant_id?, inputEl }
  const inputMap = [];

  const form = el("form", {
    class: "igm-form igm-form--change-parent",
    onsubmit: (e) => {
      e.preventDefault();
      const implementations = {};

      for (const entry of inputMap) {
        const value = parseValue(entry.data_type, entry.inputEl.value);
        if (!implementations[entry.attribute_key]) {
          implementations[entry.attribute_key] = [];
        }

        if (entry.is_static) {
          implementations[entry.attribute_key].push({ product_id: entry.product_id, value });
        } else {
          let prodEntry = implementations[entry.attribute_key]
            .find((p) => p.product_id === entry.product_id);
          if (!prodEntry) {
            prodEntry = { product_id: entry.product_id, variants: [] };
            implementations[entry.attribute_key].push(prodEntry);
          }
          prodEntry.variants.push({ variant_id: entry.variant_id, value });
        }
      }

      onSubmit(implementations);
    },
  });

  form.appendChild(ttl("Completar implementaciones para el nuevo padre", 3));
  form.appendChild(
    el("p", { class: "igm-hint" },
      "El nuevo padre aporta atributos que los productos descendientes no tienen aún. Completá los valores:"
    )
  );

  for (const attrInfo of impactWithAttrs) {
    const attrSec = sec("igm-attr-block");
    attrSec.appendChild(
      ttl(`${attrInfo.attribute_name} (${attrInfo.is_static ? "estático" : "dinámico"})`, 4)
    );

    const fakeAttr = {
      data_type:   attrInfo.data_type,
      enum_values: attrInfo.enum_values,
      name:        attrInfo.attribute_name,
    };

    for (const prod of attrInfo.products) {
      if (attrInfo.is_static) {
        const row = sec("igm-product-row");
        row.appendChild(lbl(`${prod.product_code} (id: ${prod.product_id})`));
        const inp = makeInput(fakeAttr, `cp_${attrInfo.attribute_key}_p${prod.product_id}`);
        row.appendChild(inp);
        attrSec.appendChild(row);
        inputMap.push({
          attribute_key: attrInfo.attribute_key,
          is_static: true,
          data_type: attrInfo.data_type,
          product_id: prod.product_id,
          inputEl: inp,
        });
      } else {
        const prodSec = sec("igm-product-section");
        prodSec.appendChild(
          ttl(`Producto: ${prod.product_code} (id: ${prod.product_id})`, 5)
        );
        for (const variant of prod.variants ?? []) {
          const row = sec("igm-variant-row");
          row.appendChild(lbl(`Variante #${variant.variant_id}`));
          const inp = makeInput(
            fakeAttr,
            `cp_${attrInfo.attribute_key}_p${prod.product_id}_v${variant.variant_id}`
          );
          row.appendChild(inp);
          prodSec.appendChild(row);
          inputMap.push({
            attribute_key: attrInfo.attribute_key,
            is_static: false,
            data_type: attrInfo.data_type,
            product_id: prod.product_id,
            variant_id: variant.variant_id,
            inputEl: inp,
          });
        }
        attrSec.appendChild(prodSec);
      }
    }

    form.appendChild(attrSec);
  }

  form.appendChild(
    el("button", { type: "submit", class: "igm-btn igm-btn--primary" }, "Confirmar")
  );
  container.appendChild(form);
}
