A formula **azt modellezi, hogy a látogatók hogyan dolgozzák fel vizuálisan egy weboldal (pl. hírportál) címlapját**, és ez alapján minden cikkhez egy "figyelemfelkeltési" (vagy hierarchia) pontszámot rendel.

Lényegében négy fő szempontot mérlegel a figyelem kiszámításához:

1. **Betűméret és Kiterjedés (Plusz pontok):** A nagyobb betűvel írt és nagyobb képernyőterületet elfoglaló blokkok automatikusan vonzzák a szemet, így ezek kapják a legtöbb pontot.
2. **Függőleges pozíció (Y büntetés):** Minél lejjebb kell görgetni egy cikkhez az oldalon, annál kevesebb figyelmet kap.
3. **Természetes olvasási minta (X büntetés):** Mivel az emberek (nyugaton) balról jobbra és fentről lefelé, úgynevezett "F-alakban" pásztázzák a képernyőt, a balra zárt tartalmak előnyt élveznek a jobb oldaliakkal szemben.
4. **Banner vakság (Jobb felső büntetés):** Külön, súlyosan lepontozza a jobb felső zónát, mert a netezők ösztönösen átugorják ezt a részt, mivel hagyományosan itt jelennek meg a reklámok.

Végeredményben a képlet egy weboldal elrendezésének fizikai jellemzőit (koordináták és pixelek) fordítja le a **felhasználói figyelem matematikai rangsorává**.

Hogy azokat az oldalakat is megfelelően kezeljük, ahol a jobb felső sarok erősen büntetve van (gyakran a "banner vakság" miatt, amikor a felhasználók tudat alatt figyelmen kívül hagyják ezt a területet, feltételezve, hogy ott reklámok vannak), beépítettünk egy kölcsönhatási tényezőt (interaction term) a képletbe.

A teljes képlet, amely már tartalmazza a Jobb Felső Csillapítási Zóna (Top-Right Zone Decay) számítást is:

$$
\text{Score} = (W_f \cdot f) + (W_a \cdot w \cdot h) - (W_y \cdot y) - (W_x \cdot x) - P_{tr}
$$

Az új Jobb Felső Büntetés/Csillapítási Zóna ($P_{tr}$):

$$
P_{tr} = W_{tr} \cdot x \cdot \max\left(0, 1 - \frac{y}{Y_{zone}}\right)
$$

- $f$ (Betűméret): A figyelemfelkeltés legdominánsabb tényezője. A nagyobb betűméret magasabb pontszámot eredményez.
- $w \cdot h$ (Terület = Szélesség $\times$ Magasság): A cikk határoló doboza által elfoglalt teljes képernyőterület.
- $y$ (Y-koordináta): Távolság az oldal tetejétől. (Büntetés: minél lejjebb van, annál több pontot veszít).
- $x$ (X-koordináta): Távolság az oldal bal szélétől. (Büntetés: minél jobbra van, annál több pontot veszít, az F-alakú olvasási minta miatt).
- $W_f, W_a, W_y, W_x$: Hangoló súlyok (szorzók) az egyes tulajdonságok fontosságának egyensúlyozásához.
- $P_{tr}$ (Jobb Felső Büntetés): A cikk pontszámából levont extra büntetés.
- $W_{tr}$ (Jobb Felső Súly): Egy szorzó, amely meghatározza, mennyire legyen agresszív ez a specifikus sarokbüntetés.
- $Y_{zone}$ (Felső Zóna Küszöbérték): A függőleges határvonal (képpontban), amely meghatározza, mi számít az oldal "tetejének" (pl. 600).
- $\max(0, ...)$: Egy korlátozó függvény, amely biztosítja, hogy a büntetés soha ne váljon bónusszá. Ha a matematikai művelet eredménye nulla alá esik, a büntetés egyszerűen nulla marad.

Az $1 - \frac{y}{Y_{zone}}$ algebrai kifejezés használatával egy "elhalványuló" (fade-out) hatást hozunk létre a büntetésre vonatkozóan, ahogy a felhasználó lejjebb görget az oldalon. Nem büntethetjük egyszerűen a magas $x$ koordinátát (a jobb oldalt), mert azzal igazságtalanul lepontoznánk a jobb alsó cikkeket is. A büntetésnek csak a jobb felső sarokban kell erősnek lennie.

1. Forgatókönyv: Egy cikk a legeslegjobb felső sarokban ($x=1000, y=0$)
   Ha az $Y_{zone}$ értékét 600-ra állítjuk be, a kifejezés eredménye $1 - \frac{0}{600} = 1$. A képlet a sarokbüntetés 100%-át alkalmazza ($W_{tr} \cdot 1000 \cdot 1$). A cikk pontszáma súlyosan lecsökken a banner vakság miatt.
2. Forgatókönyv: Egy cikk a jobb középső részen ($x=1000, y=300$)
   A kifejezés eredménye $1 - \frac{300}{600} = 0.5$. A képlet a büntetés 50%-át alkalmazza. Még mindig kap büntetést, mert a veszélyzónában van, de kevesebbet, mivel lejjebb helyezkedik el.
3. Forgatókönyv: Egy cikk a jobb alsó részen ($x=1000, y=800$)
   A kifejezés eredménye $1 - \frac{800}{600} = -0.33$. Mivel a számítást a $\max(0, ...)$ függvénybe csomagoltuk, a negatív érték nullára vált, így a büntetés teljesen nullázódik. A cikk biztonságosan kívül esik a jobb felső "vakfolton", és csak a normál szabályok szerint kap pontot.
4.  Egy cikk a bal felső sarokban ($x=0, y=0$)
   Mivel az $x$ értéke $0$, a $W_{tr} \cdot 0$ szorzó az egész számítást semmissé teszi. A bal oldali cikkek teljesen immunisak erre a specifikus büntetésre, tökéletesen megőrizve a természetes, balról jobbra tartó (F-alakú) olvasási hierarchiát.
