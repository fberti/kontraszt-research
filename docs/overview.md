**Manipulálnak-e minket a hírportálok, és ha igen, hogyan?**

A magyar online hírportálok (Telex, Index, Origo, HVG stb.) főoldalait vizsgáljuk, különösen választások idején. Három dolgot nézünk:

1. **Ugyanazt a politikust hogyan mutatják be különböző portálok?** – Pl. az Origo pozitívan ír valakiről, a Telex negatívan? (H1)

2. **A negatív, ijesztős vagy drámai hírek nagyobb helyet kapnak-e a főoldalon?** – Pl. nagyobb betűméret, felső pozíció? (H2)

3. **Ha egy témáról az egyik portál ír, a többi is elkezd-e írni róla?** – De ugyanolyan hangnemben? (H3)

**Hogyan csináljuk?** Egy saját program automatikusan legyűjti a portálok főoldalait, és egy mesterséges intelligencia minden hírhez megmondja, hogy pozitív, negatív vagy semleges-e (1–10 skálán). Ezután statisztikákkal elemezzük az adatokat.

**Miért fontos?** Mert a portálok nemcsak híreket közölnek – azzal, hogy mit tesznek a lap tetejére és milyen hangnemben írnak, megmondják nekünk, hogy mire figyeljünk és mit gondoljunk róla. A kutatás ezt a "rejtett befolyást" teszi láthatóvá.

---

# A `h1_hypothesis.py` összefoglalója 

## 🎯 Mit vizsgál a szkript?

**H1 hipotézis:** A kormányközeli és a független magyar hírportálok **eltérő hangnemmel** és **eltérő vizuális súllyal** mutatják be ugyanazokat a politikusokat (Magyar Péter, Orbán Viktor).

## 🔧 A módszertan lépései

1. **Adatbetöltés:** három Parquet-fájlból jönnek az adatok:
   - címsorok szövege,
   - LLM-mel kinyert szentiment (0 = nagyon negatív, 1 = nagyon pozitív) és megemlített személyek,
   - vizuális „score" (pontszám a headline főoldali mérete + pozíciója alapján).

2. **Átlagolás:** ugyanaz a címsor többször is lehet „lementve" (scrape-elve), ezért címsoronként átlagolják a vizuális score-t.

3. **Normalizálás portálonként:** mivel minden portálnak más a score-skálája (mivel minden portálnak másképp néz ki, más a layout, a betűméret stb.), min-max normalizálás készül (minden portálon belül 0 és 1 közé kerülnek az értékek). Így összehasonlíthatók.

4. **Csoportosítás:** portálokat két táborba sorolják – Kormányközeli (Origo, Magyar Nemzet, PestiSrácok, …) és Független (Telex, 444.hu, HVG, …).

5. **Leíró statisztikák + ábrák:** mintaszámok, átlag, medián, szórás; hegedűdiagramok és oszlopdiagramok.

6. **Statisztikai teszt:** minden (entitás × mérőszám) kombinációra **Mann-Whitney U tesztet** futtatnak, majd **rank-biszeriális hatásméretet** számolnak.

7. **Verdikt:** ha a 4 tesztből legalább 3 szignifikáns (p < 0,05), a H1 megerősítettnek tekinthető.

## 📊 Mit találtak (az értelmezés szerint)

Tükörszerű, polarizált mintázat:
- **Magyar Péter**-t a kormányközeli oldalak **negatívabban** (Δ szentiment negatív), a függetlenek pozitívabban írják le.
- **Orbán Viktor**-t a kormányközeli oldalak **pozitívabban**, a függetlenek negatívabban írják le.
- **Mindkét politikust nagyobb vizuális súllyal** jelenítik meg a kormányközeli portálok – intenzívebb figyelemverseny.

A szkript végén a verdikt automatikusan ✅ megerősítve / ⚠️ részben / ❌ nem értékre áll, attól függően, hány teszt szignifikáns.

---

## 🧪 Hogyan működik a Mann-Whitney U teszt?

Ez egy **nem-paraméteres teszt**, amit akkor használunk, ha **két független csoport** értékeit szeretnénk összehasonlítani, de **nem akarunk feltételezni normális eloszlást**. A teszt nem a nyers értékekkel dolgozik, hanem azok **rangsorával**.

 Mit jelent, hogy egy teszt „nem-paraméteres"?                                                                                                                                  
                                                                                                                                                                                
 A kulcskérdés: feltételez-e a teszt valamit az adatok eloszlásáról?                                                                                                            
                                                                                                                                                                                
 A statisztikai tesztek két nagy családba sorolhatók aszerint, hogy mennyit feltételeznek előre az adatokról.                                                                   
                                                                                                                                                                                
 #### Paraméteres tesztek                                                                                                                                                        
                                                                                                                                                                                
 Ezek feltételezik, hogy az adatok valamilyen konkrét eloszlást követnek – leggyakrabban normális (Gauss-) eloszlást, azt a klasszikus „haranggörbét". Az ilyen eloszlásokat    
 néhány paraméter írja le teljesen (pl. a normális eloszlást az átlag μ és a szórás σ) – innen a név: paraméteres.                                                              
                                                                                                                                                                                
 Példák:                                                                                                                                                                        
 - t-próba – két csoport átlagát hasonlítja össze, feltételezi a normalitást.                                                                                                   
 - ANOVA – több csoport átlagát hasonlítja össze, szintén normalitást feltételez.                                                                                               
 - Pearson-korreláció – lineáris kapcsolatot és normalitást feltételez.                                                                                                         
                                                                                                                                                                                
 Ha a feltételezés igaz, ezek a tesztek nagyon erősek (kis mintából is kimutatnak valódi különbséget). Ha viszont nem igaz (ferde eloszlás, sok kiugró érték), akkor hibás      
 eredményt adhatnak – hamisan jeleznek különbséget, vagy épp valódi különbséget nem vesznek észre.                                                                              
                                                                                                                                                                                
 #### Nem-paraméteres tesztek                                                                                                                                                    
                                                                                                                                                                                
 Ezek nem feltételeznek konkrét eloszlást. Nem mondják meg előre, hogy „az adatoknak harang alakban kell szóródniuk". Ezért „eloszlásmentes" (distribution-free) teszteknek is  
 hívják őket.                                                                                                                                                                   
                                                                                                                                                                                
 Hogyan oldják meg? Általában nem a nyers számokkal dolgoznak, hanem azok rangsorával (vagy előjelével, vagy gyakoriságával). Ha csak a rangsor számít, akkor teljesen mindegy, 
 milyen az eloszlás alakja – a 7. legnagyobb érték attól még 7. legnagyobb lesz, akár haranggörbe, akár ferde, akár kétpúpú az eloszlás.                                        
                                                                                                                                                                                
 Példák:                                                                                                                                                                        
 - Mann-Whitney U – a t-próba nem-paraméteres párja.                                                                                                                            
 - Wilcoxon-teszt – párosított minták.                                                                                                                                          
 - Kruskal-Wallis – az ANOVA nem-paraméteres párja.                                                                                                                             
 - Spearman-korreláció – a Pearson rangsor-alapú változata.

### Lépésről lépésre egy mini példán

Tegyük fel, hogy 4 kormányközeli és 4 független címsor szentiment-értékeit látjuk Magyar Péterről:

| Csoport | Értékek |
|---|---|
| **Gov** (kormányközeli) | 0,20; 0,30; 0,25; 0,40 |
| **Ind** (független) | 0,55; 0,70; 0,65; 0,50 |

**1. lépés – összerakjuk az értékeket egy közös sorba és rangsoroljuk őket (1 = legkisebb):**

| Érték | 0,20 | 0,25 | 0,30 | 0,40 | 0,50 | 0,55 | 0,65 | 0,70 |
|---|---|---|---|---|---|---|---|---|
| Csoport | Gov | Gov | Gov | Gov | Ind | Ind | Ind | Ind |
| **Rang** | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |

**2. lépés – összeadjuk a rangokat csoportonként:**

- Gov rangösszeg: 1 + 2 + 3 + 4 = **10**
- Ind rangösszeg: 5 + 6 + 7 + 8 = **26**

**3. lépés – kiszámítjuk az U statisztikát.** Az U lényege: **hány olyan (Gov, Ind) páros van, ahol a Gov-érték kisebb, mint az Ind-érték?**

Itt **minden** Gov érték kisebb, mint **bármelyik** Ind érték → 4 × 4 = 16 „győzelem" az Ind oldalának. Így:
- U(Gov) = 0 (egyszer sem verte meg a Gov az Ind-et)
- U(Ind) = 16

A `scipy.stats.mannwhitneyu`(a scipy egy statisztikai könyvtár amit pythonban használunk) a kisebbik U-t (vagy a megadottat) adja vissza – itt U = 0.

**4. lépés – p-érték:** mennyire valószínű, hogy ilyen szélsőséges eredményt kapjunk, ha valójában a két csoport ugyanolyan? U = 0 nagyon szélsőséges → kis p-érték → a különbség szignifikáns.

**Intuíció:** ha a két csoport értékei teljesen össze lennének keveredve a rangsorban, U ≈ n₁·n₂/2 lenne (itt 8). Minél jobban „elkülönülnek" a rangsor két végére, annál szélsőségesebb U és annál kisebb p.

### Miért ezt használják a szkriptben?
- A szentiment- és score-eloszlások ferdék, sok kiugró értékkel → a t-próba nem lenne megbízható.
- Csak a **sorrend** számít, nem a pontos távolságok.
- Robusztus a kiugró értékekre.

---

## 📏 Mi az a rank-biszeriális hatásméret?

A p-érték csak azt árulja el, hogy **van-e** különbség, de nem azt, hogy **mekkora**. Erre kell egy **hatásméret** (effect size).

A **rank-biszeriális korreláció** képlete a Mann-Whitney U-ból közvetlenül:

$$r = 1 - \frac{2U}{n_1 \cdot n_2}$$

### Mit jelent intuitíven?

A képlet lényegében ezt mondja: **„ha véletlenszerűen kiválasztok egy Gov- és egy Ind-értéket, mekkora valószínűséggel lesz a Gov nagyobb, mint az Ind, mínusz a fordított eset valószínűsége"**.

- **r = +1** → minden Gov-érték nagyobb, mint bármelyik Ind-érték (tökéletes szétválás).
- **r = −1** → minden Gov-érték kisebb, mint bármelyik Ind-érték (fordított tökéletes szétválás).
- **r = 0** → véletlenszerű az, hogy a Gov vagy az Ind lesz-e nagyobb (nincs különbség).

### A mini példánkban

U = 0, n₁ = n₂ = 4 → r = 1 − (2·0)/(4·4) = **+1**

Ez azt jelenti: **teljesen elkülönül** a két csoport. (Persze csak 4–4 elemmel, ezért óvatosnak kell lenni, de ez csak ilyen mini példa)

### Értelmezési skála (amit a szkript is közöl)

| |r| | Jelentés |
|---|---|
| < 0,1 | elhanyagolható |
| 0,1–0,3 | gyenge |
| 0,3–0,5 | közepes |
| > 0,5 | erős |

**Miért hasznos a „rank"-biszeriális név?** Mert **rangsorokon** alapul (nem nyers értékeken), és kétértékű („biszeriális") csoportváltozóval (Gov/Ind) hasonlít össze egy folytonos mutatót. Így tökéletesen illik a Mann-Whitney teszt logikájához – ugyanabból az U-ból származtatható, amit a teszt már úgyis kiszámol.

Egyszerű hasonlat 🍎                                                                                                                                                           
                                                                                                                                                                                
 Képzeld el, hogy almákat akarsz összehasonlítani két gyümölcsöskertből.                                                                                                        
                                                                                                                                                                                
 - Paraméteres módszer: lemérem mindegyik alma pontos tömegét grammban, és átlagot számolok. Csak akkor működik jól, ha az almák szépen, szabályosan szóródnak egy átlag körül  
 (pl. normálisan).                                                                                                                                                              
 - Nem-paraméteres módszer: sorba rakom az almákat méret szerint (1., 2., 3., 4. …), és csak azt nézem, melyik kertből való almák kerültek előre, melyek hátra a sorban. Nem    
 érdekel a pontos gramm – csak a sorrend. Ez akkor is működik, ha van egy óriási kakukktojás alma, ami egy paraméteres tesztnél elrontaná az átlagot.  
---

**Egy mondatban összefoglalva:** a szkript a Mann-Whitney U teszttel megmutatja, hogy **van-e** statisztikailag szignifikáns különbség a kormányközeli és a független portálok között, a rank-biszeriális r-rel pedig azt, hogy ez a különbség **mekkora** a gyakorlatban – és az eredmények szerint mind hangnemben, mind vizuális hangsúlyban tükörszerű polarizáció rajzolódik ki.

---

# A `h2_hypothesis.py` részletes összefoglalója

## 🎯 Mit vizsgál a szkript?

A `h2_hypothesis.py` a **H2 hipotézist** teszteli:

> **A negatív érzelmi töltetű szalagcímek átlagosan nagyobb vizuális hangsúlyt kapnak** a hírportálok főoldalain, mint a semleges vagy pozitív hírek.

A kérdés mögötti intuíció egyszerű: a szerkesztőségek nemcsak azzal befolyásolják a figyelmünket, **miről írnak**, hanem azzal is, **mit tesznek nagy betűvel, előre, középre vagy a hajtás fölé**. A H2 tehát azt nézi, hogy a **negatív hangulatú hírek kiemeltebb helyet kapnak-e**.

A szkript nemcsak összességében vizsgálja ezt, hanem külön bontásban is:
- **kormányközeli portáloknál**
- **független portáloknál**

Így az is kiderülhet, hogy a negatív hírek kiemelése általános médiaminta, vagy inkább valamelyik portáltípus sajátossága.

---

## 🧱 Az elemzés teljes menete röviden

A fájl három, egymásra épülő szinten vizsgálja ugyanazt a kérdést:

1. **Spearman-korreláció**  
   Megnézi, hogy a szentiment és a vizuális hangsúly együtt mozog-e.

2. **Mann–Whitney U tesztek szentiment-sávok között**  
   Közvetlenül összeveti, hogy a negatív, semleges és pozitív címek mennyire kiemeltek.

3. **Regressziós modell interakcióval**  
   Egyszerre kezeli a szentimentet és a portáltípust, és azt is teszteli, hogy a két portáltípusnál eltér-e a kapcsolat erőssége.

Ez jó elemzési stratégia, mert ugyanarra a kérdésre **három külön nézőpontból** ad választ:
- van-e általános együttjárás,
- van-e csoportkülönbség,
- fennmarad-e a hatás akkor is, ha több tényezőt egyszerre vizsgálunk.

---

## 📥 Milyen adatokat használ?

A szkript három Parquet-fájlból dolgozik:

- `headlineDefinitions_2026-04-19.parquet`  
  az egyes címsorok alapadatai
- `llmAnalysis_2026-04-19.parquet`  
  az LLM által becsült szentiment (`sentiment_score`) és más szöveges jellemzők
- `headlines_2026-04-19.parquet`  
  a főoldali vizuális megjelenésből számolt `score`

A lényegi változók:

- **`sentiment_score`**: 0 és 1 közötti szám  
  - 0 felé: negatívabb cím
  - 1 felé: pozitívabb cím

- **`score` / `mean_score`**: vizuális hangsúly  
  Minél nagyobb, annál hangsúlyosabb a cím a főoldalon.

- **`norm_score`**: portálon belül normalizált vizuális hangsúly  
  Ez a végső változó, amit az elemzés használ.

---

## ⚙️ Előkészítés: hogyan lesz a nyers adatokból elemezhető tábla?

### 1. Címsoronként átlagolt vizuális score

Ugyanaz a headline több scrape-ben is megjelenhetett. Emiatt a szkript először `hashedId` szerint csoportosít, majd kiszámolja a headline-hoz tartozó átlagos vizuális score-t:

- egy headline = egy átlagos vizuális hangsúly

Ez azért fontos, mert különben a gyakrabban mentett oldalak túlreprezentáltak lennének.

### 2. Tábla-összefűzés

A headline-metaadatok, az LLM-szentiment és a vizuális score összejoinolódik `hashedId` alapján. Így minden címsorhoz egy sorban lesz:

- melyik portálról származik,
- milyen a szentimentje,
- mekkora volt a vizuális hangsúlya.

### 3. Portálon belüli min-max normalizálás

A különböző portálok layoutja eltérő. Ami az egyik oldalon „nagy kiemelés”, az a másikon lehet átlagos. Ezért a szkript **portálonként** normalizál:

$$
\text{norm\_score} = \frac{\text{mean\_score} - \text{min}}{\text{max} - \text{min}}
$$

Így minden portálon belül:
- a legkevésbé hangsúlyos headline közel 0,
- a leginkább hangsúlyos headline közel 1.

### Miért jó ez?

Mert nem abszolút pixeleket vagy betűméreteket hasonlítunk össze különböző oldalak között, hanem azt kérdezzük:

> **az adott portál saját logikáján belül mennyire emelte ki ezt a címet?**

---

## 🏷️ Portáltípusok kialakítása

A szkript két kategóriába sorolja a portálokat:

### Kormányközeli
- Origo
- Magyar Nemzet
- PestiSracok
- Hirado.hu
- Ripost
- Metropol
- Mandiner

### Független
- Telex
- 444.hu
- HVG
- ATV
- Magyar Hang
- 24.hu
- Nepszava
- Valasz Online

Minden további elemzés ezeket a kategóriákat használja.

---

## 📊 Mintaeloszlás: miért nézi a szkript a szentiment-sávokat?

A folytonos `sentiment_score`-ból a kód három könnyebben értelmezhető csoportot képez:

- **Negatív**: `sentiment_score < 0.35`
- **Semleges**: `0.35 ≤ sentiment_score ≤ 0.65`
- **Pozitív**: `sentiment_score > 0.65`

Ezután megszámolja, hogy a két portáltípuson belül milyen arányban fordulnak elő ezek a sávok.

### Miért fontos ez?

Mert mielőtt összehasonlítjuk a vizuális hangsúlyt, látni kell, hogy:
- van-e elég adat minden sávban,
- nagyon torz-e valamelyik portáltípus eloszlása,
- nem pusztán abból fakad-e egy eredmény, hogy az egyik oldalon alig vannak pozitív vagy negatív címek.

---

## 1. lépés – Spearman-féle rangkorreláció

### 🧠 Mit kérdez ez a lépés?

Azt, hogy:

> **ha egy headline szentimentje negatívabb, akkor hajlamos-e nagyobb vizuális hangsúlyt kapni?**

A Spearman-korreláció nem a nyers számokat, hanem azok **rangsorát** nézi. Ezért jó választás, ha:
- az eloszlások nem szépek,
- nem feltétlen lineáris kapcsolatot keresünk,
- inkább azt vizsgáljuk, hogy „egyik változó növekedésével a másik tipikusan nő vagy csökken-e”.

### 📐 A Spearman ρ jelentése

- **ρ < 0** → minél negatívabb a cím, annál nagyobb a vizuális hangsúly  
- **ρ ≈ 0** → nincs érdemi kapcsolat  
- **ρ > 0** → minél pozitívabb a cím, annál nagyobb a vizuális hangsúly

A szkript külön kiszámítja ezt:
- az **összes headline-ra**,
- a **kormányközeli** portálokra,
- a **független** portálokra.

### 🧾 Mit olvasunk ki a táblából?

A kódban kiszámolt értékek szerint:

- **Összes**: `ρ = -0.100`
- **Kormányközeli**: `ρ = -0.085`
- **Független**: `ρ = -0.114`

#### Egyszerű értelmezés

Mindhárom negatív, tehát ugyanabba az irányba mutatnak:

> **a negatívabb címek átlagosan valamivel hangsúlyosabb helyet kapnak.**

#### Mennyire erős ez?

A szkript saját skálája szerint:
- `|ρ| < 0.1` → elhanyagolható
- `0.1–0.3` → gyenge

Ez alapján a kapcsolat:
- **kormányközeli portálokon** nagyon gyenge / elhanyagolható,
- **független portálokon** gyenge,
- **összességében** gyenge.

#### Fontos tanulság

A kapcsolat **nem erős**, de a minta nagyon nagy, ezért statisztikailag mégis meggyőző lehet.

Ez azt jelenti:
- **nem minden negatív headline lesz kiemelt**,
- de **átlagosan van egy kis, következetes eltolódás** ebbe az irányba.

---

## 2. lépés – Mann–Whitney U tesztek a szentiment-sávok között

A Spearman csak azt mondja meg, hogy van-e általános együttjárás. A következő kérdés már konkrétabb:

> **A negatív címek ténylegesen jobban ki vannak-e emelve, mint a semleges vagy pozitív címek?**

Ehhez a szkript a három szentiment-sáv vizuális hangsúly-eloszlását hasonlítja össze.

### Vizsgált összehasonlítások

- **Negatív vs. Semleges**  
  Ez a H2 legfontosabb tesztje.

- **Negatív vs. Pozitív**  
  A két véglet összevetése.

- **Semleges vs. Pozitív**  
  Kontroll-összehasonlítás.

A tesztet lefuttatja:
- összesen,
- kormányközeli portálokra,
- független portálokra.

### Miért nem t-próba?

Mert a `norm_score` tipikusan nem szép normális eloszlású:
- össze van nyomva 0 és 1 közé,
- lehet ferde,
- lehetnek sűrűsödések és szélsőértékek.

A Mann–Whitney U teszt nem-paraméteres, tehát itt robusztusabb.

### Mit ad vissza a teszt?

- **U statisztika**
- **p-érték**
- **rank-biszériális r** mint hatásméret

A szkript H2-irányban egyoldali tesztet használ a negatív összevetésekhez:

> tényleg igaz-e, hogy a negatív sáv score-ja nagyobb?

### Hogyan értelmezzük az eredményt?

Ha a negatív sáv mediánja magasabb, a p-érték kicsi, és az `r` pozitív, akkor ez a H2-t támogatja.

A végén a szkript megszámolja, hogy a H2 szempontjából releváns tesztek közül hány lett szignifikáns a várt irányban, és ebből ad egy részverdiktet:
- ✅ alátámasztva
- ⚠️ részben alátámasztva
- ❌ nem alátámasztva / ellentmond

---

## 3. lépés – Regressziós modell interakcióval

Ez a fájl legfontosabb és legmélyebb része. Itt már nem csak két csoportot hasonlítunk össze, hanem **egy modellt építünk**, ami egyszerre több tényezőt kezel.

### 🎯 Mit akarunk tudni a regresszióból?

Két fő kérdést:

1. **Ha a portáltípust kontrolláljuk, akkor is látszik-e a szentiment hatása a vizuális hangsúlyra?**
2. **Ugyanolyan erős ez a hatás a kormányközeli és a független portálokon?**

A regresszió pont erre jó: egyszerre becsüli meg a tényezők önálló és közös hatását.

---

### 🧮 A modell képlete

A kód ezt a lineáris modellt becsli:

$$
\text{norm\_score} = \beta_0 + \beta_1 \cdot \text{sentiment\_score} + \beta_2 \cdot \text{gov} + \beta_3 \cdot (\text{sentiment\_score} \times \text{gov}) + \varepsilon
$$

ahol:
- `norm_score` = a headline normalizált vizuális hangsúlya
- `sentiment_score` = a headline érzelmi tónusa 0 és 1 között
- `gov` = 1, ha kormányközeli portál; 0, ha független
- `sentiment_score × gov` = interakciós tag
- `ε` = minden más, amit a modell nem magyaráz meg

---

### 🧠 Mit jelent az, hogy lineáris regresszió?

A lineáris regresszió megpróbál egy olyan egyenest találni, ami a lehető legjobban leírja:

> hogyan változik az egyik változó (`norm_score`), ha változik a másik (`sentiment_score`), illetve ha másik csoportba tartozunk (`gov`).

Nem azt mondja, hogy minden pont pontosan az egyenesre esik. Azt mondja:

> **átlagosan milyen irányú és mekkora eltolódás várható**.

A modell tehát nem egyetlen headline sorsát jósolja meg tökéletesen, hanem az általános mintázatot becsli.

---

### 🧩 Az együtthatók jelentése nagyon egyszerűen

#### `β₀` – Intercept

Ez az alapkiinduló érték.

Ebben a modellben azt mondja meg, hogy:

> **független portáloknál**, teljesen negatív cím esetén (`sentiment_score = 0`), várhatóan mekkora a `norm_score`.

Tehát ez egy referencia-pont.

#### `β₁` – a szentiment hatása a független portálokon

Ez azt mondja meg, hogy:

> ha a headline szentimentje 0-ról 1-re megy, mennyit változik a vizuális hangsúly a **független** portálokon?

- Ha **negatív**, akkor a pozitívabb címek kisebb hangsúlyt kapnak → vagyis a negatívabbak nagyobbat.
- Ha **pozitív**, akkor fordítva.

#### `β₂` – kormányközeli alapszint-különbség

Ez azt mutatja meg, hogy:

> ugyanannál a nagyon negatív címnél (`sentiment = 0`) a kormányközeli portálok átlagosan mennyivel térnek el a függetlenektől a vizuális hangsúlyban.

Tehát ez egy **függőleges eltolás** a két csoport egyenese között.

#### `β₃` – interakció

Ez a legfontosabb extra elem. Azt mondja meg, hogy:

> **mennyivel más a szentiment meredeksége a kormányközeli portálokon**, mint a függetleneken.

Másképp:
- `β₁` = független portálok meredeksége
- `β₁ + β₃` = kormányközeli portálok meredeksége

Ha `β₃` szignifikáns, akkor a két portáltípus **nem ugyanúgy reagál** a negatív/pozitív tónusra.

---

### 📈 Hogyan néz ki ez fejben?

A modell két egyenest rajzol:

- egyet a **független** portálokra,
- egyet a **kormányközeli** portálokra.

A kérdés:
- lefelé mennek-e ezek az egyenesek?  
  → akkor a negatívabb címek hangsúlyosabbak
- ugyanolyan meredekek-e?  
  → ha nem, akkor a két portáltípus eltérően működik
- azonos magasságban indulnak-e?  
  → ha nem, akkor van alapszint-különbség is

---

### 🧪 Rövid fake data példa

Tegyük fel, hogy csak 8 headline-unk van.

| Portáltípus | gov | sentiment_score | norm_score |
|---|---:|---:|---:|
| Független | 0 | 0.1 | 0.90 |
| Független | 0 | 0.3 | 0.75 |
| Független | 0 | 0.7 | 0.45 |
| Független | 0 | 0.9 | 0.30 |
| Kormányközeli | 1 | 0.1 | 0.80 |
| Kormányközeli | 1 | 0.3 | 0.72 |
| Kormányközeli | 1 | 0.7 | 0.60 |
| Kormányközeli | 1 | 0.9 | 0.58 |

#### Mit látunk szemre?

- A **független** portáloknál ahogy nő a szentiment (egyre pozitívabb a cím), a vizuális hangsúly elég erősen csökken.
- A **kormányközeli** portáloknál is csökken, de laposabban.

Tehát mindkét csoportban igaznak tűnik, hogy a negatívabb címek kiemeltebbek, de a hatás erősebb a függetleneknél.

#### Képzeljünk el hozzá egy becsült modellt

Mondjuk a regresszió ezt adja:

$$
\hat y = 0.95 - 0.70 \cdot sentiment - 0.10 \cdot gov + 0.40 \cdot (sentiment \times gov)
$$

Ez mit jelent?

##### Független portálokra (`gov = 0`)

Ekkor a modell:

$$
\hat y = 0.95 - 0.70 \cdot sentiment
$$

- **Intercept = 0.95**  
  teljesen negatív címnél kb. 0.95-ös kiemelés várható
- **Meredekség = -0.70**  
  ahogy a headline pozitívabb lesz, a kiemelés csökken

##### Kormányközeli portálokra (`gov = 1`)

Ekkor:

$$
\hat y = 0.95 - 0.70 \cdot sentiment - 0.10 + 0.40 \cdot sentiment
$$

ami egyszerűsítve:

$$
\hat y = 0.85 - 0.30 \cdot sentiment
$$

Vagyis:
- **alacsonyabbról indul** (`0.85` vs `0.95`), tehát a nagyon negatív headline-oknál is kicsit kisebb az alapszintű kiemelés,
- **kevésbé meredek** (`-0.30` vs `-0.70`), tehát a negatív-pozitív különbség kevésbé számít.

#### Ebből hogyan olvassuk ki az együtthatókat?

- **`β₀ = 0.95`**  
  független portál, teljesen negatív cím, várható score

- **`β₁ = -0.70`**  
  független portálokon erős negatív kapcsolat: minél pozitívabb a cím, annál kisebb a hangsúly

- **`β₂ = -0.10`**  
  a kormányközeli portálok 0.10-del alacsonyabbról indulnak a referenciahelyzetben

- **`β₃ = +0.40`**  
  a kormányközeli portálok meredeksége ennyivel kevésbé negatív  
  (`-0.70 + 0.40 = -0.30`)

#### Intuitív mondatban

> A fake példában a negatív headline-ok mindkét portáltípusnál kiemeltebbek, **de a független portáloknál sokkal erősebb ez a hatás**.

Ez pontosan az, amire az interakciós regresszió alkalmas: nemcsak azt mondja meg, hogy „van-e hatás”, hanem azt is, hogy **melyik csoportban mennyire erős**.

---

### 🧭 Hogyan értelmezzük a valódi modell kimenetét?

A szkript a `statsmodels` OLS-modellt használja, és táblába rendezi:

- becslés (`becslés`)
- standard hiba (`std. hiba`)
- 95%-os konfidenciaintervallum
- p-érték
- szignifikancia-jelölés

#### Mit nézzünk először?

##### 1. `β₁` – a fő H2 jel

Ez a legfontosabb:
- ha **negatív és szignifikáns**, akkor a H2 támogatást kap,
- mert ez azt jelenti, hogy a **független portáloknál** a negatívabb címek jobban kiemeltek.

##### 2. `β₃` – eltér-e a két portáltípus?

- ha **szignifikáns**, akkor a szentiment hatása nem egyforma a két oldaltípuson,
- ha **nem szignifikáns**, akkor nincs erős bizonyíték arra, hogy különböznének.

##### 3. `β₂` – van-e alapszint-különbség?

Ez azt mutatja, hogy az egyik portáltípus önmagában, a referenciahelyzetben, eleve feljebb vagy lejjebb van-e.

---

### ⚠️ Fontos: mit tud és mit nem tud a regresszió?

#### Amit tud

- egyszerre több változót kezel,
- kontrollálni tudja a portáltípust,
- megmutatja, hogy a kapcsolat iránya és erőssége fennmarad-e,
- teszteli a csoportok közötti eltérő meredekséget.

#### Amit nem tud

- nem bizonyít ok-okozatot,
- nem mondja meg, hogy a szerkesztők tudatosan csinálják-e,
- nem kezeli automatikusan az összes lehetséges zavaró változót (pl. téma, breaking news, bűnügy, háború, katasztrófa).

Vagyis ha a negatív címek kiemeltebbek, attól még lehet, hogy egyszerűen a negatív hírek gyakrabban „hard news”-ok, amelyeket amúgy is előre tesznek.

---

## 🪜 Miért kell mindhárom módszer együtt?

A három lépés együtt sokkal erősebb, mint bármelyik önmagában.

### Spearman
Jó első ellenőrzés arra, hogy van-e általános monotón kapcsolat.

### Mann–Whitney
Közérthető módon összehasonlítja a negatív, semleges és pozitív csoportokat.

### Regresszió
A legösszetettebb ellenőrzés: egyszerre több tényezőt kezel és interakciót tesztel.

Ha ugyanabba az irányba mutatnak, akkor az eredmény sokkal meggyőzőbb.

---

## 🧾 A szkript végső verdikt-logikája

A fájl a végén összegyűjti a három bizonyítékvonal eredményét:

1. támogatja-e a H2-t a **Spearman**,
2. támogatják-e a H2-t a **Mann–Whitney** tesztek,
3. támogatja-e a H2-t a **regresszió** (`β₁ < 0` és szignifikáns).

Ezután pontoz:
- **3 / 3** → H2 megerősítve
- **2 / 3** → H2 túlnyomóan megerősítve
- **1 / 3** → H2 részben megerősítve
- **0 / 3** → H2 nincs megerősítve

Ez kifejezetten jó gyakorlat, mert nem egyetlen tesztre bízza a teljes következtetést.

---

## 🧠 Egyszerű, emberi nyelvű összefoglalás

A `h2_hypothesis.py` lényegében ezt kérdezi:

> **A hírportálok a negatívabb híreket jobban az arcunkba tolják-e?**

Ehhez először headline-onként kiszámolja, mennyire volt kiemelt egy cím a saját portálján belül, majd összekapcsolja ezt a headline érzelmi tónusával. Ezután háromféle statisztikai nézőpontból ellenőrzi ugyanazt az állítást:

- együtt jár-e a negatív hangnem és a nagyobb kiemelés,
- magasabb-e a negatív headline-ok medián kiemelése,
- fennmarad-e a kapcsolat akkor is, ha a portáltípust is figyelembe vesszük.

A regressziós modell ebben a struktúrában a legerősebb elem, mert külön tudja választani:
- a szentiment főhatását,
- a portáltípus hatását,
- és azt, hogy a két portáltípusnál azonos-e a szentiment hatása.

---

## ✅ Mit érdemes megjegyezni ebből az egészből?

Ha valaki csak a lényegre kíváncsi, ez a néhány mondat a kulcs:

1. A fájl azt vizsgálja, hogy **a negatív headline-ok nagyobb vizuális hangsúlyt kapnak-e**.
2. A vizuális hangsúlyt portálon belül normalizálja, így **relatív kiemelést** mér.
3. A Spearman-korreláció azt nézi, hogy **együtt mozog-e** a negatív hangnem és a kiemelés.
4. A Mann–Whitney tesztek azt nézik, hogy **a negatív sáv ténylegesen magasabb hangsúlyú-e**, mint a semleges vagy pozitív.
5. A regresszió azt nézi, hogy **a hatás fennmarad-e kontroll után is**, és hogy **különbözik-e a két portáltípus között**.
6. Az interakciós együttható (`β₃`) a kulcs ahhoz, hogy megmondjuk: **nemcsak van-e hatás, hanem ugyanúgy működik-e mindenhol**.

---

## 🛑 Korlátok és óvatos értelmezés

A szkript maga is helyesen jelzi a korlátokat:

- a szentimentet LLM becsli, tehát nem „objektív műszeres” mérés,
- a `norm_score` relatív mutató, nem abszolút vizuális erő,
- az összefüggés korrelációs jellegű,
- nem zárható ki, hogy a negatív headline-ok más okból hangsúlyosak (pl. objektíven fontosabb események).

Ezért a helyes megfogalmazás nem az, hogy:

> „bebizonyítottuk, hogy a szerkesztők manipulálnak”

hanem inkább az, hogy:

> **kimutatható statisztikai kapcsolat van a headline negatív érzelmi tónusa és a főoldali vizuális kiemelés között, és ez a kapcsolat több módszerrel is ellenőrizhető.**

Ez már önmagában nagyon erős kutatási eredmény.

---

# A `h3_hypothesis.py` részletes összefoglalója

## 🎯 Mit vizsgál a szkript?

A `h3_hypothesis.py` a **H3 hipotézist** vizsgálja, amely a média működésének egy másik, fontosabb szerkezeti szintjére kérdez rá:

> **A különböző portálok nemcsak máshogy írnak ugyanarról, hanem összehangoltan azt is eldöntik-e, hogy egyáltalán miről írjanak?**

Ez az úgynevezett **agenda-setting**, magyarul **napirend-kijelölés** kérdése.

A H3 két részre bontja ezt a problémát:

### (A) Belső napirend-szinkronitás
Azt vizsgálja, hogy a kormányközeli portálok **egymással jobban szinkronban mozognak-e**, mint a független portálok. 

Ez azt jelentené, hogy ha egy adott napon bizonyos szereplők vagy témák hirtelen sokszor jelennek meg az egyik kormányközeli oldalon, akkor ugyanezek az entitások a többi kormányközeli oldalon is hasonló ritmusban jelennek meg.

### (B) Portálspecifikus dinamika
Azt vizsgálja, hogy ha **ugyanaz az entitás** mindkét portáltípusnál megjelenik, akkor:
- ugyanazzal a hangulattal írnak-e róla,
- ugyanakkora vizuális hangsúlyt kap-e.

Ez már a **framing**, vagyis a **keretezés** kérdése: nem az a lényeg, hogy *megjelenik-e* a téma, hanem az, hogy *hogyan* jelenik meg.

---

## 🧠 Mit jelent itt pontosan a „napirend-kijelölés”?

A napirend-kijelölés nem azt jelenti, hogy a média megmondja, mit gondoljunk. Inkább azt, hogy:

> **megmondja, miről gondolkodjunk.**

Ha több portál ugyanazokat a szereplőket és ügyeket emeli ki ugyanabban az időben, akkor az olvasók figyelme is ugyanabba az irányba terelődik.

A H3 ezért két szintet különít el:

1. **Miről írnak?** → ezt a napi entitás-említések szinkronja méri.
2. **Hogyan írnak róla?** → ezt a szentiment és a vizuális hangsúly különbsége méri.

Ez nagyon jó kutatási logika, mert külön választja:
- a **tematikus koordinációt**
- és az **értelmezési / tálalási különbségeket**.

---

## 📥 Milyen adatokat használ a szkript?

A `h3_hypothesis.py` ugyanazokra az alapfájlokra épít, mint a H1 és H2:

- `headlineDefinitions_2026-04-19.parquet`
- `llmAnalysis_2026-04-19.parquet`
- `headlines_2026-04-19.parquet`

A legfontosabb mezők:

- **`entities`**: a headline-ban felismert entitások listája
- **`sentiment_score`**: az adott headline érzelmi tónusa 0 és 1 között
- **`score` / `mean_score`**: vizuális hangsúlyból számolt pontszám
- **`norm_score`**: portálon belül normalizált vizuális hangsúly
- **`date`**: a headline napja
- **`siteName`** és **`portal_type`**: melyik portálról és melyik portáltípusból származik a headline

---

## ⚙️ Adatelőkészítés lépésről lépésre

### 1. Vizuális score átlagolása headline-onként

Mivel ugyanaz a címsor több scrape-pillanatban is megjelenhetett, a szkript először `hashedId` alapján átlagolja a vizuális score-t.

Ez azt biztosítja, hogy:
- egy headline ne számítson többször csak azért, mert többször lett elmentve,
- minden címsorhoz egy stabilabb vizuális hangsúlyérték tartozzon.

### 2. Portálon belüli normalizálás

A H1-hez és H2-höz hasonlóan a vizuális hangsúly itt is **portálonként min-max normalizált**:

$$
\text{norm\_score} = \frac{\text{mean\_score} - \text{score\_min}}{\text{score\_max} - \text{score\_min}}
$$

Ez azért fontos, mert különböző portálok eltérő designnal dolgoznak. A kutatási kérdés itt sem az, hogy abszolút pixelben melyik volt nagyobb, hanem az, hogy:

> **az adott portál saját főoldali logikáján belül mennyire emelte ki a headline-t.**

### 3. Dátumképzés napi szinten

A `_creationTime` mezőből napi bontású dátum képződik. Ez azért kell, mert a H3 idősoros kérdés:

> egy adott napon mely entitásokat mennyit említenek a portálok?

### 4. Entitások „felrobbantása” sorokra

Az `entities` mező lista jellegű. Ha egy headline több szereplőt is említ, akkor a szkript ezt **explode** művelettel több sorra bontja.

Például ha egy headline egyszerre említi Orbán Viktort és Magyar Pétert, akkor abból két sor lesz:
- ugyanaz a headline-adat,
- de külön entitással.

Ez kulcsfontosságú, mert a H3 entitásalapú elemzés:
- nem pusztán headline-okat,
- hanem **headline × entitás előfordulásokat** elemez.

---

## 🏷️ Mely portálcsoportok szerepelnek?

A szkript két ismert blokkot használ:

### Kormányközeli
- Origo
- Magyar Nemzet
- PestiSracok
- Hirado.hu
- Ripost
- Metropol
- Mandiner

### Független
- Telex
- 444.hu
- HVG
- ATV
- Magyar Hang
- 24.hu
- Nepszava
- Valasz Online

A további elemzés mindenütt ezekre a csoportokra épül.

---

## 🔝 Miért kell top entitásokat választani?

A H3 célja az időbeli együttmozgás vizsgálata. Ehhez olyan entitások kellenek,
- amelyek elég gyakran fordulnak elő,
- több portálon megjelennek,
- és mindkét portáltípusban szerepelnek.

Ezért a szkript kiválasztja a **leggyakoribb entitásokat**, és csak azokat tartja meg, amelyek mindkét médiablokkban ténylegesen jelen vannak.

Ez módszertanilag jó döntés, mert ritka entitásoknál:
- túl sok lenne a nulla,
- instabillá válna a korreláció,
- és nehezebb lenne tartalmi következtetést levonni.

---

# (A) részhipotézis – Csoporton belüli napirend-szinkronitás

## 🎯 Mit kérdez ez a rész?

Azt, hogy:

> **a kormányközeli portálok napi entitás-említési mintázata jobban együtt mozog-e egymással, mint a független portáloké?**

Ha igen, az arra utalhat, hogy a kormányközeli portálok **koordináltabban** jelölik ki a napirendet.

---

## 📈 Először: napi entitás-idősorok

A szkript először elkészíti az egyes entitások napi említésszámát portálonként.

Példa:
- adott entitás: „Magyar Péter”
- adott nap: 2026-04-10
- adott portál: Telex
- érték: hány headline említette ezen a napon ezt az entitást

Ezután ezeket vonaldiagramokon ábrázolja külön:
- a kormányközeli portálokra,
- a független portálokra.

### Mit mutatnak ezek az ábrák?

Ha a csoporton belüli vonalak együtt mozognak, az arra utal, hogy a portálok hasonló ritmusban vesznek fel ugyanazokat a témákat.

Ha viszont széttartanak, az arra utal, hogy inkább saját, önálló napirendet követnek.

Ez még csak vizuális benyomás. A formális méréshez jön a Pearson-korreláció.

---

## 📐 A Pearson-korreláció részletes magyarázata

A H3 (A) részének központi statisztikai eszköze a **Pearson-féle korrelációs együttható**.

### Mit mér a Pearson r?

A Pearson r két folytonos változó **lineáris együttjárását** méri, és -1 és +1 közé esik:

- **r = +1** → tökéletes együttmozgás
- **r = 0** → nincs lineáris kapcsolat
- **r = -1** → tökéletes ellentétes mozgás

Ebben az elemzésben a két változó valójában két portál napi idősora. Például:
- az egyik sorozat: Origo napi entitás-említései
- a másik sorozat: Magyar Nemzet napi entitás-említései

Ha amikor az egyik portálnál sok az említés, a másiknál is sok, és amikor az egyiknél kevés, a másiknál is kevés, akkor **pozitív korreláció** lesz.

### A Pearson képlete

A klasszikus képlet:

$$
r = \frac{\sum (x_i - \bar x)(y_i - \bar y)}{\sqrt{\sum (x_i - \bar x)^2} \sqrt{\sum (y_i - \bar y)^2}}
$$

ahol:
- $x_i$ és $y_i$ a két portál adott napi értékei,
- $\bar x$ és $\bar y$ ezek átlaga.

### Intuíció

A Pearson azt nézi, hogy a két sorozat az átlagához képest **együtt tér-e ki**:
- ha mindkettő egyszerre megy az átlag fölé vagy alá, akkor pozitív r,
- ha ellenkező irányba térnek ki, akkor negatív r.

---

## 🧪 Rövid mini példa Pearson-korrelációra

Tegyük fel, hogy egy entitás napi említése így néz ki két portálon:

| Nap | Portál A | Portál B |
|---|---:|---:|
| Hétfő | 2 | 1 |
| Kedd | 5 | 4 |
| Szerda | 1 | 2 |
| Csütörtök | 6 | 5 |
| Péntek | 3 | 2 |

Itt jól látszik, hogy amikor az A portál többet ír az entitásról, a B is többet ír. A Pearson r itt magas, pozitív érték lenne.

Most nézzünk egy másik párt:

| Nap | Portál C | Portál D |
|---|---:|---:|
| Hétfő | 0 | 5 |
| Kedd | 5 | 0 |
| Szerda | 0 | 4 |
| Csütörtök | 4 | 0 |
| Péntek | 0 | 3 |

Itt amikor az egyik aktív, a másik inaktív. Ez alacsony vagy negatív korrelációhoz vezetne.

---

## ❓ Miért Pearson, és nem Spearman?

Mert itt a kutatási kérdés nem elsősorban a rangsorokra, hanem az **idősorok együttmozgására** vonatkozik. A Pearson érzékeny arra, hogy a napi csúcsok és visszaesések mennyire esnek egybe.

Másképp mondva:
- a Spearman inkább azt kérdezné, hogy a sorrendek hasonlóak-e,
- a Pearson azt kérdezi, hogy a napi intenzitásváltozások mennyire együtt mozognak.

Napirend-szinkronitás vizsgálatára ez jól indokolható választás.

---

## 🧱 Hogyan épül fel a korrelációs mátrix?

A szkript minden portálcsoportban:

1. összeadja portálonként és naponként a top entitások említéseit,
2. létrehoz egy széles táblát, ahol
   - sorok = napok,
   - oszlopok = portálok,
3. minden portálpárra kiszámítja a Pearson r-t.

Ennek eredménye egy **korrelációs mátrix**.

### Mi van a mátrixban?

Ha 7 kormányközeli portál van, akkor 7×7-es mátrix készül:
- átlóban mindig 1.00 van, mert egy portál önmagával tökéletesen korrelál,
- az átlón kívül minden cella két külön portál kapcsolatát mutatja.

A heatmap ezt teszi vizuálissá.

---

## 🌡️ A heatmap értelmezése

A heatmap színei azt mutatják, mekkora az r érték.

- **zöldebb** → magasabb pozitív korreláció
- **sárgás / semleges** → gyenge kapcsolat
- **pirosas** → negatív kapcsolat

Ha a kormányközeli heatmap „egyenletesebben zöld”, az azt jelenti, hogy a kormányközeli portálok jobban követik egymás napi entitás-ritmusát.

Ez lenne a H3(A) fő empirikus jele.

---

## 📏 Miért számol átlagos páronkénti korrelációt is?

A heatmap vizuálisan hasznos, de kell egy összegző szám is.

Ezért a szkript:
- csak az **átló feletti** portálpárokat veszi,
- kiszámítja ezek Pearson r értékeit,
- majd ezekből átlagot és szórást számol.

### Miért csak átló felett?

Mert:
- az átló önkorreláció, mindig 1 → ezt nem akarjuk beleszámolni,
- az alsó és felső háromszög egymás duplikátuma.

Így az átlag valóban az egyedi portálpárok átlagos szinkronját méri.

### Mit jelent az átlag és a szórás?

- **magasabb átlag r** → általában erősebb csoporton belüli szinkronitás
- **nagyobb szórás** → a csoporton belül nagyobb különbségek vannak; egyes párok nagyon együtt mozognak, mások kevésbé

---

## ⚠️ Fontos módszertani megjegyzés: nincs formális csoportközi próba

A szkript helyesen jelzi, hogy itt **nincs formális statisztikai teszt** arra, hogy a két csoport átlagos korrelációja közti különbség szignifikáns-e.

A döntés egy **heurisztikus küszöbre** épül:
- ha a kormányközeli átlagr legalább 0.05-tel magasabb, akkor az (A) támogatott.

Ez értelmes első közelítés, de nem teljes inferenciális teszt.

### Mi lenne a formálisabb megoldás?

Például:
- **bootstrap konfidenciaintervallum** az átlagos korrelációkülönbségre,
- **permutációs teszt**, amely véletlenszerű újracsoportosítással becsüli meg, mennyire különleges a megfigyelt Δr,
- vagy hálózati / idősoros modellek.

Ez nagyon fontos korlát, és jó, hogy a dokumentáció ezt expliciten jelzi.

---

# Entitásonkénti belső korreláció

## 🎯 Miért kell ez a plusz lépés?

Az összesített átlagos korreláció megmutatja, hogy **általában** mennyire szinkron a két médiablokk. De ebből még nem látszik, hogy:

> **mely entitások körül alakul ki a legerősebb koordináció.**

Lehet ugyanis, hogy a szinkronitás főleg néhány kiemelt politikus vagy téma köré koncentrálódik.

Ezért a szkript entitásonként is kiszámítja a csoporton belüli páronkénti korrelációt.

---

## 🧮 Hogyan történik ez?

Minden top entitásra külön:
1. létrejön a napi említésszám portálonként,
2. minden portálpárra kiszámítódik a Pearson r,
3. ezekből átlagos r és átlagos p-érték készül.

### Mit jelent itt a p-érték?

A `scipy.stats.pearsonr` nemcsak r-t, hanem p-értéket is ad. Ez azt teszteli, hogy a megfigyelt lineáris kapcsolat eltér-e nullától.

A nullhipotézis:

$$
H_0: \rho = 0
$$

vagyis a populációban nincs lineáris kapcsolat a két idősor között.

Kicsi p-érték esetén azt mondjuk, hogy a korreláció **statisztikailag szignifikáns**.

### Fontos óvatosság

A szkript itt több portálpár p-értékét **átlagolja** entitásonként. Ez praktikus összegző mutató, de klasszikus inferenciális értelemben nem a legtisztább megoldás, mert:
- a p-értékek átlaga nem standard meta-analitikus statisztika,
- a párok nem függetlenek,
- többes tesztelési kérdés is felmerül.

Ezért az itt kapott „átlag p-érték” inkább **heurisztikus megbízhatósági jelzés**, mint szigorú formális bizonyítás.

---

## 📍 Az entitásonkénti scatter plot értelmezése

A scatter ploton minden pont egy entitás.

- **x tengely**: átlag páronkénti Pearson r
- **y tengely**: átlag p-érték

### Hogyan olvassuk?

- **jobb alsó sarok** → magas korreláció, alacsony p → erős és megbízható szinkronitás
- **bal felső sarok** → gyenge korreláció, magas p → nincs koordinált együttmozgás

A színek segítenek:
- színes pont → p < 0.05
- szürke pont → nem szignifikáns

Ezzel a grafikon már nemcsak azt mondja meg, hogy „melyik csoport koordináltabb összességében”, hanem azt is, hogy **mely szereplők körül épül ki a koordináció**.

---

# (B) részhipotézis – Portálspecifikus dinamika

## 🎯 Mit kérdez ez a rész?

Az (A) rész a „mikor és miről írnak?” kérdésére válaszol. A (B) rész azt kérdezi:

> **ha ugyanaz az entitás megjelenik, ugyanúgy kezelik-e a két portáltípusban?**

Vagyis:
- ugyanazt az entitást pozitívabban vagy negatívabban írják-e le,
- ugyanakkora vizuális súlyt adnak-e neki.

Ez már nem agenda-szinkron, hanem **portálspecifikus keretezés**.

---

## 📊 Miért Mann–Whitney U-teszt?

Itt a H1-hez hasonlóan a szkript a **Mann–Whitney U-próbát** használja.

### Miért nem t-próbát?

Mert a vizsgált változók:
- `sentiment_score` (0 és 1 közé szorított),
- `norm_score` (0 és 1 közé normalizált),

nem biztos, hogy normális eloszlásúak. Lehetnek:
- ferdék,
- torlódók,
- szélsőértékesek,
- eltérő szórásúak.

A Mann–Whitney U ezért robusztusabb választás.

---

## 🧠 A Mann–Whitney U részletes logikája

A nullhipotézis az, hogy a két csoport eloszlása azonos. A próba nem az átlagokat teszteli közvetlenül, hanem a **rangsorokat**.

### A teszt menete

1. Összerakjuk a két csoport összes értékét.
2. Rangsoroljuk őket a legkisebbtől a legnagyobbig.
3. Megnézzük, hogy az egyik csoport értékei jellemzően előrébb vagy hátrébb helyezkednek-e el a rangsorban.
4. Ebből számoljuk az **U statisztikát**.

### Intuíció

Ha a kormányközeli portálok egy adott entitásnál következetesen pozitívabb szentiment-score-okat kapnak, akkor a rangsorban sok kormányközeli érték kerül a magasabb helyekre. Ez kis p-értékhez vezethet.

### Kétoldali teszt

A kódban `alternative="two-sided"` szerepel, tehát a kérdés nem az, hogy előre megadott irányban van-e különbség, hanem egyszerűen az:

> **van-e különbség a két portáltípus között?**

Ez konzervatívabb és módszertanilag tiszta döntés, ha nincs biztos irányhipotézis minden egyes entitásra.

---

## 🧪 Mini példa a Mann–Whitney-re H3 kontextusban

Tegyük fel, hogy egy entitás szentimentje így alakul:

- **Kormányközeli**: 0.70, 0.75, 0.80, 0.72
- **Független**: 0.35, 0.40, 0.45, 0.50

Ha a két csoportot egy közös rangsorba rakjuk, a kormányközeli értékek szinte mind a rangsor felső végébe kerülnek. Ez azt jelezné, hogy a kormányközeli portálok **pozitívabban** írnak az entitásról.

Ugyanez a logika működik a vizuális score-ra is:
- ha az egyik portáltípusnál az entitáshoz tartozó headline-ok rendre magasabb `norm_score`-t kapnak,
- akkor az arra utal, hogy ott vizuálisan is jobban kiemelik.

---

## 📋 A H3 dinamikatáblázat oszlopainak értelmezése

A `df_dynamics` tábla entitásonként mutatja:
- a két csoport mintanagyságát,
- a szentimentátlagokat,
- a vizuális átlagokat,
- a különbségeket,
- a p-értékeket,
- és hogy szignifikáns-e az eltérés.

### Kiemelten fontos oszlopok

#### `sent_diff = sent_gov_mean − sent_ind_mean`
- **pozitív** → a kormányközeli portálok pozitívabban írnak az entitásról
- **negatív** → a független portálok pozitívabbak

#### `vis_diff = vis_gov_mean − vis_ind_mean`
- **pozitív** → a kormányközeli portálok jobban kiemelik
- **negatív** → a függetlenek emelik ki jobban

#### `sent_p` és `vis_p`
Azt mutatják, hogy a különbség valószínűleg nem véletlen-e.

---

## 📉 A kétpaneles sávdiagram értelmezése

A vizualizáció két panelt mutat:

1. **Szentiment panel**
2. **Vizuális hangsúly panel**

Minden sor egy entitás, és egymás mellett látszik a két portáltípus átlaga.

A csillag (`★`) azt jelzi, ha az adott entitásnál a különbség szignifikáns.

Ez a grafikon különösen jó arra, hogy egyszerre lássuk:
- mely entitásokról írnak más hangnemben,
- és melyeket emelik ki másképp.

---

## ⚠️ Többszörös összehasonlítás problémája

A szkript nagyon korrekt módon ki is mondja, hogy itt körülbelül:
- 15 entitás × 2 dimenzió = ~30 teszt fut le.

Ha minden tesztnél `α = 0.05` küszöböt használunk korrekció nélkül, akkor:

> pusztán véletlenül is várható néhány hamis pozitív eredmény.

### Mit jelent ez gyakorlatban?

Ha például 30 független nullhipotézis mind igaz lenne, akkor átlagosan kb. 1.5 teszt lehetne „szignifikáns” pusztán véletlenből.

### Mi lenne a szigorúbb megoldás?

- **Bonferroni-korrekció**: nagyon konzervatív
- **FDR / Benjamini–Hochberg**: rugalmasabb és gyakran jobb ilyen soktesztes helyzetben

A jelenlegi megközelítés tehát **feltáró jellegű** elemzésként jól védhető, de az eredmények értelmezésénél óvatosságot igényel.

---

# 🧾 A H3 végső verdikt-logikája

A szkript a végén külön értékeli az (A) és (B) részt, majd ezekből képez összesített következtetést.

## (A) támogatott, ha

$$
\text{mean}_\text{gov}(r) > \text{mean}_\text{ind}(r) + 0.05
$$

Ez tehát **nem szignifikanciateszt**, hanem heurisztikus döntési szabály.

## (B) támogatott, ha

az entitások elég nagy részénél van szignifikáns eltérés:
- a szentimentben,
- vagy a vizuális hangsúlyban.

A küszöb a kódban:
- legalább 3 entitás,
- vagy az összes entitás kb. 30%-a.

Ez egy gyakorlati döntési szabály arra, hogy ne egy-egy véletlen eltérésből mondjunk ki általános mintázatot.

---

# 🧠 Mit mond a H3 emberi nyelven?

A H3 nemcsak azt kérdezi, hogy a médiablokkok másképp írnak-e ugyanarról, hanem ennél mélyebbre megy:

> **egyáltalán ugyanakkor kezdenek-e el írni ugyanazokról a szereplőkről, és ha igen, ugyanúgy tálalják-e őket?**

Ez két nagyon fontos médiaelméleti szintet kapcsol össze:

- **agenda-setting** → milyen témák kerülnek napirendre
- **framing** → milyen értelmezési keretben jelennek meg ezek a témák

Ha az (A) rész támogatott, az azt sugallja, hogy a kormányközeli portálok **koordináltabban mozognak a témafelvételben**.

Ha a (B) rész támogatott, az azt mutatja, hogy ugyanazon entitás esetén is **eltérő médiakeretezés** történik.

A kettő együtt különösen erős eredmény lenne, mert akkor nemcsak az látszana, hogy másképp írnak, hanem az is, hogy **szorosabban összehangolják, mikor mit emelnek napirendre**.

---

# ✅ Mit érdemes megjegyezni a H3-ból?

1. A H3 két külön mechanizmust vizsgál: **napirend-szinkronitást** és **keretezési különbséget**.
2. A napirend-szinkronitást napi entitás-említési idősorok **Pearson-korrelációjával** méri.
3. A Pearson r azt mutatja meg, hogy két portál napi említésmintái **mennyire mozognak együtt**.
4. A csoportszintű összehasonlítás itt **heurisztikus**, nem teljes formális statisztikai próba.
5. Az entitásonkénti különbségeket a szkript **Mann–Whitney U-teszttel** vizsgálja, mert a szentiment és vizuális score nem feltétlen normális eloszlású.
6. A H3 különösen értékes, mert összekapcsolja a **miről írnak** és a **hogyan írnak róla** kérdését.
7. A többszörös összehasonlítás miatt a (B) rész eredményeit **óvatosan** kell értelmezni, különösen korrekció hiányában.

---

## 🛑 Korlátok és helyes értelmezés

A H3 eredményeit csak a saját módszertani keretükön belül szabad olvasni.

### Amit a H3 jól meg tud mutatni
- vannak-e szinkron mintázatok a portálok napi entitáskezelésében,
- vannak-e portáltípus szerinti keretezési különbségek,
- mely entitások körül látható erősebb koordináció vagy megosztottság.

### Amit a H3 nem tud teljes bizonyossággal állítani
- hogy a szinkronitás biztosan tudatos központi koordinációból fakad,
- hogy az összes megfigyelt különbség oksági értelemben médiamanipuláció,
- hogy a korrelációkülönbség formálisan szignifikáns a két blokk között,
- hogy a sok entitásra futtatott tesztekből mindegyik robusztusan megállna többszörös korrekció után is.

A helyes, óvatos összegzés inkább ez:

> **a H3 elemzés azt vizsgálja, hogy a portálok mennyire mozognak együtt az entitások napirendre emelésében, és hogy ugyanazon entitásokat mennyire kezelik eltérően a két médiablokkban. A Pearson-korrelációs és Mann–Whitney-alapú eredmények együtt képet adnak a napirend-kijelölés és a keretezés szerkezetéről, de a következtetések egy része feltáró és heurisztikus jellegű.**

Ez így módszertanilag pontos és kutatásban is jól védhető megfogalmazás.

