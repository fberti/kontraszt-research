import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import polars as pl
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats

    return mo, np, pl, plt, stats


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # H3 – Napirend kijelölés (Agenda-setting)

    **Hipotézis:** Bizonyos kulcsszavak vagy személyek megjelenése időben
    korrelál a különböző portálok között, de a hozzájuk társított dinamika
    (szentiment, vizuális súly) portálspecifikus.

    ## Elemzési terv

    1. **Entitás-idősorok**: Melyik entitások jelennek meg leggyakrabban,
       és hogyan alakul napi említésszámuk portáltípusonként?
    2. **Portálok közti korreláció**: Az egyes entitások napi említésszáma
       mennyire korrelál a kormányközeli és független portálok között?
       (Pearson-korreláció + cross-correlation lag elemzés)
    3. **Portálspecifikus dinamika**: Ugyanazon entitás megjelenésekor eltérő-e
       a szentiment és a vizuális hangsúly a portáltípusok között?
    """)
    return


@app.cell
def _(pl):
    # adatelőkészítés

    GOV_PORTALS = [
        "Origo",
        "Magyar Nemzet",
        "PestiSracok",
        "Hirado.hu",
        "Ripost",
        "Metropol",
        "Mandiner",
    ]
    IND_PORTALS = [
        "Telex",
        "444.hu",
        "HVG",
        "ATV",
        "Magyar Hang",
        "24.hu",
        "Nepszava",
        "Valasz Online",
    ]

    _df_hd = pl.read_parquet("data/headlineDefinitions_2026-04-19.parquet")
    _df_llm = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    _df_hl = pl.read_parquet("data/headlines_2026-04-19.parquet")

    # Átlagos vizuális score kiszámítása
    """Mivel egy-egy címsorhoz több scrape pillanatkép is tartozhat 
     (különböző időpontokban lefotózva a címlapot), itt hashedId-nként 
     átlagolja a vizuális score-okat. 
     Ez a score a score_formula.md-ben leírt figyelemfelkeltési képlet 
     eredménye (betűméret, pozíció, terület, banner-vakság büntetés alapján)."""

    _df_vis = (
        _df_hl.select(["hashedId", "score"])
        .group_by("hashedId")
        .agg(pl.col("score").mean().alias("mean_score"))
    )

    _df_base = (
        _df_hd.join(
            _df_llm.select(
                ["hashedId", "sentiment_score", "sentiment", "entities", "label"]
            ),
            on="hashedId",
            how="left",
        )
        .join(_df_vis, on="hashedId", how="left")
        .with_columns(
            # Creation date (day granularity) – _creationTime is in ms
            pl.col("_creationTime")
            .cast(pl.Datetime("ms"))
            .dt.date()
            .alias("date"),
            # Portal type classification
            pl.when(pl.col("siteName").is_in(GOV_PORTALS))
            .then(pl.lit("Kormányközeli"))
            .when(pl.col("siteName").is_in(IND_PORTALS))
            .then(pl.lit("Független"))
            .otherwise(pl.lit("Egyéb"))
            .alias("portal_type"),
        )
    )

    # Minden portálhoz meghatározza a mean_score minimumát és maximumát 
    _site_stats = _df_base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("score_min"),
        pl.col("mean_score").max().alias("score_max"),
    )

    # a norm_score minden portálon belül 0 és 1 közé skálázódik
    df_normed = (
        _df_base.join(_site_stats, on="siteName", how="left")
        .with_columns(
            (
                (pl.col("mean_score") - pl.col("score_min"))
                / (pl.col("score_max") - pl.col("score_min") + 1e-9)
            ).alias("norm_score")
        )
        .drop(["score_min", "score_max"])
    )

    df_normed
    return GOV_PORTALS, IND_PORTALS, df_normed


@app.cell
def _(df_normed, pl):
    # entitások denormalizálása
    # egy címsorból, amelyhez 3 entitás tartozik, 3 sor lesz – minden más oszlop (siteName, sentiment_score, norm_score, date, portal_type stb.) megduplázódik:
    df_entities = (
        df_normed.filter(
            pl.col("entities").is_not_null() & (pl.col("entities") != "[]")
        )
        .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
        .with_columns(
            pl.col("entities")
            .str.strip_chars("[]")
            .str.replace_all('"', "")
            .str.split(", ")
            .alias("entity_list")
        )
        .explode("entity_list")
        .rename({"entity_list": "entity"})
        .filter(pl.col("entity").str.len_chars() > 1)  
    )

    df_entities
    return (df_entities,)


@app.cell
def _(df_entities, mo, pl):
    top_entities = (
        df_entities.group_by("entity")
        .agg(
            pl.len().alias("total_mentions"),
            pl.col("siteName").n_unique().alias("n_portals"),
            pl.col("portal_type").n_unique().alias("n_portal_types"),
        )
        .filter(pl.col("n_portal_types") == 2)  # appears in both types
        .sort("total_mentions", descending=True)
        .head(30)
    )

    mo.vstack(
        [
            mo.md(
                "## Top 30 entitás (mindkét portáltípusban megjelenik)"
            ),
            mo.ui.table(top_entities),
        ]
    )
    return (top_entities,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Csoporton belüli korreláció

    Vizsgáljuk meg, hogy az egyes portálok **egy csoporton
    belül** mennyire mozognak együtt:

    - Kormányközeli portálok egymás között szinkronban vannak-e?
    - Független portálok egymás között szinkronban vannak-e?

    Minden top entitásra kirajzoljuk az egyedi portálok napi említéseit,
    majd páronkénti Pearson-korrelációs hőtérképet mutatunk.
    """)
    return


@app.cell
def _(df_entities, pl, top_entities):
    top_entity_list = top_entities.head(15)["entity"].to_list()
    df_daily_site = (
        df_entities.filter(pl.col("entity").is_in(top_entity_list))
        .group_by(["entity", "siteName", "portal_type", "date"])
        .agg(pl.len().alias("mentions"))
        .sort(["entity", "siteName", "date"])
    )

    df_daily_site
    return df_daily_site, top_entity_list


@app.cell
def _(GOV_PORTALS, df_daily_site, pl, plt, top_entity_list):
    import itertools as _itertools

    _palette = [
        "#c0392b",
        "#f39c12",
        "#8e44ad",
        "#d35400",
        "#2c3e50",
        "#e74c3c",
        "#1abc9c",
    ]
    _entities_to_plot = top_entity_list[:8]
    _n = len(_entities_to_plot)
    _cols = 2
    _rows = (_n + 1) // _cols

    fig_ts_gov, axes_gov = plt.subplots(
        _rows, _cols, figsize=(15, 4.5 * _rows), sharex=True
    )
    axes_gov = axes_gov.flatten()

    for _i, _ent in enumerate(_entities_to_plot):
        _ax = axes_gov[_i]
        _color_cycle = _itertools.cycle(_palette)
        for _site in sorted(GOV_PORTALS):
            _sub = df_daily_site.filter(
                (pl.col("entity") == _ent) & (pl.col("siteName") == _site)
            ).sort("date")
            if _sub.height > 0:
                _ax.plot(
                    _sub["date"].to_list(),
                    _sub["mentions"].to_list(),
                    marker="o",
                    markersize=3,
                    alpha=0.75,
                    color=next(_color_cycle),
                    label=_site,
                )
            else:
                next(_color_cycle)

        _ax.set_title(_ent, fontsize=11, fontweight="bold")
        _ax.set_ylabel("Említések / nap")
        _ax.legend(fontsize=6, ncol=2, loc="upper right")
        _ax.grid(True, alpha=0.3)

    for _j in range(_n, len(axes_gov)):
        axes_gov[_j].set_visible(False)

    fig_ts_gov.suptitle(
        "Kormányközeli portálok – egyedi portálok napi említései",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fig_ts_gov.autofmt_xdate()
    fig_ts_gov.tight_layout()
    fig_ts_gov
    return


@app.cell
def _(IND_PORTALS, df_daily_site, pl, plt, top_entity_list):
    import itertools as _itertools

    _palette = [
        "#2980b9",
        "#e74c3c",
        "#f1c40f",
        "#8e44ad",
        "#1abc9c",
        "#e67e22",
        "#2ecc71",
        "#c0392b",
    ]
    _entities_to_plot = top_entity_list[:8]
    _n = len(_entities_to_plot)
    _cols = 2
    _rows = (_n + 1) // _cols

    fig_ts_ind, axes_ind = plt.subplots(
        _rows, _cols, figsize=(15, 4.5 * _rows), sharex=True
    )
    axes_ind = axes_ind.flatten()

    for _i, _ent in enumerate(_entities_to_plot):
        _ax = axes_ind[_i]
        _color_cycle = _itertools.cycle(_palette)
        for _site in sorted(IND_PORTALS):
            _sub = df_daily_site.filter(
                (pl.col("entity") == _ent) & (pl.col("siteName") == _site)
            ).sort("date")
            if _sub.height > 0:
                _ax.plot(
                    _sub["date"].to_list(),
                    _sub["mentions"].to_list(),
                    marker="o",
                    markersize=3,
                    alpha=0.75,
                    color=next(_color_cycle),
                    label=_site,
                )
            else:
                next(_color_cycle)

        _ax.set_title(_ent, fontsize=11, fontweight="bold")
        _ax.set_ylabel("Említések / nap")
        _ax.legend(fontsize=6, ncol=2, loc="upper right")
        _ax.grid(True, alpha=0.3)

    for _j in range(_n, len(axes_ind)):
        axes_ind[_j].set_visible(False)

    fig_ts_ind.suptitle(
        "Független portálok – egyedi portálok napi említései",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fig_ts_ind.autofmt_xdate()
    fig_ts_ind.tight_layout()
    fig_ts_ind
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Ez a cella azt vizsgálja, hogy **egy portálcsoporton belül** (kormányközeli / független) az egyes portálok mennyire **szinkronizáltan tudósítanak** – azaz napról napra hasonló entitásokat említenek-e.
    """)
    return


@app.cell
def _(GOV_PORTALS, IND_PORTALS, df_daily_site, np, pl, plt, stats):
    """
    Minden portálcsoport esetében számítsuk ki az összes legfontosabb entitás napi említéseinek összesített számát
    portálonként, majd számítsuk ki a portálok közötti páronkénti Pearson-korrelációt.
    Ez megmutatja, hogy egy csoporton belüli portálok ugyanazt a napirend-ritmust követik-e.
    """
    _all_dates = df_daily_site["date"].unique().sort()
    _date_range = pl.DataFrame({"date": _all_dates})

    def _build_corr_matrix(portals):
        # a napi említések összesített száma (az összes legfontosabb entitásra vonatkozóan) portálonként
        _agg = (
            df_daily_site.filter(pl.col("siteName").is_in(portals))
            .group_by(["siteName", "date"])
            .agg(pl.col("mentions").sum().alias("mentions"))
        )
        # portálonként egy oszlop, dátumonként egy sor
        _wide = _date_range.clone()
        _active_portals = []
        for _p in sorted(portals):
            _col = (
                _agg.filter(pl.col("siteName") == _p)
                .select(["date", "mentions"])
                .rename({"mentions": _p})
            )
            _wide = _wide.join(_col, on="date", how="left")
            if _wide[_p].sum() > 0:
                _active_portals.append(_p)
        _wide = _wide.fill_null(0).sort("date")

        """
        Minden portálpárra kiszámítja a Pearson-korrelációs együtthatót (r):
        - r ≈ 1 → a két portál napi említésszáma szorosan együtt mozog (ha az egyiknél sok említés van, a másiknál is)
        - r ≈ 0 → nincs lineáris kapcsolat
        - r ≈ -1 → ellentétesen mozognak (az egyik aktív napon a másik inaktív)
        """
        _n = len(_active_portals)
        _matrix = np.zeros((_n, _n))
        for _i in range(_n):
            for _j in range(_n):
                _a = _wide[_active_portals[_i]].to_numpy().astype(float)
                _b = _wide[_active_portals[_j]].to_numpy().astype(float)
            
                """
                Az `np.std > 0` ellenőrzés kiszűri a konstans (nulla varianciájú) idősorokat,
                ahol a Pearson-korreláció nem értelmezhető.
                """
                if np.std(_a) > 0 and np.std(_b) > 0:
                    _matrix[_i, _j], _ = stats.pearsonr(_a, _b)
                else:
                    _matrix[_i, _j] = 0.0
        return _active_portals, _matrix

    _gov_names, _gov_matrix = _build_corr_matrix(GOV_PORTALS)
    _ind_names, _ind_matrix = _build_corr_matrix(IND_PORTALS)

    fig_hm, (ax_hm_gov, ax_hm_ind) = plt.subplots(1, 2, figsize=(16, 7))

    # — Kormányközeli heatmap —
    _im1 = ax_hm_gov.imshow(_gov_matrix, vmin=-1, vmax=1, cmap="RdYlGn", aspect="auto")
    ax_hm_gov.set_xticks(range(len(_gov_names)))
    ax_hm_gov.set_yticks(range(len(_gov_names)))
    ax_hm_gov.set_xticklabels(_gov_names, rotation=45, ha="right", fontsize=8)
    ax_hm_gov.set_yticklabels(_gov_names, fontsize=8)
    ax_hm_gov.set_title(
        "Kormányközeli portálok\npáronkénti korreláció", fontsize=12, fontweight="bold"
    )
    for _i in range(len(_gov_names)):
        for _j in range(len(_gov_names)):
            ax_hm_gov.text(
                _j,
                _i,
                f"{_gov_matrix[_i, _j]:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if abs(_gov_matrix[_i, _j]) > 0.6 else "black",
            )
    plt.colorbar(_im1, ax=ax_hm_gov, fraction=0.046, pad=0.04)

    # — Független heatmap —
    _im2 = ax_hm_ind.imshow(_ind_matrix, vmin=-1, vmax=1, cmap="RdYlGn", aspect="auto")
    ax_hm_ind.set_xticks(range(len(_ind_names)))
    ax_hm_ind.set_yticks(range(len(_ind_names)))
    ax_hm_ind.set_xticklabels(_ind_names, rotation=45, ha="right", fontsize=8)
    ax_hm_ind.set_yticklabels(_ind_names, fontsize=8)
    ax_hm_ind.set_title(
        "Független portálok\npáronkénti korreláció", fontsize=12, fontweight="bold"
    )
    for _i in range(len(_ind_names)):
        for _j in range(len(_ind_names)):
            ax_hm_ind.text(
                _j,
                _i,
                f"{_ind_matrix[_i, _j]:.2f}",
                ha="center",
                va="center",
                fontsize=7,
                color="white" if abs(_ind_matrix[_i, _j]) > 0.6 else "black",
            )
    plt.colorbar(_im2, ax=ax_hm_ind, fraction=0.046, pad=0.04)

    fig_hm.suptitle(
        "Csoporton belüli napirend-szinkronitás\n(Pearson r – napi összes entitás-említés)",
        fontsize=13,
        fontweight="bold",
    )
    fig_hm.tight_layout()
    fig_hm
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    | Ami látható a heatmapen | Jelentése |
    |---|---|
    | Végig zöld, magas r értékekkel | A csoport portáljai **erősen szinkronizálnak** – ugyanazokat az entitásokat ugyanakkor említik |
    | Vegyes, alacsony r értékekkel | A portálok **önálló napirendet** követnek a csoporton belül is |
    | Egy sor/oszlop kitűnően zöld | Az adott portál különösen erősen korrelál a csoport többi tagjával |
    | Egy sor/oszlop inkább sárga/piros | Az adott portál „kilóg" a csoportból, eltérő napirenddel |

    A H3 hipotézis szempontjából ez a cella arra ad választ, hogy **a kormányközeli portálok belső koordinációja erősebb-e, mint a független portáloké** – ami központosított napirendkijelölésre (agenda-setting) utalna.
    """)
    return


@app.cell
def _(GOV_PORTALS, IND_PORTALS, df_daily_site, mo, np, pl, stats):

    _all_dates = df_daily_site["date"].unique().sort()
    _date_range = pl.DataFrame({"date": _all_dates})

    """
    Pearson korreláció mindkét csoportra, visszaadja a korrelációk átlagát és szórását
    - csak az átló feletti párokat számolja (nincs önkorreláció, ahol mindig 1.0 az eredmény és duplikátum)
    """
    def _mean_offdiag_corr(portals):
        _agg = (
            df_daily_site.filter(pl.col("siteName").is_in(portals))
            .group_by(["siteName", "date"])
            .agg(pl.col("mentions").sum().alias("mentions"))
        )
        _wide = _date_range.clone()
        _active = []
        for _p in sorted(portals):
            _col = (
                _agg.filter(pl.col("siteName") == _p)
                .select(["date", "mentions"])
                .rename({"mentions": _p})
            )
            _wide = _wide.join(_col, on="date", how="left")
            if _wide[_p].sum() > 0:
                _active.append(_p)
        _wide = _wide.fill_null(0).sort("date")

        _rs = []
        for _i in range(len(_active)):
            for _j in range(_i + 1, len(_active)):
                _a = _wide[_active[_i]].to_numpy().astype(float)
                _b = _wide[_active[_j]].to_numpy().astype(float)
                if np.std(_a) > 0 and np.std(_b) > 0:
                    _r, _ = stats.pearsonr(_a, _b)
                    _rs.append(_r)
        return np.mean(_rs) if _rs else 0.0, np.std(_rs) if _rs else 0.0

    _gov_mean, _gov_std = _mean_offdiag_corr(GOV_PORTALS)
    _ind_mean, _ind_std = _mean_offdiag_corr(IND_PORTALS)

    mo.md(f"""
    ### Csoporton belüli szinkronitás összefoglaló
    Melyik portálcsoportban erősebb a belső napirend-koordináció?

    | Csoport | Átlag páronkénti r | Szórás |
    |---|---|---|
    | Kormányközeli | **{_gov_mean:.3f}** | ±{_gov_std:.3f} |
    | Független | **{_ind_mean:.3f}** | ±{_ind_std:.3f} |

    {"✅ A kormányközeli portálok erősebben szinkronizálnak egymással, mint a függetlenek." if _gov_mean > _ind_mean + 0.05 else "🔵 A független portálok erősebben szinkronizálnak egymással, mint a kormányközeliek." if _ind_mean > _gov_mean + 0.05 else "≈ A két csoport hasonló mértékben szinkronizál belül."}
    Magasabb átlag r → a csoport portáljai koordináltabb napirendet mutatnak.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Melyik entitás (pl. Orbán, EU, NATO) az, amelyikről a csoport portáljai koordináltan tudósítanak, és melyikről nem?
    """)
    return


@app.cell
def _(GOV_PORTALS, IND_PORTALS, df_daily_site, np, pl, stats, top_entity_list):
    """
    Minden vezető entity esetében számítsuk ki a portálok közötti páronkénti Pearson-korrelációs együttható átlagát
    az egyes csoportokon belül. Ez megmutatja, mely entity-k járulnak hozzá a szinkronizált tudósításhoz
    a kormányközeli vagy a független táboron belül.
    """
    _all_dates = df_daily_site["date"].unique().sort()
    _date_range = pl.DataFrame({"date": _all_dates})

    def _entity_pairwise(entity, portals):
        _sub = (
            df_daily_site.filter(
                (pl.col("entity") == entity) & (pl.col("siteName").is_in(portals))
            )
            .group_by(["siteName", "date"])
            .agg(pl.col("mentions").sum().alias("mentions"))
        )
        _wide = _date_range.clone()
        _active = []
        for _p in sorted(portals):
            _col = (
                _sub.filter(pl.col("siteName") == _p)
                .select(["date", "mentions"])
                .rename({"mentions": _p})
            )
            _wide = _wide.join(_col, on="date", how="left")
            if _wide[_p].sum() > 0:
                _active.append(_p)
        _wide = _wide.fill_null(0).sort("date")

        _rs = []
        _ps = []
        for _i in range(len(_active)):
            for _j in range(_i + 1, len(_active)):
                _a = _wide[_active[_i]].to_numpy().astype(float)
                _b = _wide[_active[_j]].to_numpy().astype(float)
                if np.std(_a) > 0 and np.std(_b) > 0:
                    _r, _p = stats.pearsonr(_a, _b)
                    _rs.append(_r)
                    _ps.append(_p)
        if _rs:
            return float(np.mean(_rs)), float(np.mean(_ps)), len(_active)
        return None, None, len(_active)

    intra_gov_results = []
    intra_ind_results = []

    for _ent in top_entity_list:
        _r_gov, _p_gov, _n_gov = _entity_pairwise(_ent, GOV_PORTALS)
        if _r_gov is not None:
            intra_gov_results.append(
                {
                    "entity": _ent,
                    "mean_r": round(_r_gov, 3),
                    "mean_p": round(_p_gov, 4),
                    "n_portals": _n_gov,
                }
            )
        _r_ind, _p_ind, _n_ind = _entity_pairwise(_ent, IND_PORTALS)
        if _r_ind is not None:
            intra_ind_results.append(
                {
                    "entity": _ent,
                    "mean_r": round(_r_ind, 3),
                    "mean_p": round(_p_ind, 4),
                    "n_portals": _n_ind,
                }
            )

    df_intra_gov = pl.DataFrame(intra_gov_results).sort("mean_r", descending=True)
    df_intra_ind = pl.DataFrame(intra_ind_results).sort("mean_r", descending=True)
    return df_intra_gov, df_intra_ind


@app.cell
def _(df_intra_gov, df_intra_ind, plt):
    fig_intra_scatter, (ax_ig, ax_ii) = plt.subplots(1, 2, figsize=(16, 7))

    # ── Kormányközeli scatter ──
    _r = df_intra_gov["mean_r"].to_numpy()
    _p = df_intra_gov["mean_p"].to_numpy()
    _ent = df_intra_gov["entity"].to_list()
    _colors = ["#c0392b" if p < 0.05 else "#bdc3c7" for p in _p]

    ax_ig.scatter(_r, _p, c=_colors, s=80, edgecolors="k", linewidths=0.5, alpha=0.85)
    for _i, _e in enumerate(_ent):
        ax_ig.annotate(
            _e,
            (_r[_i], _p[_i]),
            fontsize=7,
            ha="left",
            xytext=(5, 3),
            textcoords="offset points",
        )
    ax_ig.axhline(0.05, color="red", linestyle="--", alpha=0.5, label="p = 0.05")
    ax_ig.set_xlabel("Átlag páronkénti Pearson r", fontsize=10)
    ax_ig.set_ylabel("Átlag p-érték", fontsize=10)
    ax_ig.set_title(
        "Kormányközeli portálok\nentitásonkénti belső korreláció",
        fontsize=12,
        fontweight="bold",
    )
    ax_ig.legend(fontsize=9)
    ax_ig.grid(True, alpha=0.3)

    # ── Független scatter ──
    _r2 = df_intra_ind["mean_r"].to_numpy()
    _p2 = df_intra_ind["mean_p"].to_numpy()
    _ent2 = df_intra_ind["entity"].to_list()
    _colors2 = ["#2980b9" if p < 0.05 else "#bdc3c7" for p in _p2]

    ax_ii.scatter(
        _r2, _p2, c=_colors2, s=80, edgecolors="k", linewidths=0.5, alpha=0.85
    )
    for _i, _e in enumerate(_ent2):
        ax_ii.annotate(
            _e,
            (_r2[_i], _p2[_i]),
            fontsize=7,
            ha="left",
            xytext=(5, 3),
            textcoords="offset points",
        )
    ax_ii.axhline(0.05, color="red", linestyle="--", alpha=0.5, label="p = 0.05")
    ax_ii.set_xlabel("Átlag páronkénti Pearson r", fontsize=10)
    ax_ii.set_ylabel("Átlag p-érték", fontsize=10)
    ax_ii.set_title(
        "Független portálok\nentitásonkénti belső korreláció",
        fontsize=12,
        fontweight="bold",
    )
    ax_ii.legend(fontsize=9)
    ax_ii.grid(True, alpha=0.3)

    fig_intra_scatter.suptitle(
        "Csoporton belüli korreláció entitásonként\n(szines = szignifikáns p < 0.05, szürke = nem szignifikáns)",
        fontsize=13,
        fontweight="bold",
    )
    fig_intra_scatter.tight_layout()
    fig_intra_scatter
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Tengelyek definíciója

    | Tengely | Jelentés | Leírás |
    | :--- | :--- | :--- |
    | **Vízszintes (x)** | Átlag páronkénti Pearson r | Megmutatja, mennyire korrelálnak a csoporton belüli portálok az adott entitásnál. |
    | **Függőleges (y)** | Átlag p-érték | Megmutatja, mennyire megbízható a korreláció az adott adathalmazon. |

    ---

    #### Értelmezés és vizuális jelölések

    | Pozíció / Megjelenés | Értelmezés |
    | :--- | :--- |
    | **Jobb alsó** (magas r, alacsony p) | A csoport portáljai **szignifikánsan szinkronban** tudósítanak erről az entitásról. |
    | **Bal felső** (alacsony r, magas p) | Az entitásról **nem koordináltan** írnak a csoport tagjai. |
    | **Színes pont** | Szignifikáns eredmény ($p < 0.05$). |
    | **Szürke pont** | Nem szignifikáns eredmény. |Tengely	Jelentés
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---
    ## Portálspecifikus dinamika

    Most vizsgáljuk a hipotézis második felét: **ugyanazon entitás megjelenésekor
    eltérő-e a szentiment és vizuális hangsúly** a kormányközeli és független
    portálokon?

    Minden top entitásra kiszámoljuk a portáltípusonkénti átlag szentimentet
    és norm_score-t, majd Mann–Whitney U-teszttel vizsgáljuk az eltérést.
    https://hu.wikipedia.org/wiki/Mann%E2%80%93Whitney-pr%C3%B3ba
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Rövid leírás a Mann-Whitney-ről:

    1. A két csoport összes értékét összevonva rangsorolja (legkisebbtől a legnagyobbig).
    2. Kiszámítja az egyes csoportokhoz tartozó rangösszegeket.
    3. Ebből képezi az U-statisztikát, amely méri, hogy az egyik csoport értékei mennyire hajlamosak nagyobbak lenni a másikénál.
    4. A p-érték megmutatja, mekkora a valószínűsége, hogy a megfigyelt (vagy annál nagyobb) eltérés véletlenül adódna, ha a két csoport valójában azonos eloszlású lenne.

    - alternative="two-sided" → kétoldali teszt, azaz nem feltételezzük előre, melyik irányban tér el.
    - Ha p < 0.05, az eredmény szignifikáns ("Igen"), vagyis a kormányközeli és független portálok szentiment-értékei (vagy vizuális súlyai) statisztikailag kimutathatóan különböznek az adott entitásnál.
    - Ha p ≥ 0.05, a különbség nem szignifikáns ("Nem"), azaz nem zárható ki, hogy a megfigyelt eltérés pusztán véletlenből adódik.
    """)
    return


@app.cell
def _(df_entities, mo, np, pl, stats):
    """
    top 15 entitás, entitásonként hányszor fordul elő és hány portáltípusban jelenik meg
    - csak azok maradnak, amelyek mind a GOV mind a IND portálokban megjelennek
    - csökkenő sorrend
    """
    _top_15 = (
        df_entities.group_by("entity")
        .agg(
            pl.len().alias("n"),
            pl.col("portal_type").n_unique().alias("n_types"),
        )
        .filter(pl.col("n_types") == 2)
        .sort("n", descending=True)
        .head(15)["entity"]
        .to_list()
    )

    dynamics_results = []

    for _ent in _top_15:
        _sub = df_entities.filter(pl.col("entity") == _ent).filter(
            pl.col("sentiment_score").is_not_null() & pl.col("norm_score").is_not_null()
        )

        _gov = _sub.filter(pl.col("portal_type") == "Kormányközeli")
        _ind = _sub.filter(pl.col("portal_type") == "Független")
    
        # ha bármelyik csoportban kevesebb, mint 3 elem van, kimarad
        if _gov.height < 3 or _ind.height < 3:
            continue

        _gov_sent = _gov["sentiment_score"].to_numpy()
        _ind_sent = _ind["sentiment_score"].to_numpy()
        _gov_vis = _gov["norm_score"].to_numpy()
        _ind_vis = _ind["norm_score"].to_numpy()

        # Mann-Whitney U
        # mivel az adatok nem normál eloszlásúak, nem jó a t-próba
        _u_sent, _p_sent = stats.mannwhitneyu(
            _gov_sent, _ind_sent, alternative="two-sided"
        )
        # Mann-Whitney vizuális score-hoz
        _u_vis, _p_vis = stats.mannwhitneyu(_gov_vis, _ind_vis, alternative="two-sided")

        dynamics_results.append(
            {
                "entity": _ent,
                "n_gov": _gov.height,
                "n_ind": _ind.height,
                "sent_gov_mean": round(float(np.mean(_gov_sent)), 3),
                "sent_ind_mean": round(float(np.mean(_ind_sent)), 3),
                "sent_diff": round(float(np.mean(_gov_sent) - np.mean(_ind_sent)), 3),
                "sent_p": round(float(_p_sent), 4),
                "sent_sig": "Igen" if _p_sent < 0.05 else "Nem",
                "vis_gov_mean": round(float(np.mean(_gov_vis)), 3),
                "vis_ind_mean": round(float(np.mean(_ind_vis)), 3),
                "vis_diff": round(float(np.mean(_gov_vis) - np.mean(_ind_vis)), 3),
                "vis_p": round(float(_p_vis), 4),
                "vis_sig": "Igen" if _p_vis < 0.05 else "Nem",
            }
        )

    df_dynamics = pl.DataFrame(dynamics_results).sort("sent_diff", descending=True)

    mo.vstack(
        [
            mo.md(
                """## Szentiment és vizuális súly összehasonlítása portáltípusonként

    - **sent_diff > 0**: a kormányközeli portálok pozitívabb szentimenttel mutatják az entitást
    - **sent_diff < 0**: a független portálok pozitívabbak
    - **vis_diff**: hasonlóan a vizuális hangsúlyra
    - Mann–Whitney U-teszt (p < 0.05 → szignifikáns eltérés)"""
            ),
            mo.ui.table(df_dynamics),
        ]
    )
    return (df_dynamics,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    A fenti táblázat oszlopainak magyarázata

    | Oszlop | Magyarázat |
    |---|---|
    | **`entity`** | Az entitás neve (személy, szervezet, téma), amelyre az összehasonlítás vonatkozik |
    | **`n_gov`** | Hány említés tartozik az entitáshoz **kormányközeli** portálokon (a Mann–Whitney minta mérete az egyik oldalon) |
    | **`n_ind`** | Hány említés tartozik az entitáshoz **független** portálokon (a Mann–Whitney minta mérete a másik oldalon) |
    | **`sent_gov_mean`** | A kormányközeli portálokon mért **szentiment-értékek átlaga** az adott entitásra (3 tizedesre kerekítve) |
    | **`sent_ind_mean`** | A független portálokon mért **szentiment-értékek átlaga** az adott entitásra (3 tizedesre kerekítve) |
    | **`sent_diff`** | A szentiment-átlagok különbsége: `sent_gov_mean − sent_ind_mean`. Pozitív → a kormányközeli portálok pozitívabbak, negatív → a függetlenek pozitívabbak |
    | **`sent_p`** | A szentimentre vonatkozó Mann–Whitney U-teszt **p-értéke** (4 tizedesre kerekítve). Minél kisebb, annál valószínűbb, hogy a különbség nem véletlenszerű |
    | **`sent_sig`** | Szignifikáns-e a szentiment-eltérés: `"Igen"` ha `p < 0.05`, `"Nem"` ha `p ≥ 0.05` |
    | **`vis_gov_mean`** | A kormányközeli portálokon mért **normalizált vizuális súly** (`norm_score`) átlaga az adott entitásra |
    | **`vis_ind_mean`** | A független portálokon mért **normalizált vizuális súly** átlaga az adott entitásra |
    | **`vis_diff`** | A vizuális súly átlagok különbsége: `vis_gov_mean − vis_ind_mean`. Pozitív → a kormányközeli portálok nagyobb vizuális hangsúlyt adnak, negatív → a függetlenek |
    | **`vis_p`** | A vizuális súlyra vonatkozó Mann–Whitney U-teszt **p-értéke** (4 tizedesre kerekítve) |
    | **`vis_sig`** | Szignifikáns-e a vizuális súly eltérése: `"Igen"` ha `p < 0.05`, `"Nem"` ha `p ≥ 0.05` |

    A táblázat a `sent_diff` szerint csökkenő sorrendben van rendezve, tehát felül azok az entitások állnak, amelyeknél a kormányközeli portálok a **legpozitívabb** szentimenttel írnak a függetlenekhez képest.
    """)
    return


@app.cell
def _(df_dynamics, np, plt):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"

    fig_div, (ax_sent, ax_vis) = plt.subplots(1, 2, figsize=(16, 7))

    _ents = df_dynamics["entity"].to_list()
    _y = np.arange(len(_ents))
    _bw = 0.35

    # -- Sentiment panel --
    _sg = df_dynamics["sent_gov_mean"].to_list()
    _si = df_dynamics["sent_ind_mean"].to_list()
    _sp = df_dynamics["sent_sig"].to_list()

    ax_sent.barh(
        _y - _bw / 2, _sg, _bw, label="Kormányközeli", color=_COLOR_GOV, alpha=0.8
    )
    ax_sent.barh(_y + _bw / 2, _si, _bw, label="Független", color=_COLOR_IND, alpha=0.8)

    for _j, _e in enumerate(_ents):
        if _sp[_j] == "Igen":
            ax_sent.text(
                max(_sg[_j], _si[_j]) + 0.02,
                _j,
                "★",
                fontsize=12,
                va="center",
                color="#e67e22",
            )

    ax_sent.set_yticks(_y)
    ax_sent.set_yticklabels(_ents, fontsize=9)
    ax_sent.set_xlabel("Átlag szentiment score", fontsize=10)
    ax_sent.set_title("Szentiment portáltípusonként", fontsize=12, fontweight="bold")
    ax_sent.legend(fontsize=9)
    ax_sent.grid(True, axis="x", alpha=0.3)

    # -- Visual score panel --
    _vg = df_dynamics["vis_gov_mean"].to_list()
    _vi = df_dynamics["vis_ind_mean"].to_list()
    _vp = df_dynamics["vis_sig"].to_list()

    ax_vis.barh(
        _y - _bw / 2, _vg, _bw, label="Kormányközeli", color=_COLOR_GOV, alpha=0.8
    )
    ax_vis.barh(_y + _bw / 2, _vi, _bw, label="Független", color=_COLOR_IND, alpha=0.8)

    for _j, _e in enumerate(_ents):
        if _vp[_j] == "Igen":
            ax_vis.text(
                max(_vg[_j], _vi[_j]) + 0.02,
                _j,
                "★",
                fontsize=12,
                va="center",
                color="#e67e22",
            )

    ax_vis.set_yticks(_y)
    ax_vis.set_yticklabels(_ents, fontsize=9)
    ax_vis.set_xlabel("Átlag normalizált vizuális score", fontsize=10)
    ax_vis.set_title(
        "Vizuális hangsúly portáltípusonként", fontsize=12, fontweight="bold"
    )
    ax_vis.legend(fontsize=9)
    ax_vis.grid(True, axis="x", alpha=0.3)

    fig_div.suptitle(
        "Portálspecifikus dinamika – Ugyanazon entitások eltérő kezelése\n(★ = szignifikáns eltérés, p < 0.05)",
        fontsize=13,
        fontweight="bold",
    )
    fig_div.tight_layout()
    fig_div
    return


@app.cell
def _(df_dynamics, mo, pl):


    _n_sig_sent = df_dynamics.filter(pl.col("sent_sig") == "Igen").height
    _n_sig_vis = df_dynamics.filter(pl.col("vis_sig") == "Igen").height
    _n_total_dyn = df_dynamics.height

    mo.md(f"""
    ---
    ## Összefoglalás

    ### Portálspecifikus dinamika
    - **Szentiment**: {_n_sig_sent} / {_n_total_dyn} entitásnál szignifikáns eltérés
    - **Vizuális hangsúly**: {_n_sig_vis} / {_n_total_dyn} entitásnál szignifikáns eltérés

    ### Értelmezés a H3 hipotézis szempontjából
    {"✅ **A hipotézis támogatást nyer**: Bár a portálok gyakran egyszerre foglalkoznak ugyanazokkal az entitásokkal (közös napirend), a hozzájuk társított szentiment és/vagy vizuális dinamika szignifikánsan eltér – azaz a napirend kijelölés közös, de a keretezés portálspecifikus." if _n_sig_sent >= _n_total_dyn * 0.3 or _n_sig_vis >= _n_total_dyn * 0.3 else "⚠️ **A hipotézis részben nyer támogatást**: Az entitások megjelenése korrelál, de a dinamikai eltérések nem minden entitásnál szignifikánsak. Nagyobb mintára vagy finomabb időfelbontásra lehet szükség."}
    """)
    return


if __name__ == "__main__":
    app.run()
