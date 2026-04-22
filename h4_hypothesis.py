import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # H4 - Érzelmi töltet és a címlapon eltöltött idő

    **Hipotézis:** A negatív érzelmi töltetű szalagcímek átlagosan kiemeltebbek,
    mint a pozitív érzelmi töltetű szalagcímek.

    Vizsgáljuk ezt összességében és portáltípusonként (kormányközeli vs. független).

    ---

    ## Módszertani kiindulópont

    A `headlines` tábla **minden sora egy ~2 órás scrape-pillanatkép** egy
    címhez. Egy `hashedId`-hoz átlagosan ~7-8 snapshot tartozik, ami azt
    jelenti, hogy minden címnek van egy **címlapi életpályája**: mikor
    jelent meg, meddig maradt fent, milyen vizuális hangsúllyal.

    A H2 hipotézis ezt `mean_score`-ra átlagolta – ezzel viszont elveszik
    az idődimenzió. A H4 pont az idő szerepére kérdez rá, ezért `hashedId`
    szintre aggregálunk **több expozíció-metrikát**:

    | Metrika | Definíció | Mit mér |
    |---|---|---|
    | `dwell_hours` | `n_snapshots × 2` | Mennyi ideig volt címlapon |
    | `mean_score` | snapshot score-ok átlaga | Átlagos vizuális hangsúly |
    | `peak_score` | snapshot score-ok maximuma | Legmagasabb elért kiemelés |
    | `auc_score` | `Σ score × 2h` – score integrál az idő szerint | **Össz-figyelem-expozíció** |
    | `hours_in_top_q` | hány 2h-s ablakban volt a saját portálja felső negyedében | Mennyi időt töltött *kiemelt* pozícióban |

    A portálok score-skálája jelentősen eltér, ezért a `mean_score`,
    `peak_score` és `auc_score` metrikákat **portálonként min-max
    normalizáljuk** (ahogy H2/H3-ban is). A `dwell_hours` és
    `hours_in_top_q` már eleve portál-semleges (órában mérve).
    """)
    return


@app.cell
def _():
    import polars as pl
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt

    return mo, np, pl, plt


@app.cell
def _(pl):
    df_headlineDefinitions = pl.read_parquet(
        "data/headlineDefinitions_2026-04-19.parquet"
    )
    df_llmAnalysis = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    df_headlines = pl.read_parquet("data/headlines_2026-04-19.parquet")
    return df_headlineDefinitions, df_headlines, df_llmAnalysis


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. Leíró összehasonlítás

    ### 1.1 Per-headline expozíció-metrikák építése

    Minden `hashedId`-ra kiszámoljuk az öt metrikát. A `hours_in_top_q`-hoz
    először portálonként meghatározzuk a raw snapshot-`score` felső
    kvartilisét (Q₃), majd minden címnél megszámoljuk, hány 2h-s ablakban
    lépte túl ezt a küszöböt a saját portálján.
    """)
    return


@app.cell
def _(df_headlineDefinitions, df_headlines, pl):
    # Snapshot-szintű tábla site-tel együtt (top-quartile küszöbhöz portálonként)
    _df_snap_with_site = df_headlines.select(
        ["hashedId", "score", "scrapedAt"]
    ).join(
        df_headlineDefinitions.select(["hashedId", "siteName"]).unique(
            subset=["hashedId"]
        ),
        on="hashedId",
        how="inner",
    )

    # Portálonkénti felső kvartilis küszöb a raw snapshot score-on
    _site_topq = _df_snap_with_site.group_by("siteName").agg(
        pl.col("score").quantile(0.75).alias("score_topq")
    )

    _df_snap = _df_snap_with_site.join(
        _site_topq, on="siteName", how="left"
    ).with_columns(
        (pl.col("score") >= pl.col("score_topq")).cast(pl.Int8).alias("is_top_q")
    )

    # Per-hashedId aggregáció
    df_hl_metrics = (
        _df_snap.group_by("hashedId")
        .agg(
            pl.len().alias("n_snapshots"),
            pl.col("score").mean().alias("mean_score"),
            pl.col("score").max().alias("peak_score"),
            pl.col("score").sum().alias("_sum_score"),
            pl.col("is_top_q").sum().alias("_n_snap_top_q"),
        )
        .with_columns(
            (pl.col("n_snapshots") * 2).alias("dwell_hours"),
            (pl.col("_sum_score") * 2).alias("auc_score"),
            (pl.col("_n_snap_top_q") * 2).alias("hours_in_top_q"),
        )
        .drop(["_sum_score", "_n_snap_top_q"])
    )

    df_hl_metrics
    return (df_hl_metrics,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1.2 Metadata hozzáfűzése, portálszintű normalizálás, szentiment-sávok

    - Összekötjük a metrikákat a `siteName`-mel és a szentimenttel.
    - `mean_score`, `peak_score`, `auc_score` portálonként min-max
      normalizálva (`*_norm` oszlopok).
    - Portáltípus besorolás (H2/H3-mal azonos listák).
    - Szentiment-sávok (H2-vel azonos küszöbök): `< 0.35` → **Negatív**,
      `0.35–0.65` → **Semleges**, `> 0.65` → **Pozitív**.
    """)
    return


@app.cell
def _(df_headlineDefinitions, df_hl_metrics, df_llmAnalysis, pl):
    GOV_PORTALS = [
        "Origo", "Magyar Nemzet", "PestiSracok", "Hirado.hu",
        "Ripost", "Metropol", "Mandiner",
    ]
    IND_PORTALS = [
        "Telex", "444.hu", "HVG", "ATV", "Magyar Hang",
        "24.hu", "Nepszava", "Valasz Online",
    ]

    _df = (
        df_hl_metrics.join(
            df_headlineDefinitions.select(["hashedId", "siteName"]).unique(
                subset=["hashedId"]
            ),
            on="hashedId",
            how="left",
        )
        .join(
            df_llmAnalysis.select(
                ["hashedId", "sentiment_score", "sentiment"]
            ).unique(subset=["hashedId"]),
            on="hashedId",
            how="left",
        )
    )

    # Portálonkénti min-max normalizálás a score-alapú metrikákra
    _norm_cols = ["mean_score", "peak_score", "auc_score"]
    _site_stats = _df.group_by("siteName").agg(
        *[pl.col(c).min().alias(f"{c}_min") for c in _norm_cols],
        *[pl.col(c).max().alias(f"{c}_max") for c in _norm_cols],
    )

    df_h4 = (
        _df.join(_site_stats, on="siteName", how="left")
        .with_columns(
            *[
                (
                    (pl.col(c) - pl.col(f"{c}_min"))
                    / (pl.col(f"{c}_max") - pl.col(f"{c}_min") + 1e-9)
                ).alias(f"{c}_norm")
                for c in _norm_cols
            ],
            pl.when(pl.col("siteName").is_in(GOV_PORTALS))
            .then(pl.lit("Kormányközeli"))
            .when(pl.col("siteName").is_in(IND_PORTALS))
            .then(pl.lit("Független"))
            .otherwise(pl.lit("Egyéb"))
            .alias("portal_type"),
        )
        .drop([f"{c}_min" for c in _norm_cols] + [f"{c}_max" for c in _norm_cols])
        .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
        .filter(pl.col("sentiment_score").is_not_null())
        .with_columns(
            pl.when(pl.col("sentiment_score") < 0.35)
            .then(pl.lit("Negatív"))
            .when(pl.col("sentiment_score") <= 0.65)
            .then(pl.lit("Semleges"))
            .otherwise(pl.lit("Pozitív"))
            .alias("sentiment_band")
        )
    )

    df_h4
    return (df_h4,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1.3 Mintaeloszlás (portáltípus × szentiment-sáv)

    Mielőtt a metrikákat összehasonlítanánk, nézzük meg, hányas
    mintaelemszámról beszélünk az egyes cellákban. Aszimmetrikus
    mintaeloszlás (pl. sok Negatív, kevés Pozitív) a medián-összehasonlítást
    nem torzítja, de a statisztikai teszteknél később fontos lesz.
    """)
    return


@app.cell(hide_code=True)
def _(df_h4, mo, pl):
    samples_h4 = (
        df_h4.group_by(["portal_type", "sentiment_band"])
        .agg(pl.len().alias("n"))
        .with_columns(
            (pl.col("n") * 100.0 / pl.col("n").sum().over("portal_type"))
            .round(2)
            .alias("százalék (%)")
        )
        .sort(["portal_type", "sentiment_band"])
    )

    mo.vstack(
        [
            mo.md("#### Mintaeloszlás"),
            mo.ui.table(samples_h4),
        ]
    )
    return (samples_h4,)


@app.cell(hide_code=True)
def _(np, pl, plt, samples_h4):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"
    _BANDS = ["Negatív", "Semleges", "Pozitív"]
    _bw = 0.32

    _gov = samples_h4.filter(pl.col("portal_type") == "Kormányközeli").sort("sentiment_band")
    _ind = samples_h4.filter(pl.col("portal_type") == "Független").sort("sentiment_band")

    fig_dist_h4, ax_d = plt.subplots(figsize=(9, 5))
    _x = np.arange(len(_BANDS))

    _gov_pcts = [
        _gov.filter(pl.col("sentiment_band") == b)["százalék (%)"][0]
        if _gov.filter(pl.col("sentiment_band") == b).height else 0
        for b in _BANDS
    ]
    _ind_pcts = [
        _ind.filter(pl.col("sentiment_band") == b)["százalék (%)"][0]
        if _ind.filter(pl.col("sentiment_band") == b).height else 0
        for b in _BANDS
    ]
    _gov_ns = [
        _gov.filter(pl.col("sentiment_band") == b)["n"][0]
        if _gov.filter(pl.col("sentiment_band") == b).height else 0
        for b in _BANDS
    ]
    _ind_ns = [
        _ind.filter(pl.col("sentiment_band") == b)["n"][0]
        if _ind.filter(pl.col("sentiment_band") == b).height else 0
        for b in _BANDS
    ]

    _bars_gov = ax_d.bar(_x - _bw / 2, _gov_pcts, _bw,
                         label="Kormányközeli", color=_COLOR_GOV, alpha=0.82)
    _bars_ind = ax_d.bar(_x + _bw / 2, _ind_pcts, _bw,
                         label="Független", color=_COLOR_IND, alpha=0.82)

    for _bar, _pct, _n in zip(_bars_gov, _gov_pcts, _gov_ns):
        ax_d.text(_bar.get_x() + _bar.get_width() / 2, _bar.get_height() + 0.6,
                  f"{_pct:.1f}%\n(n={_n})", ha="center", va="bottom",
                  fontsize=9, fontweight="bold", color=_COLOR_GOV)
    for _bar, _pct, _n in zip(_bars_ind, _ind_pcts, _ind_ns):
        ax_d.text(_bar.get_x() + _bar.get_width() / 2, _bar.get_height() + 0.6,
                  f"{_pct:.1f}%\n(n={_n})", ha="center", va="bottom",
                  fontsize=9, fontweight="bold", color=_COLOR_IND)

    ax_d.set_xticks(_x)
    ax_d.set_xticklabels(_BANDS)
    ax_d.set_ylabel("Arány a portáltípuson belül (%)")
    ax_d.set_title("H4 mintaeloszlás – szentiment-sávok portáltípusonként",
                   fontsize=12, fontweight="bold")
    ax_d.legend()
    ax_d.grid(True, axis="y", alpha=0.3)
    fig_dist_h4.tight_layout()
    fig_dist_h4
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1.4 Összefoglaló statisztikai táblázat

    Minden metrikánál a **medián** és az **IQR** (interkvartilis terjedelem,
    Q₃ − Q₁) a legfontosabb leíró szám: a score-eloszlások erősen ferdék
    (kevés nagyon kiemelt, sok alacsony score-ú cím), ezért az átlag
    félrevezető lehet.

    Amit keresünk: **a Negatív sáv medián értékei magasabbak-e a Pozitívnál**
    mindkét portáltípusban, és mindegyik metrikánál?
    """)
    return


@app.cell(hide_code=True)
def _(df_h4, mo, pl):
    _metrics = [
        ("dwell_hours", "Dwell (h)"),
        ("hours_in_top_q", "Óra top-25%-ban"),
        ("mean_score_norm", "Átlag score (norm.)"),
        ("peak_score_norm", "Peak score (norm.)"),
        ("auc_score_norm", "AUC score (norm.)"),
    ]

    _rows = []
    for _pt in ["Kormányközeli", "Független"]:
        for _band in ["Negatív", "Semleges", "Pozitív"]:
            _sub = df_h4.filter(
                (pl.col("portal_type") == _pt) & (pl.col("sentiment_band") == _band)
            )
            _row = {"Portáltípus": _pt, "Szentiment": _band, "n": _sub.height}
            for _col, _label in _metrics:
                _med = _sub[_col].median()
                _q1 = _sub[_col].quantile(0.25)
                _q3 = _sub[_col].quantile(0.75)
                _row[f"{_label} medián"] = round(float(_med), 3) if _med is not None else None
                _row[f"{_label} IQR"] = (
                    round(float(_q3 - _q1), 3) if (_q1 is not None and _q3 is not None) else None
                )
            _rows.append(_row)

    df_summary_h4 = pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md(
                "#### Medián és IQR portáltípus × szentiment-sáv × metrika bontásban"
            ),
            mo.ui.table(df_summary_h4),
        ]
    )
    return (df_summary_h4,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### 1.5 Boxplotok metrikánként

    Minden metrikához egy külön panel: a három szentiment-sáv boxplotja
    egymás mellett, **portáltípusonként színezve**. A H4 hipotézis
    (negatívabb cím → nagyobb kiemelés / hosszabb idő) **akkor látszik
    vizuálisan**, ha a boxok **balról jobbra lefelé lejtenek** (Negatív
    sáv a legmagasabban).

    A `dwell_hours` és `auc_score` eloszlásai erősen jobbra ferdék (sok
    rövid életű cím, kevés nagyon tartós), ezért ezeket **log-skálán**
    mutatjuk a jobb összehasonlíthatóság érdekében.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### 📦 Mi az a boxplot és hogyan kell olvasni?

    A boxplot (dobozdiagram) egy eloszlást **öt számmal** foglal össze –
    gyakorlatilag egy „eloszlás-ujjlenyomat". Nem azt mutatja meg, hogy
    mennyi az átlag, hanem azt, hogy **hol helyezkedik el az értékek
    középső 50%-a**, és hogy az eloszlás szimmetrikus vagy ferde-e.

    ```
                  ┌──────┬──────┐
       ├──────────┤  Q2  │      ├──────────┤
                  └──────┴──────┘
       │          │      │      │          │
      alsó       Q1   medián   Q3         felső
     „bajusz"   (25%)  (50%)  (75%)       „bajusz"
    ```

    | Elem | Jelentés |
    |---|---|
    | **Doboz alja (Q1)** | Az értékek alsó negyede itt végződik – a minta 25%-a ez alatt van |
    | **Doboz belső vonala (medián, Q2)** | Az adatok **fele** e felett, fele e alatt – ez a „tipikus" érték |
    | **Doboz teteje (Q3)** | A minta 75%-a ez alatt van, a felső 25% felette |
    | **Doboz magassága = IQR** | Interkvartilis terjedelem (Q3 − Q1): **a középső 50% szórása** |
    | **Bajuszok** | A „nem-outlier" tartomány széle (általában Q1 − 1.5×IQR és Q3 + 1.5×IQR) |
    | **Pontok a bajuszon kívül** | Kiugró értékek (outlierek) – itt le vannak kapcsolva a jobb olvashatóságért |

    **Hogyan értelmezd H4 szempontjából?**

    | Ami látszik a boxon | Mit jelent |
    |---|---|
    | A **medián vonal feljebb van** a Negatív csoportban, mint a Pozitívban | A negatív címek tipikusan magasabb értéket érnek el az adott metrikán → **H4-kompatibilis** |
    | A doboz **magasabb pozícióba csúszik** Negatív → Pozitív irányban lépegetve | A teljes középső 50% elmozdul – robusztus jele a különbségnek |
    | A dobozok **átfednek egymással** | A különbség valószínűleg **nem szignifikáns** – a két csoport hasonló eloszlást mutat |
    | A **doboz nagyon magas (nagy IQR)** | Nagy a szórás a csoporton belül – egy-egy cím teljesítménye sokban eltérhet |
    | **Ferde doboz** (medián nem középen) | Az eloszlás ferde – jelen esetben legtöbbször jobbra ferdít (a medián a doboz aljához közelebb) |

    **Fontos:** a boxplot **vizuális előtanulmány**, nem statisztikai teszt.
    Két doboz átfedése *nem* azonos a szignifikanciával – azt a Mann–Whitney
    tesztek fogják eldönteni a következő szakaszban. Itt most az a célunk,
    hogy lássuk, **van-e egyáltalán szemmel látható mintázat**, és ha igen,
    **milyen irányú**.
    """)
    return


@app.cell(hide_code=True)
def _(df_h4, np, pl, plt):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"
    _BANDS = ["Negatív", "Semleges", "Pozitív"]

    _metrics = [
        ("dwell_hours", "Dwell (óra)", True),
        ("hours_in_top_q", "Idő a portál top-25%-ában (óra)", False),
        ("mean_score_norm", "Átlag score (portálon belül normalizált)", False),
        ("peak_score_norm", "Peak score (portálon belül normalizált)", False),
        ("auc_score_norm", "AUC score = Σ score × 2h (norm.)", False),
    ]

    _n = len(_metrics)
    _cols = 2
    _rows = (_n + 1) // _cols

    fig_box_h4, axes_box = plt.subplots(_rows, _cols, figsize=(15, 4.5 * _rows))
    axes_box = axes_box.flatten()

    _bw = 0.32
    _x = np.arange(len(_BANDS))

    for _i, (_col, _label, _use_log) in enumerate(_metrics):
        _ax = axes_box[_i]

        _gov_data = [
            df_h4.filter(
                (pl.col("portal_type") == "Kormányközeli")
                & (pl.col("sentiment_band") == _b)
            )[_col].drop_nulls().to_numpy()
            for _b in _BANDS
        ]
        _ind_data = [
            df_h4.filter(
                (pl.col("portal_type") == "Független")
                & (pl.col("sentiment_band") == _b)
            )[_col].drop_nulls().to_numpy()
            for _b in _BANDS
        ]

        _bp_gov = _ax.boxplot(
            _gov_data,
            positions=_x - _bw / 2,
            widths=_bw * 0.9,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color="black", linewidth=1.5),
        )
        for _patch in _bp_gov["boxes"]:
            _patch.set_facecolor(_COLOR_GOV)
            _patch.set_alpha(0.65)

        _bp_ind = _ax.boxplot(
            _ind_data,
            positions=_x + _bw / 2,
            widths=_bw * 0.9,
            patch_artist=True,
            showfliers=False,
            medianprops=dict(color="black", linewidth=1.5),
        )
        for _patch in _bp_ind["boxes"]:
            _patch.set_facecolor(_COLOR_IND)
            _patch.set_alpha(0.65)

        # Medián-érték feliratok a boxok fölé
        for _j, _d in enumerate(_gov_data):
            if len(_d) > 0:
                _ax.text(_x[_j] - _bw / 2, np.median(_d),
                         f"{np.median(_d):.2f}", ha="center", va="bottom",
                         fontsize=7, color=_COLOR_GOV, fontweight="bold")
        for _j, _d in enumerate(_ind_data):
            if len(_d) > 0:
                _ax.text(_x[_j] + _bw / 2, np.median(_d),
                         f"{np.median(_d):.2f}", ha="center", va="bottom",
                         fontsize=7, color=_COLOR_IND, fontweight="bold")

        _ax.set_xticks(_x)
        _ax.set_xticklabels(_BANDS)
        _ax.set_title(_label, fontsize=11, fontweight="bold")
        _ax.grid(True, axis="y", alpha=0.3)
        if _use_log:
            _ax.set_yscale("log")

    # Közös legend
    from matplotlib.patches import Patch
    _legend = [
        Patch(facecolor=_COLOR_GOV, alpha=0.65, label="Kormányközeli"),
        Patch(facecolor=_COLOR_IND, alpha=0.65, label="Független"),
    ]
    axes_box[0].legend(handles=_legend, loc="upper right", fontsize=9)

    # Ha páratlan, utolsó üres
    for _j in range(_n, len(axes_box)):
        axes_box[_j].set_visible(False)

    fig_box_h4.suptitle(
        "H4 – Expozíció-metrikák szentiment-sáv és portáltípus szerint",
        fontsize=13, fontweight="bold", y=1.00,
    )
    fig_box_h4.tight_layout()
    fig_box_h4
    return


@app.cell(hide_code=True)
def _(df_summary_h4, mo, pl):
    # Vizuális iránymutató: melyik metrikánál melyik portáltípusban lejt-e
    # a medián a Negatív → Pozitív irányban (H4-kompatibilis minta)?
    _metric_labels = [
        "Dwell (h)",
        "Óra top-25%-ban",
        "Átlag score (norm.)",
        "Peak score (norm.)",
        "AUC score (norm.)",
    ]

    _rows = []
    for _label in _metric_labels:
        _col = f"{_label} medián"
        _row = {"Metrika": _label}
        for _pt in ["Kormányközeli", "Független"]:
            _neg = df_summary_h4.filter(
                (pl.col("Portáltípus") == _pt) & (pl.col("Szentiment") == "Negatív")
            )[_col][0]
            _pos = df_summary_h4.filter(
                (pl.col("Portáltípus") == _pt) & (pl.col("Szentiment") == "Pozitív")
            )[_col][0]
            _diff = (_neg or 0) - (_pos or 0)
            _row[f"{_pt} Δ (Neg − Poz)"] = round(_diff, 3)
            _row[f"{_pt} irány"] = (
                "✅ H4-konform" if _diff > 0 else ("↔ közel azonos" if abs(_diff) < 1e-3 else "❌ ellentétes")
            )
        _rows.append(_row)

    import polars as _pl
    df_direction = _pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md(r"""
    ### 1.6 Iránymutató összefoglaló

    Az alábbi táblázat metrikánként és portáltípusonként mutatja a
    **Negatív − Pozitív medián különbséget**. Pozitív Δ → a negatív címek
    magasabb értéket érnek el → **H4-kompatibilis** irány. A formális
    statisztikai teszteket (Mann–Whitney, Spearman, survival, regresszió)
    a következő szakaszok tartalmazzák majd.
            """),
            mo.ui.table(df_direction),
        ]
    )
    return


if __name__ == "__main__":
    app.run()
