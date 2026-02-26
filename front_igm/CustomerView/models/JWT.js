export class JWT {

    constructor(at = null, rt = null) {
        this.at = at;
        this.rt = rt;
    }

    toJson() {
        return {
            at: this.at,
            rt: this.rt
        };
    }

    static fromJson(json) {
        if (!json) return null;
        return new JWT(json.at ?? null, json.rt ?? null);
    }
}