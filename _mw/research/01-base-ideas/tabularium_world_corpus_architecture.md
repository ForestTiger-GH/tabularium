# Tabularium: архитектура мирового корпуса корпоративной отчетности

**Статус:** архитектурная заметка / development-layer  
**Проект:** `ForestTiger-GH/tabularium`  
**Дата:** 2026-09-28  
**Предмет:** физическая архитектура `scrolls/world/`, классификация мировой корпоративной отчетности и именование файлов

## 1. Исходная задача

В `Tabularium` предполагается расширить первичный корпус за пределы России.

Планируемый мировой корпус может включать, в частности:

- крупные международные банки;
- аграрно-ориентированные банки, включая Rabobank и Agricultural Bank of China;
- крупные ИТ-компании, включая Cisco и NVIDIA;
- доступные первичные финансовые публикации OpenAI и Anthropic;
- крупные международные нефтегазовые компании;
- другие значимые зарубежные компании и финансовые организации.

При этом физическую архитектуру репозитория необходимо сохранить простой.

Нежелательна структура вида:

```text
world/
  country/
    sector/
      accounting-standard/
        report-type/
          year/
```

Такой подход быстро превращает корпус в глубокий лабиринт и затрудняет массовое обновление.

Основная задача — сохранить source-faithful модель Tabularium, но не кодировать все свойства источника через дерево каталогов.

---

## 2. Основной вывод

Для мировой части корпуса рекомендуется использовать **плоскую архитектуру по устойчивым типам первичных публикаций**.

Страна, стандарт учета, рынок листинга, регуляторный режим и другие свойства должны преимущественно храниться:

1. в имени файла;
2. в реестре;
3. в будущих машинных метаданных;

но не в дополнительных уровнях каталогов.

Базовая структура:

```text
scrolls/
├── russia/
└── world/
    ├── README.md
    ├── financial-reporting/
    └── annual-reports/
```

В дальнейшем новые каталоги следует создавать только при появлении реального устойчивого класса источников.

Например:

```text
scrolls/
└── world/
    ├── financial-reporting/
    ├── annual-reports/
    ├── prudential-reporting/
    └── sustainability-reporting/
```

При этом `prudential-reporting/` или `sustainability-reporting/` не следует создавать заранее без фактического корпуса соответствующих публикаций.

---

## 3. Почему не следует создавать отдельные каталоги по стандартам учета

На первый взгляд возможна структура:

```text
world/
├── ifrs/
├── us-gaap/
├── prc-asbe/
├── hkfrs/
├── j-gaap/
└── ...
```

Но такая модель плохо масштабируется.

По мере расширения мирового корпуса появятся:

- IFRS Accounting Standards;
- IFRS as adopted by the European Union;
- UK-adopted international accounting standards;
- US GAAP;
- PRC Accounting Standards for Business Enterprises;
- HKFRS;
- Japanese GAAP;
- Korean IFRS;
- Indian Accounting Standards;
- Australian Accounting Standards;
- Canadian IFRS;
- Swiss GAAP FER;
- другие национальные режимы.

Кроме того, один первичный отчет может содержать несколько accounting representations.

Например, в одном Annual Report могут одновременно присутствовать:

- consolidated financial statements по IFRS;
- standalone company financial statements по национальному законодательству.

Следовательно:

> accounting framework — важное свойство representation, но не всегда устойчивый физический класс публикации.

Поэтому стандарт учета лучше хранить как атрибут источника, а не как обязательный уровень физической директории.

---

## 4. Почему страна также не должна становиться дочерним каталогом внутри `world/`

Не рекомендуется:

```text
world/
├── china/
├── united-states/
├── netherlands/
├── united-kingdom/
└── ...
```

Вместо этого страна должна кодироваться непосредственно в идентичности файла.

Это дает:

- плоскую структуру;
- естественную сортировку;
- возможность быстро увидеть страну происхождения;
- отсутствие десятков пустых или почти пустых каталогов;
- простое массовое добавление новых компаний.

---

## 5. Страна в начале имени файла

Для файлов в `scrolls/world/` рекомендуется использовать двухбуквенный код страны **ISO 3166-1 alpha-2**.

Примеры:

```text
US  United States
CN  China
NL  Netherlands
GB  United Kingdom
DE  Germany
FR  France
CH  Switzerland
JP  Japan
KR  South Korea
CA  Canada
AU  Australia
BR  Brazil
SA  Saudi Arabia
AE  United Arab Emirates
HK  Hong Kong
```

Следует использовать `GB`, а не неформальное `UK`, если принимается ISO-контракт.

Пример естественной сортировки:

```text
CN_AGRICULTURAL-BANK-OF-CHINA_...
CN_BANK-OF-CHINA_...
CN_ICBC_...

GB_BP_...
GB_SHELL_...

NL_RABOBANK_...

US_CISCO_...
US_EXXONMOBIL_...
US_NVIDIA_...
```

---

## 6. Что означает код страны

Код страны должен иметь однозначную семантику.

Рекомендуемый контракт:

> **country prefix = юрисдикция reporting entity**

Он не должен означать:

- страну биржи;
- страну, в которой находится регулятор, получивший filing;
- происхождение accounting framework;
- язык документа;
- основной рынок деятельности группы.

Например, британская Shell остается:

```text
GB_SHELL_...
```

даже если конкретный документ представляет собой Form 20-F, поданную в SEC.

Китайский Agricultural Bank of China остается:

```text
CN_AGRICULTURAL-BANK-OF-CHINA_...
```

даже если конкретная версия отчета предназначена для Hong Kong Stock Exchange.

Если же источником является самостоятельная гонконгская reporting entity, тогда корректным может быть `HK`.

Это позволяет разделить:

```text
entity jurisdiction
```

и:

```text
filing jurisdiction / market / regulator
```

как разные свойства источника.

---

## 7. Рекомендуемый формат имени файла

Базовый контракт:

```text
<CC>_<ENTITY>_<PERIOD-END>_<PUBLICATION-TYPE>[_<ACCOUNTING-FRAMEWORK>][_<VARIANT>].<ext>
```

Где:

- `<CC>` — ISO alpha-2 код юрисдикции reporting entity;
- `<ENTITY>` — устойчивое имя reporting entity;
- `<PERIOD-END>` — дата окончания отчетного периода;
- `<PUBLICATION-TYPE>` — класс или вид публикации;
- `<ACCOUNTING-FRAMEWORK>` — стандарт учета, если он однозначен и полезен;
- `<VARIANT>` — дополнительная версия/рынок/класс акций при необходимости;
- `<ext>` — исходный или source-faithful формат.

Примеры:

```text
US_NVIDIA_2026-01-25_10K_US-GAAP.html

US_CISCO_2025-07-26_10K_US-GAAP.html

US_EXXONMOBIL_2025-12-31_10K_US-GAAP.html

NL_RABOBANK_2026-06-30_INTERIM_EU-IFRS.md

NL_RABOBANK_2025-12-31_ANNUAL.md

CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-HSHARE_IFRS.md

CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-ASHARE_PRC-ASBE.md

GB_SHELL_2025-12-31_ANNUAL_IFRS.md

GB_SHELL_2025-12-31_20F_IFRS.html
```

---

## 8. Почему для мира лучше использовать полную дату окончания периода

Российский контракт вида:

```text
СБЕР_2026М6_МСФО.md
```

удобен для российского корпуса, где большинство отчетных периодов естественно выражаются календарным месяцем.

Для мировых компаний этот подход менее надежен.

У многих компаний финансовый год не совпадает с календарным.

Например:

```text
NVIDIA fiscal 2026
period end: 2026-01-25
```

или:

```text
Cisco fiscal 2025
period end: 2025-07-26
```

Поэтому для `world/` предпочтительна ISO-дата:

```text
YYYY-MM-DD
```

Например:

```text
US_NVIDIA_2026-01-25_10K_US-GAAP.html
US_CISCO_2025-07-26_10K_US-GAAP.html
```

А в машинном реестре можно отдельно хранить:

```yaml
fiscal_year_label: 2026
period_end: 2026-01-25
period_type: annual
```

Таким образом источник не нормализуется искусственно к календарному месяцу.

---

## 9. Accounting framework не обязан присутствовать в имени файла

Поле accounting framework полезно только когда источник действительно позволяет однозначно идентифицировать режим учета.

Например:

```text
US_NVIDIA_2026-01-25_10K_US-GAAP.html
```

или:

```text
CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-HSHARE_IFRS.md
```

Но если один Annual Report включает несколько режимов учета, нельзя искусственно назначать всему документу один framework.

Например:

```text
NL_RABOBANK_2025-12-31_ANNUAL.md
```

может быть предпочтительнее, если внутри:

- consolidated statements — EU-adopted IFRS;
- company statements — нидерландский statutory framework.

В таком случае полная семантика хранится в registry/metadata.

Пример:

```yaml
entity_country: NL
publication_type: annual-report

accounting_representations:
  - perimeter: consolidated
    framework: eu-ifrs

  - perimeter: company
    framework: nl-statutory
```

Это соответствует принципу:

> source → representation → observation

и не заставляет физический путь делать ложное семантическое утверждение.

---

## 10. Agricultural Bank of China как пример нескольких representations

Agricultural Bank of China хорошо показывает проблему.

Одна и та же китайская группа может публиковать версии отчетности:

- для A-shares;
- для H-shares.

При этом разные версии могут использовать разные accounting frameworks.

Пример физического хранения:

```text
CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-ASHARE_PRC-ASBE.md

CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-HSHARE_IFRS.md
```

Оба файла имеют `CN`, поскольку страна относится к reporting entity.

Семантически:

```text
source
├── A-share publication
│   └── PRC-ASBE / CAS
│
└── H-share publication
    └── IFRS
```

Это разные representations одного экономического объекта и периода.

Одинаковые или близкие значения нельзя автоматически считать одним observation.

---

## 11. Rabobank как пример документа с несколькими accounting bases

Rabobank показывает обратную проблему.

Annual Report может содержать:

- consolidated financial statements по IFRS as adopted by the EU;
- company financial statements по требованиям нидерландского законодательства.

Поэтому помещение всего документа в:

```text
world/ifrs/
```

будет семантически неточным.

Предпочтительная физическая идентичность:

```text
NL_RABOBANK_2025-12-31_ANNUAL.md
```

А accounting framework должен описываться на уровне representations внутри документа.

Это одна из основных причин не использовать framework как физический route верхнего уровня.

---

## 12. NVIDIA и Cisco как типичный US GAAP-контур

Для американских публичных компаний ситуация зачастую проще.

Например:

```text
US_NVIDIA_2026-01-25_10K_US-GAAP.html
US_CISCO_2025-07-26_10K_US-GAAP.html
```

Здесь:

- `US` — юрисдикция reporting entity;
- `10K` — вид SEC filing;
- `US-GAAP` — accounting framework;
- дата — реальный конец fiscal reporting period.

При этом:

> 10-K ≠ US GAAP

`10-K` — вид регуляторной публикации.

`US GAAP` — стандарт бухгалтерского учета.

Это два разных измерения, даже если для domestic issuers они часто встречаются вместе.

---

## 13. Shell как пример параллельных первичных публикаций

У крупной международной группы могут существовать:

- Annual Report and Accounts;
- Form 20-F;
- отдельные финансовые таблицы;
- XBRL/iXBRL-представления.

Если Annual Report и 20-F являются отдельными официальными первичными публикациями, они могут храниться отдельно:

```text
GB_SHELL_2025-12-31_ANNUAL.md
GB_SHELL_2025-12-31_20F_IFRS.html
```

Это не нарушает правило:

> один первичный материал физически хранится один раз.

Здесь речь идет о двух самостоятельных первичных publications/representations, даже если их содержание существенно пересекается.

---

## 14. Что идет в `financial-reporting/`

Рекомендуемое определение:

> General-purpose annual, interim and quarterly financial reporting and closely related statutory or regulatory financial filings whose principal retained evidentiary value is the financial statements.

Примеры:

```text
US_NVIDIA_2026-01-25_10K_US-GAAP.html

US_CISCO_2025-07-26_10K_US-GAAP.html

NL_RABOBANK_2026-06-30_INTERIM_EU-IFRS.md

CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-HSHARE_IFRS.md

CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-ASHARE_PRC-ASBE.md
```

`10-K`, `20-F`, annual financial statements, interim financial statements и аналогичные публикации могут сосуществовать в одном физическом классе, если их основная ценность для корпуса — финансовая отчетность.

---

## 15. Что идет в `annual-reports/`

Сюда следует помещать широкие корпоративные Annual Reports / Integrated Reports, если они являются самостоятельным классом публикации.

Например:

```text
NL_RABOBANK_2025-12-31_ANNUAL.md

GB_SHELL_2025-12-31_ANNUAL.md

DE_BASF_2025-12-31_ANNUAL.md

CH_NESTLE_2025-12-31_ANNUAL.md
```

То, что внутри Annual Report содержатся audited IFRS financial statements, само по себе не превращает весь Annual Report в standalone IFRS financial statements.

Source identity должна сохраняться.

---

## 16. Пример итоговой структуры

```text
scrolls/
│
├── russia/
│   └── ... существующая российская архитектура
│
└── world/
    │
    ├── README.md
    │
    ├── financial-reporting/
    │   ├── CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-ASHARE_PRC-ASBE.md
    │   ├── CN_AGRICULTURAL-BANK-OF-CHINA_2025-12-31_ANNUAL-HSHARE_IFRS.md
    │   ├── NL_RABOBANK_2026-06-30_INTERIM_EU-IFRS.md
    │   ├── US_CISCO_2025-07-26_10K_US-GAAP.html
    │   ├── US_EXXONMOBIL_2025-12-31_10K_US-GAAP.html
    │   ├── US_NVIDIA_2026-01-25_10K_US-GAAP.html
    │   └── ...
    │
    └── annual-reports/
        ├── GB_SHELL_2025-12-31_ANNUAL.md
        ├── NL_RABOBANK_2025-12-31_ANNUAL.md
        └── ...
```

---

## 17. Какие каталоги не следует создавать

Не рекомендуется физически создавать отдельные routes по аналитическим темам:

```text
banks/
technology/
oil-and-gas/
agriculture/
ai-companies/
private-companies/
```

Также не рекомендуется создавать routes по странам:

```text
usa/
china/
netherlands/
united-kingdom/
```

И не рекомендуется создавать routes по accounting frameworks:

```text
ifrs/
us-gaap/
prc-asbe/
hkfrs/
j-gaap/
```

Эти признаки лучше реализовать как:

- поля registry;
- фильтры интерфейса;
- machine-readable metadata;
- части имени файла там, где это полезно.

Физическое дерево должно отражать устойчивые классы первичных публикаций, а не все возможные измерения источника.

---

## 18. Не использовать биржевой тикер как основную идентичность компании

Рекомендуется:

```text
US_NVIDIA
CN_AGRICULTURAL-BANK-OF-CHINA
NL_RABOBANK
GB_SHELL
```

Не рекомендуется:

```text
US_NVDA
CN_601288
HK_1288
GB_SHEL
```

Причины:

- одна группа может иметь несколько листингов;
- могут существовать A-shares, H-shares, ADR и другие инструменты;
- тикеры могут меняться;
- некоторые значимые reporting entities вообще не имеют публичного тикера;
- OpenAI, Anthropic и некоторые кооперативные/частные организации не укладываются в ticker-first модель.

Тикеры следует хранить в entity registry как свойства, а не как каноническое имя source artifact.

---

## 19. OpenAI и Anthropic

Для OpenAI, Anthropic и других частных компаний не требуется отдельная физическая таксономия.

Если появляется настоящий публичный финансовый источник:

```text
US_OPENAI_<period-end>_<actual-publication-type>...
US_ANTHROPIC_<period-end>_<actual-publication-type>...
```

он помещается в существующий устойчивый класс.

Не следует заранее создавать:

```text
ai-companies/
private-companies/
venture-backed/
```

Это аналитические категории, а не классы первичных публикаций.

---

## 20. Accounting framework как отдельное измерение реестра

В будущем реестр может использовать контролируемый словарь вроде:

```text
ifrs
eu-ifrs
uk-ifrs
us-gaap
prc-asbe
hkfrs
j-gaap
k-ifrs
ind-as
...
```

При этом нельзя автоматически нормализовать все IFRS-подобные режимы до одного `ifrs`.

Если источник сообщает:

```text
IFRS as adopted by the European Union
```

это следует сохранить как отдельный source-faithful representation.

Если источник сообщает:

```text
IFRS Accounting Standards as issued by IASB
```

это отдельное assertion источника.

Сходство стандартов не дает права молча объединять их в evidence-layer.

---

## 21. Разделение ответственности между физическим путем, именем файла и реестром

### Физическая папка

Отвечает на вопрос:

> Что это за устойчивый класс первичной публикации?

Например:

```text
financial-reporting/
annual-reports/
prudential-reporting/
```

### Имя файла

Отвечает на вопросы:

- чья публикация;
- из какой юрисдикции reporting entity;
- какой период;
- какого вида публикация;
- какой framework или variant, если это необходимо для различения.

### Реестр

Должен хранить более богатую семантику:

```text
entity
entity jurisdiction
industry
accounting framework
filing regime
publication type
period start
period end
fiscal-year label
consolidated / standalone
language
market
listing
source
format
version
```

### Observation layer

Отвечает на вопрос:

> Что конкретно утверждается в публикации?

Таким образом структура остается совместимой с цепочкой:

```text
source
→ representation
→ observation
→ derivation / bridge
→ analytical claim
```

---

## 22. Связь с текущим контрактом Tabularium

Текущий `AGENTS.md` закрепляет:

```text
Within scrolls/, route by country first.
```

Создание:

```text
scrolls/world/
```

формально требует небольшого осознанного изменения этого правила.

Необходимо не перестраивать существующий `russia/`, а добавить исключение для мирового корпоративного корпуса.

По смыслу новое правило может быть сформулировано так:

```text
The Russian primary-source corpus routes under scrolls/russia/.

Non-Russian corporate publications may be grouped under scrolls/world/,
where the reporting entity jurisdiction is preserved by an ISO 3166-1
alpha-2 country code in the artifact identity and registry.
```

Это позволяет:

- оставить российскую архитектуру без миграции;
- не создавать отдельный каталог для каждой иностранной страны;
- сохранить country provenance;
- не противоречить source-faithful принципам;
- обеспечить удобное массовое пополнение мирового корпуса.

---

## 23. Итоговый архитектурный принцип

Рекомендуемый принцип для `scrolls/world/`:

> **страна — в имени файла; accounting framework — в имени и/или реестре; физическая папка — только устойчивый тип первичной публикации.**

Минимальная архитектура:

```text
scrolls/world/
├── README.md
├── financial-reporting/
└── annual-reports/
```

Новые маршруты должны появляться только после возникновения реального массива первичных источников, который неестественно помещать в существующие классы.

Это дает компромисс между:

- source-faithful хранением;
- минимальной вложенностью;
- масштабируемостью;
- удобным массовым обновлением;
- возможностью будущей машинной фильтрации;
- сохранением различий между jurisdiction, publication type, accounting framework и representation.

Главное правило:

> **физическая архитектура не должна пытаться кодировать все свойства источника одновременно.**

Именно registry и metadata должны обеспечивать богатую многомерную классификацию, тогда как `scrolls/world/` остается простым, устойчивым и пригодным для расширения корпусом первичных публикаций.
