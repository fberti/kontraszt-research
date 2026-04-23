Az **OLS (Ordinary Least Squares)** regresszió interakcióval egy olyan statisztikai modell, amely feltételezi, hogy egy magyarázó változó ($X_1$) hatása a függő változóra ($Y$) nem állandó, hanem függ egy másik magyarázó változó ($X_2$) értékétől.

Egyszerűbben fogalmazva: az interakció azt jelenti, hogy **"attól függ"**. Például a műtrágya hatása a terméshozamra *attól függ*, hogy mennyi öntözővizet kap a növény. Ha nincs víz, a műtrágya mit sem ér.

---

## 1. A matematikai modell

Míg egy sima additív modell így néz ki:
$$Y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \varepsilon$$

Az **interakciós modell** kiegészül egy szorzattal:
$$Y = \beta_0 + \beta_1 X_1 + \beta_2 X_2 + \beta_3 (X_1 \cdot X_2) + \varepsilon$$

### Mit jelentenek az együtthatók?
* $\beta_0$: Konstans (tengelymetszet).
* $\beta_1$: $X_1$ hatása, amikor $X_2 = 0$.
* $\beta_2$: $X_2$ hatása, amikor $X_1 = 0$.
* **$\beta_3$**: Az interakciós tag. Ez mutatja meg, mennyivel változik meg $X_1$ meredeksége, ha $X_2$ egy egységgel nő.



---

## 2. Példa "fake" adatokkal

Tegyük fel, hogy azt vizsgáljuk, hogyan alakul a **havi fizetés** ($Y$, ezer Ft) a **munkatapasztalat** ($X_1$, évek száma) és a **diploma megléte** ($X_2$, dummy változó: 0 = nincs, 1 = van) függvényében.

### A modellünk becsült egyenlete:
$$\text{Fizetés} = 300 + 20 \cdot \text{Tapasztalat} + 50 \cdot \text{Diploma} + 15 \cdot (\text{Tapasztalat} \cdot \text{Diploma})$$

### Értelmezés:

1.  **Akinek nincs diplomája ($X_2 = 0$):**
    A modell leegyszerűsödik: $\text{Fizetés} = 300 + 20 \cdot \text{Tapasztalat}$.
    * Kezdőbér: 300e Ft.
    * Minden év tapasztalat **20e Ft** emelést jelent.

2.  **Akinek van diplomája ($X_2 = 1$):**
    Behelyettesítjük az 1-est: $\text{Fizetés} = 300 + 20 \cdot \text{Tapasztalat} + 50(1) + 15 \cdot \text{Tapasztalat}(1)$.
    Összevonva: $\text{Fizetés} = 350 + 35 \cdot \text{Tapasztalat}$.
    * Kezdőbér: 350e Ft.
    * Minden év tapasztalat **35e Ft** emelést jelent.

---

## 3. Mi a tanulság?

Ebben a példában az interakció ($\beta_3 = 15$) azt mutatja meg, hogy a diploma nemcsak egy egyszeri fizetésemelést ad (a $+50$ a konstanshoz képest), hanem **felgyorsítja a bérnövekedést is**. 

* **Interakció nélkül:** A két csoport (diplomás vs. nem diplomás) bérnövekedési vonala párhuzamos lenne.
* **Interakcióval:** A két vonal távolodik egymástól, mert a diplomásoknál a tapasztalat "többet ér" a munkaerőpiacon.

> **Fontos:** Ha az interakciós tag ($\beta_3$) p-értéke nem szignifikáns (nagyobb, mint 0,05), akkor statisztikailag nem bizonyítható, hogy a két változó között van ilyen típusú összefüggés, és érdemes visszatérni az egyszerűbb, additív modellhez.