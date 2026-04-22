# A `h1_hypothesis.py` laikusbarát összefoglalója

## Mit akar kideríteni ez az elemzés?

A `h1_hypothesis.py` azt vizsgálja, hogy a **kormányközeli** és a **független** hírportálok ugyanazokat a politikusokat **más hangnemben** és **más vizuális hangsúllyal** mutatják-e be.

A két vizsgált szereplő:
- **Magyar Péter**
- **Orbán Viktor**

A fő kérdés nagyon egyszerű:

> **Ugyanarról az emberről mást sugall-e a különböző médiavilág?**

Vagyis:
- az egyik portáltípus pozitívabban ír-e róla,
- a másik negatívabban,
- és közben nagyobb vagy kisebb figyelmet is ad-e neki.

Ez a hipotézis a **média-polarizációról** szól: arról, hogy a sajtó nemcsak mást emel ki, hanem **ugyanazt a szereplőt is eltérő keretben mutathatja meg**.

---

## Milyen adatból dolgozik a szkript?

A program itt is több adatforrást kapcsol össze ugyanahhoz a headline-hoz.

### 1. A headline szövege és alapadatai
Ez mondja meg, melyik címsorról és melyik portálról van szó.

### 2. A headline hangulata
Ezt egy mesterséges intelligencia becsli meg `sentiment_score` formában:
- **0-hoz közel** → negatívabb
- **1-hez közel** → pozitívabb

### 3. Kik szerepelnek a headline-ban?
Az LLM azt is megjelöli, hogy említi-e a cím például:
- Magyar Pétert
- Orbán Viktort

### 4. Mennyire volt vizuálisan kiemelve a headline?
A `score`, majd annak normalizált változata (`norm_score`) azt méri, hogy a cím mennyire volt hangsúlyos a főoldalon.

---

## Miért kell itt is normalizálni a vizuális score-t?

Mert a különböző portálok nagyon másképp néznek ki. Az egyik oldalon a fő hír óriási, a másikon visszafogottabb lehet a design.

Ezért a szkript itt sem nyers formában hasonlítja össze a vizuális score-t, hanem portálon belül 0 és 1 közé skálázza.

Így a kérdés ez lesz:

> **Az adott portál a saját rendszerén belül mennyire emelte ki ezt a politikusról szóló headline-t?**

---

## Hogyan készül az elemzés?

A program először kiválasztja azokat a headline-okat, amelyekben szerepel:
- **Magyar Péter**
- vagy **Orbán Viktor**

Ezután minden ilyen headline-hoz hozzárendeli:
- a portáltípust,
- a szentimentet,
- a vizuális hangsúlyt.

Így végül minden sorban nagyjából ez a logika van:

> ez a headline erről a politikusról szólt, ezen a portálon jelent meg, ilyen hangulatú volt, és ennyire volt kiemelve.

---

# Mit néz meg a szkript?

A H1 két külön dolgot vizsgál:

## 1. Hangnem
A két portáltípus **pozitívabban vagy negatívabban** ír-e ugyanarról a politikusról?

## 2. Vizuális hangsúly
A két portáltípus **nagyobb vagy kisebb figyelmet** ad-e ugyanannak a politikusnak?

Ez tehát nemcsak arról szól, hogy „mit mondanak”, hanem arról is, hogy:

> **mekkora reflektorfénybe teszik az adott szereplőt.**

---

# Mit mutatnak az ábrák laikus szemmel?

A szkript kétféle fő ábrát használ:
- **hegedűdiagramot**
- **oszlopdiagramot**

---

## 1. Hegedűdiagram – hogyan oszlanak el az értékek?

Ez az ábra azt mutatja, hogy a headline-ok értékei hogyan szóródnak a két portáltípusnál.

Két sor van:
- felül a **szentiment**
- alul a **vizuális prominencia**

Két oszlop van:
- Magyar Péter
- Orbán Viktor

### Hogyan kell ezt egyszerűen olvasni?

Ha az egyik oldal „hegedűje” magasabban van, akkor annál a csoportnál nagyobbak az értékek.

#### A szentimentnél ez azt jelenti:
- magasabb → pozitívabb hangnem
- alacsonyabb → negatívabb hangnem

#### A vizuális prominenciánál ez azt jelenti:
- magasabb → jobban kiemelt headline-ok
- alacsonyabb → kevésbé hangsúlyos headline-ok

### Mi a fő minta?
A szkript szöveges értelmezése szerint egy **tükörszerű mintázat** rajzolódik ki:

- **Magyar Pétert** a kormányközeli portálok inkább negatívabban,
  a függetlenek inkább pozitívabban mutatják be.
- **Orbán Viktort** a kormányközeliek inkább pozitívabban,
  a függetlenek inkább negatívabban mutatják be.

Ez nagyon tipikus polarizációs jelenség:

> minden médiablokk kedvezőbben mutatja a „saját oldalát”, és kedvezőtlenebben az ellenfelet.

---

## 2. Oszlopdiagram – gyors átlagos összehasonlítás

Ez az ábra egyszerűbb, mert nem az egész eloszlást mutatja, hanem csak az átlagokat.

Itt könnyebben látszik:
- melyik portáltípus ír pozitívabban egy politikusról,
- melyik portáltípus emeli ki jobban.

A `Δ` érték azt mutatja, mennyi a különbség a két oldal között.

### Mit érdemes nézni rajta?

- **Szentiment oszlopok** → ki beszél kedvezőbben vagy kedvezőtlenebbül
- **Prominencia oszlopok** → ki ad nagyobb láthatóságot

Ez az ábra tehát a „nagy kép” gyors változata.

---

# Miért használ a szkript statisztikai tesztet?

Mert pusztán ránézésre egy ábrára könnyű túl sokat belelátni.

A statisztikai teszt azt kérdezi:

> **Valódi különbséget látunk, vagy csak véletlen ingadozást?**

Ehhez a program **Mann–Whitney U tesztet** használ.

---

## Mi az a Mann–Whitney U teszt nagyon egyszerűen?

Ez egy olyan módszer, ami két csoportot hasonlít össze úgy, hogy nem feltételezi, hogy az adatok „szép haranggörbe” szerint oszlanak el.

Ez itt hasznos, mert a headline-ok:
- nagyon vegyesek,
- lehetnek szélsőségesek,
- és nem biztos, hogy szépen, szabályosan oszlanak el.

A teszt lényegében azt nézi:

> ha összekevernénk a két csoport headline-jait, akkor az egyik csoport értékei tényleg rendszeresen magasabbak/alacsonyabbak-e, mint a másiké?

---

## Mit tesztel pontosan a H1-ben?

Összesen **4 összehasonlítást**:

### Magyar Péter
1. szentiment: kormányközeli vs. független
2. vizuális prominencia: kormányközeli vs. független

### Orbán Viktor
3. szentiment: kormányközeli vs. független
4. vizuális prominencia: kormányközeli vs. független

Tehát minden politikusnál két dolgot kérdez:
- más a hangnem?
- más a kiemelés?

---

## Mit jelentenek a táblázat fő számai?

### `Gov átlag`
A kormányközeli portálok átlagos értéke.

### `Ind átlag`
A független portálok átlagos értéke.

### `Δ (Gov−Ind)`
A két csoport különbsége.

- pozitív → a kormányközeli oldalak átlaga magasabb
- negatív → a független oldalak átlaga magasabb

### `p-érték`
Azt mutatja, mennyire valószínű, hogy a látott különbség pusztán véletlen.

- **kicsi p-érték** → valószínűleg valódi különbség
- **nagy p-érték** → nem lehetünk biztosak benne

### `r (hatásméret)`
Ez azt mutatja meg, hogy a különbség mennyire nagy a gyakorlatban.

Mert nem ugyanaz, hogy:
- van egy nagyon pici, de kimutatható különbség,
- vagy van egy igazán látványos eltérés.

---

# Mit jelent a H1 eredménye emberi nyelven?

Ha a szentiment-különbségek szignifikánsak, az azt jelenti:

> a két médiablokk **nem ugyanabban a hangnemben** beszél ugyanarról a politikusról.

Ha a prominencia-különbségek is szignifikánsak, az azt jelenti:

> nemcsak mást mondanak róla, hanem **más erősséggel tolják az olvasó elé**.

Ez együtt már sokkal erősebb állítás, mint önmagában bármelyik:
- nemcsak a tartalom más,
- hanem a figyelem szerkezete is más.

---

# Mi a szkript végső logikája?

A fájl a végén megnézi, hogy a 4 tesztből hány lett szignifikáns.

- **3 vagy 4 szignifikáns teszt** → H1 megerősítve
- **1 vagy 2** → részben megerősítve
- **0** → nem megerősítve

Ez azért jó, mert a végső következtetés nem egyetlen összehasonlításon múlik.

---

# Egyszerű hétköznapi példa

Képzeld el, hogy két sportújság ír ugyanarról a focistáról.

### Az egyik újság
- „Briliáns teljesítmény”
- nagy fotóval, fő helyen

### A másik újság
- „Újabb vitatott szereplés”
- kisebb helyen, oldalt

Mindkettő ugyanarról az emberről szól.
De:
- az egyik pozitív keretben mutatja,
- a másik negatív keretben,
- és még a láthatóság is eltér.

Pontosan ezt próbálja számszerűsíteni a H1.

---

# Mi a fő tanulság?

A `h1_hypothesis.py` nem azt kérdezi, hogy „hazudik-e” valamelyik portál.
Hanem ezt:

> **ugyanazt a politikai szereplőt az eltérő médiaterek következetesen másképp mutatják-e be?**

A szkript logikája szerint a válasz erre az, hogy:
- igen, a hangnem eltér,
- és a vizuális kiemelés is eltérhet,
- ez pedig a polarizált médiarendszer egyik legerősebb jele.

---

# Egy mondatban a lényeg

A `h1_hypothesis.py` azt vizsgálja, hogy a kormányközeli és a független hírportálok **ugyanazokat a politikusokat más hangnemben és más vizuális hangsúllyal mutatják-e be**, és ezt ábrákkal, leíró statisztikákkal és Mann–Whitney U tesztekkel ellenőrzi.

---
---


# A `h2_hypothesis.py` laikusbarát összefoglalója

## Mit akar kideríteni ez az elemzés?

Ez a rész azt vizsgálja, hogy a magyar hírportálok **a negatív hangulatú híreket jobban kiemelik-e**, mint a semleges vagy pozitív híreket.

Egyszerűen fogalmazva:

> **A rossz hírek nagyobb betűvel, feltűnőbb helyen jelennek meg?**

Például:
- egy drámai, félelmet keltő vagy dühös cím
- kap-e nagyobb helyet a főoldalon,
- mint egy nyugodt, tényszerű vagy pozitív hír?

Ez azért fontos, mert az emberek figyelmét nemcsak a cím tartalma irányítja, hanem az is, hogy **mekkora helyet kap**, **hol van az oldalon**, és **mennyire ugrik a szemünkbe**.

---

## Milyen adatból dolgozik a szkript?

A program minden headline-ról két fontos dolgot tud:

### 1. Milyen a hangulata?
Ezt egy mesterséges intelligencia becsli meg egy `sentiment_score` nevű számmal.

- **0-hoz közel** → inkább negatív
- **1-hez közel** → inkább pozitív
- a kettő között → inkább semleges

### 2. Mennyire volt kiemelve a főoldalon?
Ezt egy vizuális pontszám írja le. Ez abból jön, hogy:
- mekkora a headline,
- hol van az oldalon,
- mennyire hangsúlyos az elhelyezése.

Mivel minden portál máshogy néz ki, a program ezt **portálon belül átskálázza** 0 és 1 közé. Így nem azt nézi, hogy „ugyanakkora volt-e pixelekben”, hanem azt, hogy:

> **az adott portál saját rendszerén belül mennyire volt kiemelt ez a hír?**

---

## Hogyan halad az elemzés?

A szkript háromféleképpen nézi meg ugyanazt a kérdést.

---

# 1. Első kérdés: együtt jár-e a negatív hangulat és a kiemelés?

Itt a program azt nézi meg, hogy általánosságban:

> ha egy cím negatívabb, akkor általában jobban ki van-e emelve?

Ehhez egy olyan statisztikai módszert használ, ami azt vizsgálja, hogy két dolog **együtt mozog-e**.

### Mit mutatott?
Az eredmény szerint:
- van kapcsolat a negatívabb hangnem és a nagyobb vizuális kiemelés között,
- de ez a kapcsolat **nem nagyon erős**, inkább csak **enyhe tendencia**.

Ez magyarul azt jelenti:

> nem minden negatív hír lesz automatikusan kiemelt,  
> de átlagosan mégis látszik, hogy a negatívabb címek valamivel nagyobb hangsúlyt kapnak.

---

# 2. Második kérdés: tényleg jobban kiemeltek-e a negatív hírek?

Itt a szkript már nem folytonos skálán dolgozik, hanem három csoportot csinál:

- **negatív**
- **semleges**
- **pozitív**

Ezután azt hasonlítja össze, hogy ezek közül melyik csoport headline-jai kapnak nagyobb vizuális hangsúlyt.

A legfontosabb összevetés:

> **negatív vs. semleges**

mert a hipotézis lényege az, hogy a negatív hírek jobban kiemeltek.

### Ez mit ad hozzá?
Ez a lépés emberibben érthetővé teszi az eredményt.

Nem azt kérdezi, hogy „van-e monoton kapcsolat”, hanem ezt:

> **ha fogok egy rakás negatív és egy rakás semleges címet, a negatívak tipikusan előrébb vannak-e?**

Ha igen, az már sokkal kézzelfoghatóbb állítás.

---

# 3. Harmadik kérdés: akkor is látszik ez, ha a portáltípust is figyelembe vesszük?

Ez a legfontosabb rész.

A program ugyanis nemcsak azt akarja tudni, hogy van-e kapcsolat a negatív hangnem és a kiemelés között, hanem azt is, hogy:

1. ez a kapcsolat akkor is megmarad-e, ha külön kezeljük a portáltípust,
2. ugyanolyan erős-e a **kormányközeli** és a **független** portálokon.

Ehhez használja a **regressziós modellt**.

---

# Mi az a regressziós modell nagyon egyszerűen?

A regresszió egy olyan statisztikai eszköz, ami azt próbálja megbecsülni:

> **átlagosan hogyan változik egy dolog, ha változik egy másik dolog.**

Itt ez azt jelenti:

> hogyan változik a headline vizuális kiemelése attól függően, hogy mennyire negatív vagy pozitív a címe?

És közben ezt is figyeli:

> melyik portáltípusról van szó?

---

## Egyszerű hétköznapi hasonlat

Képzeld el, hogy azt akarjuk megérteni, mitől függ egy növény magassága.

Nézzük:
- mennyi vizet kapott,
- napos vagy árnyékos helyen nőtt-e.

Ha csak a vízmennyiséget nézzük, könnyen félreérthetünk valamit, mert lehet, hogy a napfény is számít.

A regresszió azért jó, mert egyszerre tudja nézni:
- a víz hatását,
- a napfény hatását,
- és azt is, hogy a víz hatása más-e napos és árnyékos helyen.

A headline-os példában:
- a „víz” = szentiment
- a „napos/árnyékos hely” = portáltípus
- a „növény magassága” = vizuális kiemelés

---

# Mit néz pontosan a modell?

A modell négy fontos számot becsül. Ezeket együtthatóknak hívjuk.

## 1. Alapszint
Ez azt mutatja meg, hogy egy kiinduló helyzetben mekkora kiemelés várható.

## 2. A szentiment hatása
Ez mondja meg, hogy ha a headline pozitívabbá válik, akkor a kiemelés nő vagy csökken.

- Ha ez a szám **negatív**, akkor a pozitívabb címek kevésbé hangsúlyosak.
- Ez egyben azt jelenti, hogy a **negatívabb címek nagyobb hangsúlyt kapnak**.

## 3. A portáltípus hatása
Ez azt mutatja meg, hogy az egyik portáltípus eleve másképp emel-e ki híreket, mint a másik.

## 4. Az interakció
Ez a legérdekesebb rész. Azt mondja meg, hogy:

> **a negatív hangnem ugyanannyira számít-e a két portáltípusnál, vagy nem?**

Másképp fogalmazva:
- lehet, hogy mindkét oldaltípus kiemeli a negatív híreket,
- de az egyik sokkal erősebben teszi ezt, mint a másik.

Pont ezt mutatja meg az interakció.

---

# Rövid, teljesen egyszerű fake data példa

Tegyük fel, hogy csak ennyi headline-unk van:

### Független portál
- nagyon negatív cím → nagyon kiemelt
- kicsit negatív cím → eléggé kiemelt
- inkább pozitív cím → kevésbé kiemelt
- nagyon pozitív cím → alig kiemelt

### Kormányközeli portál
- nagyon negatív cím → kiemelt
- kicsit negatív cím → közepesen kiemelt
- inkább pozitív cím → kicsit kevésbé kiemelt
- nagyon pozitív cím → szintén kevésbé kiemelt

### Ebből mit látunk?
Mindkét helyen igaz, hogy a negatívabb címek jobban látszanak.

De a **független portálon erősebb ez a lejtés**:
- ott nagyobb a különbség a negatív és pozitív címek között,
- míg a kormányközelinél laposabb a különbség.

A regresszió ezt így fordítja le számokra:
- van egy általános negatív kapcsolat,
- és meg tudja mondani, hogy ez a kapcsolat az egyik csoportban erősebb-e.

---

# Miért jó ez a módszer?

Mert nem csak azt mondja, hogy:

> „úgy tűnik, a negatív hírek kiemeltebbek”

hanem ezt is:

- mennyire igaz ez,
- mennyire biztos ez statisztikailag,
- mindkét portáltípusnál igaz-e,
- és ugyanolyan erősen igaz-e.

---

# Mit jelent az eredmény a gyakorlatban?

Ha a modell azt mutatja, hogy a negatívabb headline-ok nagyobb hangsúlyt kapnak, akkor az arra utal, hogy:

> a főoldali figyelem nem véletlenszerűen oszlik el,  
> hanem a negatív tartalmak felé billen.

Ez nem feltétlenül bizonyít tudatos manipulációt. Lehet olyan ártatlanabb magyarázat is, hogy:
- a negatív hírek gyakran valóban fontosabbak,
- sürgősebbek,
- vagy jobban megfelelnek a breaking news logikának.

De ettől még az eredmény fontos, mert megmutatja:

> **a médiafigyelem szerkezete nem semleges.**

---

# Mi a szkript végső logikája?

A program nem egyetlen szám alapján dönt, hanem három bizonyítékot rak egymás mellé:

1. Általánosságban együtt jár-e a negatív hangnem és a kiemelés?
2. A negatív headline-ok ténylegesen jobban kiemeltek-e, mint a semlegesek vagy pozitívak?
3. Ez a kapcsolat akkor is megmarad-e, ha a portáltípust is beleszámoljuk?

Ha ezek többsége ugyanabba az irányba mutat, akkor a H2 erős támogatást kap.

---

# Egy mondatban a lényeg

A `h2_hypothesis.py` azt vizsgálja, hogy a hírportálok **a negatívabb hangulatú címeket jobban kiemelik-e a főoldalon**, és ezt többféle statisztikai módszerrel ellenőrzi — köztük egy regressziós modellel, amely azt is megmutatja, hogy ez a minta eltér-e a kormányközeli és a független portálok között.

---

