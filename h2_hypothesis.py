import marimo

__generated_with = "0.23.1"
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
    return (samples_h2,)


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


if __name__ == "__main__":
    app.run()
