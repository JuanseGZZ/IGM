// Two operations only. Swap bodies with fetch() when backend is ready.
// bring → returns { products, brands }
// save  → persists { products, brands } (attributes live inside products)
const API = {
    bring: ()      => Promise.resolve(LocalDB.load()),
    save:  (state) => { LocalDB.save(state); return Promise.resolve(); }
};
