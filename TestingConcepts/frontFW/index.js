/**
 * frontFW — Barrel export principal
 *
 * Importa todo el framework desde un único punto:
 *
 *   import { ProductService, CategoryService, ProductDTO, Config } from "./frontFW/index.js";
 */

export { Config }                    from "./config/config.js";

export {
  AttributeDTO,
  AttributeImplementationDTO,
  VariantDTO,
  CategoryDTO,
  ProductDTO,
} from "./interfaceModels/index.js";

export {
  AttributeApi,
  CategoryApi,
  ProductApi,
  request,
  ApiError,
} from "./api/index.js";

export {
  AttributeService,
  CategoryService,
  ProductService,
  buildDynamicImplForm,
  buildStaticImplForm,
  buildDecisionForm,
  buildVariantForm,
  buildGenericForm,
} from "./service/index.js";
