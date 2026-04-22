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
---

# A `h3_hypothesis.py` laikusbarát összefoglalója

## Mit akar kideríteni ez az elemzés?

A `h3_hypothesis.py` azt vizsgálja, hogy a hírportálok **együtt mozognak-e abban, hogy miről írnak**, és hogy **ugyanazokat a témákat ugyanúgy tálalják-e**.

Ez már nemcsak arról szól, hogy egy portál pozitívabban vagy negatívabban ír valakiről, hanem arról is, hogy:

> **ha az egyik portál elkezd sokat írni valakiről vagy valamiről, a többi is ugyanakkor kezd-e el vele foglalkozni?**

Ez az úgynevezett **napirend-kijelölés** kérdése.

Egyszerűbben:
- a média eldönti, miről beszélünk,
- és azt is, hogy hogyan beszélünk róla.

A H3 ezt a két dolgot külön vizsgálja.

---

## A H3 két fő kérdése

### 1. Együtt mozognak-e a portálok?
Ez azt nézi, hogy a portálok ugyanazokat az embereket vagy témákat **ugyanabban az időben** kezdik-e emlegetni.

### 2. Ha ugyanaz a téma megjelenik, ugyanúgy tálalják-e?
Ez azt nézi, hogy ugyanarról az entitásról:
- ugyanolyan pozitívan vagy negatívan írnak-e,
- és ugyanolyan erősen kiemelik-e a főoldalon.

Vagyis a H3 egyszerre vizsgálja:
- **miről írnak**
- és **hogyan írnak róla**

---

## Milyen adatból dolgozik a szkript?

A program minden headline-ról több fontos dolgot tud:

- **melyik portálon jelent meg**
- **melyik napon jelent meg**
- **milyen entitásokat említ** (pl. egy politikust, szervezetet vagy témát)
- **milyen a headline hangulata** (`sentiment_score`)
- **mennyire volt kiemelve** a főoldalon (`norm_score`)

A `norm_score` itt is portálon belül normalizált érték, tehát azt mutatja, hogy:

> **az adott portál a saját rendszerén belül mennyire emelte ki ezt a címet**

---

## Mi történik az entitásokkal?

Ha egy headline több szereplőt is említ, a program szétbontja őket külön sorokra.

Például ha egy címben egyszerre szerepel:
- Orbán Viktor
- Magyar Péter

akkor abból két elemzési sor lesz.

Ez azért fontos, mert a H3 nem csak headline-okat néz, hanem azt, hogy:

> **egy adott személy vagy téma milyen gyakran jelenik meg a különböző portálokon és napokon.**

---

# 1. rész: együtt mozognak-e a portálok?

Ez a H3 első nagy kérdése.

A program megnézi, hogy a legfontosabb entitásokból melyek jelennek meg a leggyakrabban, majd minden portálra elkészíti a napi említésszámukat.

Ez úgy néz ki, mintha minden portálnak lenne egy naptára, és minden nap mellé odaírnánk:

- ma hányszor írta le ezt a nevet,
- hol ugrott meg a figyelem,
- mikor tűnt el a témák közül.

### Mit keres itt az elemzés?

Azt, hogy a portálok görbéi mennyire hasonlítanak egymásra.

Ha például:
- hétfőn minden kormányközeli portál sokat ír ugyanarról az emberről,
- kedden mindenhol visszaesik,
- szerdán megint megugrik,

akkor ez arra utal, hogy **együtt mozognak**.

Ha viszont mindenki más napokon kapja fel ugyanazt a témát, akkor kevésbé szinkron a működés.

---

## Milyen statisztikai módszerrel nézi ezt a szkript?

Itt a program a **Pearson-korrelációt** használja.

### Nagyon egyszerűen mi ez?
A Pearson-korreláció azt mutatja meg, hogy két idősor mennyire mozog együtt.

- **magas pozitív érték** → a két portál ritmusa hasonló
- **0 körüli érték** → nincs igazi együttmozgás
- **negatív érték** → inkább ellentétesen mozognak

### Hétköznapi példa
Képzeld el, hogy két ember naponta felírja, mennyit beszél egy adott témáról.

Ha az egyik sokat beszél róla pont akkor, amikor a másik is, és mindketten egyszerre hallgatnak el róla, akkor erős az együttmozgás.

Pontosan ezt nézi a Pearson itt a portálok között.

---

## Hogyan jelenik ez meg az ábrákon?

### Idősorábrák
A szkript külön ábrákat rajzol a kormányközeli és a független portálokról.

Ezeken minden vonal egy portál.

Ha a vonalak hasonlóan hullámoznak, akkor a portálok hasonló ritmusban emelnek napirendre ugyanazokat az entitásokat.

### Heatmap
A program ezután készít egy olyan táblázatszerű színes ábrát is, ahol minden cella két portál kapcsolatát mutatja.

- zöldebb szín → erősebb együttmozgás
- semlegesebb szín → gyengébb kapcsolat
- pirosasabb szín → ellenkező mozgás

Ez segít gyorsan meglátni, hogy egy médiablokkon belül mennyire „együtt lélegeznek” a portálok.

---

## Mit akar ebből bizonyítani a H3?

A H3 első része azt feltételezi, hogy:

> **a kormányközeli portálok jobban szinkronban vannak egymással, mint a függetlenek**

Ha ez igaz, az arra utalhat, hogy a kormányközeli médiában erősebb az összehangolt napirendképzés.

Fontos viszont, hogy a kód maga is jelzi:

> ez itt inkább erős leíró összehasonlítás, mint teljesen formális bizonyítás.

Vagyis a program megnézi, melyik csoport átlagos korrelációja magasabb, de nem futtat külön nagyon szigorú statisztikai próbát arra, hogy ez a különbség biztosan szignifikáns-e.

Ez fontos módszertani óvatosság.

---

# 2. rész: ha ugyanaz a téma megjelenik, ugyanúgy kezelik-e?

Ez a H3 második nagy kérdése.

A program megnézi a legfontosabb entitásokat, és mindegyiknél összehasonlítja:

- milyen a szentiment a kormányközeli portálokon,
- milyen a szentiment a független portálokon,
- mekkora a vizuális hangsúly az egyik oldalon,
- mekkora a másikon.

Itt tehát már nem az a kérdés, hogy ugyanakkor kezdtek-e el írni róla, hanem az, hogy:

> **ha már írnak róla, ugyanabban a stílusban és ugyanakkora erővel teszik-e?**

---

## Milyen statisztikai módszerrel vizsgálja ezt?

Itt a szkript a **Mann–Whitney U tesztet** használja.

### Nagyon egyszerűen mit csinál ez?
Ez a teszt két csoportot hasonlít össze úgy, hogy nem feltételezi, hogy az adatok szépen, szabályosan oszlanak el.

Ez azért jó, mert:
- a szentiment-score nem biztos, hogy normális eloszlású,
- a vizuális score sem feltétlen „szép” eloszlású,
- lehetnek szélsőséges headline-ok.

A teszt lényegében azt kérdezi:

> **az egyik csoport értékei rendszeresen magasabbak vagy alacsonyabbak-e, mint a másiké?**

---

## Egyszerű példa erre

Tegyük fel, hogy egy politikusról a kormányközeli portálok ilyen szentiment-értékeket kapnak:
- 0.70
- 0.75
- 0.80

A függetlenek pedig ilyeneket:
- 0.40
- 0.45
- 0.50

Itt szemre is látszik, hogy a kormányközeli portálok pozitívabban írnak róla.

A Mann–Whitney ezt fordítja le egy formális kérdésre:

> ez az eltérés elég következetes ahhoz, hogy ne csak a véletlen műve legyen?

Ugyanez a logika működik a vizuális hangsúlyra is.

---

## Mit mutat a H3 táblázata?

A táblázat minden entitásra külön megmutatja:

- hány említés volt a kormányközeli oldalon,
- hány a függetlenen,
- melyik oldalon pozitívabb a szentiment,
- melyik oldalon nagyobb a vizuális hangsúly,
- és hogy ezek a különbségek szignifikánsak-e.

### Hogyan kell olvasni?

#### `sent_diff`
- pozitív → a kormányközeli portálok pozitívabban írnak az entitásról
- negatív → a független portálok pozitívabbak

#### `vis_diff`
- pozitív → a kormányközeli portálok jobban kiemelik
- negatív → a függetlenek emelik ki jobban

#### `sent_sig` és `vis_sig`
Ezek azt jelzik, hogy a különbség statisztikailag elég erős-e.

---

## Mit mutat a kétpaneles ábra?

A szkript készít egy ábrát, ahol:
- az egyik oldalon a szentiment-különbségek látszanak,
- a másik oldalon a vizuális hangsúly különbségei.

Minden entitásnál egymás mellett látszik:
- a kormányközeli átlag,
- a független átlag.

A csillag (`★`) azt jelzi, hogy az eltérés szignifikáns.

Ez egy gyors áttekintést ad arról, hogy:
- mely témák vagy szereplők körül a legnagyobb a médiakülönbség,
- és hogy ez inkább a hangnemben, inkább a kiemelésben, vagy mindkettőben jelenik meg.

---

# Mi a H3 fő üzenete egyszerűen?

A H3 lényegében két dolgot kérdez egyszerre:

## 1. Együtt választják-e ki a témákat?
Vagyis a portálok hasonló időben kezdenek-e el ugyanazokról a szereplőkről írni.

## 2. Ugyanúgy csomagolják-e őket?
Vagyis ha már ugyanarról írnak, ugyanolyan hangnemben és ugyanolyan feltűnően teszik-e.

Ez azért fontos, mert a média hatása nemcsak abból áll, hogy mit mond, hanem abból is, hogy:
- **mit tesz napirendre**
- és **milyen keretben mutatja meg**

---

# Mire kell figyelni az eredmények értelmezésénél?

A szkript maga is óvatos, és ez helyes.

## 1. Az együttmozgás nem bizonyít automatikusan központi irányítást
Ha két portál hasonlóan mozog, az jelenthet koordinációt, de jelentheti azt is, hogy:
- ugyanazokra a nagy hírekre reagálnak,
- ugyanaz az országos esemény mindenhol felkapott lett,
- egyszerűen hasonló hírszerkesztési logikát követnek.

Tehát az együttmozgás **gyanús lehet**, de önmagában nem végső bizonyíték.

## 2. Sok külön teszt fut le
A H3 sok entitásra külön-külön tesztel szentimentet és vizuális hangsúlyt. Ilyenkor mindig fennáll az esély, hogy néhány eredmény pusztán véletlenül tűnik szignifikánsnak.

Ezért a H3 eredményeit érdemes úgy olvasni, mint:

> **erős feltáró mintázatokat**, nem feltétlen végső, lezárt bizonyításokat.

---

# Egyszerű hétköznapi hasonlat

Képzeld el, hogy több rádióadó működik egyszerre.

A H3 két dolgot néz:

### 1. Ugyanazokat a dalokat játsszák-e ugyanabban az időben?
Ez a napirend-szinkronitás része.

### 2. Ha ugyanaz a dal szól, ugyanúgy konferálják-e fel?
- az egyik lelkesebben,
- a másik hűvösebben,
- az egyik fő műsoridőben,
- a másik háttérben.

Ez a framing, vagyis a keretezés része.

Pontosan ezt próbálja meg a H3 a hírek világában számszerűsíteni.

---

# Mi a szkript végső logikája?

A program a végén külön értékeli:

- sikerült-e azt kimutatni, hogy a kormányközeli portálok jobban együtt mozognak,
- és sikerült-e azt kimutatni, hogy ugyanazokat az entitásokat eltérően kezelik.

Ezután ezekből áll össze az összesített H3-verdikt.

Így a következtetés nem egyetlen számra épül, hanem két külön bizonyítékvonalra.

---

# Egy mondatban a lényeg

A `h3_hypothesis.py` azt vizsgálja, hogy a hírportálok **mennyire mozognak együtt abban, hogy kiről és miről írnak**, és hogy **ugyanazokat az entitásokat mennyire eltérő hangnemben és vizuális hangsúllyal mutatják be**, ehhez Pearson-korrelációt és Mann–Whitney U teszteket használ.