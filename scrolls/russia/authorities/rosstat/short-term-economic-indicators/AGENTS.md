# AGENTS.md

## Scope

These instructions apply to the recurring Rosstat XLSX publication series "Краткосрочные экономические показатели Российской Федерации" stored in this directory.

The native workbook is the primary source. Preserve every admitted monthly XLSX unchanged. This file defines how an agent should read, extract, compare, and cite observations from the workbooks without silently flattening source semantics.

The July 2026 workbook (2026-07.xlsx) was used as the reference issue for the detailed structural guardrails below. Exact sheet counts, merge counts, formulas, hidden columns, classifications, and layouts may change in later or earlier issues; treat them as observed evidence about that issue, not as a permanent workbook schema.

## Source-faithful rule

Use the repository epistemic chain:

source -> representation -> observation -> derivation/bridge -> analytical claim

For this series:

- the XLSX workbook is the source artifact;
- worksheet layout, cell text, number formats, merged regions, hidden columns, formulas, footnotes, and notes are part of the source representation;
- an extracted statistical value becomes an observation only after its indicator, period, perimeter, unit, status, methodology/classification context, and provenance are resolved;
- any normalization, reclassification, rescaling, aggregation, growth calculation, seasonal adjustment, stitching of breaks, or cross-version reconciliation is a derivation/bridge and must not be silently inserted into the source layer;
- a reproducible transformation proves provenance, not economic equivalence.

Never silently correct Rosstat wording, spelling, punctuation, strange spacing, decimal representation, labels, source values, or methodological notes.

## Publication and file contract

- Keep the native workbook in XLSX format.
- Name a monthly issue by its reference period as YYYY-MM.xlsx.
- Do not convert the workbook into a replacement normalized CSV/XLSX and treat that as the source.
- Derived tabular representations may be created only as separate, traceable artifacts when the repository contract explicitly requires them.
- Preserve the original worksheet name in provenance. Do not assume that a visually identical trimmed name is the actual XLSX sheet identifier.
- Do not infer publication frequency, reference period, or observation period solely from the filename. Resolve period semantics from the worksheet itself.

## Reference workbook structure

The July 2026 issue contains 43 worksheets:

- 3 service sheets: "Титульный", "Содержание", "The Contens";
- 40 data sheets covering sections 1.1 through 4.8, with several historical/versioned sheets such as "1.2 (1999-2013)", "1.2 (2014-2026)", and multiple 4.6 classification blocks.

The workbook is not one rectangular dataset. A worksheet may contain:

- several statistical constructs;
- Russian and English parallel labels;
- multiple period conventions;
- nested categories;
- historical and current methodologies;
- source notes;
- preliminary/revised status markers;
- different perimeters;
- multiple units;
- multiple classification vintages.

Do not derive an observation key from worksheet number alone.

## Critical workbook hazards

### Merged cells

Merged cells are structural, not decorative noise.

The July 2026 issue contains 10,513 merge ranges. Sheet "1.5 " alone contains 9,221 merge ranges. Some merge ranges extend to the final Excel column XFD, including ranges such as XFA753:XFD753; sheet "4.6 (2010-2012)" contains A24:XFD24.

Therefore:

- never infer the logical data width from the maximum merged range;
- never infer the used data region from formatting or merge extent alone;
- determine the semantic table region from populated cells, headers, row labels, period labels, and source structure;
- preserve merge context when it carries a shared heading, unit, category, or note.

### Exact worksheet names

Several worksheet names in the XLSX contain trailing spaces, for example "1.1 ", "1.5 ", "2.2 ", "2.3 ", and others.

Therefore:

- preserve the exact source worksheet name in provenance;
- a trimmed alias may be used only as a convenience identifier;
- do not use trimming as an irreversible normalization step.

### Russian/English paired rows

Many labels appear as a Russian row followed by an English translation row.

The translation is not a separate statistical observation or separate construct.

When extracting:

- prefer the Russian source label as the canonical source-facing label for this Russian series;
- retain the English source text when useful for traceability;
- do not double-count Russian and English rows as two indicators;
- do not assume that the English translation is semantically more precise than the Russian original.

### Footnotes embedded inside cells

Footnote markers are frequently embedded directly in the same cell as:

- an indicator label;
- a year;
- a category;
- a numeric value.

They are often represented as rich-text superscript runs rather than separate cells.

In the July 2026 issue:

- 438 shared-string entries contain superscript formatting;
- those rich-text strings are used in 622 cells;
- 487 cell uses look like numeric/year values with an attached footnote marker.

Examples include forms such as "20262)", "157 0014)", "128,81)", "96,91)", and "7,75)".

Therefore:

- do not strip a trailing 1), 2), etc. without preserving a footnote reference;
- parse the numeric component and the footnote reference separately only in a derived representation;
- retain the literal source cell text or enough provenance to reconstruct it;
- do not treat footnote-bearing numeric cells as missing merely because Excel stores them as strings.

### Numeric cells versus text cells

A single statistical series may mix:

- genuine numeric Excel cells;
- text cells containing a number plus a footnote;
- text cells using decimal commas and spaces;
- numeric XML values using binary floating-point representation.

For example, the internal XML can contain values such as 9.700000000000001 while the workbook displays 9,7.

Therefore distinguish at least:

- source cell representation;
- displayed value;
- parsed numeric value, if one is created;
- footnote reference;
- number format / display precision where relevant.

Do not expose binary floating-point artifacts as if they were the published value.

### Hidden columns

Hidden does not mean absent, invalid, or disposable.

The July 2026 workbook contains hidden columns on sheets including "2.2 ", "2.3 ", and "4.6 (2013-2025)". In "4.6 (2013-2025)", hidden columns contain real quarterly / half-year / January-September observations.

Therefore:

- inspect hidden columns;
- never import only visible cells;
- preserve a hidden/visible presentation flag separately if useful;
- do not interpret hidden as missing, suppressed, or not applicable.

### Formulas

Most observations are stored as reported literals, but the July 2026 workbook also contains formula cells. On "2.4 ", for example:

- G213 = G183/F183*100;
- G363 = G333/F333*100.

Therefore distinguish:

- reported literal;
- source-workbook formula;
- cached formula result;
- Tabularium-derived result.

A formula that exists inside the official source workbook is still source-authored representation, but it is not the same thing as a literal reported cell.

### Notes are ordinary cells, not Excel comments

The July 2026 issue contains no Excel comment objects. Methodological notes and footnotes are written as ordinary worksheet cells below or around the tables.

Therefore:

- do not rely on a comments API to find source notes;
- scan note blocks and footnote rows as part of the table structure;
- preserve the relationship between a marker and its explanatory note.

### Embedded line breaks

The July 2026 issue uses source strings containing line breaks in more than one hundred cell occurrences, including period labels and notes.

A line break inside a cell is not a record separator.

### Missing and special-value states

Source cells may use:

- blank cells;
- …;
- … plus a footnote marker;
- -;
- other textual markers.

Preserve the literal source state.

Never map any of these automatically to zero. Do not collapse:

blank != … != - != zero != not applicable != suppressed != unavailable

If a semantic state cannot be established from the source, keep it unknown rather than guessing.

## Period semantics

Do not reduce all columns to a generic date.

The workbook can use:

- single month;
- cumulative period from the beginning of the year;
- quarter;
- half-year;
- January-September;
- year;
- point in time at the beginning of a period;
- point in time at the end of a month/period;
- average over a period;
- comparison index relative to another period.

Examples:

- budget tables can use "Янв.", "Янв-фев.", "I квартал", "Янв-апр." as cumulative intervals;
- other sheets use January, February, etc. as discrete monthly observations;
- bank-related stock values can be stated "на начало периода";
- debt values can be stated "на конец месяца";
- producer prices can be stated "на конец периода".

Preserve the source period boundary and basis. Do not infer cumulative versus discrete semantics from the month name alone.

Growth/index columns such as month-on-month, year-on-year, percentage-of-total, or percentage-to-previous-period are presentation/measure dimensions. Do not multiply the indicator dictionary merely because one construct is shown under several comparison bases.

## Construct boundaries

The same or similar label does not prove semantic identity.

Always keep distinct when the source changes:

- methodology;
- classification;
- age perimeter;
- geographic perimeter;
- institutional perimeter;
- period basis;
- unit;
- price basis;
- nominal/real concept;
- reported/estimated/preliminary/revised status.

Do not stitch series across breaks unless an explicit reproducible bridge is created outside the source layer.

### Industrial production break

Sheets "1.2 (1999-2013)" and "1.2 (2014-2026)" are deliberately separated.

Historical industrial classifications and the later OKVED2 structure are not automatically one homogeneous series. In particular, the earlier combined activity "производство и распределение электроэнергии, газа и воды" is not identical to the later separate constructs for electricity/gas/steam and water/waste activities.

### Income-distribution classification break

The 4.6 distribution tables use different income-band classifications over time.

Observed source blocks include:

- "4.6 (2007-2009)";
- "4.6 (2010-2012)";
- "4.6 (2013-2025)";
- "4.6 (2025-2026)".

The cutoffs differ between blocks. The year 2025 appears in two source classification schemes.

Therefore:

- an income band is part of the observation key;
- classification version is part of the observation key;
- never deduplicate 2025 observations by indicator + year alone;
- never remap old bands to new bands without an explicit bridge.

### Labour-market age perimeter

The workbook distinguishes labour-market constructs for "15-72 лет" and "15 лет и старше".

These are distinct observation perimeters.

### Poverty construct break

The workbook contains both:

- "население с денежными доходами ниже величины прожиточного минимума";
- "население с денежными доходами ниже границы бедности".

Do not treat these as a harmless label rename.

### Geography and revision notes

Footnotes can change geographic perimeter or comparability, including Crimea/Sevastopol-related coverage, revised population bases, and other source-defined changes.

Geographic or revision information carried only in a note is still part of observation provenance.

## Status and revision semantics

Footnotes and notes may identify:

- первая оценка;
- вторая оценка;
- последующие оценки;
- предварительные данные;
- оперативная оценка;
- уточненные / пересмотренные данные;
- временно не публикуемую информацию.

Preserve these statuses explicitly where they can be resolved.

A value with a revision/status note is not semantically identical to the same numeric value without that status.

Do not infer final merely because no preliminary marker is visible.

## Recommended observation provenance

For every extracted observation, preserve enough information to resolve it back to the workbook.

Recommended fields:

- source_file — e.g. 2026-07.xlsx;
- source_sheet_exact — exact XLSX worksheet name;
- source_cell or source range;
- source_label_literal;
- construct;
- category / subcategory;
- classification_version where relevant;
- period_label_literal;
- period_start and period_end only when they can be established without reinterpretation;
- period_basis — month, cumulative YTD, quarter, half-year, year, point-in-time, average, etc.;
- reference_basis for index/comparison measures where applicable;
- perimeter;
- geography;
- unit;
- value_literal;
- value_numeric only if parsed losslessly and separately;
- value_representation — numeric cell, text number, formula result, special marker, etc.;
- formula_literal where present;
- footnote_refs;
- status;
- methodology_note_refs;
- visibility if a hidden-column distinction is material;
- extraction version/method if a machine representation is produced.

Not every field must be populated for every observation. Unknown must remain unknown.

## Indicator inventory

The list below is a source-oriented construct inventory observed in the July 2026 workbook. It intentionally does not enumerate every month-on-month, year-on-year, percent, index-base, or comparison presentation as a separate indicator unless it is a distinct statistical construct in its own right.

### 1.1 ВВП

- объем валового внутреннего продукта;
- индекс физического объема произведенного ВВП.

### 1.2 Промышленность

- индекс промышленного производства;
- индекс производства по добыче полезных ископаемых;
- индекс производства по обрабатывающим производствам;
- исторический показатель "производство и распределение электроэнергии, газа и воды";
- современный показатель "обеспечение электрической энергией, газом и паром; кондиционирование воздуха";
- "водоснабжение; водоотведение, организация сбора и утилизации отходов, деятельность по ликвидации загрязнений".

### 1.3 Сельское хозяйство

- индекс производства продукции сельского хозяйства в хозяйствах всех категорий.

### 1.4 Животноводство

- скот и птица на убой в живом весе;
- производство молока;
- производство яиц.

### 1.5 Грузовой транспорт

- грузооборот транспорта всего;
- перевозка грузов транспортом всего;
- грузооборот железнодорожного транспорта;
- грузооборот автомобильного транспорта;
- перевозка грузов автомобильным транспортом;
- грузооборот морского транспорта;
- перевозка грузов морским транспортом;
- грузооборот внутреннего водного транспорта;
- перевозка грузов внутренним водным транспортом;
- грузооборот воздушного транспорта;
- перевозка грузов воздушным транспортом;
- грузооборот трубопроводного транспорта;
- перевозка грузов трубопроводным транспортом;
- коммерческий грузооборот транспорта;
- коммерческая перевозка грузов транспортом;
- коммерческий грузооборот автомобильного транспорта;
- перевозка грузов автомобильным транспортом на коммерческой основе;
- погрузка грузов на железнодорожном транспорте.

### 1.5.1 Пассажирский транспорт

- пассажирооборот транспорта всего;
- перевозка пассажиров транспортом всего;
- пассажирооборот железнодорожного транспорта;
- перевозка пассажиров железнодорожным транспортом;
- пассажирооборот автобусов по маршрутам регулярных перевозок;
- перевозка пассажиров автобусами по маршрутам регулярных перевозок;
- пассажирооборот морского транспорта;
- перевозка пассажиров морским транспортом;
- пассажирооборот внутреннего водного транспорта;
- перевозка пассажиров внутренним водным транспортом;
- пассажирооборот воздушного транспорта;
- перевозка пассажиров воздушным транспортом.

### 1.6 Инвестиции

- инвестиции в основной капитал.

### 1.6.1 Источники инвестиций в основной капитал организаций без субъектов малого предпринимательства

- собственные средства предприятий;
- привлеченные средства;
- бюджетные средства;
- средства федерального бюджета;
- средства бюджетов субъектов Российской Федерации.

### 1.7 Строительство

- объем работ по виду деятельности "Строительство".

### 1.8 Жилье

- ввод в действие жилых домов организациями всех форм собственности.

### 1.9 Внешняя торговля

- внешнеторговый оборот всего;
- экспорт товаров всего;
- импорт товаров всего;
- внешнеторговый оборот со странами дальнего зарубежья;
- экспорт в страны дальнего зарубежья;
- импорт из стран дальнего зарубежья;
- внешнеторговый оборот с государствами — участниками СНГ;
- экспорт в СНГ;
- импорт из СНГ.

### 1.10 Валютные курсы

- официальный курс доллара США к рублю;
- официальный курс евро к рублю.

### 1.11 Бюджет

- дефицит / профицит консолидированного бюджета.

### 1.12 Розничная торговля

- оборот розничной торговли;
- оборот пищевых продуктов, включая напитки и табачные изделия;
- оборот непродовольственных товаров;
- оборот общественного питания;
- товарные запасы в организациях розничной торговли;
- обеспеченность оборота розничной торговли запасами в днях торговли.

### 1.13 Услуги

- объем платных услуг населению.

### 1.14 Потребительские цены и наборы

- индекс потребительских цен;
- стоимость условного минимального набора продуктов питания;
- стоимость фиксированного набора потребительских товаров и услуг.

### 1.15 Оптовая торговля

- оборот оптовой торговли;
- индекс физического объема оборота оптовой торговли.

### 2.1 Доходы бюджетов

- доходы консолидированного бюджета;
- доходы федерального бюджета;
- доходы консолидированных бюджетов субъектов Российской Федерации;
- доля налога на прибыль организаций в соответствующих бюджетных доходах;
- доля налога на доходы физических лиц;
- доля налога на добавленную стоимость;
- доля акцизов по подакцизным товарам;
- доля доходов от внешнеэкономической деятельности.

The budget perimeter attached to each tax/revenue component is part of the construct and must be preserved.

### 2.1 Расходы бюджетов

- расходы консолидированного бюджета;
- расходы федерального бюджета;
- расходы консолидированных бюджетов субъектов Российской Федерации;
- расходы на общегосударственные вопросы + национальную безопасность и правоохранительную деятельность + обслуживание государственного и муниципального долга;
- расходы на национальную оборону;
- расходы на национальную экономику;
- расходы на образование;
- объединенная исходная группа расходов "культура, кинематография и СМИ, здравоохранение, физическая культура и спорт, социальная политика".

Do not decompose a source-published combined category into artificial components.

### 2.1 Бюджетное сальдо

- превышение доходов над расходами федерального бюджета;
- превышение расходов над доходами федерального бюджета;
- превышение доходов над расходами консолидированных бюджетов субъектов Российской Федерации;
- превышение расходов над доходами консолидированных бюджетов субъектов Российской Федерации.

### 2.2 Финансовый результат организаций

Сальдированный финансовый результат:

- всего;
- добыча полезных ископаемых;
- обрабатывающие производства;
- обеспечение электрической энергией, газом и паром; кондиционирование воздуха;
- строительство;
- транспортировка и хранение.

### 2.2 Убыточные организации

Для соответствующих видов деятельности публикуются:

- количество убыточных организаций;
- удельный вес убыточных организаций.

Виды деятельности:

- добыча полезных ископаемых;
- обрабатывающие производства;
- обеспечение электрической энергией, газом и паром; кондиционирование воздуха;
- строительство;
- транспортировка и хранение.

### 2.3 Банковское кредитование и размещенные средства

- кредиты, депозиты и прочие средства, предоставленные корпоративным клиентам, физическим лицам и кредитным организациям;
- кредиты и прочие средства, предоставленные корпоративным клиентам;
- кредиты и прочие средства корпоративным клиентам сроком до 1 года;
- кредиты и прочие средства корпоративным клиентам сроком свыше 1 года.

Do not assume that every visible child row decomposes every parent total.

### 2.4 Задолженность организаций

- кредиторская задолженность;
- просроченная кредиторская задолженность;
- просроченная задолженность поставщикам;
- просроченная задолженность в бюджеты всех уровней;
- дебиторская задолженность;
- просроченная дебиторская задолженность;
- просроченная дебиторская задолженность покупателей.

### 2.5 Заработная плата

- просроченная задолженность по заработной плате.

### 3.1 Цены производителей промышленности

- индекс цен производителей промышленных товаров всего;
- индекс цен производителей по добыче полезных ископаемых;
- индекс цен производителей по обрабатывающим производствам;
- индекс цен производителей по обеспечению электрической энергией, газом и паром; кондиционированию воздуха;
- индекс цен производителей по водоснабжению, водоотведению, организации сбора и утилизации отходов, деятельности по ликвидации загрязнений.

### 3.1.1 Средние цены производителей на энергоресурсы и нефтепродукты

- нефть обезвоженная, обессоленная и стабилизированная;
- уголь, кроме антрацита, коксующегося угля и бурого угля;
- газ природный горючий;
- бензин автомобильный;
- топливо дизельное;
- мазут топочный.

### 3.2 Животноводство — цены

- индекс цен производителей на продукцию животноводства;
- средняя цена производителей крупного рогатого скота в живом весе;
- средняя цена производителей сельскохозяйственной птицы в живом весе;
- средняя цена производителей сырого коровьего молока;
- средняя цена производителей свежих куриных яиц.

### 3.3 Инвестиционные цены

- сводный индекс цен на продукцию, затраты и услуги инвестиционного назначения;
- индекс цен производителей на строительную продукцию.

### 3.4 Транспортные тарифы

- индекс тарифов на грузовые перевозки.

### 3.5 Потребительские цены

- индекс потребительских цен всего;
- индекс потребительских цен на продукты питания;
- индекс потребительских цен на алкогольные напитки;
- индекс потребительских цен на непродовольственные товары;
- индекс потребительских цен на услуги.

### 4.1 Занятость и безработица

- численность занятых в возрасте 15-72 лет;
- численность занятых в возрасте 15 лет и старше;
- общая численность безработных в возрасте 15-72 лет;
- общая численность безработных в возрасте 15 лет и старше;
- уровень безработицы населения в возрасте 15-72 лет;
- уровень безработицы населения в возрасте 15 лет и старше;
- численность официально зарегистрированных безработных;
- численность официально зарегистрированных безработных, получающих пособие по безработице;
- численность незанятых граждан, состоящих на учете в службе занятости;
- заявленная работодателями потребность в работниках;
- нагрузка незанятого населения на 100 заявленных вакансий.

### 4.2 Заработная плата

- среднемесячная номинальная начисленная заработная плата работников организаций;
- реальная начисленная заработная плата.

### 4.3 Пенсии

- средний размер назначенных пенсий;
- реальный размер назначенных пенсий.

### 4.4 Доходы населения

- денежные доходы в среднем на душу населения;
- реальные денежные доходы;
- реальные располагаемые денежные доходы.

### 4.4 Использование денежных доходов

- покупка товаров и оплата услуг;
- обязательные платежи и взносы и прочие расходы;
- сбережения во вкладах и ценных бумагах + изменение средств на счетах индивидуальных предпринимателей + изменение задолженности по кредитам + приобретение недвижимости;
- покупка валюты;
- прирост / уменьшение денег на руках.

Preserve combined source categories as combined constructs unless a separate primary-source decomposition is explicitly published.

### 4.5 Средства физических лиц

- объем вкладов, депозитов и прочих привлеченных средств физических лиц всего;
- объем вкладов, депозитов и прочих привлеченных средств физических лиц в учреждениях ПАО Сбербанк;
- средний размер вклада на рублевых и валютных счетах в учреждениях ПАО Сбербанк.

### 4.6 Распределение населения по доходам

- распределение населения России по величине среднедушевых денежных доходов;
- численность населения — всего as the source total/control row;
- доли населения по опубликованным интервалам среднемесячных среднедушевых денежных доходов.

The income interval itself is a classification category, not free text to be discarded.

### 4.7 Прожиточный минимум

- величина прожиточного минимума в среднем на душу населения;
- величина прожиточного минимума для трудоспособного населения;
- величина прожиточного минимума для пенсионеров;
- величина прожиточного минимума для детей.

### 4.8 Бедность

- численность населения с денежными доходами ниже величины прожиточного минимума;
- численность населения с денежными доходами ниже границы бедности.

Absolute and share/percentage presentations may coexist. Preserve their units and measure types rather than treating them as separate underlying population constructs.

## Extraction workflow

When asked to retrieve or build a series from these workbooks:

1. Identify the exact source workbook(s) and exact worksheet(s).
2. Read the Russian table title, row label, column/period label, unit, and all attached footnote markers.
3. Inspect merged headings that govern the target cell.
4. Inspect hidden columns/rows relevant to the logical table.
5. Resolve whether the value is a literal numeric cell, a text-encoded number, a source formula, or a special marker.
6. Resolve the period basis and perimeter.
7. Resolve all footnotes and methodological/status notes that apply.
8. Keep historical classification/methodology versions distinct.
9. Return the source observation before performing any requested analytical transformation.
10. If a bridge is needed, document inputs, formula/mapping, assumptions, and output separately.

## Prohibited shortcuts

Do not:

- flatten every worksheet into one schema by column position alone;
- use only visible cells;
- use merge extents to determine table width;
- strip all footnote digits with a regex and discard the link;
- convert every string-looking number to numeric without preserving the literal;
- interpret blank, …, or - as zero;
- treat the English translation row as a second observation;
- trim and overwrite exact worksheet names without keeping the original;
- join series merely because labels are similar;
- assume 2025 duplicate-looking distribution observations are duplicates;
- infer a classification bridge;
- silently revise Rosstat typos or strange formatting;
- decompose source-published combined categories;
- treat a source-workbook formula as a Tabularium-derived calculation;
- expose binary floating-point tails as published precision.

## Validation checklist

Before considering an extraction complete, verify:

- exact workbook and exact sheet provenance are retained;
- all relevant source rows/columns are included, including hidden ones;
- merged headings were interpreted but not used as the sole data-boundary signal;
- Russian/English duplicate presentation has not doubled the observation count;
- source footnote markers have been resolved or preserved;
- methodology, revision, preliminary status, geography, and classification notes are not lost;
- period semantics are explicit;
- missing/special markers remain distinct from zero;
- displayed precision is respected;
- formula cells are identified;
- historical breaks are not silently stitched;
- every derived result resolves back to source observations and a reproducible bridge.
