# Kontraszt Research – módszertani útmutató

Ez a dokumentum a projekt részletesebb, de még mindig tanulásbarát módszertani leírása. Az a célja, hogy ne csak azt lásd, **mit** csinálunk, hanem azt is, hogy **miért pont így**.

A hangnem szándékosan kötetlenebb, mint egy klasszikus módszertani appendixben. Lesznek mini példák, fake adatok, és olyan magyarázatok is, amelyek inkább intuíciót adnak, mint tankönyvi formalizmust.

---

## 1. A kutatás logikája röviden

A projekt alapkérdése ez:

> A magyar online hírportálok hogyan rendezik el a figyelmet a főoldalaikon?

Ezt három nézőpontból bontjuk szét:

1. **H1 – polarizáció:** ugyanazokat a politikai szereplőket másképp mutatják-e be?
2. **H2 – negativitás:** a negatív headline-ok nagyobb hangsúlyt kapnak-e?
3. **H3 – napirend:** együtt mozognak-e a portálok a témaválasztásban, és ha igen, ugyanúgy kereteznek-e?

---

## 2. Miből lesz az elemzési adatbázis?

A projekt több réteget rak egymásra ugyanahhoz a headline-hoz.

### 2.1. Raw scrape
A scraper időnként elmenti a portálok főoldalát.

Ebből kinyerhető például:
- headline szöveg,
- headline pozíció,
- méret,
- portál neve,
- időbélyeg.

### 2.2. Headline-szintű vizuális score
A headline kap egy score-t, amely azt próbálja mérni, mennyire feltűnő a főoldalon.

A score mögött jellemzően ilyen tényezők vannak:
- nagyobb betű = nagyobb figyelem,
- nagyobb terület = nagyobb figyelem,
- lejjebb az oldalon = kisebb figyelem,
- jobbra tolva = kisebb figyelem,
- jobb felső sarok bizonyos esetekben extra büntetést kaphat.

A részletes képletet lásd itt: [`docs/score_formula.md`](../score_formula.md)

### 2.3. LLM-annotáció
Egy nagy nyelvi modell becsli:
- a headline szentimentjét,
- a headline-ban szereplő entitásokat.

### 2.4. Headline-onként átlagolás
Ugyanaz a headline több scrape-ben is szerepelhet. Emiatt gyakran headline-szinten átlagoljuk a vizuális score-t.

Ez azért fontos, mert különben a gyakrabban elmentett headline-ok túl nagy súlyt kapnának.

### 2.5. Hogyan néz ki a 3 Parquet-fájl?

A három fő inputfájl szerepe röviden:

- `headlineDefinitions_2026-04-19.parquet` → **mi a headline, hol jelent meg**
- `llmAnalysis_2026-04-19.parquet` → **mit mond róla az LLM**
- `headlines_2026-04-19.parquet` → **hogyan nézett ki a főoldalon**

#### 1. `headlineDefinitions_2026-04-19.parquet`
Ez az alap „headline-törzs”. Nálunk **48599 sor** van benne, és a `hashedId` itt headline-onként egyedi.

Fő oszlopok:
- `_creationTime`
- `_id`
- `hashedId`
- `headlineText`
- `href`
- `siteName`

Pár minta sor:

| hashedId | headlineText | href | siteName |
|---|---|---|---|
| `f4ad2cbd71798f23` | Szijjártó: Nem kért tőlem semmit semmilyen oligarcha | `https://telex.hu/...` | Telex |
| `a5b9d2e6b58fc60a` | Az a baj, hogy akkor tartjuk jónak a demokráciát, ha a mi emberünk van hatalmon | `https://telex.hu/...` | Telex |
| `82cb0921702a5663` | Az a baj, hogy akkor tartjuk jónak a demokráciát, ha a mi emberünk van... | `https://telex.hu/...` | Telex |

#### 2. `llmAnalysis_2026-04-19.parquet`
Ez az LLM-annotációs réteg. Nálunk **49671 sor** van benne, tehát itt már vannak olyan `hashedId`-k, amelyek többször is előfordulnak.

Fő oszlopok:
- `hashedId`
- `headlineText`
- `entities`
- `label`
- `sentiment`
- `sentiment_score`
- `confidence`

Pár minta sor:

| hashedId | headlineText | entities | label | sentiment | sentiment_score | confidence |
|---|---|---|---|---|---:|---:|
| `fbb80da964218468` | Toplistás körözött bűnöző volt a Mexikóban elfogott magyar drogbáró... | `["Mexikó"]` | bűnügy | negatív | 0.1 | 0.98 |
| `eb3ccd6638e94acc` | Beintett Orbán Viktor szövetségesének a két uniós tagállam... | `["Orbán Viktor", "Moszkva"]` | politika | negatív | 0.2 | 0.95 |
| `ea5ce1ac4eb87ff5` | Ilyet sem látni minden nap: hihetetlen trükkel... | `[]` | bűnügy | negatív | 0.2 | 0.90 |

#### 3. `headlines_2026-04-19.parquet`
Ez a vizuális megjelenés réteg. Nálunk **374891 sor** van benne, vagyis egy headline sok scrape-pillanatban újra megjelenhet.

Fő oszlopok:
- `hashedId`
- `fontSize`
- `width`
- `height`
- `x`
- `y`
- `score`
- `scrapedAt`

Pár minta sor:

| hashedId | fontSize | width | height | x | y | score |
|---|---:|---:|---:|---:|---:|---:|
| `ca4729fad9fe2b2b` | 18.0 | 416.0 | 43.19 | 1192.0 | 6363.48 | -38756.31 |
| `ef9ee07bf32f64ae` | 18.0 | 416.0 | 21.59 | 1192.0 | 6186.50 | -38592.70 |
| `5b309d8eea1c3f04` | 16.0 | 392.0 | 38.38 | 764.0 | 6394.06 | -37934.07 |

### 2.6. Hogyan joinolódnak ezek össze?

A kulcsmező a három fájl között a **`hashedId`**.

Durván ez történik:

1. a `headlineDefinitions` adja az alap headline-listát,
2. erre rájoinoljuk az `llmAnalysis` táblát `hashedId` alapján,
3. külön összesítjük a `headlines` táblát headline-szintre,
4. majd ezt az aggregált vizuális táblát is rájoinoljuk ugyanarra a `hashedId`-ra.

### Miért kell külön aggregálni a `headlines` táblát?
Mert ott ugyanaz a headline nagyon sokszor szerepelhet.

A mostani adatokban például:
- `headlineDefinitions`: **48599 sor**, minden `hashedId` egyedi
- `llmAnalysis`: **49671 sor**, itt vannak duplikált `hashedId`-k
- `headlines`: **374891 sor**, itt nagyon sok a duplikált `hashedId`

Vagyis ha vakon joinolnánk mindent mindennel, könnyen szétszórnánk a megfigyeléseket és túlreprezentálnánk a gyakrabban scrape-elt headline-okat.

### A legegyszerűbb elemzési logika
Először készítünk egy headline-szintű vizuális táblát, például így:

```python
visual_df = (
    headlines
    .groupby("hashedId", as_index=False)
    .agg(
        mean_score=("score", "mean"),
        mean_fontSize=("fontSize", "mean"),
        n_scrapes=("hashedId", "size")
    )
)
```

Ezután jöhet a join:

```python
analysis_df = (
    headline_definitions
    .merge(llm_analysis, on="hashedId", how="inner")
    .merge(visual_df, on="hashedId", how="inner")
)
```

### Emberi nyelven mit jelent ez?
Minden headline-hoz végül egy helyre kerül:
- a szövege,
- a portál neve,
- az LLM által becsült szentiment,
- a felismert entitások,
- és egy headline-szintű vizuális score.

Ez már egy olyan tábla, amivel lehet statisztikázni.

### 2.7. Hol jön a filterezés?
A filterezés több ponton is történhet, attól függően, melyik hipotézist nézzük.

#### Általános tisztítás
Tipikus lépések:
- csak olyan sorok maradnak, ahol van `hashedId`,
- eldobhatók a hiányzó `sentiment_score`-os sorok,
- kiszűrhetők a problémás vagy üres headline-ok,
- portálon belüli score-normalizálás után lehet továbbmenni.

#### H1 esetén
Itt tipikusan szűrünk azokra a headline-okra,
- amelyekben szerepel a vizsgált entitás,
- például `"Magyar Péter"` vagy `"Orbán Viktor"`.

#### H2 esetén
Itt inkább az marad bent,
- ahol van használható `sentiment_score`,
- és van headline-szintű vizuális score,
- majd ebből készülhet negatív / semleges / pozitív bontás.

#### H3 esetén
Itt jön még pluszban:
- dátumképzés,
- entitáslista „felrobbantása” külön sorokra,
- top entitások kiválasztása,
- és napi aggregálás portálonként.

### Egy mini, szemléletes példa a joinra
Tegyük fel, hogy van ez a három részlet.

#### `headlineDefinitions`
| hashedId | headlineText | siteName |
|---|---|---|
| `abc123` | Orbán Viktor Brüsszelbe utazik | Telex |

#### `llmAnalysis`
| hashedId | entities | sentiment_score |
|---|---|---:|
| `abc123` | `["Orbán Viktor", "Brüsszel"]` | 0.40 |

#### `headlines` aggregálva
| hashedId | mean_score | n_scrapes |
|---|---:|---:|
| `abc123` | 1542.8 | 6 |

A join után ebből lesz:

| hashedId | headlineText | siteName | entities | sentiment_score | mean_score | n_scrapes |
|---|---|---|---|---:|---:|---:|
| `abc123` | Orbán Viktor Brüsszelbe utazik | Telex | `["Orbán Viktor", "Brüsszel"]` | 0.40 | 1542.8 | 6 |

Na, ez már tényleg elemzésre kész dataframe-szerű állapot.

---

## 3. Miért kell normalizálni a vizuális score-t?

Mert a portálok layoutja nem egyforma.

Egy headline lehet:
- az egyik oldalon óriási,
- a másikon már az átlagos kiemelés része.

Ha nyers score-okat hasonlítanánk össze, könnyen összekevernénk:
- a portál dizájnját
- a szerkesztői kiemelést.

Ezért portálon belüli min-max normalizálást használunk:

$$
\mathrm{normScore} = \frac{\mathrm{score} - \min(\mathrm{score})}{\max(\mathrm{score}) - \min(\mathrm{score})}
$$

### Mit jelent ez emberileg?
Azt, hogy nem azt kérdezzük:
> abszolút értelemben mekkora ez a headline?

hanem ezt:
> a saját portálján belül mennyire számít kiemeltnek?

Ez sokkal fair összehasonlítás.

---

## 4. A három hipotézis módszertana röviden

## H1 – Polarizáció
**Kérdés:** ugyanazokról a politikusokról eltér-e a hangnem és a vizuális hangsúly a két portáltípus között?

**Tipikus lépések:**
- kiválasztjuk az adott entitást említő headline-okat,
- csoportosítunk portáltípus szerint,
- összehasonlítjuk a szentimentet,
- összehasonlítjuk a normalizált vizuális score-t,
- Mann–Whitney U tesztet használunk,
- hatásméretet is számolunk.

---

## H2 – Negatív headline-ok kiemelése
**Kérdés:** a negatívabb címek átlagosan jobban kiemeltek-e?

**Tipikus lépések:**
- headline-szintű szentiment és norm_score összekapcsolása,
- Spearman-korreláció,
- negatív / semleges / pozitív sávok képzése,
- Mann–Whitney összehasonlítások,
- lineáris regresszió portáltípussal és interakcióval.

---

## H3 – Napirend-szinkron és framing
**Kérdés:** a portálok együtt mozognak-e abban, hogy milyen entitásokról írnak, és ugyanúgy keretezik-e őket?

**Tipikus lépések:**
- entitások napi említésszámainak előállítása,
- portálpárok közti Pearson-korreláció,
- top entitások kiválasztása,
- szentiment- és score-különbségek összevetése csoportok között,
- Mann–Whitney tesztek entitásonként.

---

# 5. Statisztikai eszköztár – lazábban, mini példákkal

Itt jön az a rész, ami sokakat vagy megijeszt, vagy feldob. Próbáljuk az utóbbit.

---

## 5.1. Mann–Whitney U teszt

### Mire jó?
Két független csoport összehasonlítására, amikor nem akarunk abból kiindulni, hogy az adatok szépen normális eloszlásúak.

Ez médiás adatoknál gyakori helyzet, mert:
- a score-ok ferdék lehetnek,
- lehetnek kilógó headline-ok,
- és sokszor nem túl elegáns az eloszlás.

### Rövid intuíció
A teszt nem annyira a nyers értékeket szereti, hanem azt nézi, hogy **a két csoport értékei mennyire keverednek össze a rangsorban**.

Ha az egyik csoport szinte végig a másik fölött van, akkor valószínűleg tényleg különbség van köztük.

### Fake példa
Tegyük fel, hogy Magyar Péterről szóló headline-ok szentimentjét hasonlítjuk össze.

**Kormányközeli:**
- 0.20
- 0.25
- 0.30
- 0.35

**Független:**
- 0.55
- 0.60
- 0.70
- 0.75

Ha ezeket egy sorba rakjuk, akkor a kormányközeliek mind a lista alján vannak, a függetlenek meg a tetején. Ez nagyon erős jel arra, hogy a két csoport másként kezeli ugyanazt a szereplőt.

### Mit mond ilyenkor a teszt?
Nagyjából azt:
> haver, ezek itt nem nagyon keverednek, ez valószínűleg nem véletlen.

### Mikor használjuk ebben a projektben?
- H1-ben: két portáltípus szentimentjének vagy norm_score-jának összehasonlítására
- H2-ben: negatív vs. semleges vs. pozitív headline-ok összevetésére
- H3-ban: entitásonkénti csoportkülönbségekre

### Mit nem mond?
Nem mond okságot. Csak azt mondja, hogy a két csoport eloszlása között van-e szisztematikus eltérés.

---

## 5.2. Rank-biszerális korreláció

### Mire jó?
A p-érték önmagában csak azt mondja meg, hogy **van-e jel**, de nem mondja meg, hogy **mekkora**.

Erre kell a hatásméret. A Mann–Whitney mellé kényelmes választás a **rank-biszerális korreláció**.

### Rövid intuíció
Ez azt próbálja megfogni, hogy egy véletlenszerűen kiválasztott párnál milyen eséllyel nagyobb az egyik csoport értéke, mint a másiké.

### Egyszerű értelmezés
- **+1 körül**: az első csoport szinte mindig nagyobb
- **0 körül**: a két csoport eléggé keveredik
- **-1 körül**: a második csoport szinte mindig nagyobb

### Fake példa
Vegyük a fenti adatokat.

**Gov:** 0.20, 0.25, 0.30, 0.35  
**Ind:** 0.55, 0.60, 0.70, 0.75

Ha itt minden független érték nagyobb minden kormányközelinél, akkor a hatásméret extrém erős lesz. Magyarul nem csak az van, hogy „statisztikailag szignifikáns”, hanem az is, hogy **a különbség nagyon látványos**.

### Hétköznapi hasonlat
Képzeld el, hogy két kosár alma van. Ha becsukott szemmel is jó eséllyel meg tudod mondani, melyik kosárból jött a nagyobb alma, akkor a hatásméret erős.

---

## 5.3. Spearman-korreláció

### Mire jó?
Azt nézi, hogy két változó között van-e **monoton együttjárás**. Nem kell, hogy szép egyenes kapcsolat legyen, elég, ha általában az egyik növekedésével a másik nő vagy csökken.

### Miért jó itt?
Mert H2-ben azt kérdezzük:
> minél pozitívabb vagy negatívabb egy headline, annál kevésbé vagy jobban kiemelt?

A Spearman jól bírja, ha:
- nem lineáris a kapcsolat,
- rangszerűbb az információ,
- vannak csúnyább eloszlások.

### Fake példa
Tegyük fel, hogy van 6 headline:

| Headline | sentiment_score | norm_score |
|---|---:|---:|
| A | 0.10 | 0.90 |
| B | 0.20 | 0.82 |
| C | 0.35 | 0.70 |
| D | 0.60 | 0.50 |
| E | 0.75 | 0.32 |
| F | 0.90 | 0.20 |

Itt ahogy nő a szentiment, csökken a kiemelés. A Spearman negatív lenne.

### Emberi nyelven ez mit jelent?
> Minél pozitívabb a cím, annál kevésbé van előretolva. Vagy fordítva: a negatívabb címek nagyobb hangsúlyt kapnak.

### Fontos
A Spearman nem azt mondja, hogy minden pont tökéletesen vonalra illeszkedik. Csak azt, hogy **a sorrendek együtt mozognak-e**.

---

## 5.4. Pearson-korreláció

### Mire jó?
A Pearson-korreláció két folytonos változó **lineáris együttmozgását** méri.

A H3-ban főleg arra használjuk, hogy portálok napi entitás-említési idősorait hasonlítsuk össze.

### Rövid intuíció
Ha két portál ugyanazon a napokon pörög fel ugyanarra a témára, és ugyanazon a napokon engedi el, akkor a Pearson-korreláció magas lesz.

### Fake példa
Tegyük fel, hogy az „Orbán Viktor” említések napi száma így alakul:

| Nap | Portál A | Portál B |
|---|---:|---:|
| Hétfő | 2 | 1 |
| Kedd | 5 | 4 |
| Szerda | 1 | 2 |
| Csütörtök | 6 | 5 |
| Péntek | 3 | 2 |

A két sorozat együtt hullámzik. Itt a Pearson erősen pozitív lenne.

### És ha nem együtt mozognak?

| Nap | Portál C | Portál D |
|---|---:|---:|
| Hétfő | 0 | 5 |
| Kedd | 5 | 0 |
| Szerda | 0 | 4 |
| Csütörtök | 4 | 0 |
| Péntek | 0 | 3 |

Itt amikor az egyik aktív, a másik hallgat. A Pearson gyenge vagy negatív lenne.

### Miért nem Spearman itt?
Lehetne az is bizonyos helyzetekben, de a H3 kérdése inkább a **napi csúcsok és visszaesések együttmozgására** vonatkozik, arra pedig a Pearson jó, intuitív választás.

---

## 5.5. Lineáris regresszió interakcióval

Na, ez az a rész, amitől a legtöbb ember először hátralép egyet. Pedig az alapötlet teljesen vállalható.

### Mire jó?
Egyszerre több dolgot tud figyelembe venni, és azt is meg tudja mondani, hogy egy kapcsolat **ugyanolyan-e minden csoportban**.

H2-ben például ezt kérdezzük:
- van-e kapcsolat a szentiment és a vizuális hangsúly között?
- ez ugyanakkora a kormányközeli és a független portálokon?

### Az alapmodell
$$
\text{norm\_score} = \beta_0 + \beta_1 \cdot \text{sentiment} + \beta_2 \cdot \text{gov} + \beta_3 \cdot (\text{sentiment} \times \text{gov}) + \varepsilon
$$

ahol:
- `sentiment` = mennyire pozitív a headline,
- `gov` = 1, ha kormányközeli portál, 0, ha független,
- `sentiment × gov` = interakciós tag.

### Mit jelent az interakció, teljesen lazán?
Azt, hogy:
> oké, van egy kapcsolat a szentiment és a kiemelés között, de biztos, hogy ugyanilyen meredekséggel működik mindkét médiablokkban?

Ha nem, akkor kell az interakció.

### Fake példa
Legyen 8 headline-unk:

| Portáltípus | gov | sentiment | norm_score |
|---|---:|---:|---:|
| Független | 0 | 0.1 | 0.90 |
| Független | 0 | 0.3 | 0.78 |
| Független | 0 | 0.7 | 0.42 |
| Független | 0 | 0.9 | 0.25 |
| Kormányközeli | 1 | 0.1 | 0.82 |
| Kormányközeli | 1 | 0.3 | 0.74 |
| Kormányközeli | 1 | 0.7 | 0.62 |
| Kormányközeli | 1 | 0.9 | 0.55 |

### Mit látunk szemre?
- mindkét csoportban a pozitívabb headline-ok kisebb hangsúlyt kapnak,
- de a független portáloknál sokkal meredekebb a lejtés.

### Képzeljünk el egy becsült modellt
$$
\hat y = 0.95 - 0.70 \cdot sentiment - 0.10 \cdot gov + 0.40 \cdot (sentiment \times gov)
$$

### Hogyan olvassuk ezt?

#### Független portálokra (`gov = 0`)
A modell:
$$
\hat y = 0.95 - 0.70 \cdot sentiment
$$

Ez azt jelenti:
- a teljesen negatív headline-ok nagyon kiemeltek,
- ahogy pozitívabb lesz a headline, eléggé csökken a kiemelés.

#### Kormányközeli portálokra (`gov = 1`)
A modell:
$$
\hat y = 0.85 - 0.30 \cdot sentiment
$$

Itt is csökken a kiemelés, de jóval laposabban.

### Emberi fordítás
> Mindkét médiablokk szereti jobban kiemelni a negatívabb headline-okat, csak az egyik sokkal erősebben csinálja.

### Mire figyelünk a modellben?
- **β1**: van-e általános szentimenthatás?
- **β2**: van-e alapszint-különbség a két portáltípus között?
- **β3**: eltér-e a szentiment hatásának erőssége a két csoportban?

### Mit nem tud a regresszió?
Nem bizonyít okságot. Attól, hogy a negatív headline-ok kiemeltebbek, még lehet, hogy egyszerűen fontosabb hard news témákról van szó.

### Modell-illeszkedési mutatók: mit érdemes nézni?
Amikor lefut egy regresszió, nem csak az érdekes, hogy az egyes együtthatók szignifikánsak-e. Az is fontos, hogy a modell **összességében mennyire írja le az adatokat**.

A leggyakoribb mutatók, amikkel itt érdemes megbarátkozni:
- **R²**
- **korrigált R²**
- **F-statisztika**

---

### R² – mennyit magyaráz meg a modell?
Az **R²** azt mutatja, hogy a függő változó szóródásának mekkora részét tudja megmagyarázni a modell.

Ha például:
- a függő változó a `norm_score`,
- a magyarázó változók pedig a `sentiment`, a `gov` és az interakció,

akkor az R² azt mondja meg, hogy a `norm_score` varianciájából mennyi az, amit ez a három elem együtt „elkap”.

### Fake példa
Képzeld el, hogy a headline-ok vizuális hangsúlya nagyon sok mindentől függ:
- szentiment,
- portáltípus,
- téma,
- breaking news jelleg,
- képhasználat,
- napszak,
- szerkesztői rutin,
- meg még egy csomó minden mástól.

Ha a modellünk csak ezek közül hármat használ, és **R² = 0.07**, az azt jelenti, hogy a teljes szóródás kb. **7%-át** magyarázza meg.

### Ez sok vagy kevés?
Társadalomtudományi és médiás adatoknál ez simán lehet teljesen értelmes eredmény.

Nem azt jelenti, hogy a modell rossz. Inkább azt jelenti:
> van benne valódi jel, de a vizsgált jelenséget sok más tényező is alakítja.

### Emberi nyelven
> Az R² nem azt kérdezi, hogy a modell „igaz-e”, hanem azt, hogy mennyit tud megfogni a valóság kuszaságából.

---

### Korrigált R² – ugyanaz, csak kevésbé hagyja magát átverni
A sima R² szinte mindig nő, ha új változókat teszel a modellbe — még akkor is, ha azok nem túl hasznosak.

A **korrigált R²** ezért egy kicsit szigorúbb. Figyelembe veszi, hogy hány prediktor van a modellben, és nem jutalmazza automatikusan a felesleges bővítgetést.

### Rövid intuíció
- **R²**: „mennyi varianciát fogtál meg?”
- **korrigált R²**: „oké, de ezt értelmesen fogtad meg, vagy csak teleszórtad a modellt változókkal?”

### Fake példa
Tegyük fel, hogy van egy modell:
- `sentiment`
- `gov`
- `sentiment × gov`

és erre:
- **R² = 0.071**
- **korrigált R² = 0.070**

Ez azt sugallja, hogy a modell változói tényleg hordoznak információt, és nem csak azért lett jobb az illeszkedés, mert több mindent beledobtunk.

Ha viszont ez lenne:
- **R² = 0.15**
- **korrigált R² = 0.04**

az már gyanúsabb lenne: lehet, hogy túl sok fölösleges változó van a modellben.

---

### F-statisztika – jobb-e a modell, mint a nagy semmi?
Az **F-statisztika** azt teszteli, hogy a modell **egészében** jobb-e, mint egy olyan buta alapmodell, amely semmit nem használ a magyarázó változókból, csak az átlagot.

Magyarul a kérdés ez:
> az egész regresszió együtt ad-e valami értelmes pluszt, vagy ugyanott lennénk nélküle is?

### Fake példa
Képzeld el, hogy a `norm_score` átlagosan 0.48.

Az egyik „modell” azt mondja minden headline-ra, hogy:
> szerintem 0.48 lesz, mindegy milyen a szentiment és melyik portálról jön.

A rendes regressziós modell viszont már használja:
- a szentimentet,
- a portáltípust,
- és az interakciót.

Az F-teszt azt vizsgálja, hogy ez az összetettebb modell **érdemben jobb-e**, mint az a lusta átlagmodell.

### Hogyan olvassuk?
- **nagyobb F** + **kicsi p-érték** → a modell összességében szignifikáns
- **kicsi F** + **nagy p-érték** → a modell egészében nem túl meggyőző

### Fontos
Az F-statisztika nem azt mondja meg, hogy a modell mindent megmagyaráz.
Csak azt, hogy:
> a bevitt változók együtt többet tudnak, mint a puszta átlag.

---

### A három mutató együtt
A legjobb, ha ezt a három számot együtt olvasod:

- **R²** → mekkora szeletét magyarázza a varianciának a modell?
- **korrigált R²** → ez a magyarázóerő mennyire stabil a modell bonyolultságához képest?
- **F-statisztika** → a modell egészében jobb-e, mint az üres referencia?

### Egy tipikus, józan értelmezés
Ha ezt látod:
- **R² = 0.07**
- **korrigált R² = 0.07**
- **F p < 0.001**

akkor az értelmezés kb. ez:
> a modell összességében egyértelműen szignifikáns, van benne valódi jel, de a magyarázóereje korlátozott — vagyis a headline-ok vizuális hangsúlyát sok más tényező is alakítja.

Ez médiakutatásban teljesen életszerű helyzet.

### Mini cheat sheet – gyors olvasóverzió

| Mutató | Mit kérdez? | Egyszerű olvasat | Mire figyelj? |
|---|---|---|---|
| **R²** | A modell mennyi varianciát magyaráz meg? | Minél nagyobb, annál több mintázatot fog meg | Társadalomtudományban a kisebb R² sem feltétlen baj |
| **Korrigált R²** | Ugyanez, de bünteti a felesleges változókat | Ha közel van az R²-hez, az jó jel | Ha nagyon beesik az R²-hez képest, lehet túlzsúfolt a modell |
| **F-statisztika** | A modell összességében jobb-e, mint az átlagmodell? | Kicsi p-érték esetén a modell egészében szignifikáns | Ez nem ugyanaz, mint a nagy magyarázóerő |
| **Együttható p-érték** | Egy adott változó külön számít-e? | Kicsi p-érték → van jel | Önmagában nem mondja meg a gyakorlati jelentőséget |
| **Hatásirány** | Pozitív vagy negatív az összefüggés? | Megmondja, merre mozdul a kapcsolat | Mindig a modell kontextusában olvasd |

### Konkrét példa a projektből
A H2 regressziós modelljének egyik futásában ezek a főbb illeszkedési mutatók szerepeltek:

- **N = 29686**
- **R² = 0.0706**
- **korrigált R² = 0.0706**
- **F = 752.15**
- **F-teszt p < 0.001**

### Mit jelent ez magyarul?

#### 1. A minta nagy
A majdnem harmincezres elemszám azt jelenti, hogy elég sok headline alapján becsüljük a modellt. Ez növeli a statisztikai erőt, vagyis könnyebben észrevehetőek kisebb, de stabil mintázatok is.

#### 2. Az R² alapján a modell nem „mindent megmagyarázó”, de nem is üres
Az **R² = 0.0706** azt jelenti, hogy a modell a `norm_score` varianciájának kb. **7,1%-át** magyarázza meg.

Ez elsőre nem tűnik óriásinak, de itt nem is azt várjuk, hogy három változó teljesen leírja a szerkesztőségi döntéseket. A headline-ok kiemelését rengeteg más dolog is alakítja, például:
- a hír témája,
- breaking news jelleg,
- képhasználat,
- portálspecifikus szerkesztési rutin,
- aktuális politikai helyzet,
- napszak vagy ciklushatás.

A helyes olvasat tehát inkább ez:
> a szentiment és a portáltípus kimutathatóan számít, de messze nem csak ezek számítanak.

#### 3. A korrigált R² gyakorlatilag ugyanaz
Az, hogy a **korrigált R² = 0.0706** szinte megegyezik az R²-vel, jó jel.

Ez arra utal, hogy a modell nem attól „látszik jónak”, hogy tele van pakolva fölösleges változókkal. A bevitt prediktorok valóban hordoznak információt.

#### 4. Az F-statisztika nagyon erős összképet ad
Az **F = 752.15** és a **p < 0.001** azt mondja, hogy a modell egészében nagyon messze van attól a helyzettől, amikor csak az átlaggal dobálóznánk.

Vagyis:
> a `sentiment`, a `gov` és az interakció együtt egyértelműen több információt ad a `norm_score`-ról, mint az üres referencia.

### Rövid, kész interpretáció ehhez a konkrét számcsomaghoz
Ha ezt egy kész dolgozatban vagy prezentációban egy mondatban kellene elmondani, valahogy így hangzana:

> A regressziós modell összességében szignifikáns (F = 752.15, p < 0.001), de a magyarázóereje mérsékelt (R² = 0.0706), ami arra utal, hogy a szentiment és a portáltípus valódi, de részleges magyarázatot ad a headline-ok vizuális kiemelésére.

---

# 6. Miért használunk több módszert ugyanarra a kérdésre?

Mert egyetlen teszt alapján könnyű túl sokat mondani.

### H2 jó példa erre
Ugyanazt a kérdést több oldalról nézzük:
- **Spearman:** van-e általános együttjárás?
- **Mann–Whitney:** a negatív headline-ok tényleg kiemeltebbek-e?
- **Regresszió:** fennmarad-e a kapcsolat akkor is, ha a portáltípust is belerakjuk?

Ha mind ugyanabba az irányba mutat, akkor az eredmény meggyőzőbb.

---

# 7. Gyakori értelmezési hibák

## 7.1. „Szignifikáns, tehát fontos”
Nem feltétlenül. Nagy mintán pici különbségek is szignifikánsak lehetnek.

Ezért kell a hatásméret.

## 7.2. „Korreláció, tehát ok-okozat”
Nem. A korreláció együttjárás, nem automatikus bizonyíték arra, hogy az egyik okozza a másikat.

## 7.3. „Az LLM mondta, tehát objektív”
Nem. Az LLM hasznos annotátor, de nem tévedhetetlen mérőeszköz.

## 7.4. „A norm_score abszolút igazság”
Nem. Ez egy relatív, portálon belüli kiemelésmutató.

---

# 8. Módszertani korlátok

## 8.1. Szentimentbecslés
A headline szentimentjét modell becsli. Ez praktikus, de zajos lehet.

## 8.2. Portálcsoportok
A „kormányközeli” és „független” címkék hasznos egyszerűsítések, de a valóság ennél árnyaltabb lehet.

## 8.3. Vizuális score
A score jó közelítés, de nem azonos a valós emberi figyelemmel.

## 8.4. Témakülönbségek
A negatív headline-ok lehetnek azért is kiemeltebbek, mert gyakrabban kapcsolódnak breaking news vagy hard news témákhoz.

## 8.5. H3 inferenciális ereje
A csoporton belüli korrelációkülönbségek egy része inkább leíró/heurisztikus, mint teljesen lezárt formális teszt.

---

# 9. Ha ezt tanítanád, milyen sorrendben magyaráznád?

1. Mi a headline és mi a vizuális kiemelés?
2. Miért kell normalizálni?
3. Mi a különbség a „miről írnak?” és a „hogyan írnak róla?” között?
4. Mit tud a Mann–Whitney, a Spearman és a Pearson?
5. Mire jó a regresszió, amikor már több tényezőt akarunk egyszerre kezelni?
6. Miért kell mindig külön beszélni eredményről és korlátról?

---

# 10. Rövid módszertani takeaway-k

### H1 takeaway
Két médiablokkot hasonlítunk össze ugyanarra a szereplőre, és azt nézzük, különbözik-e a hangnem és a kiemelés.

### H2 takeaway
Azt ellenőrizzük több módszerrel, hogy a negatív headline-ok tényleg előnyt élveznek-e a főoldali figyelemversenyben.

### H3 takeaway
Elválasztjuk egymástól a témaválasztás szinkronját és a keretezés különbségeit.

---

# 11. Egy mondatban a dokumentum lényege

A projekt módszertana headline-szintű szöveg- és vizuális jellemzőkből épít fel egy olyan elemzési keretet, amelyben a média **hangneme**, **kiemelési logikája** és **napirendképző működése** egyszerre vizsgálható.
