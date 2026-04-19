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

    return mo, pl


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
    return (df_normed,)


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
    return


if __name__ == "__main__":
    app.run()
