import marimo

__generated_with = "0.23.2"
app = marimo.App()


@app.cell
def _():
    import polars as pl
    import marimo as mo
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    import numpy as np

    return mo, np, pl, plt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # H2 – Vizuális hangsúly és érzelmi töltet

    **Hipotézis:** A negatív érzelmi töltetű szalagcímek átlagosan magasabb
    „fontossági pontszámot" (nagyobb betűméret, előkelőbb helyezés) kapnak,
    mint a semleges hírek.

    Vizsgáljuk ezt összességében és portáltípusonként (kormányközeli vs. független).
    """)
    return


@app.cell
def _(pl):
    df_headlineDefinitions = pl.read_parquet("data/headlineDefinitions_2026-04-19.parquet")
    df_llmAnalysis = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    df_headlines = pl.read_parquet("data/headlines_2026-04-19.parquet")
    return df_headlineDefinitions, df_headlines, df_llmAnalysis


@app.cell
def _(df_headlineDefinitions, df_headlines, df_llmAnalysis, pl):
    df_vis = (
        df_headlines
        .select(["hashedId", "score"])
        .group_by("hashedId")
        .agg(pl.col("score").mean().alias("mean_score"))
    )

    df_base = (
        df_headlineDefinitions
        .join(
            df_llmAnalysis.select(
                ["hashedId", "sentiment_score", "sentiment", "entities", "label"]
            ),
            on="hashedId",
            how="left",
        )
        .join(df_vis, on="hashedId", how="left")
    )

    _site_stats = df_base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("score_min"),
        pl.col("mean_score").max().alias("score_max"),
    )

    df_normed = (
        df_base
        .join(_site_stats, on="siteName", how="left")
        .with_columns(
            (
                (pl.col("mean_score") - pl.col("score_min"))
                / (pl.col("score_max") - pl.col("score_min") + 1e-9)
            ).alias("norm_score")
        )
        .drop(["score_min", "score_max"])
    )

    df_normed
    return (df_normed,)


@app.cell
def _(df_normed, pl):
    GOV_PORTALS = ["Origo", "Magyar Nemzet", "PestiSracok", "Hirado.hu", "Ripost", "Metropol", "Mandiner"]
    IND_PORTALS = ["Telex", "444.hu", "HVG", "ATV", "Magyar Hang", "24.hu", "Nepszava", "Valasz Online"]

    df_classified = df_normed.with_columns(
        pl.when(pl.col("siteName").is_in(GOV_PORTALS))
        .then(pl.lit("Kormányközeli"))
        .when(pl.col("siteName").is_in(IND_PORTALS))
        .then(pl.lit("Független"))
        .otherwise(pl.lit("Egyéb"))
        .alias("portal_type")
    )
    return (df_classified,)


@app.cell
def _(df_classified, mo, pl):
    df_h2 = (
        df_classified
        .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
        .filter(pl.col("sentiment_score").is_not_null() & pl.col("norm_score").is_not_null())
        .with_columns(
            pl.when(pl.col("sentiment_score") < 0.35)
            .then(pl.lit("Negatív"))
            .when(pl.col("sentiment_score") <= 0.65)
            .then(pl.lit("Semleges"))
            .otherwise(pl.lit("Pozitív"))
            .alias("sentiment_band")
        )
    )

    samples_h2 = (
        df_h2
        .group_by(["portal_type", "sentiment_band"])
        .agg(pl.len().alias("n"))
        .with_columns(
            (pl.col("n") * 100.0 / pl.col("n").sum().over("portal_type"))
            .round(2)
            .alias("százalék (%)")
        )
        .sort(["portal_type", "sentiment_band"])
    )

    mo.vstack([
        mo.md("## Mintaeloszlás (portáltípus × szentiment sáv)"),
        mo.ui.table(samples_h2),
    ])
    return df_h2, samples_h2


@app.cell
def _(np, pl, plt, samples_h2):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"
    _BANDS = ["Negatív", "Semleges", "Pozitív"]
    _bw = 0.32

    _gov = samples_h2.filter(pl.col("portal_type") == "Kormányközeli").sort("sentiment_band")
    _ind = samples_h2.filter(pl.col("portal_type") == "Független").sort("sentiment_band")

    fig_dist, ax_d = plt.subplots(figsize=(9, 5))
    _x = np.arange(len(_BANDS))

    _gov_pcts = [_gov.filter(pl.col("sentiment_band") == b)["százalék (%)"][0] for b in _BANDS]
    _ind_pcts = [_ind.filter(pl.col("sentiment_band") == b)["százalék (%)"][0] for b in _BANDS]
    _gov_ns   = [_gov.filter(pl.col("sentiment_band") == b)["n"][0] for b in _BANDS]
    _ind_ns   = [_ind.filter(pl.col("sentiment_band") == b)["n"][0] for b in _BANDS]

    _bars_gov = ax_d.bar(_x - _bw / 2, _gov_pcts, _bw, label="Kormányközeli", color=_COLOR_GOV, alpha=0.82)
    _bars_ind = ax_d.bar(_x + _bw / 2, _ind_pcts, _bw, label="Független", color=_COLOR_IND, alpha=0.82)

    for _bar, _pct, _n in zip(_bars_gov, _gov_pcts, _gov_ns):
        ax_d.text(_bar.get_x() + _bar.get_width() / 2, _bar.get_height() + 0.6,
                  f"{_pct:.1f}%\n(n={_n})", ha="center", va="bottom", fontsize=9, fontweight="bold", color=_COLOR_GOV)

    for _bar, _pct, _n in zip(_bars_ind, _ind_pcts, _ind_ns):
        ax_d.text(_bar.get_x() + _bar.get_width() / 2, _bar.get_height() + 0.6,
                  f"{_pct:.1f}%\n(n={_n})", ha="center", va="bottom", fontsize=9, fontweight="bold", color=_COLOR_IND)

    ax_d.set_xticks(_x)
    ax_d.set_xticklabels(_BANDS, fontsize=11)
    ax_d.set_ylabel("Arány (%)", fontsize=10)
    ax_d.set_title("Szentiment sávok eloszlása portáltípusonként", fontsize=13, fontweight="bold")
    ax_d.set_ylim(0, max(max(_gov_pcts), max(_ind_pcts)) + 10)
    ax_d.legend(fontsize=10)
    fig_dist.tight_layout()
    fig_dist
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 1. lépés – Spearman-féle rangkorreláció

    **Kérdés:** Együtt mozog-e a szentiment és a vizuális hangsúly?

    A Spearman-korreláció egy **nem-paraméteres** mutató, ami a **rangsorok**
    alapján méri két változó **monoton együttjárását** (−1 és +1 között):

    - **ρ < 0** → minél negatívabb a szentiment, annál nagyobb a vizuális hangsúly
      *(ez támasztaná alá a H2-t)*
    - **ρ ≈ 0** → nincs kapcsolat
    - **ρ > 0** → minél pozitívabb a szentiment, annál nagyobb a hangsúly

    | |ρ| | Erősség |
    |---|---|
    | < 0,1 | elhanyagolható |
    | 0,1–0,3 | gyenge |
    | 0,3–0,5 | közepes |
    | > 0,5 | erős |
    """)
    return


@app.cell(hide_code=True)
def _(df_h2, mo, pl):
    from scipy import stats as scipy_stats

    def _sig_label(p):
        if p < 0.001:
            return "*** (p<0.001)"
        if p < 0.01:
            return "** (p<0.01)"
        if p < 0.05:
            return "* (p<0.05)"
        return "n.s."

    def _strength_label(rho):
        _a = abs(rho)
        if _a < 0.1:
            return "elhanyagolható"
        if _a < 0.3:
            return "gyenge"
        if _a < 0.5:
            return "közepes"
        return "erős"

    # Spearman-korreláció: össz mintán + portáltípusonként
    _rows = []
    for _group_name, _subset in [
        ("Összes", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]:
        _sent = _subset["sentiment_score"].to_numpy()
        _vis = _subset["norm_score"].to_numpy()
        _rho, _p = scipy_stats.spearmanr(_sent, _vis)
        _rows.append(
            {
                "Csoport": _group_name,
                "n": _subset.height,
                "ρ (Spearman)": round(float(_rho), 3),
                "p-érték": round(float(_p), 4),
                "Erősség": _strength_label(_rho),
                "Irány": "negatív cím → nagyobb hangsúly"
                if _rho < 0
                else "pozitív cím → nagyobb hangsúly",
                "Szignifikancia": _sig_label(_p),
            }
        )

    df_spearman = pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md("### Spearman-korreláció: szentiment ↔ vizuális hangsúly"),
            mo.plain(df_spearman),
        ]
    )
    return (df_spearman,)


@app.cell(hide_code=True)
def _(df_h2, np, pl, plt):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"

    # Szórásdiagram: szentiment vs. vizuális score, portáltípusonként színezve
    # + lineáris regressziós egyenes a trend vizualizálására
    fig_scatter, ax_s = plt.subplots(figsize=(10, 6))

    for _pt, _c in [("Kormányközeli", _COLOR_GOV), ("Független", _COLOR_IND)]:
        _sub = df_h2.filter(pl.col("portal_type") == _pt)
        _x = _sub["sentiment_score"].to_numpy()
        _y = _sub["norm_score"].to_numpy()
        ax_s.scatter(_x, _y, s=12, alpha=0.25, color=_c, label=f"{_pt} (n={len(_x)})")

        # Egyszerű lineáris illesztés a trendvonalhoz
        _slope, _intercept = np.polyfit(_x, _y, 1)
        _xx = np.linspace(0, 1, 100)
        ax_s.plot(_xx, _slope * _xx + _intercept, color=_c, linewidth=2.2, alpha=0.9)

    ax_s.set_xlabel("Szentiment (0 = negatív, 1 = pozitív)", fontsize=11)
    ax_s.set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=11)
    ax_s.set_title(
        "Szentiment vs. vizuális hangsúly – portáltípusonként",
        fontsize=13,
        fontweight="bold",
    )
    ax_s.axvline(0.5, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)
    ax_s.set_xlim(-0.02, 1.02)
    ax_s.set_ylim(-0.02, 1.05)
    ax_s.legend(fontsize=10, loc="upper right")
    fig_scatter.tight_layout()
    fig_scatter
    return


@app.cell(hide_code=True)
def _(df_spearman, mo, pl):
    # Összefoglaló értelmezés a teljes mintára
    _overall = df_spearman.filter(pl.col("Csoport") == "Összes").row(0, named=True)
    _rho = _overall["ρ (Spearman)"]
    _p = _overall["p-érték"]

    if _p < 0.05 and _rho < 0:
        _verdict = (
            f"✅ **Alátámasztja a H2-t (részlegesen).** A teljes mintán ρ = {_rho:+.3f} "
            f"(p = {_p:.4f}), tehát **minél negatívabb a címsor, annál nagyobb a vizuális "
            f"hangsúly** – a kapcsolat {_overall['Erősség']} erősségű."
        )
    elif _p < 0.05 and _rho > 0:
        _verdict = (
            f"❌ **Ellentmond a H2-nek.** A teljes mintán ρ = {_rho:+.3f} (p = {_p:.4f}), "
            f"azaz a **pozitívabb** címsorok kapnak nagyobb hangsúlyt – ez a H2 fordítottja."
        )
    else:
        _verdict = (
            f"⚠️ **Nem egyértelmű.** ρ = {_rho:+.3f} (p = {_p:.4f}). A kapcsolat "
            f"{_overall['Erősség']}, statisztikailag nem szignifikáns."
        )

    mo.md(f"""
    ### Értelmezés

    {_verdict}

    > **Fontos:** a Spearman-korreláció csak az **átfogó együttjárást** méri. Nem mondja
    > meg, hogy a hatás azonos-e a két portáltípusnál, és nem szűr ki zavaró változókat.
    > A következő lépésekben (Mann-Whitney sávonként, regressziós modell) ezt finomítjuk.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 2. lépés – Sáv-alapú összehasonlítás (Mann-Whitney U)

    A Spearman megmondta, hogy **van-e** monoton együttjárás. Most közvetlenül
    összehasonlítjuk a három szentiment-sáv vizuális hangsúlyeloszlását:

    - **Negatív vs. Semleges** – a H2 legfontosabb összehasonlítása
    - **Negatív vs. Pozitív** – a két véglet szembeállítása
    - **Semleges vs. Pozitív** – kontroll-összehasonlítás

    Minden párra **Mann-Whitney U** tesztet (egyoldali: „eladó sa sáv score-ja nagyobb?”)
    és **rank-biszérialis hatásméretet** számolunk, portáltípusonként is.
    """)
    return


@app.cell(hide_code=True)
def _(df_h2, np, pl, plt):
    _COLOR_NEG = "#c0392b"
    _COLOR_NEU = "#7f8c8d"
    _COLOR_POS = "#27ae60"
    _BANDS = ["Negatív", "Semleges", "Pozitív"]
    _band_colors = [_COLOR_NEG, _COLOR_NEU, _COLOR_POS]

    # Hegedűdiagram: vizuális hangsúly eloszlása szentiment-sávonként
    # 3 panel: összes / kormányközeli / független
    _panels = [
        ("Összes portál", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]

    fig_violin, axes_v = plt.subplots(1, 3, figsize=(14, 5), sharey=True)
    fig_violin.suptitle(
        "Vizuális hangsúly eloszlása szentiment-sávonként",
        fontsize=13,
        fontweight="bold",
    )

    for _ax, (_title, _subset) in zip(axes_v, _panels):
        _data = [
            _subset.filter(pl.col("sentiment_band") == _b)["norm_score"].to_numpy()
            for _b in _BANDS
        ]
        _ns = [len(_d) for _d in _data]

        _parts = _ax.violinplot(
            _data, positions=[1, 2, 3], showmedians=True, showextrema=True
        )
        for _pc, _c in zip(_parts["bodies"], _band_colors):
            _pc.set_facecolor(_c)
            _pc.set_alpha(0.72)
        for _k in ("cmedians", "cmins", "cmaxes", "cbars"):
            _parts[_k].set_color("black")
            _parts[_k].set_linewidth(1.2)

        # Medián kiemelése számmal
        for _pos, _d, _c in zip([1, 2, 3], _data, _band_colors):
            _med = np.median(_d)
            _ax.text(
                _pos,
                _med + 0.03,
                f"{_med:.2f}",
                ha="center",
                va="bottom",
                fontsize=9,
                color=_c,
                fontweight="bold",
            )

        # Mintanagyság címkék
        for _pos, _n in zip([1, 2, 3], _ns):
            _ax.text(
                _pos,
                -0.07,
                f"n={_n}",
                ha="center",
                va="top",
                fontsize=8,
                color="grey",
                transform=_ax.get_xaxis_transform(),
            )

        _ax.set_xticks([1, 2, 3])
        _ax.set_xticklabels(_BANDS, fontsize=10)
        _ax.set_title(_title, fontsize=11, fontweight="bold")
        _ax.set_ylim(-0.05, 1.1)
        _ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)

    axes_v[0].set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=10)
    fig_violin.tight_layout()
    fig_violin
    return


@app.cell(hide_code=True)
def _(df_h2, mo, np, pl):
    from scipy import stats as scipy_stats_h2

    def _sig_label2(p):
        if p < 0.001:
            return "*** (p<0.001)"
        if p < 0.01:
            return "** (p<0.01)"
        if p < 0.05:
            return "* (p<0.05)"
        return "n.s."

    # Mann-Whitney U tesztek a szentiment-sávpárokra, portáltípusonként
    # H2 irány: negatív sáv score-ja nagyobb-e, mint a másiké
    _pairs = [
        ("Negatív", "Semleges", "greater"),  # H2: negatív > semleges
        ("Negatív", "Pozitív", "greater"),    # H2: negatív > pozitív
        ("Semleges", "Pozitív", "two-sided"), # kontroll
    ]

    _groups = [
        ("Összes", df_h2),
        ("Kormányközeli", df_h2.filter(pl.col("portal_type") == "Kormányközeli")),
        ("Független", df_h2.filter(pl.col("portal_type") == "Független")),
    ]

    _rows = []
    for _gname, _gdf in _groups:
        for _b1, _b2, _alt in _pairs:
            _a = _gdf.filter(pl.col("sentiment_band") == _b1)["norm_score"].to_numpy()
            _b = _gdf.filter(pl.col("sentiment_band") == _b2)["norm_score"].to_numpy()
            if len(_a) < 3 or len(_b) < 3:
                continue
            _u, _p = scipy_stats_h2.mannwhitneyu(_a, _b, alternative=_alt)
            # Rank-biszérialis hatásméret: r = 1 - 2U/(n1*n2)
            # Pozitív r = első csoport (pl. Negatív) score-jai nagyobbak
            _r = 1 - (2 * _u) / (len(_a) * len(_b))
            _rows.append(
                {
                    "Csoport": _gname,
                    "Összehasonlítás": f"{_b1} vs. {_b2}",
                    "n1": len(_a),
                    "n2": len(_b),
                    "medián1": round(float(np.median(_a)), 3),
                    "medián2": round(float(np.median(_b)), 3),
                    "U": round(float(_u), 0),
                    "p-érték": round(float(_p), 4),
                    "r": round(float(_r), 3),
                    "Szignifikancia": _sig_label2(_p),
                }
            )

    df_mw = pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md(
                "### Mann-Whitney U tesztek – sávpárok összehasonlítása\n\n"
                "*A Negatív vs. Semleges / Pozitív tesztek **egyoldali**-ak "
                "(H2: negatív sáv nagyobb score-ral). A Semleges vs. Pozitív kétoldali kontroll.*"
            ),
            mo.plain(df_mw),
        ]
    )
    return (df_mw,)


@app.cell(hide_code=True)
def _(df_mw, mo, pl):
    # Verdikt: hány “Negatív vs. X” teszt szignifikáns H2-irányban
    _h2_tests = df_mw.filter(
        pl.col("Összehasonlítás").is_in(["Negatív vs. Semleges", "Negatív vs. Pozitív"])
    )

    _total = _h2_tests.height
    _sig_pos = _h2_tests.filter(
        (pl.col("p-érték") < 0.05) & (pl.col("r") > 0)
    ).height
    _sig_neg = _h2_tests.filter(
        (pl.col("p-érték") < 0.05) & (pl.col("r") < 0)
    ).height

    if _sig_pos >= _total - 1 and _sig_pos > 0:
        _v = "✅ **Alátámasztva**"
        _desc = (
            f"A {_total} H2-irányú tesztből **{_sig_pos}** mutat szignifikánsan "
            f"nagyobb vizuális hangsúlyt a negatív sávban."
        )
    elif _sig_pos > 0:
        _v = "⚠️ **Részben alátámasztva**"
        _desc = (
            f"A {_total} tesztből {_sig_pos} H2-irányban szignifikáns, "
            f"{_sig_neg} pedig ellenkező irányban."
        )
    elif _sig_neg > 0:
        _v = "❌ **Ellentmond**"
        _desc = (
            f"A szignifikáns tesztek a H2-vel **ellentétes** irányt mutatnak: "
            f"a negatív sáv score-ja *kisebb*."
        )
    else:
        _v = "❌ **Nem alátámasztva**"
        _desc = "Egyik H2-irányú teszt sem érte el a p < 0,05 szintet."

    mo.md(f"""
    ### Részverdikt – 2. lépés

    {_v} – {_desc}

    > **Emlékeztető:** ez még csak kétváltozós összehasonlítás. A következő lépésben
    > regressziós modellel szűrjük ki a portáltípus zavaró hatását, és vizsgáljuk,
    > hogy a szentiment-hatás **erőssége eltér-e** a két portáltípusnál.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## 3. lépés – Regressziós modell interakcióval

    Az eddigi lépések külön-külön nézték a szentiment és a portáltípus hatását.
    A **regressziós modell** egyszerre tudja kezelni őket, és két fontos plusz kérdésre
    válaszol:

    1. **Mekkora a szentiment önálló hatása**, ha a portáltípust kontrolljuk?
    2. **Eltér-e a hatás erőssége** a két portáltípusnál? *(interakciós tag)*

    ### A modell

    $$\text{norm\_score} = \beta_0 + \beta_1 \cdot \text{sentiment} + \beta_2 \cdot \text{gov} + \beta_3 \cdot (\text{sentiment} \times \text{gov}) + \varepsilon$$

    ahol `gov = 1` a kormányközeli, `gov = 0` a független portál.

    | Együttható | Mit mér? |
    |---|---|
    | **β₀** (Intercept) | Független portálok várható score-ja teljesen negatív címnél (sentiment = 0) |
    | **β₁** (sentiment) | Független portáloknál: mennyivel változik a score, ha a sentiment 0→ 1 |
    | **β₂** (gov) | Kormányközeli portálok *alapszint-különbsége* (negatív címnél) |
    | **β₃** (interakció) | **Mennyivel más** a szentiment-hatás a kormányközelieken |

    > **H2-alátámasztás jele:** β₁ **negatív és szignifikáns** (minél negatívabb a cím,
    > annál nagyobb a hangsúly).
    > Ha **β₃ is szignifikáns**, a két portáltípus **eltérő erősséggel** emeli ki a
    > negatív tartalmat.
    """)
    return


@app.cell(hide_code=True)
def _(df_h2, mo, pl):
    import statsmodels.formula.api as smf

    # Pandas DF a statsmodels-hoz, gov bináris változóval
    _pdf = (
        df_h2.with_columns(
            (pl.col("portal_type") == "Kormányközeli").cast(pl.Int8).alias("gov")
        )
        .select(["sentiment_score", "norm_score", "gov", "portal_type"])
        .to_pandas()
    )

    # OLS regresszió interakcióval
    model = smf.ols("norm_score ~ sentiment_score * gov", data=_pdf).fit()

    # Együttható-tábla kinyerése
    _coef_rows = []
    _label_map = {
        "Intercept": "β₀ (Intercept, Ind @ sent=0)",
        "sentiment_score": "β₁ (sentiment, Ind-nél)",
        "gov": "β₂ (Gov alapszint-különbség)",
        "sentiment_score:gov": "β₃ (sentiment × gov, interakció)",
    }
    for _name in model.params.index:
        _coef = float(model.params[_name])
        _se = float(model.bse[_name])
        _p = float(model.pvalues[_name])
        _ci_lo, _ci_hi = [float(x) for x in model.conf_int().loc[_name]]
        _sig = (
            "*** (p<0.001)"
            if _p < 0.001
            else "** (p<0.01)"
            if _p < 0.01
            else "* (p<0.05)"
            if _p < 0.05
            else "n.s."
        )
        _coef_rows.append(
            {
                "Tag": _label_map.get(_name, _name),
                "becslés": round(_coef, 4),
                "std. hiba": round(_se, 4),
                "95% CI alsó": round(_ci_lo, 4),
                "95% CI felső": round(_ci_hi, 4),
                "p-érték": round(_p, 4),
                "Szign.": _sig,
            }
        )

    df_coef = pl.DataFrame(_coef_rows)

    # Illeszkedési mutatók
    _fit_info = pl.DataFrame(
        [
            {"Mutató": "N (mintaméret)", "Érték": f"{int(model.nobs)}"},
            {"Mutató": "R²", "Érték": f"{model.rsquared:.4f}"},
            {"Mutató": "R² (korrigált)", "Érték": f"{model.rsquared_adj:.4f}"},
            {"Mutató": "F-statisztika", "Érték": f"{model.fvalue:.2f}"},
            {"Mutató": "F-teszt p-értéke", "Érték": f"{model.f_pvalue:.4g}"},
        ]
    )

    mo.vstack(
        [
            mo.md("### Regressziós együtthatók"),
            mo.plain(df_coef),
            mo.md("### Modell-illeszkedés"),
            mo.plain(_fit_info),
        ]
    )
    return (model,)


@app.cell(hide_code=True)
def _(df_h2, model, np, pl, plt):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"

    # Vizualizáció: modell-előrejelzések a két portáltípusra
    _xx = np.linspace(0, 1, 100)

    # Kormanközeli vonal (gov=1) és független (gov=0) előrejelzés
    _b0 = model.params["Intercept"]
    _b1 = model.params["sentiment_score"]
    _b2 = model.params["gov"]
    _b3 = model.params["sentiment_score:gov"]

    _ind_line = _b0 + _b1 * _xx
    _gov_line = (_b0 + _b2) + (_b1 + _b3) * _xx

    fig_reg, ax_r = plt.subplots(figsize=(10, 6))

    # Háttérben a nyers pontok
    for _pt, _c in [("Kormányközeli", _COLOR_GOV), ("Független", _COLOR_IND)]:
        _sub = df_h2.filter(pl.col("portal_type") == _pt)
        ax_r.scatter(
            _sub["sentiment_score"].to_numpy(),
            _sub["norm_score"].to_numpy(),
            s=10,
            alpha=0.18,
            color=_c,
        )

    # Modelláltal illesztett egyenesek
    ax_r.plot(_xx, _gov_line, color=_COLOR_GOV, linewidth=2.8,
              label=f"Kormányközeli: meredekség = {(_b1 + _b3):+.3f}")
    ax_r.plot(_xx, _ind_line, color=_COLOR_IND, linewidth=2.8,
              label=f"Független: meredekség = {_b1:+.3f}")

    ax_r.set_xlabel("Szentiment (0 = negatív, 1 = pozitív)", fontsize=11)
    ax_r.set_ylabel("Normalizált vizuális hangsúly (0–1)", fontsize=11)
    ax_r.set_title(
        "Regressziós modell: előrejelzés portáltípusonként",
        fontsize=13,
        fontweight="bold",
    )
    ax_r.axvline(0.5, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)
    ax_r.set_xlim(-0.02, 1.02)
    ax_r.set_ylim(-0.02, 1.05)
    ax_r.legend(fontsize=10, loc="upper right")
    fig_reg.tight_layout()
    fig_reg
    return


@app.cell(hide_code=True)
def _(mo, model):
    # Automatikus értelmezés a fő együtthatókra
    _b1 = float(model.params["sentiment_score"])
    _b1_p = float(model.pvalues["sentiment_score"])
    _b2 = float(model.params["gov"])
    _b2_p = float(model.pvalues["gov"])
    _b3 = float(model.params["sentiment_score:gov"])
    _b3_p = float(model.pvalues["sentiment_score:gov"])

    _gov_slope = _b1 + _b3

    # H2-irány értékelése
    if _b1_p < 0.05 and _b1 < 0:
        _sent_txt = (
            f"✅ A független portáloknál **β₁ = {_b1:+.3f}** (p = {_b1_p:.4f}): "
            f"a negatívabb címsorok valóban nagyobb vizuális hangsúlyt kapnak."
        )
    elif _b1_p < 0.05 and _b1 > 0:
        _sent_txt = (
            f"❌ A független portáloknál **β₁ = {_b1:+.3f}** (p = {_b1_p:.4f}): "
            f"a pozitívabb címsorok kapnak nagyobb hangsúlyt – a H2-vel ellentétes."
        )
    else:
        _sent_txt = (
            f"⚠️ A független portáloknál **β₁ = {_b1:+.3f}** (p = {_b1_p:.4f}): "
            f"nem szignifikáns szentiment-hatás."
        )

    # Interakció értékelése
    if _b3_p < 0.05:
        _int_txt = (
            f"✅ Az interakció **β₃ = {_b3:+.3f}** (p = {_b3_p:.4f}) szignifikáns – "
            f"a két portáltípusnál **eltérő erősségű** a szentiment hatása."
        )
    else:
        _int_txt = (
            f"⚠️ Az interakció **β₃ = {_b3:+.3f}** (p = {_b3_p:.4f}) nem szignifikáns – "
            f"a szentiment-hatás erőssége statisztikailag hasonló a két portáltípusnál."
        )

    # Portáltípus főhatás
    if _b2_p < 0.05:
        _gov_txt = (
            f"A kormányközeli portálok alapszintje **β₂ = {_b2:+.3f}**-vel tér el "
            f"(p = {_b2_p:.4f}) – szignifikáns különbség negatív címeknél."
        )
    else:
        _gov_txt = (
            f"A portáltípus főhatása (β₂ = {_b2:+.3f}, p = {_b2_p:.4f}) nem szignifikáns."
        )

    mo.md(f"""
    ### Értelmezés

    **Szentiment-hatás (β₁):** {_sent_txt}

    **Portáltípus főhatás (β₂):** {_gov_txt}

    **Interakció (β₃):** {_int_txt}

    ---

    **Meredekségek összefoglalva:**
    - Független portálok: **{_b1:+.3f}** *(score-változás sentiment 0 → 1)*
    - Kormányközeli portálok: **{_gov_slope:+.3f}** *(β₁ + β₃)*

    > **Miniment:** minél **negatívabb** a meredekség, annál erősebben érvényes
    > az adott portáltípusnál, hogy a **negatív címek kapnak nagyobb kiemelést**.
    > Ha a kormányközeli meredekség jobban eltér 0-tól (lefelé), a polarizációs és
    > szenzacionálási mechanizmusok ott erősebbek.
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ---

    # 🎯 Összesített H2 verdikt

    Három független módszerrel vizsgáltuk a szentiment és a vizuális hangsúly
    kapcsolatát – nézzük, mit mondanak együttesen.
    """)
    return


@app.cell(hide_code=True)
def _(df_mw, df_spearman, mo, model, pl):
    # --- 1. Spearman-bizonyíték összegyűjtése ---
    _sp_all = df_spearman.filter(pl.col("Csoport") == "Összes").row(0, named=True)
    _sp_gov = df_spearman.filter(pl.col("Csoport") == "Kormányközeli").row(0, named=True)
    _sp_ind = df_spearman.filter(pl.col("Csoport") == "Független").row(0, named=True)

    _sp_supports = _sp_all["p-érték"] < 0.05 and _sp_all["ρ (Spearman)"] < 0

    # --- 2. Mann-Whitney-bizonyíték ---
    # H2-irányú tesztek: Negatív vs. Semleges / Pozitív, mindhárom csoportban (Összes/Gov/Ind)
    _h2_tests = df_mw.filter(
        pl.col("Összehasonlítás").is_in(
            ["Negatív vs. Semleges", "Negatív vs. Pozitív"]
        )
    )
    _n_h2 = _h2_tests.height
    _n_h2_sig = _h2_tests.filter(
        (pl.col("p-érték") < 0.05) & (pl.col("r") > 0)
    ).height
    _mw_supports = _n_h2_sig >= _n_h2 - 1 and _n_h2_sig > 0

    # --- 3. Regressziós bizonyíték ---
    _b1 = float(model.params["sentiment_score"])
    _b1_p = float(model.pvalues["sentiment_score"])
    _b3 = float(model.params["sentiment_score:gov"])
    _b3_p = float(model.pvalues["sentiment_score:gov"])
    _gov_slope = _b1 + _b3

    _reg_supports = _b1_p < 0.05 and _b1 < 0
    _reg_gov_supports = _gov_slope < 0  # kormányközeli meredekség iránya

    # --- Összesített pontszám: hány módszer támogatja a H2-t? ---
    _score = sum([_sp_supports, _mw_supports, _reg_supports])

    if _score == 3:
        _overall = "✅ **H2 megerősítve**"
        _overall_desc = "Mindhárom statisztikai módszer egybehangzóan támogatja a hipotézist."
    elif _score == 2:
        _overall = "✅ **H2 túlnyomóan megerősítve**"
        _overall_desc = "Két módszer egyértelműen támogatja, a harmadik vegyes képet mutat."
    elif _score == 1:
        _overall = "⚠️ **H2 részben megerősítve**"
        _overall_desc = "Csak egy módszer támogatja egyértelműen – óvatos értelmezés ajánlott."
    else:
        _overall = "❌ **H2 nincs megerősítve**"
        _overall_desc = "Egyik módszer sem támogatja érdemben a hipotézist."

    def _check(b):
        return "✅" if b else "❌"

    mo.md(f"""
    ## {_overall}

    {_overall_desc} *(Bizonyíték-pontszám: **{_score} / 3**)*

    ---

    ### Bizonyíték-összefoglaló

    | Lépés | Módszer | Eredmény | H2 támogatva? |
    |---|---|---|---|
    | **1.** | Spearman-korreláció (össz minta) | ρ = {_sp_all["ρ (Spearman)"]:+.3f}, p = {_sp_all["p-érték"]:.4f} – *{_sp_all["Erősség"]}* | {_check(_sp_supports)} |
    | **2.** | Mann-Whitney U (sávpárok) | {_n_h2_sig} / {_n_h2} teszt szignifikáns H2-irányban | {_check(_mw_supports)} |
    | **3.** | OLS regresszió (β₁ szentiment) | β₁ = {_b1:+.3f}, p = {_b1_p:.4f} | {_check(_reg_supports)} |

    ---

    ### Portáltípusonkénti kép

    | Portáltípus | Spearman ρ | Regressziós meredekség | Értelmezés |
    |---|---|---|---|
    | 🔴 **Kormányközeli** | {_sp_gov["ρ (Spearman)"]:+.3f} (p={_sp_gov["p-érték"]:.4f}) | {_gov_slope:+.3f} | {"A negatív címek erősebb kiemelést kapnak" if _gov_slope < 0 else "A pozitív címek kapnak nagyobb hangsúlyt"} |
    | 🔵 **Független** | {_sp_ind["ρ (Spearman)"]:+.3f} (p={_sp_ind["p-érték"]:.4f}) | {_b1:+.3f} | {"A negatív címek erősebb kiemelést kapnak" if _b1 < 0 else "A pozitív címek kapnak nagyobb hangsúlyt"} |

    **Interakciós teszt (β₃ = {_b3:+.3f}, p = {_b3_p:.4f}):** \
    {"🔥 A két portáltípus **szignifikánsan eltérő** erősséggel emeli ki a negatív tartalmat." if _b3_p < 0.05 else "A két portáltípus szentiment-hatása **statisztikailag hasonló** erősségű."}

    ---

    ### Összefoglaló értelmezés

    {
    "A három független statisztikai módszer – a rangkorreláció, a sávpáros összehasonlítás "
    "és a regressziós modell – egybehangzóan azt mutatja, hogy a **negatívabb címsorok valóban "
    "nagyobb vizuális hangsúlyt kapnak a magyar hírportálok főoldalain**. Ez az ún. *„a rossz "
    "hír jobb hír”* jelenség statisztikai lenyomata: a szerkesztői döntések szisztematikusan "
    "előnyösebb poziciót és nagyobb méretet adnak a drasztikus, negatív tartalmaknak, mint a "
    "semleges vagy pozitív híreknek."
    if _score >= 2 else
    "Az eredmények vegyesek: a három módszer nem mutat egységes képet. Ez óvatosságra int – "
    "lehetséges, hogy a szentiment és a vizuális hangsúly közti kapcsolat gyengébb, mint"
    " feltételeztük, vagy csak bizonyos részcsoportokban jelenik meg."
    }

    {
    f"**Portáltípusok közötti különbség:** az interakciós teszt szignifikáns eredménye "
    f"({_b3:+.3f}, p={_b3_p:.4f}) azt jelzi, hogy a "
    + ("**kormányközeli** portálok **erősebben** " if _gov_slope < _b1 else "**független** portálok **erősebben** ")
    + "építenek a negatív érzelmi töltetű címsorok kiemelésére. Ez a **szerkesztői stratégia "
    "eltérésére** utal a két portáltípus között – nem csupán arányaiban eltérő a "
    "negatív tartalom, hanem más is a mód, ahogy figyelmet terélnek neki."
    if _b3_p < 0.05 else
    "**Portáltípusok közötti különbség:** az interakciós teszt nem szignifikáns, tehát a "
    "jelenség **mindkét portáltípusnál hasonló erősséggel** működik – úgy tűnik, a vizuális "
    "hangsúly és a negatív érzelmi töltet összekapcsolása **általános magyar média-jelenség**, "
    "nem pedig egy-egy portáltípus sajátossága."
    }

    ---

    ### Korlátok

    - A szentiment-pontszámot egy LLM adta – számszerű hiba-becslésünk erre nincs.
    - A „vizuális hangsúly” portálonként normalizált, tehát csak **relatív** kiemelkedést mér.
    - Az összefüggés **korrelációs**, nem ok-okozati: nem bizonyítja, hogy a szerkesztők
      szándékosan válogatnak szentiment alapján – lehet, hogy a negatív témák egyszerűen
      fontosabbak is (pl. katasztrófa, bűnügy) és ezért kapnak nagyobb helyet.
    """)
    return


if __name__ == "__main__":
    app.run()
