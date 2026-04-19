import marimo

__generated_with = "0.23.1"
app = marimo.App()


@app.cell
def _():
    import polars as pl
    import marimo as mo

    return mo, pl


@app.cell
def _(pl):
    df_headlineDefinitions = pl.read_parquet(
        "data/headlineDefinitions_2026-04-19.parquet"
    )
    df_llmAnalysis = pl.read_parquet("data/llmAnalysis_2026-04-19.parquet")
    df_headlines = pl.read_parquet("data/headlines_2026-04-19.parquet")
    return df_headlineDefinitions, df_headlines, df_llmAnalysis


@app.cell
def _(df_headlineDefinitions, df_headlines, df_llmAnalysis, pl):
    # Átlagos vizuális pontszám egyedi címsoronként (több scrape-pillanatkép is létezik)
    df_vis = (
        df_headlines.select(["hashedId", "score"])
        .group_by("hashedId")
        .agg(pl.col("score").mean().alias("mean_score"))
    )

    # Alaptábla: címsor-definíciók + LLM szentiment/entitás/label + vizuális pontszám összekapcsolása
    df_base = df_headlineDefinitions.join(
        df_llmAnalysis.select(["hashedId", "sentiment_score", "entities", "label"]),
        on="hashedId",
        how="left",
    ).join(df_vis, on="hashedId", how="left")

    # Min-max normalizálás portálonként, hogy az eltérő skálájú portálok összehasonlíthatók legyenek
    _site_stats = df_base.group_by("siteName").agg(
        pl.col("mean_score").min().alias("score_min"),
        pl.col("mean_score").max().alias("score_max"),
    )

    # Normalizált pontszám kiszámítása: (érték - min) / (max - min), epsilon a nullával osztás ellen
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

    df_normed
    return (df_normed,)


@app.cell
def _(df_normed, pl):
    # Portálok besorolása kormányközeli / független / egyéb kategóriákba
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
def _(df_classified, pl):
    ENTITIES = ["Magyar Péter", "Orbán Viktor"]

    # Egy sor minden (címsor, entitás) párhoz — egy címsor mindkét entitást említheti
    _rows = []
    for _entity in ENTITIES:
        _subset = (
            df_classified.filter(pl.col("entities").str.contains(_entity))
            .filter(pl.col("portal_type").is_in(["Kormányközeli", "Független"]))
            .with_columns(pl.lit(_entity).alias("entity"))
        )
        _rows.append(_subset)

    df_entities = pl.concat(_rows)
    df_entities
    return (df_entities,)


@app.cell
def _(df_entities, mo, pl):
    _sample_sizes = (
        df_entities.group_by(["entity", "portal_type"])
        .agg(pl.len().alias("n"))
        .sort(["entity", "portal_type"])
    )

    mo.vstack(
        [
            mo.md("## Minták száma"),
            mo.plain(_sample_sizes),
        ]
    )
    return


@app.cell
def _(df_entities, mo, pl):
    _desc = (
        df_entities.group_by(["entity", "portal_type"])
        .agg(
            pl.len().alias("n"),
            pl.col("sentiment_score").mean().round(3).alias("szentiment_átlag"),
            pl.col("sentiment_score").median().round(3).alias("szentiment_medián"),
            pl.col("sentiment_score").std().round(3).alias("szentiment_std"),
            pl.col("norm_score").mean().round(3).alias("vizuális_átlag"),
            pl.col("norm_score").median().round(3).alias("vizuális_medián"),
            pl.col("norm_score").std().round(3).alias("vizuális_std"),
        )
        .sort(["entity", "portal_type"])
    )

    mo.vstack(
        [
            mo.md("## Leíró statisztikák"),
            mo.plain(_desc),
        ]
    )
    return


@app.cell
def _(df_entities, pl):
    import numpy as np

    # Numpy tömbök előkészítése entitás × portáltípus bontásban a statisztikai tesztekhez és ábrákhoz
    arrays = {}
    for _ent in ["Magyar Péter", "Orbán Viktor"]:
        for _pt in ["Kormányközeli", "Független"]:
            _sub = df_entities.filter(
                (pl.col("entity") == _ent) & (pl.col("portal_type") == _pt)
            )
            arrays[(_ent, _pt)] = {
                "sent": _sub["sentiment_score"].to_numpy(),
                "score": _sub["norm_score"].drop_nulls().to_numpy(),
                "n": _sub.height,
            }
    return arrays, np


@app.cell
def _(arrays, np):
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"
    _ALPHA = 0.72

    _ptypes = ["Kormányközeli", "Független"]
    _colors = [_COLOR_GOV, _COLOR_IND]
    _entities = ["Magyar Péter", "Orbán Viktor"]
    _metrics = [
        ("sent", "Szentiment (0=negatív, 1=pozitív)"),
        ("score", "Normalizált vizuális prominencia (0–1)"),
    ]

    # Hegedűdiagram (violin plot): eloszlás-összehasonlítás portáltípusonként
    fig_violin, axes_v = plt.subplots(2, 2, figsize=(12, 9), sharey="row")
    fig_violin.suptitle(
        "H1 – Szentiment és vizuális prominencia\nMagyar Péter vs. Orbán Viktor, portáltípusonként",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )

    for _row, (_mk, _ylabel) in enumerate(_metrics):
        for _col, _ent in enumerate(_entities):
            _ax = axes_v[_row][_col]
            _data = [arrays[(_ent, _pt)][_mk] for _pt in _ptypes]
            _ns = [arrays[(_ent, _pt)]["n"] for _pt in _ptypes]

            # Hegedűtestek színezése portáltípus szerint
            _parts = _ax.violinplot(
                _data, positions=[1, 2], showmedians=True, showextrema=True
            )
            for _pc, _c in zip(_parts["bodies"], _colors):
                _pc.set_facecolor(_c)
                _pc.set_alpha(_ALPHA)
            for _k in ("cmedians", "cmins", "cmaxes", "cbars"):
                _parts[_k].set_color("black")
                _parts[_k].set_linewidth(1.2)

            # Medián értékek kiírása a hegedű fölé
            for _pos, _d, _c in zip([1, 2], _data, _colors):
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

            # Mintanagyság címkék az x-tengely alá
            for _pos, _n in zip([1, 2], _ns):
                _ax.text(
                    _pos,
                    -0.08,
                    f"n={_n}",
                    ha="center",
                    va="top",
                    fontsize=8,
                    color="grey",
                    transform=_ax.get_xaxis_transform(),
                )

            _ax.set_xticks([1, 2])
            _ax.set_xticklabels(_ptypes, fontsize=10)
            _ax.set_ylim(-0.05, 1.1)
            _ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)
            if _col == 0:
                _ax.set_ylabel(_ylabel, fontsize=10)
            if _row == 0:
                _ax.set_title(_ent, fontsize=12, fontweight="bold")

    _legend_patches = [
        mpatches.Patch(color=_COLOR_GOV, alpha=_ALPHA, label="Kormányközeli"),
        mpatches.Patch(color=_COLOR_IND, alpha=_ALPHA, label="Független"),
    ]
    fig_violin.legend(
        handles=_legend_patches,
        loc="lower center",
        ncol=2,
        frameon=False,
        fontsize=11,
        bbox_to_anchor=(0.5, -0.02),
    )
    fig_violin.tight_layout()
    fig_violin
    return (plt,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## A hegedűdiagramok értelmezése

    ### 🎭 Szentiment (felső sor)

    | Portáltípus | Magyar Péter | Orbán Viktor |
    |---|---|---|
    | 🔴 Kormányközeli | Negatívabb hangnem | Pozitívabb hangnem |
    | 🔵 Független | Pozitívabb hangnem | Negatívabb hangnem |


    > **Tükörszerű mintázat:** a saját oldal politikusát kedvezőbb, az ellenzékit kedvezőtlenebb színben tüntetik fel — a médiaelfogultság klasszikus jele.

    ---

    ### 👁️ Vizuális prominencia (alsó sor)

    Ez a mutató azt méri, mekkora vizuális hangsúlyt kap egy címsor a főoldalon *(méret és pozíció alapján, 0–1-re normalizálva portálon belül)*.

    - Ha a 🔴 kormányközeli hegedű **mindkét entitásnál magasabban** helyezkedik el, az azt jelenti, hogy ezek a portálok mindkét politikust **nagyobb vizuális kieméléssel** jelenítik meg
    - Ez fokozott figyelemversenyre utal a kormányközeli médiában
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    Az ábra **vizuálisan igazolja a H1 hipotézist:** a kormányközeli és független portálok szisztematikusan eltérően kezelik a két politikust mind hangnemben (szentiment), mind megjelenítésben (vizuális prominencia). Ez egy polarizált médiarendszer jellegzetes lenyomata.
    """)
    return


@app.cell
def _(arrays, np, plt):
    _COLOR_GOV = "#c0392b"
    _COLOR_IND = "#2980b9"
    _entities = ["Magyar Péter", "Orbán Viktor"]
    _ptypes = ["Kormányközeli", "Független"]
    _colors = [_COLOR_GOV, _COLOR_IND]
    _bw = 0.3

    _metrics_bar = [
        ("sent", "Szentiment átlag (0–1)"),
        ("score", "Vizuális prominencia átlag (0–1)"),
    ]

    # Oszlopdiagram: átlagértékek entitásonként és portáltípusonként, egymás melletti oszlopokkal
    fig_bar, axes_b = plt.subplots(1, 2, figsize=(12, 5))
    fig_bar.suptitle(
        "Átlagos értékek entitásonként és portáltípusonként",
        fontsize=13,
        fontweight="bold",
    )

    for (_mk, _ylabel), _ax in zip(_metrics_bar, axes_b):
        _x = np.arange(len(_entities))
        for _i, (_pt, _c) in enumerate(zip(_ptypes, _colors)):
            _vals = [np.mean(arrays[(_ent, _pt)][_mk]) for _ent in _entities]
            _bars = _ax.bar(
                _x + (_i - 0.5) * _bw, _vals, _bw, label=_pt, color=_c, alpha=0.82
            )
            for _bar, _v in zip(_bars, _vals):
                _ax.text(
                    _bar.get_x() + _bar.get_width() / 2,
                    _bar.get_height() + 0.012,
                    f"{_v:.2f}",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )

        # Δ annotációk: a kormányközeli és független átlag közti különbség jelzése
        for _j, _ent in enumerate(_entities):
            _gv = np.mean(arrays[(_ent, "Kormányközeli")][_mk])
            _iv = np.mean(arrays[(_ent, "Független")][_mk])
            _delta = _gv - _iv
            _ax.annotate(
                f"Δ={_delta:+.2f}",
                xy=(_x[_j], max(_gv, _iv) + 0.04),
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color=_COLOR_GOV if _delta > 0 else _COLOR_IND,
            )

        _ax.set_xticks(_x)
        _ax.set_xticklabels(_entities, fontsize=11)
        _ax.set_ylabel(_ylabel, fontsize=10)
        _ax.set_ylim(0, 0.95)
        _ax.axhline(0.5, color="grey", linestyle="--", linewidth=0.7, alpha=0.5)
        _ax.legend(fontsize=10)

    fig_bar.tight_layout()
    fig_bar
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Az oszlopdiagram értelmezése

    Az oszlopdiagram az átlagos értékeket hasonlítja össze — nem az eloszlást, hanem egy könnyen olvasható összefoglalót nyújt.

    | Elem | Jelentés |
    |---|---|
    | 🔴 Piros oszlop | Kormányközeli portálok átlaga |
    | 🔵 Kék oszlop | Független portálok átlaga |
    | **Δ érték** | A két portáltípus közti különbség *(pozitív = kormányközeli magasabb)* |
    | Szaggatott vonal | Semleges szint (0.5) |

    - **Szentiment oszlopok** → melyik portáltípus ír *pozitívabban* az adott politikusról
    - **Prominencia oszlopok** → melyik portáltípus ad *nagyobb vizuális hangsúlyt* nekik
    - Az **0.5 feletti** értékek pozitív, az **0.5 alatti** értékek negatív hangvételt jeleznek
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ### *Szignifikánsan különbözik-e, ahogyan a kormányközeli vs. független portálok írnak egy-egy politikusról?*
    """)
    return


@app.cell
def _(arrays, mo, pl):
    from scipy import stats as scipy_stats

    # Szignifikanciaszint jelölő segédfüggvény
    def _sig_label(p):
        if p < 0.001:
            return "*** (p<0.001)"
        if p < 0.01:
            return "** (p<0.01)"
        if p < 0.05:
            return "* (p<0.05)"
        return "n.s."

    # Mann-Whitney U teszt minden (entitás, mérőszám) kombinációra
    # r hatásméret: rank-biszeriális korreláció (r = 1 - 2U/(n1*n2))
    _rows = []
    for _ent in ["Magyar Péter", "Orbán Viktor"]:
        for _mk, _mlabel in [("sent", "Szentiment"), ("score", "Vizuális prominencia")]:
            _gov = arrays[(_ent, "Kormányközeli")][_mk]
            _ind = arrays[(_ent, "Független")][_mk]
            _u, _p = scipy_stats.mannwhitneyu(_gov, _ind, alternative="two-sided")
            _r = 1 - (2 * _u) / (len(_gov) * len(_ind))
            _rows.append(
                {
                    "Entitás": _ent,
                    "Mérőszám": _mlabel,
                    "Gov átlag": round(_gov.mean(), 3),
                    "Ind átlag": round(_ind.mean(), 3),
                    "Δ (Gov−Ind)": round(_gov.mean() - _ind.mean(), 3),
                    "U": round(_u, 0),
                    "p-érték": round(_p, 4),
                    "r (hatásméret)": round(_r, 3),
                    "Szignifikancia": _sig_label(_p),
                }
            )

    df_tests = pl.DataFrame(_rows)

    mo.vstack(
        [
            mo.md("## Statisztikai tesztek – Mann-Whitney U (kétoldali)"),
            mo.plain(df_tests),
        ]
    )
    return (df_tests,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    #### Mann-Whitney U teszt


    Ezt két mérőszámra vizsgálja (szentiment + vizuális prominencia), két entitásra (Magyar Péter + Orbán Viktor) — összesen **4 teszt**.


    A Mann-Whitney U egy **nem-paraméteres teszt**, ami két független csoport eloszlását hasonlítja össze. Három ok miatt megfelelő itt:

    1. **Nem feltételez normális eloszlást** — a szentiment és prominencia értékek jellemzően ferdék (sok szélsőséges érték), így a klasszikus t-próba kevésbé megbízható lenne.
    2. **Ordinális adatokra is működik** — a 0–1 skálán mért értékek sorrendje számít, nem feltétlenül a pontos különbségek.
    3. **Robusztus kiugró értékekkel szemben** — a medián-alapú logika miatt egy-két extrém címsor nem torzítja el az eredményt.

    ##### Mit jelentenek az oszlopok?

    | Oszlop | Jelentés |
    |---|---|
    | **Gov átlag** | Kormányközeli portálok átlagértéke |
    | **Ind átlag** | Független portálok átlagértéke |
    | **Δ (Gov−Ind)** | A kettő különbsége — pozitív = Gov magasabb, negatív = Ind magasabb |
    | **U** | A teszt statisztikája — hány esetben „veri" az egyik csoport a másikat a rangsorban |
    | **p-érték** | Annak valószínűsége, hogy ekkora (vagy nagyobb) különbség pusztán véletlenből adódna |
    | **r (hatásméret)** | Rank-biszeriális korreláció: a különbség **gyakorlati nagysága** (−1 és +1 között, 0 = nincs különbség) |
    | **Szignifikancia** | Csillagos jelölés: `*` = p<0.05, `**` = p<0.01, `***` = p<0.001, `n.s.` = nem szignifikáns |


    - **p < 0.05** → a különbség statisztikailag szignifikáns, azaz nem a véletlen műve.
    - **r értéke** mondja meg, hogy ez a különbség mennyire erős:
      - |r| < 0.1 → elhanyagolható
      - |r| ≈ 0.1–0.3 → gyenge
      - |r| ≈ 0.3–0.5 → közepes
      - |r| > 0.5 → erős

    Tehát ha pl. Magyar Péter szentimentjénél p < 0.001 és r = −0.3, az azt jelenti: **statisztikailag bizonyított, közepes erősségű különbség van** — a kormányközeli portálok negatívabban írnak róla, és ez nem a véletlen műve.
    """)
    return


@app.cell
def _(df_tests, mo, pl):
    # H1 hipotézis végső verdiktje: szignifikáns tesztek számának összesítése és értelmezés
    def _get(entity, metric):
        _row = df_tests.filter(
            (pl.col("Entitás") == entity) & (pl.col("Mérőszám") == metric)
        )
        return _row["p-érték"][0], _row["Δ (Gov−Ind)"][0], _row["r (hatásméret)"][0]

    mp_sp, mp_sd, mp_sr = _get("Magyar Péter", "Szentiment")
    mp_vp, mp_vd, mp_vr = _get("Magyar Péter", "Vizuális prominencia")
    ov_sp, ov_sd, ov_sr = _get("Orbán Viktor", "Szentiment")
    ov_vp, ov_vd, ov_vr = _get("Orbán Viktor", "Vizuális prominencia")

    def _icon(p):
        return "✅" if p < 0.05 else "❌"

    def _dir_sent(d):
        return "Gov pozitívabb" if d > 0 else "Ind pozitívabb"

    def _dir_vis(d):
        return "Gov prominensebb" if d > 0 else "Ind prominensebb"

    # Összesített verdikt: 3+ szignifikáns → megerősítve, 1-2 → részben, 0 → nem
    _n_sig = sum(p < 0.05 for p in [mp_sp, mp_vp, ov_sp, ov_vp])
    _overall = (
        "✅ **megerősítve**"
        if _n_sig >= 3
        else "⚠️ **részben megerősítve**"
        if _n_sig >= 1
        else "❌ **nem megerősítve**"
    )

    mo.md(f"""
    ## {_overall} – H1 Verdikt

    ### Magyar Péter
    | Mérőszám | Gov átlag | Ind átlag | Δ (Gov−Ind) | p-érték | r | Szignifikáns? |
    |---|---|---|---|---|---|---|
    | Szentiment | {df_tests.filter((pl.col("Entitás") == "Magyar Péter") & (pl.col("Mérőszám") == "Szentiment"))["Gov átlag"][0]:.3f} | {df_tests.filter((pl.col("Entitás") == "Magyar Péter") & (pl.col("Mérőszám") == "Szentiment"))["Ind átlag"][0]:.3f} | `{mp_sd:+.3f}` – {_dir_sent(mp_sd)} | {mp_sp:.4f} | {mp_sr:.3f} | {_icon(mp_sp)} |
    | Vizuális prominencia | {df_tests.filter((pl.col("Entitás") == "Magyar Péter") & (pl.col("Mérőszám") == "Vizuális prominencia"))["Gov átlag"][0]:.3f} | {df_tests.filter((pl.col("Entitás") == "Magyar Péter") & (pl.col("Mérőszám") == "Vizuális prominencia"))["Ind átlag"][0]:.3f} | `{mp_vd:+.3f}` – {_dir_vis(mp_vd)} | {mp_vp:.4f} | {mp_vr:.3f} | {_icon(mp_vp)} |

    ### Orbán Viktor
    | Mérőszám | Gov átlag | Ind átlag | Δ (Gov−Ind) | p-érték | r | Szignifikáns? |
    |---|---|---|---|---|---|---|
    | Szentiment | {df_tests.filter((pl.col("Entitás") == "Orbán Viktor") & (pl.col("Mérőszám") == "Szentiment"))["Gov átlag"][0]:.3f} | {df_tests.filter((pl.col("Entitás") == "Orbán Viktor") & (pl.col("Mérőszám") == "Szentiment"))["Ind átlag"][0]:.3f} | `{ov_sd:+.3f}` – {_dir_sent(ov_sd)} | {ov_sp:.4f} | {ov_sr:.3f} | {_icon(ov_sp)} |
    | Vizuális prominencia | {df_tests.filter((pl.col("Entitás") == "Orbán Viktor") & (pl.col("Mérőszám") == "Vizuális prominencia"))["Gov átlag"][0]:.3f} | {df_tests.filter((pl.col("Entitás") == "Orbán Viktor") & (pl.col("Mérőszám") == "Vizuális prominencia"))["Ind átlag"][0]:.3f} | `{ov_vd:+.3f}` – {_dir_vis(ov_vd)} | {ov_vp:.4f} | {ov_vr:.3f} | {_icon(ov_vp)} |

    ---

    > **Értelmezés:** A kormányközeli portálok **Magyar Pétert negatívabban**
    > (Δ={mp_sd:+.3f}), **Orbán Viktort pozitívabban** (Δ={ov_sd:+.3f}) ábrázolják –
    > ez a szimmetrikus, tükörszerű mintázat a polarizáció klasszikus jele.
    > Mindkét szereplőt **nagyobb vizuális hangsúllyal** jelenítik meg a kormányközeli
    > oldalak (Magyar Péter Δ={mp_vd:+.3f}, Orbán Viktor Δ={ov_vd:+.3f}), ami azt
    > jelzi, hogy a figyelemért folytatott verseny intenzívebb ezeken a portálokon.
    """)
    return


if __name__ == "__main__":
    app.run()
