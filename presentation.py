import marimo

__generated_with = "0.23.2"
app = marimo.App(
    width="medium",
    layout_file="layouts/presentation.slides.json",
)


@app.cell(hide_code=True)
def _():
    # ----- Setup: adatbetöltés, előfeldolgozás, tesztek (rejtett) -----
    import marimo as mo
    import numpy as np
    import polars as pl
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from scipy import stats as scipy_stats

    # Adatok
    df_headlineDefinitions = pl.read_parquet(
        "data/headlineDefinitions_2026-04-19.parquet"
    )
    df_llmAnalysis = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    df_headlines = pl.read_parquet("data/headlines_2026-04-19.parquet")

    # Átlagos vizuális pontszám címsoronként, majd összekapcsolás
    df_vis = (
        df_headlines.select(["hashedId", "score"])
        .group_by("hashedId")
        .agg(pl.col("score").mean().alias("mean_score"))
    )
    df_base = df_headlineDefinitions.join(
        df_llmAnalysis.select(["hashedId", "sentiment_score", "entities", "label"]),
        on="hashedId",
        how="left",
    ).join(df_vis, on="hashedId", how="left")

    # Min-max normalizálás portálonként
    _site_stats = df_base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("score_min"),
        pl.col("mean_score").max().alias("score_max"),
    )
    df_normed = (
        df_base.join(_site_stats, on="siteName", how="left")
        .with_columns(
            (
                (pl.col("mean_score") - pl.col("score_min"))
                / (pl.col("score_max") - pl.col("score_min") + 1e-9)
            ).alias("norm_score")
        )
        .drop(["score_min", "score_max"])
    )

    # Portálok besorolása
    GOV_PORTALS = ["Origo", "Magyar Nemzet", "PestiSracok", "Hirado.hu",
                   "Ripost", "Metropol", "Mandiner"]
    IND_PORTALS = ["Telex", "444.hu", "HVG", "ATV", "Magyar Hang",
                   "24.hu", "Nepszava", "Valasz Online"]
    df_classified = df_normed.with_columns(
        pl.when(pl.col("siteName").is_in(GOV_PORTALS))
        .then(pl.lit("Kormányközeli"))
        .when(pl.col("siteName").is_in(IND_PORTALS))
        .then(pl.lit("Független"))
        .otherwise(pl.lit("Egyéb"))
        .alias("portal_type")
    )

    # Entitásonkénti részminták
    ENTITIES = ["Magyar Péter", "Orbán Viktor"]
    _rows = []
    for _entity in ENTITIES:
        _subset = (
            df_classified.filter(pl.col("entities").str.contains(_entity))
            .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
            .with_columns(pl.lit(_entity).alias("entity"))
        )
        _rows.append(_subset)
    df_entities = pl.concat(_rows)

    # Numpy tömbök + Mann-Whitney U tesztek
    arrays = {}
    for _ent in ENTITIES:
        for _pt in ["Kormányközeli", "Független"]:
            _sub = df_entities.filter(
                (pl.col("entity") == _ent) & (pl.col("portal_type") == _pt)
            )
            arrays[(_ent, _pt)] = {
                "sent": _sub["sentiment_score"].to_numpy(),
                "score": _sub["norm_score"].drop_nulls().to_numpy(),
                "n": _sub.height,
            }

    def _sig(p):
        if p < 0.001: return "*** (p<0.001)"
        if p < 0.01:  return "** (p<0.01)"
        if p < 0.05:  return "* (p<0.05)"
        return "n.s."

    test_rows = []
    for _ent in ENTITIES:
        for _mk, _ml in [("sent", "Szentiment"), ("score", "Vizuális prominencia")]:
            _gov = arrays[(_ent, "Kormányközeli")][_mk]
            _ind = arrays[(_ent, "Független")][_mk]
            _u, _p = scipy_stats.mannwhitneyu(_gov, _ind, alternative="two-sided")
            _r = 1 - (2 * _u) / (len(_gov) * len(_ind))
            test_rows.append({
                "Entitás": _ent, "Mérőszám": _ml,
                "Gov átlag": round(_gov.mean(), 3),
                "Ind átlag": round(_ind.mean(), 3),
                "Δ (Gov−Ind)": round(_gov.mean() - _ind.mean(), 3),
                "p-érték": round(_p, 4),
                "r (hatásméret)": round(_r, 3),
                "Szignifikancia": _sig(_p),
            })
    df_tests = pl.DataFrame(test_rows)

    COLOR_GOV = "#c0392b"
    COLOR_IND = "#2980b9"
    return COLOR_GOV, COLOR_IND, arrays, df_tests, mo, mpatches, np, pl, plt


@app.cell(hide_code=True)
def _(mo):
    # ----- Bevezető slide: projekt célja -----
    mo.md(r"""
    # Kontraszt – Médiaviselkedés a figyelemgazdaságban

    ### *A magyar online hírportálok címlapjainak empirikus vizsgálata*

    ---

    ## Miről szól ez a kutatás?

    A **figyelem** a digitális médiatér legszűkösebb erőforrása (Simon, Goldhaber).
    A hírportálok nem pusztán információt közölnek: **vizuális hierarchiával,
    kiemeléssel és érzelmi tónussal** versenyeznek az olvasó figyelméért.

    Ez a projekt a figyelemgazdaság **kínálati oldalát** méri – azt,
    hogy a szerkesztőség **mely híreket próbálja figyelemre méltóvá tenni**,
    nem azt, hogy az olvasó ténylegesen mire kattint.

    ## Kutatási kérdés

    > Hogyan tükröződik a magyar online hírportálok szerkesztési gyakorlatában
    > (vizuális hangsúly és érzelmi töltet) a választási kampány dinamikája,
    > és mennyire mutatnak **homogén képet** az egyes politikai szereplők
    > megjelenítésében?

    ## Három hipotézis

    | | Hipotézis | Fókusz |
    |---|---|---|
    | **H1** | **Polarizáció** – a kormányközeli és független portálok eltérő szentimenttel és vizuális súllyal jelenítik meg ugyanazokat a politikai szereplőket | *portáltípus × entitás* |
    | **H2** | **Vizuális hangsúly** – a negatív címsorok átlagosan magasabb „fontossági pontszámot" kapnak, mint a semlegesek | *sentiment → score* |
    | **H3** | **Napirend-kijelölés** – a kulcsszereplők megjelenése időben korrelál a portálok között, de a hozzájuk társított dinamika portálspecifikus | *koordináció + framing* |

    ## Mérnöki háttér – saját teljes pipeline

    - **Scraper** (`kontraszt`): 21 magyar hírportál óránkénti főoldal-mérése
      (Playwright + Crawlee + Convex)
    - **LLM-service** (`kontraszt-llm_service`): headline-onkénti szentiment-,
      entitás- és címke-elemzés (JSON-schema kényszerítéssel)
    - **Research notebook** (ez a prezentáció): Polars + SciPy + statsmodels,
      marimo-alapú reprodukálható elemzés

    ## Üzenet

    A médiafogyasztók tudatosságának növelése: **hogyan manipulál egy vizuális
    elrendezés** – kvantitatívan, adatvezérelten, nem benyomások alapján.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # ----- Adatgyűjtés 1. slide: Scraper (kontraszt) -----
    mo.md(r"""
    # Adatgyűjtés I. – Főoldali scraper (`kontraszt`)

    ## Cél
    A 21 legolvasottabb magyar hírportál **főoldali szalagcímeinek** és azok
    **vizuális paramétereinek** óránkénti rögzítése – ez adja a „figyelem
    kínálati oldalának" nyers mérőszámait.

    ## Technológia
    - **Playwright + Crawlee** (TypeScript) – valódi böngésző renderel, így a
      JS-sel betöltődő címsorok is láthatók; pontos DOM-geometria mérhető
    - **Convex** backend – típusos séma, real-time szinkronizáció
    - **Docker Compose** + cron – futás óránként, webhook értesíti az LLM-szolgáltatást

    ## Portálok (21 db)
    Telex, Origo, Blikk, 24.hu, Index, BorsOnline, 444.hu, Magyar Nemzet, Ripost,
    HVG, ATV, Hirado.hu, Metropol, Nepszava, Mandiner, PestiSracok, Napi,
    Valasz Online, Vilaggazdasag, Portfolio, Magyar Hang

    ## Két tábla (`convex/schema.ts`)

    | `headlineDefinitions` | `headlines` |
    |---|---|
    | `hashedId` (SHA1 a URL-ből) | `hashedId` |
    | `siteName` | `score`, `fontSize` |
    | `headlineText` | `width`, `height`, `x`, `y` |
    | `href` | `scrapedAt` |

    → **Cím = definíció** (1×), **megjelenés = snapshot** (N× óránként).

    ## A vizuális „fontossági pontszám" (`score`)

    $$\text{score} = 100 \cdot \text{fontSize} + 0.1 \cdot \text{area} - 6y - 3.5x - 4 \cdot x \cdot \max\!\left(0,\ 1 - \tfrac{y}{600}\right)$$

    - **+ nagy betű** és **nagy terület** → több figyelem
    - **− lejjebb/jobbra** → kisebb hangsúly (a szem balra fent kezd)
    - **− jobb felső büntetés** csak a „top zónára" (y < 600 px) érvényes –
      ott a reklámhelyek kiszűrésére
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    # ----- Adatgyűjtés 2. slide: LLM service -----
    mo.md(r"""
    # Adatgyűjtés II. – LLM-elemzés (`kontraszt-llm_service`)

    ## Cél
    Minden új headline-hoz strukturált **szemantikai annotáció** készítése:
    szentiment, entitások, címke – ezek a H1–H3 hipotézisek magyarázó változói.

    ## Pipeline

    ```
    [Scraper Convex]  ──webhook──▶  [LLM-service]  ──batch──▶  [Kilo API (LLM)]
          │                              │                            │
          │                              │◀──JSON schema válasz───────┘
          │                              ▼
          └──────────────────────▶ [Target Convex] ──▶ llmAnalysis tábla
    ```

    - Node.js szolgáltatás (`apps/llm-service`), `POST /webhook/scrape-complete`
      végponttal – a scraper futása után automatikusan indul
    - **Forrás Convex**-ből olvas pager-rel (`SOURCE_PAGE_SIZE=200`),
      **cél Convex**-be ír batch-ben (`CONVEX_SAVE_BATCH_SIZE=200`)
    - **Kilo API gateway** (`api.kilo.ai`) felé OpenAI-kompatibilis
      `chat/completions` hívás, **JSON Schema**-kényszerítéssel

    ## A promptra kért mezők (headline-onként)

    | Mező | Típus | Leírás |
    |---|---|---|
    | `label` | string | tematikus címke |
    | `sentiment` | string | negatív / semleges / pozitív |
    | **`sentiment_score`** | float 0–1 | 0 = teljesen negatív, 1 = teljesen pozitív |
    | **`entities`** | string[] | szereplők, szervezetek (pl. „Orbán Viktor") |
    | `confidence` | float 0–1 | modell önbizalma |

    Ez a struktúra garantálja, hogy minden címsorhoz **ugyanaz** a négy
    elemzési dimenzió álljon rendelkezésre → közvetlenül csatlakoztatható
    a `headlineDefinitions`-höz `hashedId` mentén.

    ## Megbízhatóság
    - **JSON Schema** response format → nincs parsing-hiba
    - **Retry logika** max 3 kísérlettel batchenként
    - **Pointer-alapú szinkronizáció** (`SYNC_STATE_KEY`) → sosem dolgoz fel
      kétszer ugyanazt a headline-t

    > Az eredmény a kutatás három parquet fájlja:
    > `headlineDefinitions`, `headlines`, `llmAnalysis` – `hashedId` join-kulccsal.
    """)
    return


@app.cell(hide_code=True)
def _(df_tests, mo, pl):
    # ----- Slide 1: Hipotézis + módszertan -----
    _n = df_tests.filter(pl.col("p-érték") < 0.05).height
    mo.md(rf"""
    # H1 – Médiapolarizáció a magyar hírportálokon

    ## Hipotézis
    > A **kormányközeli** és a **független** hírportálok jelentősen eltérő **érzelmi
    > szentimenttel** és **vizuális súllyal** jelenítik meg ugyanazokat a politikai
    > szereplőket.

    ## Módszertan röviden
    - **Adat:** címsorok + LLM-alapú szentiment- és entitáselemzés + főoldali vizuális score
    - **Portálok besorolása:** 🔴 Kormányközeli (Origo, M. Nemzet, Hirado.hu, …) vs. 🔵 Független (Telex, 444, HVG, …)
    - **Fókusz entitások:** *Magyar Péter* és *Orbán Viktor*
    - **Normalizálás:** vizuális score min-max skálázás portálonként (0–1)
    - **Statisztika:** Mann-Whitney U teszt + rank-biszeriális hatásméret (r)

    → **{_n} / 4** teszt mutat p < 0.05 szignifikanciát.
    """)
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, arrays, mo, mpatches, np, plt):
    # ----- Slide 2: Hegedűdiagramok -----
    _ptypes = ["Kormányközeli", "Független"]
    _colors = [COLOR_GOV, COLOR_IND]
    _entities = ["Magyar Péter", "Orbán Viktor"]
    _metrics = [
        ("sent", "Szentiment (0=neg, 1=poz)"),
        ("score", "Vizuális prominencia (0–1)"),
    ]

    fig_violin, axes_v = plt.subplots(2, 2, figsize=(11, 8), sharey="row")
    fig_violin.suptitle(
        "Szentiment és vizuális prominencia eloszlása portáltípusonként",
        fontsize=13, fontweight="bold", y=1.01,
    )
    for _row, (_mk, _yl) in enumerate(_metrics):
        for _col, _ent in enumerate(_entities):
            _ax = axes_v[_row][_col]
            _data = [arrays[(_ent, _pt)][_mk] for _pt in _ptypes]
            _ns = [arrays[(_ent, _pt)]["n"] for _pt in _ptypes]
            _parts = _ax.violinplot(_data, positions=[1, 2],
                                    showmedians=True, showextrema=True)
            for _pc, _c in zip(_parts["bodies"], _colors):
                _pc.set_facecolor(_c); _pc.set_alpha(0.72)
            for _k in ("cmedians", "cmins", "cmaxes", "cbars"):
                _parts[_k].set_color("black"); _parts[_k].set_linewidth(1.2)
            for _pos, _d, _c in zip([1, 2], _data, _colors):
                _ax.text(_pos, np.median(_d) + 0.03, f"{np.median(_d):.2f}",
                         ha="center", va="bottom", fontsize=9,
                         color=_c, fontweight="bold")
            for _pos, _n in zip([1, 2], _ns):
                _ax.text(_pos, -0.08, f"n={_n}", ha="center", va="top",
                         fontsize=8, color="grey",
                         transform=_ax.get_xaxis_transform())
            _ax.set_xticks([1, 2]); _ax.set_xticklabels(_ptypes, fontsize=10)
            _ax.set_ylim(-0.05, 1.1)
            _ax.axhline(0.5, color="grey", ls="--", lw=0.7, alpha=0.5)
            if _col == 0: _ax.set_ylabel(_yl, fontsize=10)
            if _row == 0: _ax.set_title(_ent, fontsize=12, fontweight="bold")
    fig_violin.legend(
        handles=[mpatches.Patch(color=COLOR_GOV, alpha=0.72, label="Kormányközeli"),
                 mpatches.Patch(color=COLOR_IND, alpha=0.72, label="Független")],
        loc="lower center", ncol=2, frameon=False, fontsize=11,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig_violin.tight_layout()

    mo.vstack([
        mo.md("## Eloszlások – hegedűdiagram"),
        fig_violin,
        mo.md(
            "**Tükörszerű mintázat:** a kormányközeli oldalak *Orbánt* pozitívabban, "
            "*Magyar Pétert* negatívabban ábrázolják — a független oldalak fordítva. "
            "A vizuális prominencia (alsó sor) mindkét szereplőnél a kormányközeli "
            "portálokon magasabb."
        ),
    ])
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, arrays, mo, np, plt):
    # ----- Slide 3: Oszlopdiagram Δ-val -----
    _entities = ["Magyar Péter", "Orbán Viktor"]
    _ptypes = ["Kormányközeli", "Független"]
    _colors = [COLOR_GOV, COLOR_IND]
    _bw = 0.3
    _metrics_bar = [
        ("sent", "Szentiment átlag (0–1)"),
        ("score", "Vizuális prominencia átlag (0–1)"),
    ]

    fig_bar, axes_b = plt.subplots(1, 2, figsize=(12, 4.5))
    fig_bar.suptitle(
        "Átlagértékek és Δ különbségek",
        fontsize=13, fontweight="bold",
    )
    for (_mk, _yl), _ax in zip(_metrics_bar, axes_b):
        _x = np.arange(len(_entities))
        for _i, (_pt, _c) in enumerate(zip(_ptypes, _colors)):
            _vals = [np.mean(arrays[(_ent, _pt)][_mk]) for _ent in _entities]
            _bars = _ax.bar(_x + (_i - 0.5) * _bw, _vals, _bw,
                            label=_pt, color=_c, alpha=0.82)
            for _b, _v in zip(_bars, _vals):
                _ax.text(_b.get_x() + _b.get_width() / 2, _b.get_height() + 0.012,
                         f"{_v:.2f}", ha="center", va="bottom",
                         fontsize=9, fontweight="bold")
        for _j, _ent in enumerate(_entities):
            _gv = np.mean(arrays[(_ent, "Kormányközeli")][_mk])
            _iv = np.mean(arrays[(_ent, "Független")][_mk])
            _delta = _gv - _iv
            _ax.annotate(f"Δ={_delta:+.2f}",
                         xy=(_x[_j], max(_gv, _iv) + 0.04),
                         ha="center", va="bottom", fontsize=9,
                         fontweight="bold",
                         color=COLOR_GOV if _delta > 0 else COLOR_IND)
        _ax.set_xticks(_x); _ax.set_xticklabels(_entities, fontsize=11)
        _ax.set_ylabel(_yl, fontsize=10)
        _ax.set_ylim(0, 0.95)
        _ax.axhline(0.5, color="grey", ls="--", lw=0.7, alpha=0.5)
        _ax.legend(fontsize=10)
    fig_bar.tight_layout()

    mo.vstack([
        mo.md("## Átlagok összehasonlítása"),
        fig_bar,
        mo.md(
            "A **Δ érték** a kormányközeli és független átlagok különbsége. "
            "Pozitív Δ → a kormányközeli portálok értéke a magasabb. "
            "A szentimentnél ellentétes irányú Δ-k (Magyar Péter vs. Orbán Viktor) "
            "erősítik a polarizáció hipotézisét."
        ),
    ])
    return


@app.cell(hide_code=True)
def _(df_tests, mo):
    # ----- Slide 4: Statisztikai tesztek -----
    mo.vstack([
        mo.md(r"""
        ## Statisztikai tesztek – Mann-Whitney U

        **Miért ez a teszt?** Nem-paraméteres, nem feltételez normális eloszlást,
        robusztus kiugró értékekre — ideális 0–1-re normalizált, ferde eloszlású
        szentiment/prominencia adatokra.

        - **p < 0.05** → a különbség nem a véletlen műve
        - **r (rank-biszeriális)** → a hatás gyakorlati nagysága
          (|r|<0.1 elhanyagolható · 0.1–0.3 gyenge · 0.3–0.5 közepes · >0.5 erős)
        """),
        mo.plain(df_tests),
    ])
    return


@app.cell(hide_code=True)
def _(df_tests, mo, pl):
    # ----- Slide 5: Verdikt -----
    def _get(ent, mt):
        _r = df_tests.filter(
            (pl.col("Entitás") == ent) & (pl.col("Mérőszám") == mt)
        )
        return _r["p-érték"][0], _r["Δ (Gov−Ind)"][0], _r["r (hatásméret)"][0]

    mp_sp, mp_sd, _ = _get("Magyar Péter", "Szentiment")
    mp_vp, mp_vd, _ = _get("Magyar Péter", "Vizuális prominencia")
    ov_sp, ov_sd, _ = _get("Orbán Viktor", "Szentiment")
    ov_vp, ov_vd, _ = _get("Orbán Viktor", "Vizuális prominencia")

    _n_sig = sum(p < 0.05 for p in [mp_sp, mp_vp, ov_sp, ov_vp])
    _verdict = ("✅ **megerősítve**" if _n_sig >= 3
                else "⚠️ **részben megerősítve**" if _n_sig >= 1
                else "❌ **nem megerősítve**")

    mo.md(f"""
    # H1 Verdikt: {_verdict}

    **{_n_sig} / 4** teszt szignifikáns (p < 0.05).

    ## A fő eredmény

    | Szereplő | Szentiment Δ (Gov−Ind) | Vizuális Δ (Gov−Ind) |
    |---|---|---|
    | Magyar Péter | `{mp_sd:+.3f}` (p={mp_sp:.4f}) | `{mp_vd:+.3f}` (p={mp_vp:.4f}) |
    | Orbán Viktor | `{ov_sd:+.3f}` (p={ov_sp:.4f}) | `{ov_vd:+.3f}` (p={ov_vp:.4f}) |

    ## Értelmezés

    - A kormányközeli portálok **Magyar Pétert negatívabban**
      (Δ={mp_sd:+.3f}), **Orbán Viktort pozitívabban** (Δ={ov_sd:+.3f}) ábrázolják
      → **szimmetrikus, tükörszerű mintázat** — a polarizáció klasszikus jele.
    - Mindkét szereplőt **nagyobb vizuális hangsúllyal** jelenítik meg a
      kormányközeli oldalak (Δ_MP={mp_vd:+.3f}, Δ_OV={ov_vd:+.3f})
      → intenzívebb figyelemverseny a kormányközeli médiában.

    > A magyar online médiarendszer **szisztematikusan és mérhetően polarizált**
    > mind hangnemben, mind vizuális megjelenítésben.
    """)
    return


@app.cell(hide_code=True)
def _(pl):
    # ----- H2 Setup (rejtett): df_h2 + Spearman + Mann-Whitney + regresszió -----
    from scipy import stats as _scipy_h2
    import statsmodels.formula.api as _smf_h2

    _GOV_H2 = ["Origo", "Magyar Nemzet", "PestiSracok", "Hirado.hu",
               "Ripost", "Metropol", "Mandiner"]
    _IND_H2 = ["Telex", "444.hu", "HVG", "ATV", "Magyar Hang",
               "24.hu", "Nepszava", "Valasz Online"]

    _hd = pl.read_parquet("data/headlineDefinitions_2026-04-19.parquet")
    _llm = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    _hl = pl.read_parquet("data/headlines_2026-04-19.parquet")

    _vis = (_hl.select(["hashedId", "score"]).group_by("hashedId")
            .agg(pl.col("score").mean().alias("mean_score")))
    _base = (_hd.join(
        _llm.select(["hashedId", "sentiment_score", "entities", "label"]),
        on="hashedId", how="left",
    ).join(_vis, on="hashedId", how="left"))
    _ss = _base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("smin"),
        pl.col("mean_score").max().alias("smax"),
    )
    _normed = (_base.join(_ss, on="siteName", how="left").with_columns(
        ((pl.col("mean_score") - pl.col("smin"))
         / (pl.col("smax") - pl.col("smin") + 1e-9)).alias("norm_score")
    ).drop(["smin", "smax"]))
    _cls = _normed.with_columns(
        pl.when(pl.col("siteName").is_in(_GOV_H2)).then(pl.lit("Kormányközeli"))
        .when(pl.col("siteName").is_in(_IND_H2)).then(pl.lit("Független"))
        .otherwise(pl.lit("Egyéb")).alias("portal_type")
    )

    df_h2 = (
        _cls.filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
        .filter(pl.col("sentiment_score").is_not_null() & pl.col("norm_score").is_not_null())
        .with_columns(
            pl.when(pl.col("sentiment_score") < 0.35).then(pl.lit("Negatív"))
            .when(pl.col("sentiment_score") <= 0.65).then(pl.lit("Semleges"))
            .otherwise(pl.lit("Pozitív")).alias("sentiment_band")
        )
    )

    h2_samples = (
        df_h2.group_by(["portal_type", "sentiment_band"]).agg(pl.len().alias("n"))
        .with_columns(
            (pl.col("n") * 100.0 / pl.col("n").sum().over("portal_type"))
            .round(2).alias("pct")
        ).sort(["portal_type", "sentiment_band"])
    )

    def _sig_h2(p):
        if p < 0.001: return "*** (p<0.001)"
        if p < 0.01:  return "** (p<0.01)"
        if p < 0.05:  return "* (p<0.05)"
        return "n.s."

    def _strength_h2(r):
        _a = abs(r)
        if _a < 0.1: return "elhanyagolható"
        if _a < 0.3: return "gyenge"
        if _a < 0.5: return "közepes"
        return "erős"

    # Spearman
    _sp_rows = []
    for _gn, _sub in [
        ("Összes", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]:
        _rho, _p = _scipy_h2.spearmanr(
            _sub["sentiment_score"].to_numpy(),
            _sub["norm_score"].to_numpy(),
        )
        _sp_rows.append({
            "Csoport": _gn, "n": _sub.height,
            "ρ (Spearman)": round(float(_rho), 3),
            "p-érték": round(float(_p), 4),
            "Erősség": _strength_h2(_rho),
            "Szignifikancia": _sig_h2(_p),
        })
    df_h2_spearman = pl.DataFrame(_sp_rows)

    # Mann-Whitney sávpárokra
    _pairs = [("Negatív", "Semleges", "greater"),
              ("Negatív", "Pozitív", "greater"),
              ("Semleges", "Pozitív", "two-sided")]
    _mw_rows = []
    for _gn, _gdf in [
        ("Összes", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]:
        for _b1, _b2, _alt in _pairs:
            _a = _gdf.filter(pl.col("sentiment_band") == _b1)["norm_score"].to_numpy()
            _bb = _gdf.filter(pl.col("sentiment_band") == _b2)["norm_score"].to_numpy()
            if len(_a) < 3 or len(_bb) < 3:
                continue
            _u, _p = _scipy_h2.mannwhitneyu(_a, _bb, alternative=_alt)
            _r = 1 - (2 * _u) / (len(_a) * len(_bb))
            _mw_rows.append({
                "Csoport": _gn,
                "Összehasonlítás": f"{_b1} vs. {_b2}",
                "n1": len(_a), "n2": len(_bb),
                "p-érték": round(float(_p), 4),
                "r": round(float(_r), 3),
                "Szignifikancia": _sig_h2(_p),
            })
    df_h2_mw = pl.DataFrame(_mw_rows)

    # Regresszió interakcióval
    _pdf = (df_h2.with_columns(
        (pl.col("portal_type") == "Kormányközeli").cast(pl.Int8).alias("gov")
    ).select(["sentiment_score", "norm_score", "gov"]).to_pandas())
    h2_model = _smf_h2.ols("norm_score ~ sentiment_score * gov", data=_pdf).fit()
    return df_h2, df_h2_mw, df_h2_spearman, h2_model, h2_samples


@app.cell(hide_code=True)
def _(df_h2_spearman, mo, pl):
    # ----- H2 Slide 1: Hipotézis + módszertan -----
    _sp_all = df_h2_spearman.filter(pl.col("Csoport") == "Összes").row(0, named=True)
    mo.md(rf"""
    # H2 – Vizuális hangsúly és érzelmi töltet

    ## Hipotézis
    > A **negatív érzelmi töltetű** szalagcímek átlagosan magasabb
    > **„fontossági pontszámot"** (nagyobb betűméret, előkelőbb helyezés)
    > kapnak, mint a **semleges** hírek.

    ## Módszertan – 3 független lépés

    1. **Spearman-rangkorreláció** – van-e monoton együttjárás a szentiment és
       a normalizált vizuális hangsúly között? *(negatív ρ → H2 támogatva)*
    2. **Mann-Whitney U sávpárokra** – a **Negatív / Semleges / Pozitív** sávok
       score-eloszlásának összehasonlítása (egyoldali tesztek H2-irányba).
    3. **OLS regresszió interakcióval** – `norm_score ~ sentiment × gov` –
       szűri a portáltípus zavaró hatását, és méri, hogy **eltér-e**
       a szentiment-hatás a két portáltípusnál.

    ## Változók
    - **Függő:** portálonként min-max normalizált `norm_score` (0–1)
    - **Magyarázó:** `sentiment_score` (0 = neg, 1 = poz), `portal_type`

    → Első előzetes jelzés: ρ_össz = **{_sp_all["ρ (Spearman)"]:+.3f}** (p = {_sp_all["p-érték"]:.4f})
    """)
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, h2_samples, mo, np, pl, plt):
    # ----- H2 Slide 2: Mintaeloszlás szentiment-sávonként -----
    _BANDS = ["Negatív", "Semleges", "Pozitív"]
    _bw = 0.32
    _gov = h2_samples.filter(pl.col("portal_type") == "Kormányközeli").sort("sentiment_band")
    _ind = h2_samples.filter(pl.col("portal_type") == "Független").sort("sentiment_band")

    fig_h2_dist, _ax = plt.subplots(figsize=(9, 4.8))
    _x = np.arange(len(_BANDS))
    _gp = [_gov.filter(pl.col("sentiment_band") == b)["pct"][0] for b in _BANDS]
    _ip = [_ind.filter(pl.col("sentiment_band") == b)["pct"][0] for b in _BANDS]
    _gn = [_gov.filter(pl.col("sentiment_band") == b)["n"][0] for b in _BANDS]
    _in = [_ind.filter(pl.col("sentiment_band") == b)["n"][0] for b in _BANDS]

    _bg = _ax.bar(_x - _bw/2, _gp, _bw, label="Kormányközeli", color=COLOR_GOV, alpha=0.82)
    _bi = _ax.bar(_x + _bw/2, _ip, _bw, label="Független", color=COLOR_IND, alpha=0.82)
    for _b, _p, _n in zip(_bg, _gp, _gn):
        _ax.text(_b.get_x() + _b.get_width()/2, _b.get_height() + 0.6,
                 f"{_p:.1f}%\n(n={_n})", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=COLOR_GOV)
    for _b, _p, _n in zip(_bi, _ip, _in):
        _ax.text(_b.get_x() + _b.get_width()/2, _b.get_height() + 0.6,
                 f"{_p:.1f}%\n(n={_n})", ha="center", va="bottom",
                 fontsize=9, fontweight="bold", color=COLOR_IND)
    _ax.set_xticks(_x); _ax.set_xticklabels(_BANDS, fontsize=11)
    _ax.set_ylabel("Arány (%)", fontsize=10)
    _ax.set_title("Szentiment-sávok eloszlása portáltípusonként",
                  fontsize=13, fontweight="bold")
    _ax.set_ylim(0, max(max(_gp), max(_ip)) + 12)
    _ax.legend(fontsize=10)
    fig_h2_dist.tight_layout()

    mo.vstack([
        mo.md("## Mintaeloszlás – szentiment-sávok"),
        fig_h2_dist,
        mo.md(
            "A minta **nem kiegyensúlyozott**: mindkét portáltípuson a "
            "**negatív sáv a legnagyobb**, de arányaiban is eltér a két csoport. "
            "A következő lépésekben a *vizuális hangsúlyt* vizsgáljuk ezen sávokon belül."
        ),
    ])
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, df_h2, df_h2_spearman, mo, np, pl, plt):
    # ----- H2 Slide 3: Spearman + szórásdiagram trendvonallal -----
    fig_h2_sc, _ax = plt.subplots(figsize=(10, 5.2))
    for _pt, _c in [("Kormányközeli", COLOR_GOV), ("Független", COLOR_IND)]:
        _sub = df_h2.filter(pl.col("portal_type") == _pt)
        _x = _sub["sentiment_score"].to_numpy()
        _y = _sub["norm_score"].to_numpy()
        _ax.scatter(_x, _y, s=10, alpha=0.22, color=_c, label=f"{_pt} (n={len(_x)})")
        _slope, _intercept = np.polyfit(_x, _y, 1)
        _xx = np.linspace(0, 1, 100)
        _ax.plot(_xx, _slope * _xx + _intercept, color=_c, linewidth=2.4, alpha=0.95)
    _ax.set_xlabel("Szentiment (0 = negatív, 1 = pozitív)", fontsize=11)
    _ax.set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=11)
    _ax.set_title("Szentiment vs. vizuális hangsúly – lineáris trend portáltípusonként",
                  fontsize=12, fontweight="bold")
    _ax.axvline(0.5, color="grey", ls="--", lw=0.7, alpha=0.5)
    _ax.set_xlim(-0.02, 1.02); _ax.set_ylim(-0.02, 1.05)
    _ax.legend(fontsize=10, loc="upper right")
    fig_h2_sc.tight_layout()

    mo.vstack([
        mo.md("## 1. lépés – Spearman-rangkorreláció"),
        fig_h2_sc,
        mo.plain(df_h2_spearman),
        mo.md(
            "A **lefelé lejtő trendvonalak** (mindkét portáltípusnál) vizuálisan "
            "alátámasztják azt, amit a negatív ρ is mutat: **minél negatívabb a cím, "
            "annál nagyobb vizuális hangsúlyt kap**. A hatás erőssége és szignifikanciája "
            "a fenti táblázatból olvasható ki."
        ),
    ])
    return


@app.cell(hide_code=True)
def _(df_h2, df_h2_mw, mo, np, pl, plt):
    # ----- H2 Slide 4: Mann-Whitney + hegedűdiagramok -----
    _COL_NEG = "#c0392b"; _COL_NEU = "#7f8c8d"; _COL_POS = "#27ae60"
    _BANDS = ["Negatív", "Semleges", "Pozitív"]
    _band_cols = [_COL_NEG, _COL_NEU, _COL_POS]
    _panels = [
        ("Összes", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]

    fig_h2_v, axes = plt.subplots(1, 3, figsize=(14, 4.8), sharey=True)
    fig_h2_v.suptitle("Vizuális hangsúly eloszlása szentiment-sávonként",
                      fontsize=13, fontweight="bold")
    for _ax, (_title, _sub) in zip(axes, _panels):
        _data = [_sub.filter(pl.col("sentiment_band") == _b)["norm_score"].to_numpy()
                 for _b in _BANDS]
        _ns = [len(_d) for _d in _data]
        _parts = _ax.violinplot(_data, positions=[1, 2, 3],
                                showmedians=True, showextrema=True)
        for _pc, _c in zip(_parts["bodies"], _band_cols):
            _pc.set_facecolor(_c); _pc.set_alpha(0.72)
        for _k in ("cmedians", "cmins", "cmaxes", "cbars"):
            _parts[_k].set_color("black"); _parts[_k].set_linewidth(1.1)
        for _pos, _d, _c in zip([1, 2, 3], _data, _band_cols):
            _ax.text(_pos, np.median(_d) + 0.03, f"{np.median(_d):.2f}",
                     ha="center", va="bottom", fontsize=9,
                     color=_c, fontweight="bold")
        for _pos, _n in zip([1, 2, 3], _ns):
            _ax.text(_pos, -0.07, f"n={_n}", ha="center", va="top",
                     fontsize=8, color="grey",
                     transform=_ax.get_xaxis_transform())
        _ax.set_xticks([1, 2, 3]); _ax.set_xticklabels(_BANDS, fontsize=10)
        _ax.set_title(_title, fontsize=11, fontweight="bold")
        _ax.set_ylim(-0.05, 1.1)
        _ax.axhline(0.5, color="grey", ls="--", lw=0.7, alpha=0.5)
    axes[0].set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=10)
    fig_h2_v.tight_layout()

    mo.vstack([
        mo.md(
            "## 2. lépés – Mann-Whitney U sávpárokra\n\n"
            "*A **Negatív vs. Semleges / Pozitív** tesztek egyoldaliak "
            "(H2: negatív sáv nagyobb score-ral). Pozitív **r** → az első csoport "
            "score-ja valóban nagyobb.*"
        ),
        fig_h2_v,
        mo.plain(df_h2_mw),
    ])
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, df_h2, h2_model, mo, np, pl, plt):
    # ----- H2 Slide 5: Regressziós modell interakcióval -----
    _b0 = h2_model.params["Intercept"]
    _b1 = h2_model.params["sentiment_score"]
    _b2 = h2_model.params["gov"]
    _b3 = h2_model.params["sentiment_score:gov"]
    _b1_p = h2_model.pvalues["sentiment_score"]
    _b3_p = h2_model.pvalues["sentiment_score:gov"]
    _gov_slope = _b1 + _b3

    _xx = np.linspace(0, 1, 100)
    _ind_line = _b0 + _b1 * _xx
    _gov_line = (_b0 + _b2) + (_b1 + _b3) * _xx

    fig_h2_r, _ax = plt.subplots(figsize=(10, 5.2))
    for _pt, _c in [("Kormányközeli", COLOR_GOV), ("Független", COLOR_IND)]:
        _sub = df_h2.filter(pl.col("portal_type") == _pt)
        _ax.scatter(_sub["sentiment_score"].to_numpy(),
                    _sub["norm_score"].to_numpy(),
                    s=9, alpha=0.15, color=_c)
    _ax.plot(_xx, _gov_line, color=COLOR_GOV, linewidth=2.8,
             label=f"Kormányközeli: meredekség = {_gov_slope:+.3f}")
    _ax.plot(_xx, _ind_line, color=COLOR_IND, linewidth=2.8,
             label=f"Független: meredekség = {_b1:+.3f}")
    _ax.set_xlabel("Szentiment (0 = negatív, 1 = pozitív)", fontsize=11)
    _ax.set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=11)
    _ax.set_title("OLS regresszió interakcióval – előrejelzett egyenesek",
                  fontsize=12, fontweight="bold")
    _ax.axvline(0.5, color="grey", ls="--", lw=0.7, alpha=0.5)
    _ax.set_xlim(-0.02, 1.02); _ax.set_ylim(-0.02, 1.05)
    _ax.legend(fontsize=10, loc="upper right")
    fig_h2_r.tight_layout()

    _coef_tbl = pl.DataFrame([
        {"Tag": "β₀ (Intercept, Ind @ sent=0)",
         "becslés": round(float(_b0), 3),
         "p-érték": round(float(h2_model.pvalues["Intercept"]), 4)},
        {"Tag": "β₁ (sentiment, Ind-nél)",
         "becslés": round(float(_b1), 3),
         "p-érték": round(float(_b1_p), 4)},
        {"Tag": "β₂ (Gov alapszint-különbség)",
         "becslés": round(float(_b2), 3),
         "p-érték": round(float(h2_model.pvalues["gov"]), 4)},
        {"Tag": "β₃ (sentiment × gov)",
         "becslés": round(float(_b3), 3),
         "p-érték": round(float(_b3_p), 4)},
    ])

    mo.vstack([
        mo.md(rf"""
        ## 3. lépés – OLS regresszió interakcióval

        $$\text{{norm\_score}} = \beta_0 + \beta_1 \cdot \text{{sent}} + \beta_2 \cdot \text{{gov}} + \beta_3 \cdot (\text{{sent}} \times \text{{gov}})$$

        **R² = {h2_model.rsquared:.4f}** · N = {int(h2_model.nobs)}
        """),
        fig_h2_r,
        mo.plain(_coef_tbl),
        mo.md(
            f"- **β₁ = {_b1:+.3f}** (p = {_b1_p:.4f}) – független portálok meredeksége. "
            f"Negatív, szignifikáns érték → **negatívabb cím → nagyobb hangsúly**.\n"
            f"- **β₃ = {_b3:+.3f}** (p = {_b3_p:.4f}) – interakció: a két portáltípus "
            f"{'**eltérő** erősséggel' if _b3_p < 0.05 else 'hasonló erősséggel'} "
            f"emeli ki a negatív tartalmat.\n"
            f"- Kormányközeli meredekség (β₁+β₃) = **{_gov_slope:+.3f}**."
        ),
    ])
    return


@app.cell(hide_code=True)
def _(df_h2_mw, df_h2_spearman, h2_model, mo, pl):
    # ----- H2 Slide 6: Összesített verdikt -----
    _sp_all = df_h2_spearman.filter(pl.col("Csoport") == "Összes").row(0, named=True)
    _sp_gov = df_h2_spearman.filter(pl.col("Csoport") == "Kormányközeli").row(0, named=True)
    _sp_ind = df_h2_spearman.filter(pl.col("Csoport") == "Független").row(0, named=True)
    _sp_supp = _sp_all["p-érték"] < 0.05 and _sp_all["ρ (Spearman)"] < 0

    _h2t = df_h2_mw.filter(pl.col("Összehasonlítás").is_in(
        ["Negatív vs. Semleges", "Negatív vs. Pozitív"]))
    _nt = _h2t.height
    _ns = _h2t.filter((pl.col("p-érték") < 0.05) & (pl.col("r") > 0)).height
    _mw_supp = _ns >= _nt - 1 and _ns > 0

    _b1 = float(h2_model.params["sentiment_score"])
    _b1_p = float(h2_model.pvalues["sentiment_score"])
    _b3 = float(h2_model.params["sentiment_score:gov"])
    _b3_p = float(h2_model.pvalues["sentiment_score:gov"])
    _gov_slope = _b1 + _b3
    _reg_supp = _b1_p < 0.05 and _b1 < 0

    _score = sum([_sp_supp, _mw_supp, _reg_supp])
    if _score == 3:
        _verdict = "✅ **H2 megerősítve**"
        _desc = "Mindhárom módszer egybehangzóan támogatja a hipotézist."
    elif _score == 2:
        _verdict = "✅ **H2 túlnyomóan megerősítve**"
        _desc = "Két módszer egyértelműen támogatja, a harmadik vegyes képet mutat."
    elif _score == 1:
        _verdict = "⚠️ **H2 részben megerősítve**"
        _desc = "Csak egy módszer támogatja egyértelműen."
    else:
        _verdict = "❌ **H2 nincs megerősítve**"
        _desc = "Egyik módszer sem támogatja érdemben."

    def _ck(b): return "✅" if b else "❌"

    _int_txt = (f"🔥 Az interakció szignifikáns (β₃ = {_b3:+.3f}, p = {_b3_p:.4f}) – "
                f"a két portáltípus **eltérő erősséggel** emeli ki a negatív tartalmat."
                if _b3_p < 0.05 else
                f"Az interakció nem szignifikáns (β₃ = {_b3:+.3f}, p = {_b3_p:.4f}) – "
                f"a hatás **mindkét portáltípusnál hasonló**.")

    mo.md(f"""
    # H2 Verdikt: {_verdict}

    {_desc} *(Bizonyíték-pontszám: **{_score} / 3**)*

    ## Bizonyíték-összefoglaló

    | Lépés | Módszer | Eredmény | H2 támogatva? |
    |---|---|---|---|
    | 1. | Spearman (össz) | ρ = {_sp_all["ρ (Spearman)"]:+.3f}, p = {_sp_all["p-érték"]:.4f} ({_sp_all["Erősség"]}) | {_ck(_sp_supp)} |
    | 2. | Mann-Whitney U | {_ns} / {_nt} H2-irányú teszt szignifikáns | {_ck(_mw_supp)} |
    | 3. | OLS β₁ (sentiment) | β₁ = {_b1:+.3f}, p = {_b1_p:.4f} | {_ck(_reg_supp)} |

    ## Portáltípusonkénti kép

    | Portáltípus | Spearman ρ | Regressziós meredekség |
    |---|---|---|
    | 🔴 Kormányközeli | {_sp_gov["ρ (Spearman)"]:+.3f} (p={_sp_gov["p-érték"]:.4f}) | {_gov_slope:+.3f} |
    | 🔵 Független | {_sp_ind["ρ (Spearman)"]:+.3f} (p={_sp_ind["p-érték"]:.4f}) | {_b1:+.3f} |

    {_int_txt}

    ---

    ### Korlátok
    - A szentiment-pontszámot LLM adja – számszerű hibabecslés nélkül.
    - A `norm_score` portálonként normalizált → csak **relatív** kiemelkedést mér.
    - Az összefüggés **korrelációs**, nem ok-okozati: lehet, hogy a negatív témák
      (katasztrófa, bűnügy) eleve fontosabbak, és ezért kapnak nagyobb helyet.
    """)
    return


@app.cell(hide_code=True)
def _(np, pl):
    # ----- H3 Setup (rejtett): adat, entitás-idősorok, korrelációk, (B) tesztek -----
    from scipy import stats as _scipy_stats

    _GOV = ["Origo", "Magyar Nemzet", "PestiSracok", "Hirado.hu",
            "Ripost", "Metropol", "Mandiner"]
    _IND = ["Telex", "444.hu", "HVG", "ATV", "Magyar Hang",
            "24.hu", "Nepszava", "Valasz Online"]

    _df_hd = pl.read_parquet("data/headlineDefinitions_2026-04-19.parquet")
    _df_llm = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    _df_hl = pl.read_parquet("data/headlines_2026-04-19.parquet")

    _df_vis = (
        _df_hl.select(["hashedId", "score"])
        .group_by("hashedId")
        .agg(pl.col("score").mean().alias("mean_score"))
    )
    _df_base = (
        _df_hd.join(
            _df_llm.select(["hashedId", "sentiment_score", "entities", "label"]),
            on="hashedId", how="left",
        )
        .join(_df_vis, on="hashedId", how="left")
        .with_columns(
            pl.col("_creationTime").cast(pl.Datetime("ms")).dt.date().alias("date"),
            pl.when(pl.col("siteName").is_in(_GOV)).then(pl.lit("Kormányközeli"))
            .when(pl.col("siteName").is_in(_IND)).then(pl.lit("Független"))
            .otherwise(pl.lit("Egyéb"))
            .alias("portal_type"),
        )
    )
    _ss = _df_base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("smin"),
        pl.col("mean_score").max().alias("smax"),
    )
    _df_n = (
        _df_base.join(_ss, on="siteName", how="left")
        .with_columns(
            ((pl.col("mean_score") - pl.col("smin"))
             / (pl.col("smax") - pl.col("smin") + 1e-9)).alias("norm_score")
        ).drop(["smin", "smax"])
    )

    # Entitások denormalizálása
    df_ent = (
        _df_n.filter(pl.col("entities").is_not_null() & (pl.col("entities") != "[]"))
        .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
        .with_columns(
            pl.col("entities").str.strip_chars("[]").str.replace_all('"', "")
            .str.split(", ").alias("elist")
        )
        .explode("elist")
        .rename({"elist": "entity"})
        .filter(pl.col("entity").str.len_chars() > 1)
    )

    # Top entitások, amelyek mindkét típusban megjelennek
    _top = (
        df_ent.group_by("entity")
        .agg(pl.len().alias("n"), pl.col("portal_type").n_unique().alias("nt"))
        .filter(pl.col("nt") == 2)
        .sort("n", descending=True)
        .head(15)["entity"].to_list()
    )

    # Napi idősor porttálonként
    df_daily = (
        df_ent.filter(pl.col("entity").is_in(_top))
        .group_by(["entity", "siteName", "portal_type", "date"])
        .agg(pl.len().alias("mentions"))
    )
    _dates = df_daily["date"].unique().sort()
    _drange = pl.DataFrame({"date": _dates})

    def _corr_matrix(portals):
        _agg = (
            df_daily.filter(pl.col("siteName").is_in(portals))
            .group_by(["siteName", "date"])
            .agg(pl.col("mentions").sum().alias("mentions"))
        )
        _w = _drange.clone()
        _act = []
        for _p in sorted(portals):
            _c = (_agg.filter(pl.col("siteName") == _p)
                  .select(["date", "mentions"]).rename({"mentions": _p}))
            _w = _w.join(_c, on="date", how="left")
            if _w[_p].sum() > 0:
                _act.append(_p)
        _w = _w.fill_null(0).sort("date")
        _n = len(_act)
        _m = np.zeros((_n, _n))
        _offdiag = []
        for _i in range(_n):
            for _j in range(_n):
                _a = _w[_act[_i]].to_numpy().astype(float)
                _b = _w[_act[_j]].to_numpy().astype(float)
                if np.std(_a) > 0 and np.std(_b) > 0:
                    _r, _ = _scipy_stats.pearsonr(_a, _b)
                    _m[_i, _j] = _r
                    if _j > _i:
                        _offdiag.append(_r)
        return _act, _m, float(np.mean(_offdiag)), float(np.std(_offdiag))

    gov_names, gov_mat, gov_r_mean, gov_r_std = _corr_matrix(_GOV)
    ind_names, ind_mat, ind_r_mean, ind_r_std = _corr_matrix(_IND)

    # (B) Porttálspecifikus dinamika: Mann-Whitney entitásonként
    _dyn_rows = []
    for _ent in _top:
        _sub = df_ent.filter(pl.col("entity") == _ent).filter(
            pl.col("sentiment_score").is_not_null() & pl.col("norm_score").is_not_null()
        )
        _gov = _sub.filter(pl.col("portal_type") == "Kormányközeli")
        _ind = _sub.filter(pl.col("portal_type") == "Független")
        if _gov.height < 3 or _ind.height < 3:
            continue
        _gs, _is_ = _gov["sentiment_score"].to_numpy(), _ind["sentiment_score"].to_numpy()
        _gv, _iv = _gov["norm_score"].to_numpy(), _ind["norm_score"].to_numpy()
        _, _ps = _scipy_stats.mannwhitneyu(_gs, _is_, alternative="two-sided")
        _, _pv = _scipy_stats.mannwhitneyu(_gv, _iv, alternative="two-sided")
        _dyn_rows.append({
            "entity": _ent,
            "sent_gov": round(float(_gs.mean()), 3),
            "sent_ind": round(float(_is_.mean()), 3),
            "sent_sig": bool(_ps < 0.05),
            "vis_gov": round(float(_gv.mean()), 3),
            "vis_ind": round(float(_iv.mean()), 3),
            "vis_sig": bool(_pv < 0.05),
        })
    df_dyn = pl.DataFrame(_dyn_rows).with_columns(
        (pl.col("sent_gov") - pl.col("sent_ind")).alias("sent_diff")
    ).sort("sent_diff", descending=True)
    return (
        df_dyn,
        gov_mat,
        gov_names,
        gov_r_mean,
        gov_r_std,
        ind_mat,
        ind_names,
        ind_r_mean,
        ind_r_std,
    )


@app.cell(hide_code=True)
def _(mo):
    # ----- H3 Slide 1: Hipotézis -----
    mo.md(r"""
    # H3 – Napirend-kijelölés (agenda-setting)

    ## Hipotézis – két rész

    **(A) Belső szinkronitás**
    > A **kormányközeli** portálok napi entitás-említései **erősebben korrelálnak
    > egymással**, mint a függetleneké → központosított napirend-kijelölés.

    **(B) Portálspecifikus dinamika**
    > Ugyanazon entitás megjelenésekor a **szentiment és vizuális hangsúly**
    > szignifikánsan eltér a két portáltípus között → a *framing* portálspecifikus.

    ## Módszertan
    1. Entitások denormalizálása (címsor → entitásonként 1 sor)
    2. Top 15 olyan entitás, ami **mindkét** portáltípusban szerepel
    3. **(A)** Napi összes említés portálonként → páronkénti Pearson *r*
       → hőtérkép + átlón kívüli átlag
    4. **(B)** Mann–Whitney U teszt szentimentre és normált vizuális
       prominenciára entitásonként
    """)
    return


@app.cell(hide_code=True)
def _(
    gov_mat,
    gov_names,
    gov_r_mean,
    gov_r_std,
    ind_mat,
    ind_names,
    ind_r_mean,
    ind_r_std,
    mo,
    plt,
):
    # ----- H3 Slide 2: (A) Hőtérképek + skalár összefoglaló -----
    fig_hm, (ax_g, ax_i) = plt.subplots(1, 2, figsize=(15, 6.5))

    _im1 = ax_g.imshow(gov_mat, vmin=-1, vmax=1, cmap="RdYlGn", aspect="auto")
    ax_g.set_xticks(range(len(gov_names))); ax_g.set_yticks(range(len(gov_names)))
    ax_g.set_xticklabels(gov_names, rotation=45, ha="right", fontsize=8)
    ax_g.set_yticklabels(gov_names, fontsize=8)
    ax_g.set_title("Kormányközeli", fontsize=12, fontweight="bold")
    for _i in range(len(gov_names)):
        for _j in range(len(gov_names)):
            ax_g.text(_j, _i, f"{gov_mat[_i, _j]:.2f}", ha="center", va="center",
                      fontsize=7, color="white" if abs(gov_mat[_i, _j]) > 0.6 else "black")
    plt.colorbar(_im1, ax=ax_g, fraction=0.046, pad=0.04)

    _im2 = ax_i.imshow(ind_mat, vmin=-1, vmax=1, cmap="RdYlGn", aspect="auto")
    ax_i.set_xticks(range(len(ind_names))); ax_i.set_yticks(range(len(ind_names)))
    ax_i.set_xticklabels(ind_names, rotation=45, ha="right", fontsize=8)
    ax_i.set_yticklabels(ind_names, fontsize=8)
    ax_i.set_title("Független", fontsize=12, fontweight="bold")
    for _i in range(len(ind_names)):
        for _j in range(len(ind_names)):
            ax_i.text(_j, _i, f"{ind_mat[_i, _j]:.2f}", ha="center", va="center",
                      fontsize=7, color="white" if abs(ind_mat[_i, _j]) > 0.6 else "black")
    plt.colorbar(_im2, ax=ax_i, fraction=0.046, pad=0.04)

    fig_hm.suptitle("(A) Csoporton belüli napirend-szinkronitás – páronkénti Pearson r",
                    fontsize=13, fontweight="bold")
    fig_hm.tight_layout()

    _delta = gov_r_mean - ind_r_mean
    mo.vstack([
        mo.md("## (A) Belső szinkronitás – hőtérkép"),
        fig_hm,
        mo.md(f"""
        | Csoport | Átlag páronkénti *r* (átlón kívül) | Szórás |
        |---|---|---|
        | 🔴 Kormányközeli | **{gov_r_mean:.3f}** | ±{gov_r_std:.3f} |
        | 🔵 Független | **{ind_r_mean:.3f}** | ±{ind_r_std:.3f} |

        **Δr = {_delta:+.3f}** — minél zöldebb egy hőtérkép, annál koordináltabb
        a csoport napirendje. Heurisztikus küszöb: Δr > 0.05 → (A) támogatva.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(COLOR_GOV, COLOR_IND, df_dyn, mo, np, pl, plt):
    # ----- H3 Slide 3: (B) Portálspecifikus dinamika – divergencia-ábra -----
    _ents = df_dyn["entity"].to_list()
    _y = np.arange(len(_ents))
    _bw = 0.35

    fig_div, (ax_s, ax_v) = plt.subplots(1, 2, figsize=(15, 6.5))

    for _ax, _gcol, _icol, _sig, _title, _xl in [
        (ax_s, "sent_gov", "sent_ind", "sent_sig",
         "Szentiment portáltípusonként", "Átlag szentiment (0–1)"),
        (ax_v, "vis_gov", "vis_ind", "vis_sig",
         "Vizuális hangsúly portáltípusonként", "Átlag normált vizuális score"),
    ]:
        _gv = df_dyn[_gcol].to_list()
        _iv = df_dyn[_icol].to_list()
        _sg = df_dyn[_sig].to_list()
        _ax.barh(_y - _bw/2, _gv, _bw, label="Kormányközeli",
                 color=COLOR_GOV, alpha=0.82)
        _ax.barh(_y + _bw/2, _iv, _bw, label="Független",
                 color=COLOR_IND, alpha=0.82)
        for _j in range(len(_ents)):
            if _sg[_j]:
                _ax.text(max(_gv[_j], _iv[_j]) + 0.02, _j, "★",
                         fontsize=12, va="center", color="#e67e22")
        _ax.set_yticks(_y); _ax.set_yticklabels(_ents, fontsize=9)
        _ax.set_xlabel(_xl, fontsize=10)
        _ax.set_title(_title, fontsize=12, fontweight="bold")
        _ax.legend(fontsize=9)
        _ax.grid(True, axis="x", alpha=0.3)

    fig_div.suptitle(
        "(B) Portálspecifikus dinamika – ugyanazon entitások eltérő kezelése\n"
        "(★ = szignifikáns eltérés, Mann–Whitney p < 0.05)",
        fontsize=13, fontweight="bold",
    )
    fig_div.tight_layout()

    _ns_sent = df_dyn.filter(pl.col("sent_sig"))["entity"].len()
    _ns_vis = df_dyn.filter(pl.col("vis_sig"))["entity"].len()
    _nt = df_dyn.height

    mo.vstack([
        mo.md("## (B) Portálspecifikus dinamika"),
        fig_div,
        mo.md(f"""
        - **Szentiment**: **{_ns_sent} / {_nt}** entitásnál szignifikáns eltérés
        - **Vizuális hangsúly**: **{_ns_vis} / {_nt}** entitásnál szignifikáns eltérés

        A csillaggal jelölt entitásoknál mondható ki, hogy a *framing*
        portáltípusonként tudatosan eltér — ugyanaról a szereplőről
        másképp kerül elő a két csoportban.
        """),
    ])
    return


@app.cell(hide_code=True)
def _(df_dyn, gov_r_mean, ind_r_mean, mo, pl):
    # ----- H3 Slide 4: Végső verdikt -----
    _delta = gov_r_mean - ind_r_mean
    _a_supp = _delta > 0.05
    _a_opp = -_delta > 0.05
    _ns_sent = df_dyn.filter(pl.col("sent_sig"))["entity"].len()
    _ns_vis = df_dyn.filter(pl.col("vis_sig"))["entity"].len()
    _nt = df_dyn.height
    _thr = max(3, _nt * 0.3)
    _b_sent = _ns_sent >= _thr
    _b_vis = _ns_vis >= _thr
    _b_supp = _b_sent or _b_vis

    if _a_supp:
        _a_text = (f"✅ **Támogatott.** A kormányközeli átlag *r* "
                   f"({gov_r_mean:.3f}) magasabb, mint a függetleneké "
                   f"({ind_r_mean:.3f}), Δr = {_delta:+.3f}. "
                   "Központosított napirend-kijelölésre utal.")
    elif _a_opp:
        _a_text = (f"❌ **Nem támogatott (ellentétes irány).** A független "
                   f"portálok szinkronizálnak erősebben "
                   f"(r = {ind_r_mean:.3f} vs. {gov_r_mean:.3f}).")
    else:
        _a_text = (f"⚠️ **Nincs érdemi különbség.** Δr = {abs(_delta):.3f} "
                   "a 0.05-ös küszöb alatt.")

    if _b_sent and _b_vis:
        _b_text = (f"✅ **Támogatott mindkét dimenzióban.** Szentiment: "
                   f"{_ns_sent}/{_nt}, vizuális: {_ns_vis}/{_nt}.")
    elif _b_supp:
        _which = "szentiment" if _b_sent else "vizuális hangsúly"
        _b_text = (f"⚠️ **Részben támogatott** – a *{_which}* dimenzióban "
                   f"({_ns_sent}/{_nt} szent., {_ns_vis}/{_nt} vis.).")
    else:
        _b_text = (f"❌ **Nem támogatott.** Sem a szentiment ({_ns_sent}/{_nt}), "
                   f"sem a vizuális hangsúly ({_ns_vis}/{_nt}) nem ér küszöböt.")

    if _a_supp and _b_supp:
        _verdict = ("✅ **H3 összességében támogatott.** A kormányközeli "
                    "portálok koordináltabb napirendet követnek és a közös "
                    "entitások *framing*-je portálspecifikus.")
    elif _a_supp or _b_supp:
        _verdict = "⚠️ **H3 részben támogatott** – csak az egyik részhipotézis igazolódott."
    else:
        _verdict = "❌ **H3 nem támogatott.**"

    mo.md(f"""
    # H3 Verdikt

    ### (A) Belső napirend-szinkronitás
    {_a_text}

    ### (B) Portálspecifikus dinamika
    {_b_text}

    ---

    ## Összesített ítélet
    {_verdict}

    ---

    ### Módszertani fenntartások
    - Az (A) csoportkülönbség nincs formalu00e1lisan tesztelve (permutációs teszt / bootstrap CI hiányzik); a Δr > 0.05 küszöb heurisztikus.
    - A (B) ~30 Mann–Whitney teszt többszörös-összehasonlítási korrekció nélkül
      (α=0.05 mellett ~1.5 hamis pozitív várható).
    - A `norm_score` portálonként normalizált → **relatív** prominenciát mér.
    """)
    return


if __name__ == "__main__":
    app.run()
