Oshi
====

[JMDICT](http://www.edrdg.org/jmdict/j_jmdict.html) files are the property of
the [Electronic Dictionary Research and Development
Group](http://www.edrdg.org), and are used in conformance with the Group's
[licence](http://www.edrdg.org/edrdg/licence.html).

# Uživatelská dokumentace

Program Oshi je slovník a analyzátor gramatiky pro japonštinu.

Pro spuštění je potřeba Python >=3.6 a balík lxml dostupný z PyPI.

Po spuštění si může uživatel vybrat mezi několika módy - vyhledávání ve slovníku
(search), zjištění gramatického tvaru výrazu (grammar) a zkoušecí mód (test). V
kterémkoli módu stačí pro návrat do menu zadat písmeno `e` (exit) nebo `q`
(quit).

## Search
Při vyhledávacím módu může uživatel zadat japonský výraz nebo jeho význam.
Program vypíše všechny nalezené výrazy se stránkováním po deseti záznamech.
Výrazy jsou vypisované v pořadí nálezu, ne relevance.

## Grammar
Uživatel zadá vyskloňovaný japonský výraz a program rekurzivně zjistí jeho
gramatickou formu. Program nezjistí, zda je zadaný výraz validní gramatický
tvar. Je proto teoreticky možné zadat uměle zkonstruovaný tvar, který se v
japonštině nevyskytuje a získat od programu zdánlivě korektní analýzu.

## Test
Testovací mód používá soubor `learn.txt` s jedním výrazem na každé řádce.
Program náhodně vybere jeden výraz, zobrazí ho a pak čeká na stisknutí klávesy
enter. Uživatel si vybaví význam výrazu a stiskne enter. Uživateli je zobrazen
záznam z databáze a poté zadá, zdali význam znal, nebo ne (y/n). Pokud ho znal,
je odebrán ze zkoušených výrazů. Poté zkoušení pokračuje, dokud není seznam
prázdný.

# Technická dokumentace
Součástí programu Oshi je soubor JMdict_e.gz, což je komprimovaný XML soubor
obsahující japonské výrazy, jejich gramatické role a významy. Při prvním
spuštění program tento soubor zpracuje (vybere pouze užitečná data) a uloží ve
formátu JSON do souboru `oshi_database.json` (pokud tento soubor ještě
neexistuje). Tento soubor je při každém dalším spuštění použit jako zdroj dat.

Po spuštění programu je do paměti načtena databáze ve vedlejším vlákně (zatímco
se čeká na vstup od uživatele v menu). Po zvolení uživatelského módu se počká na
případné ukončení vlákna.

## JMdict
Soubor [JMdict](https://www.edrdg.org/jmdict/j_jmdict.html) od skupiny EDRDG
obsahuje data japonsko-anglického slovníku ve formátu XML s kódováním UTF-8.

Ve stromě níže je znázorněna struktura jednoho záznamu z JMdict (zkrácena pouze
na XML tagy, které používá program Oshi).

- tag `<entry>` (*záznam*)
  - tag `<r_ele>` (*reading element*) (1 a více)
    - tag `<reb>` (právě 1)
  - tag `<k_ele>` (*kanji element*) (0 a více)
    - tag `<keb>` (právě 1)
  - tag `<sense>` (*význam*) (1 a více)
    - tag `<pos>` (*part of speech*) (0 a více - pokud 0, platí `pos` z
      předchozího `sense`)
    - tag `<gloss>` (*překlad*) (1 a více)

Příklad elementu `entry` pro sloveso "psát" (pouze elementy zájmu):
```xml
<entry>
<k_ele>
    <keb>書く</keb>
</k_ele>
<r_ele>
    <reb>かく</reb>
</r_ele>
<sense>
    <pos>&v5k;</pos>
    <pos>&vt;</pos>
    <gloss>to write</gloss>
    <gloss>to compose</gloss>
    <gloss>to pen</gloss>
</sense>
<sense>
    <gloss>to draw</gloss>
    <gloss>to paint</gloss>
</sense>
</entry>
```

- element `k_ele` obsahuje zápis pomocí
  [kanji](https://cs.wikipedia.org/wiki/Kand%C5%BEi)
- element `r_ele` obsahuje fonetický zápis pomocí
  [kany](https://cs.wikipedia.org/wiki/Kana_(p%C3%ADsmo))
- element `pos` je *part of speech* (ve zdrojovém kódu spíše označován jako
  *tag*, kvůli zobecnění), neboli informace o gramatické roli významu. Tato
  informace je zapsána pomocí XML entity, např. `&v5k;`. Tyto entity jsou
  definovány na začátku XML souboru, např. `v5k` znamená *Godan verb with `ku'
  ending*.

## Databáze ve formátu JSON
Po zpracování vypadá struktura jednoho záznamu v JSON následovně
- `writings` (pole textových řetězců)
- `readings` (pole textových řetězců)
- `senses` (pole objektů)
  - `glosses` (pole textových řetězců)
  - `tags` (pole textových řetězců)

Vyhledání v databázi obstarávají funkce `database.Database.search(term)` a
`database.Database.find_exact(term)`.

`search(term)` postupně vrátí každý záznam v databázi, který v nějaké položce
obsahuje `term`. Složitost je tedy `O(nm)`, kde `n` je počet položek v databázi
(konstantní) a `m` je délka slova.

`find_exact(term)` hledá `term` v položce `writings` a `readings` (tak, že se
rovnají) a vrací pouze první nález. Složitost je tedy `O(n)`.

## Moduly programu
Soubor `__main__.py` obsahuje funkce `menu_search()`, `menu_grammar()` a
`menu_test()`, které obstarávají jednotlivé uživatelské módy.

`database.py` je modul, který se stará o načítání a práci s databází. Funkce
`database.connect()` vrátí instanci třídy `Database`. Třída `Database` disponuje
funkcemi `search(term)` a `find_exact(term)` popsanými výše. Funkce
`database.build()` načte a přestaví XML soubor JMdict na soubor JSON, který
uloží. Funkce `entry_tostring(entry)` vrátí textovou reprezentaci jednoho
slovníkového záznamu.

`grammar.py` je modul pro práci s gramatikou - načítaní a reprezentace
gramatických pravidel (funkce `parse_rules` a třída `Rule`), analýza
gramatického tvaru (funkce `lookup`), a aplikovaní určitého pravidla na výraz
(funkce `apply_rule_forward(expression, rule)`)

## Gramatika

### Gramatická pravidla
Soubor `grammar.rules` obsahuje japonská gramatická pravidla ve zvláštním
formátu. Autor tohoto formátu a souboru je [Tomash
Brechko](https://github.com/kroki/). Formát je popsán autorem v komentáři v
hlavičce souboru. Pro příklad je uvedeno jedno z jednodušších pravidel:

`negative 〜アない for plain 〜ウ v5[^r]* v5r vs-c`

Toto pravidlo říká, že zápor (negative) z infinitivu (plain) godan sloves
(`v5[^r]* v5r`) a su-sloves (`vs-c`) se vytvoří odebráním ウ-zvuku (např. く) a
přidáním odpovídajícího ア-zvuku (pro く je to か) a přidáním přípony ない.

Tedy například z infinitivu godan slovesa "psát" 書く je výsledný zápor 書かない.

Gramatické role (pos/tag) jsou zadány ve formátu
[glob](https://cs.wikipedia.org/wiki/%C5%BDol%C3%ADkov%C3%BD_znak) a v Pythonu
je lze jednoduše použít pomocí funkce `fnmatch(text, glob) -> bool` z balíku
`fnmatch` (filename match).

Pro načtení těchto pravidel byl použit regex
```regex
^(\S+)\s*(\S*)\s+〜(\S*)\s*(\S*)\s+for\s+(\S*)\s+〜(\S*) +((?:[ \t]*\S+)+)\s*$
```
Význam jednotlivých zachytávacích skupin:
```
RULE [ROLE] 〜PATTERN [POS] for TARGET 〜TARGET_PATTERN POS_GLOBS
```
Výsledkem je instance třídy `grammar.Rule`.

### Rekurzivní analýza gramatického tvaru
Analýza probíhá ve funkci `grammar.lookup(rules, expression, db, tags, role,
path, verbous)`. Role jednotlivých parametrů jsou popsány v dokumentaci ve
zdrojovém kódu.

Vyhledávání začíná tak, že jsou nalezena všechna zpětně aplikovatelná gramatická
pravidla, která jsou aplikována a výsledek je znovu rekurzivně prozkoumán.
Rekurze končí v bodě, kdy je analyzovaný výraz nalezen v databázi. Jedná se o
prohledávání do hloubky s udržováním prošlé cesty, která je při prvním nalezení
řešení vrácena.

Složitost algoritmu nezáleží na délce vstupního výrazu (záleží zanedbatelně),
ale na velikosti prohledávané databáze a počtu gramatických pravidel, což jsou
konstantní hodnoty. Pro představu si je však označme jako proměnné - velikost
databáze `n`, počet pravidel `m`. V každé větvi může být každé pravidlo použito
jenom jednou, ale v různém pořadí (v programu ale ve skutečnosti dochází k
ořezávání omezením na "aplikovatelná pravidla"). Složitost je tedy `O(n*m!)`.

# Testovací příklady
## search
```
vstup: ありえない
výstup:
あり得ないほど あり得ない程 有り得ない程
ありえないほど
n: unbelievable (extent)

あり得ない 有り得ない 有得ない
ありえない
adj-i: impossible, unlikely, improbable

まずあり得ない
まずありえない
exp: very improbable, vanishingly unlikely, only with a miracle
```
```
vstup: 無理
výstup:
無理
むり ムリ
adj-na n: unreasonable, unnatural, unjustifiable
adj-na n: impossible
adj-na: forcible, forced, compulsory
adj-na: excessive (work, etc.), immoderate
vs: to work too hard, to try too hard
int: no way, not a chance, never, dream on
adj-no: irrational

... (zkráceno)

無理往生 無理圧状
むりおうじょう
n adj-na: forced compliance, coercion, compulsion

Next page? (y/n)
```

## grammar lookup

Vyskloňované sloveso
```
vstup: 書いてた
výstup:
書いてた is past for 書いてる
  書いてる is colloquial for 書いている
    書いている is continuous for 書いて
      書いて is て-form for 書いた
        書いた is past for 書く
Dictionary entry for: 書く v5k
書く
かく
v5k vt: to write, to compose, to pen
v5k vt: to draw, to paint
```
Vyskloňované přídavné jméno
```
vstup: 良くなかった
výstup:
良くなかった is past for 良くない
  良くない is negative for 良い
Dictionary entry for: 良い adj-i
良い 善い 好い 佳い 吉い 宜い
よい えい
adj-i: good, excellent, fine, nice, pleasant, agreeable
adj-i: sufficient, enough, ready, prepared
```
Neskloňované přídavné jméno (infinitiv)
```
vstup: 好き
výstup:
Dictionary entry for 好き
好き
すき
adj-na n: liked, well-liked, favourite, favorite
adj-na n: in love (with), loved, romantically interested (in)
n adj-na: faddism, eccentricity
n adj-na: the way one likes, (as) it suits one
n: refined taste, elegant pursuits
```