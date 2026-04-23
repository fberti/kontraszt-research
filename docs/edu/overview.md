# Kontraszt Research – tanulási térkép és útmutató

Ez a dokumentum nem a teljes módszertani leírás akar lenni, hanem egy **tanulási térkép**: segít gyorsan megérteni,

- miről szól a projekt,
- milyen kérdéseket tesz fel,
- milyen adatokból dolgozik,
- és milyen sorrendben érdemes tovább olvasni.

Ha a részletes statisztikai és elemzési háttér érdekel, menj tovább ide: [`docs/edu/methodology.md`](./methodology.md).

---

## 1. Miről szól ez a kutatás?

A projekt azt vizsgálja, hogy a magyar online hírportálok **nemcsak miről írnak**, hanem azt is, hogy **hogyan adják el ugyanazt a valóságot**.

A fókusz három dolgon van:

1. **Hangnem** – pozitívabb vagy negatívabb-e a cím?
2. **Vizuális hangsúly** – mennyire van előtérbe tolva a headline a főoldalon?
3. **Napirend** – ugyanazokat a szereplőket és témákat kapják-e fel egyszerre a portálok?

A kutatás nem az olvasók fejébe lát bele. Nem azt méri, hogy ki mire kattintott, hanem azt, hogy a szerkesztőségek **mit próbálnak láthatóvá és fontossá tenni**.

> Röviden: a figyelemgazdaság kínálati oldalát nézzük.

---

## 2. Miért érdekes ez?

Mert a média hatása sokszor nem ott kezdődik, hogy valami igaz vagy hamis, hanem ott, hogy:

- mi kerül a címlap tetejére,
- mi kap nagyobb betűt,
- mi jelenik meg sürgető, drámai vagy pozitív hangnemben,
- és mi marad oldalt vagy lent.

Ez a projekt azt próbálja számszerűsíteni, hogy a főoldali szerkesztésben megjelenik-e:

- **politikai polarizáció**,
- **negativitási torzítás**,
- **napirend-szinkron**.

---

## 3. A három fő hipotézis

### H1 – Polarizáció
A kormányközeli és a független portálok **eltérő hangnemben** és **eltérő vizuális súllyal** mutatják be ugyanazokat a politikai szereplőket.

**Egyszerűen:** ugyanarról a politikusról mást sugall-e a két médiablokk?

---

### H2 – Negativitás és kiemelés
A negatív érzelmi töltetű headline-ok **nagyobb vizuális hangsúlyt** kapnak, mint a semleges vagy pozitív headline-ok.

**Egyszerűen:** a rossz híreket jobban az arcunkba tolják?

---

### H3 – Napirendkijelölés és framing
A portálok között lehet időbeli együttmozgás abban, hogy **kiről és miről írnak**, de közben ugyanazokat a témákat eltérő hangnemben és eltérő hangsúllyal tálalhatják.

**Egyszerűen:** nemcsak az számít, hogy miről van szó, hanem az is, hogy ki mikor és milyen keretben hozza be.

---

## 4. Milyen adatfolyamból áll össze az elemzés?

A projekt nagyjából ezen a pipeline-on megy végig:

```text
Hírportálok főoldalának scrape-elése
→ headline-ok és vizuális pozíciók kinyerése
→ LLM-es annotáció (szentiment, entitások)
→ headline-szintű score-ok összerakása
→ portálon belüli normalizálás
→ H1 / H2 / H3 elemzés
```

### A fő adatforrások
- headline-szövegek és alapmetaadatok
- LLM által becsült szentiment
- LLM által felismert entitások
- vizuális score a főoldali elhelyezkedés alapján

---

## 5. Kulcsfogalmak röviden

### Headline
A főoldalon megjelenő címsor vagy szalagcím.

### Szentiment
A headline érzelmi tónusa. A projektben ez egy skálázott becslés: a negatívabb cím alacsonyabb, a pozitívabb magasabb értéket kap.

### Entitás
Valamilyen szereplő vagy név, amit a headline megemlít, például egy politikus, intézmény vagy szervezet.

### Vizuális score
Egy pontszám, ami azt próbálja megragadni, mennyire feltűnő a headline. Tipikusan beleszámít:
- betűméret,
- terület,
- függőleges pozíció,
- vízszintes pozíció,
- egyes zónák extra büntetése vagy jutalma.

### Normalizált score
Mivel minden portál máshogy néz ki, a nyers vizuális score-t portálon belül skálázzuk. Így azt tudjuk összehasonlítani, hogy **egy portál saját logikáján belül** mennyire emel ki valamit.

### Portáltípus
A projekt két nagy csoporttal dolgozik:
- **kormányközeli**
- **független**

---

## 6. Hogyan érdemes ezt a projektet megtanulni?

### Ajánlott olvasási sorrend kezdőknek

1. **Ez a fájl** – hogy lásd a nagy képet
2. [`docs/edu/methodology.md`](./methodology.md) – hogy lásd, hogyan lesz a kutatási kérdésből mérhető modell
3. `docs/score_formula.md` – ha érdekel, hogyan készül a vizuális score
4. `docs/simple_overview.md` – ha gyors, hipotézisenkénti összefoglalót szeretnél
5. `docs/overview.md` – ha a hosszabb háttérmagyarázat is kell

### Ajánlott olvasási sorrend haladóknak

1. `docs/research_plan.md`
2. `docs/edu/methodology.md`
3. `docs/ols_regression.md`
4. az egyes hipotéziseket implementáló szkriptek

---

## 7. A három hipotézis tanulási szemmel

### H1-et akkor érted jól, ha látod:
- hogyan lesz egy headline-ból szentiment,
- hogyan lesz ugyanabból vizuális hangsúly,
- és hogyan hasonlítunk össze két portálcsoportot ugyanarra a szereplőre.

**Kulcskérdés:** ugyanazt a politikust ugyanúgy látjuk-e mindenhol?

---

### H2-t akkor érted jól, ha látod:
- hogyan lesz a negatív / semleges / pozitív kategória,
- hogyan mérjük a kiemelést,
- és hogyan ellenőrizzük több módszerrel ugyanazt a mintázatot.

**Kulcskérdés:** a negatív címek tényleg kiemeltebbek-e?

---

### H3-at akkor érted jól, ha látod:
- hogyan készül napi entitás-idősor,
- mit jelent a portálok közti korreláció,
- és hogyan válik külön a „miről írnak?” és a „hogyan írnak róla?” kérdés.

**Kulcskérdés:** együtt mozognak-e a portálok, és ha igen, ugyanúgy kereteznek-e?

---

## 8. Mit kell fejben tartani olvasás közben?

### 1. Ez nem közvetlen olvasói viselkedésmérés
Nem kattintást, nem olvasási időt és nem memóriát mérünk, hanem szerkesztői kiemelést.

### 2. A score relatív
A normalizált vizuális score nem abszolút „figyelemmérő”, hanem portálon belüli relatív hangsúlymutató.

### 3. A szentiment becslés
A szentiment LLM-alapú annotációból jön, tehát hasznos, de nem tévedhetetlen.

### 4. A statisztikai kapcsolat nem automatikusan ok-okozat
Ha a negatív headline-ok kiemeltebbek, az még nem bizonyítja önmagában a tudatos manipulációt.

---

## 9. Mit tanulhatsz ebből a projektből?

Ez a kutatás jó belépő több témába is:

- médiakutatás
- agenda-setting
- framing
- figyelemgazdaság
- alkalmazott szentimentelemzés
- vizuális prominencia modellezése
- alap társadalomtudományi statisztika

Ha oktatási anyagként használod, akkor ezeket a kérdéseket érdemes végigvenni:

1. Mit tekintünk itt „befolyásolásnak”?
2. Miért kell portálon belül normalizálni a score-t?
3. Miért nem elég egyetlen statisztikai teszt?
4. Miért fontos külön kezelni a témaválasztást és a keretezést?
5. Mitől lenne erősebb egy oksági állítás?

---

## 10. Továbbvezető kérdések

Ha tovább akarod gondolni a projektet, innen érdemes indulni:

- Mi történne, ha több időszakot hasonlítanánk össze, nem csak kampányidőt?
- Mi történne, ha nemcsak headline-okat, hanem leadet vagy teljes cikkeket is elemeznénk?
- Mennyire stabil a portálbesorolás?
- Mennyit számítana emberi annotációval ellenőrizni az LLM-becsléseket?
- Lehetne-e kattintási vagy engagement-adatokkal összekötni a headline-szintű mutatókat?

---

## 11. Egy mondatban a dokumentum lényege

Ez a projekt azt vizsgálja, hogy a magyar online hírportálok **milyen hangnemben, mekkora vizuális hangsúllyal és milyen időbeli mintázatban** tesznek láthatóvá politikai szereplőket és témákat.

---

## 12. Merre tovább?

Ha most már megvan a nagy kép, a következő állomás ez:

➡️ [`docs/edu/methodology.md`](./methodology.md)

Ott részletesebben végigmegyünk ezen:
- hogyan készül az elemzési tábla,
- milyen statisztikai logika van a három hipotézis mögött,
- és mit jelentenek a főbb módszerek mini példákon, fake adatokkal, kötetlenebb nyelven.
