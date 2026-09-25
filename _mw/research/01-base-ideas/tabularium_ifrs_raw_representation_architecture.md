# Tabularium: source-faithful представление МСФО и переход к слою наблюдений

**Статус:** архитектурное исследование / development-layer  
**Дата:** 2026-09-23  
**Репозиторий:** `ForestTiger-GH/tabularium`  
**Предмет:** МСФО-публикации в `russia/corporate-disclosures/financial-reporting/ifrs/`

---

# 0. Главный вывод

Единый слой представления для МСФО нужен, но его не следует понимать как «нормализованные Markdown-отчеты» или как обязательную красивую табличную верстку.

Правильная цепочка для Tabularium:

```text
PRIMARY SOURCE
    ↓
SOURCE-FAITHFUL REPRESENTATION
    ↓
REPORTED OBSERVATIONS
    ↓
BRIDGE / MAPPING
    ↓
DERIVATIONS
    ↓
ANALYTICAL CLAIMS
```

Для PDF:

```text
оригинальная публикация PDF
    ↓
полная source-faithful Markdown-транскрипция
    ↓
атомарные факты конкретного выпуска
    ↓
явное сопоставление с устойчивыми constructs
```

Моя рекомендация: **не делать сначала массовую переработку всего корпуса в «идеальный Markdown»**. Нужно зафиксировать небольшой строгий контракт representation-layer, сделать валидатор и после этого сразу начинать пилот Observation Layer.

То есть не:

```text
103 файла
→ полная унификация верстки
→ идеальные Markdown tables
→ когда-нибудь факты
```

а:

```text
1. зафиксировать Markdown Representation Profile v1
2. сделать validator/linter
3. применять его ко всем новым PDF
4. выбрать несколько типологически разных МСФО
5. построить source-bound observation schema
6. проверить, хватает ли representation для точной адресации
7. только затем selectively backfill legacy corpus
```

Ключевой тезис:

> **существующие `.md` Tabularium — уже не raw source, а representation источника. Это нормально. Термин `raw` лучше не делать названием архитектурного слоя, потому что он смешивает исходные байты, транскрипцию и извлеченные факты.**

Предпочтительные термины:

```text
source artifact
source-faithful representation
reported observation
bridge / mapping
derived observation
analytical claim
```

---

# 1. Что уже закреплено текущим контрактом Tabularium

Корневой `AGENTS.md` уже задает очень сильный фундамент:

- хранить первичные публичные материалы;
- сохранять source meaning и reported values;
- не добавлять в corpus анализ, интерпретацию, нормализацию и derived calculations;
- нативно машиночитаемые HTML/XLSX/CSV/XML/JSON сохранять в исходном формате;
- PDF хранить как полные source-faithful Markdown-транскрипции;
- связанные артефакты одного выпуска держать вместе;
- не создавать новые уровни архитектуры заранее без реальной потребности;
- reporting perimeter считать частью identity источника.

Маршрут МСФО сейчас:

```text
russia/
└── corporate-disclosures/
    └── financial-reporting/
        └── ifrs/
            ├── 2023/
            ├── 2024/
            ├── 2025/
            └── 2026/
```

`ifrs/README.md` дополнительно фиксирует важнейшее правило: нельзя выводить эквивалентность юридического лица и консолидированной группы только из похожих названий.

То есть архитектурная задача сейчас — не придумать новый принцип, а **формализовать уже возникший representation-layer и правильно пристыковать к нему observations**.

---

# 2. Масштаб текущего корпуса

На момент исследования в `ifrs/2023–2026` находится:

| Год | `.md` файлов | Основные отчеты `_МСФО.md` | Презентации `_ПРЕЗ.md` | Объем |
|---|---:|---:|---:|---:|
| 2023 | 4 | 4 | 0 | ~1.66 MB |
| 2024 | 11 | 10 | 1 | ~4.00 MB |
| 2025 | 39 | 35 | 4 | ~13.76 MB |
| 2026 | 49 | 47 | 2 | ~12.60 MB |
| **Итого** | **103** | **96** | **7** | **~32 MB** |

Это уже достаточно большой корпус, чтобы неоднородность начала создавать стоимость для downstream-парсеров. Но он еще достаточно мал, чтобы правильный contract успеть зафиксировать до появления тысяч выпусков.

---

# 3. Что показал просмотр реальных файлов

## 3.1. Layout-faithful page blocks

Сбер, Газпромбанк, Самолет и многие другие отчеты используют схему:

````markdown
<!-- PAGE 5 -->

```text
Промежуточный консолидированный отчет о финансовом положении
...
Кредиты и авансы клиентам    4    49 975,0    47 972,7
...
```
````

Для evidence-layer это очень удачный baseline:

- сохраняется принадлежность текста странице;
- видна приблизительная геометрия таблиц;
- цифры не требуется «понимать», чтобы перенести;
- сложные таблицы не заставляют конвертер угадывать merged cells;
- Markdown-парсер не пытается интерпретировать `#`, `|`, `*`, скобки и прочие source characters как оформление.

## 3.2. Семантический Markdown

Например МСП Банк и ВБРР используют headings и GFM tables:

```markdown
# Заголовок

| Показатель | 30 июня 2026 | 31 декабря 2025 |
|---|---:|---:|
| Кредиты клиентам | 92 052 283 | 100 172 417 |
```

Это удобнее человеку и традиционному parser, но это уже более сильная реконструкция структуры PDF. Кто-то должен решить:

- где граница строки;
- какие визуальные строки входят в одну ячейку;
- как разложить многоуровневый header;
- что считать blank cell;
- как перенести footnotes;
- как представить merged cells.

Именно здесь representation может незаметно превратиться в interpretation.

## 3.3. Даже layout-faithful синтаксис неоднороден

Уралсиб использует:

```markdown
<!-- PAGE 1 / 64 -->

~~~text
...
~~~
```

а многие другие файлы:

```markdown
<!-- PAGE 1 -->

```text
...
```
```

Содержательно обе формы могут быть одинаково faithful, но parser должен знать обе.

## 3.4. Единого provenance header пока нет

В просмотренной выборке нет унифицированного machine-readable header с:

- source URL;
- original filename;
- SHA-256 исходного PDF;
- количеством страниц;
- методом конверсии;
- версией representation profile;
- статусом проверки.

Этот пробел сейчас важнее, чем отсутствие красивой одинаковой верстки.

---

# 4. Почему слово `raw` лучше не превращать в physical layer

У него минимум три смысла.

## 4.1. Raw source

Фактические байты публикации:

```text
issuer_ifrs_2026h1.pdf
```

Это настоящий digital source artifact.

Markdown никогда не является raw source.

## 4.2. Raw representation

Транскрипция видимого содержимого PDF:

```text
PDF
→ layout/text preserving Markdown
```

Это уже преобразование, пусть и максимально faithful.

## 4.3. Raw facts

Атомарные опубликованные значения:

```text
source row
+ source column
+ value literal
+ unit literal
+ period literal
+ locator
```

Например:

```json
{
  "reported_label": "Кредиты и авансы клиентам",
  "value_literal": "49 975,0",
  "unit_literal": "в миллиардах российских рублей"
}
```

Это уже observation-layer.

Поэтому я не рекомендую каталоги:

```text
raw/
clean/
normalized/
processed/
```

Их смысл быстро начинает плавать. Эпистемическая цепочка гораздо точнее:

```text
source → representation → observation → bridge → derivation → claim
```

---

# 5. Source-faithful не означает pixel-faithful

Цель Markdown representation — не воспроизвести PDF как картинку. Иначе проще хранить PDF.

Нужно сохранять:

- текст;
- числа и знаки;
- единицы;
- периоды;
- названия строк и колонок;
- порядок;
- структуру;
- page membership;
- примечания;
- footnotes;
- reporting perimeter и wording источника.

Необязательно сохранять:

- точные шрифты;
- координаты каждого glyph;
- цвета;
- декоративные линии;
- расстояния в пикселях;
- фирменный дизайн.

Следовательно, representation может быть типографски иным, оставаясь source-faithful по содержанию.

---

# 6. Source-faithful не означает extractor-faithful

Еще одна ловушка — считать результат `pdftotext` или иного extractor первичной истиной.

PDF может иметь:

- нелогичный порядок text objects;
- скрытый/дублированный text layer;
- split words;
- некорректные Unicode mappings;
- неправильный reading order колонок.

Поэтому:

```text
PDF text layer ≠ source truth
```

Source truth — сама опубликованная публикация. Extractor — лишь метод создания representation.

Если extractor нарушил очевидную структуру таблицы, faithfully сохранять ошибку extractor не нужно.

---

# 7. Что унифицировать, а что нельзя унифицировать

## Унифицировать стоит

- UTF-8;
- line endings;
- page marker syntax;
- page block syntax;
- provenance metadata;
- правила editor annotations;
- numeric fidelity checks;
- validation statuses;
- version representation profile;
- правила legacy compatibility.

## Нельзя унифицировать в representation-layer

Не надо превращать:

```text
Кредиты и авансы клиентам
Кредиты клиентам
Ссуды клиентам
```

в одну source label.

Не надо:

- приводить единицы к RUB mn;
- приводить периоды к одному template;
- перестраивать примечания в единую taxonomy;
- объединять разные reporting perimeters;
- заменять разные constructs одним metric id.

Это уже observation/bridge layer.

---

# 8. Рекомендуемый профиль: TMRP-1

Условное название:

```text
Tabularium Markdown Representation Profile v1
TMRP-1
```

Это не новая физическая taxonomy репозитория. Это формальный контракт того, как PDF-публикация представляется в `.md`.

---

# 9. Metadata должна быть отделена от source content

В начале файла можно иметь небольшой project-created front matter:

```yaml
---
tabularium_representation_profile: "tmrp-1"
source_media_type: "application/pdf"
source_file_name: "SBER_IFRS_2026H1.pdf"
source_url: null
source_sha256: null
source_page_count: 68
representation:
  method: "pdf-text-layer-assisted"
  review_status: "unreviewed"
---
```

Необходимо явно закрепить:

> front matter является metadata Tabularium и не является текстом исходной публикации.

В v1 я бы не добавлял туда экономическую классификацию вроде `metric_basis`, `sector`, `loan_scope`, если она требует интерпретации.

Минимально полезны:

```text
source_file_name
source_url
source_sha256
source_media_type
source_page_count
retrieved_at
representation_profile
conversion_method
review_status
```

---

# 10. Canonical page representation

Принцип:

> одна source page → один Markdown page block.

````markdown
<!-- PAGE 5 -->

```text
<все видимое текстовое содержимое страницы 5>
```
````

### Почему `text` fence хорош как baseline

CommonMark трактует fenced code block как literal content. Для evidence-layer это очень полезно:

1. `*` не превращается в emphasis;
2. `#` не превращается в heading;
3. `|` не превращает source line в таблицу;
4. internal whitespace можно использовать для таблиц;
5. complex financial table не надо насильно укладывать в ограничения GFM;
6. Git diff остается текстовым и понятным.

---

# 11. Почему GFM tables не должны быть обязательным canonical source representation

Финансовые таблицы часто имеют:

- multi-level columns;
- merged cells;
- промежуточные headings;
- blank cells;
- vertical hierarchy;
- continuation на следующей странице;
- footnotes в header;
- несколько measurement bases;
- несколько периодов и единиц одновременно.

GFM table проще этого. При конверсии появляется необходимость принимать структурные решения.

Поэтому:

> GFM table может быть допустимой структурной representation в конкретном случае, но не должна быть обязательным canonical форматом всего IFRS corpus.

Для новых PDF я бы выбрал layout-faithful fenced page blocks как default.

---

# 12. Нужно ли переписывать уже существующие Markdown tables

Нет, автоматически — не нужно.

Преобразование:

```text
PDF → current Markdown → new Markdown
```

не повышает fidelity. Оно создает еще одно поколение трансформации.

Если legacy file уже faithful, новый parser должен уметь его прочитать.

Поэтому разумны состояния:

```text
LEGACY
TMRP1_COMPATIBLE
TMRP1_NATIVE
```

Если файл действительно нужно мигрировать, источником миграции снова должен быть **первичный PDF**, а старый `.md` — только вспомогательным контролем.

---

# 13. Что стандартизировать жестко

## Encoding

```text
UTF-8
```

## Line endings

```text
LF
```

## Canonical page marker для новых файлов

```html
<!-- PAGE 1 -->
```

Общее число страниц лучше держать в metadata:

```yaml
source_page_count: 68
```

Legacy parser должен понимать и `<!-- PAGE 1 / 64 -->`.

## Fence

Для новых документов выбрать один вариант, например:

````markdown
```text
...
```
````

Legacy parser должен принимать и `~~~text`.

---

# 14. Что запрещено менять в representation-layer

Нельзя автоматически превращать:

```text
1 234,5
```

в:

```text
1234.5
```

Нельзя менять:

```text
(1 234)
```

на:

```text
-1234
```

Нельзя менять:

```text
млн руб.
```

на:

```text
RUB mn
```

Нельзя заменять:

```text
—
```

на `0`, а `н/п` на `N/A`.

Нельзя исправлять странные значения или source typos. Ошибка representation может исправляться, ошибка или странность source — только сохраняться.

---

# 15. Whitespace policy

Whitespace в PDF — не простая вещь.

### Structural whitespace

Например:

```text
Кредиты клиентам      100      90
```

Его нужно сохранять, потому что он помогает восстанавливать геометрию таблицы.

### Trailing whitespace

Пробелы в конце строки обычно не несут source semantics — их можно удалять.

### Transport artifacts

`CRLF/LF`, tabs, invisible separators можно детерминированно нормализовать, но правило должно быть частью versioned profile.

---

# 16. Line wrapping

Для canonical source representation я бы сохранял визуальные переносы строк, если они надежно восстанавливаются.

Например:

```text
Средства физических лиц и
корпоративных клиентов
```

не обязательно превращать в одну строку.

Почему:

- перенос может быть частью table layout;
- source representation не обязана быть NLP-friendly;
- downstream можно построить derived flow-text index.

---

# 17. Headers, footers и содержательные служебные блоки

По умолчанию сохранять:

- названия организации и документа;
- `неаудированные данные`;
- units;
- section titles;
- page numbers;
- регистрационные номера;
- сведения об аудиторе;
- electronic signature blocks;
- legal notices;
- source-specific qualification wording.

Нельзя удалять только потому, что эти элементы «не нужны аналитически».

---

# 18. Non-text elements

Если на странице есть визуальный элемент без машиночитаемого текста, нельзя додумывать его содержание.

Можно использовать project-created HTML comment, строго вне source block:

```html
<!-- TABULARIUM: non-text signature image present on source page -->
```

или:

```html
<!-- TABULARIUM: source page contains a non-text chart not represented in this transcription -->
```

Это именно annotation Tabularium, а не source text.

---

# 19. Provenance: самый важный недостающий слой

Для каждой representation нужно уметь ответить:

> какой именно digital source artifact использовался?

Минимальный набор:

```text
source URL
source filename
source MIME type
retrieval timestamp
source SHA-256
source page count
```

## Почему hash важен

Один URL может через месяц вернуть другой файл. Hash фиксирует конкретные source bytes.

При этом нужно различать:

```text
source_sha256
```

и hash Markdown representation / Git blob SHA.

---

# 20. Нужно ли хранить сами PDF в Git

Не обязательно. Текущий контракт уже разумно выбирает Markdown representation для PDF:

- текст хорошо diff-ится;
- Git не раздувается binary versions;
- поиск проще;
- AI/парсеру удобнее.

Если позже станет системной проблемой исчезновение originals, можно ввести отдельную функцию source preservation — например content-addressed external object store — но только при реальной потребности и после правовой/операционной оценки.

Сейчас хороший baseline:

```text
primary URL
+ original filename
+ hash downloaded artifact
+ faithful Markdown representation
```

---

# 21. Унифицированная оболочка не должна создавать ложную эквивалентность документов

В текущем IFRS corpus встречаются:

- полная отчетность;
- interim condensed statements;
- disclosure-limited reports;
- special-purpose information;
- отдельные опубликованные показатели;
- group reporting;
- standalone reporting;
- investor presentations.

Маленький файл может быть маленьким потому, что сам source раскрывает мало, а не потому, что transcription неполная.

Поэтому одинаковый `.md` wrapper не должен означать одинаковый construct или completeness.

---

# 22. Filename — routing key, но не источник полной semantics

Например:

```text
ГАЗПРОМБАНК_2026М6_МСФО.md
```

не передает полностью специальное wording источника о подготовке финансовой информации для публичного раскрытия.

Observation layer не должен выводить semantics только из filename. Он должен опираться на source wording и explicit registry.

---

# 23. Стоит ли сначала закончить representation-layer целиком

Нет.

Если ждать идеальной унификации всех файлов:

- будет потрачено много работы;
- часть правил окажется ненужной;
- реальные требования source locators еще не известны;
- легко оптимизировать Markdown под красивый GitHub, а не под evidence traceability.

Правильная последовательность:

```text
A. зафиксировать TMRP-1
B. написать linter
C. выбрать разные отчеты
D. построить source-bound observations
E. посмотреть, каких locators/provenance не хватает
F. уточнить TMRP
G. selectively backfill legacy corpus
```

Representation и observations должны развиваться итеративно.

---

# 24. Минимальный representation linter

Он должен проверять структурную целостность, а не бухгалтерскую интерпретацию.

Проверки:

```text
page markers sequential
no duplicate page numbers
no missing page numbers
all fences closed
source_page_count matches
UTF-8 valid
no replacement character �
no obviously empty/missing pages
no accidental duplicated page blocks
```

---

# 25. Numeric fidelity validator

Для Tabularium это особенно полезно.

Page-by-page можно сравнивать source-extracted и represented numeric tokens:

```text
(1 234,5)
47,2%
2026
н/п
—
```

Контролировать:

- число tokens;
- literal form;
- page membership;
- знаки;
- скобки;
- проценты;
- decimal separators.

Это ловит критические transcription errors:

- пропавший минус;
- `( )` → положительное число;
- `8` → `3`;
- `2025` → `2026`;
- потерянный `%`;
- смещение числа между строками.

Но важно:

> такой validator является discrepancy detector, а не доказательством истины. Если source extractor ошибся, совпадение с ним не гарантирует fidelity.

---

# 26. QA можно разделить на независимые уровни

| Уровень | Проверка |
|---|---|
| Q0 | файл технически читается |
| Q1 | страницы сохранены |
| Q2 | нет крупных пропусков текста |
| Q3 | numeric literals согласованы |
| Q4 | table geometry plausibly preserved |
| Q5 | notes/footnotes находятся на месте |
| Q6 | manual spot-check сложных страниц |

Статус можно хранить отдельно:

```yaml
representation:
  validation:
    structural: passed
    numeric: passed
    manual_review: partial
```

Это статус representation, а не «сертификат истинности» документа.

---

# 27. Когда нужен backfill legacy corpus

Перегенерировать старый отчет стоит, если:

1. observation extraction не может надежно локализовать data;
2. page mapping сломан;
3. numeric fidelity не проходит;
4. найдено расхождение с source;
5. provenance source недостаточен и original снова найден;
6. downstream parser обрастает большим количеством special cases;
7. документ все равно повторно обрабатывается новой ingest pipeline.

Не стоит backfill-ить только ради одинакового внешнего вида.

---

# 28. Correction history

Если обнаружена transcription error, исправление должно быть traceable.

Например commit:

```text
fix transcription mismatch on source page 37
```

Observation packs, привязанные к прежнему representation SHA, должны считаться stale до повторной проверки.

---

# 29. Representation profile должен версионироваться

Например:

```text
tmrp-1
tmrp-2
```

Если v2 меняет annotation syntax или page markers, старые v1 документы не обязаны массово мигрировать.

---

# 30. Что считать source preservation

Есть три разных уровня.

## P1 — identity preservation

Известно:

```text
что это за документ
кто издатель
откуда получен
какой у него hash
```

## P2 — semantic preservation

Representation сохраняет:

```text
values
wording
structure
units
periods
perimeter
notes
```

## P3 — byte preservation

Сохраняются исходные PDF bytes.

Tabularium уже хорошо движется к P1 + P2. P3 можно добавлять только при реальной потребности.

---

# 31. После минимального TMRP нужно сразу начинать Observation Layer

Но не с универсального metric catalog.

Первый объект должен быть **reported observation**:

> одна явно опубликованная величина в конкретном source vintage вместе с source context.

Например:

```text
report: СБЕР_2026М6_МСФО
page: 5
row: Кредиты и авансы клиентам
column: 30 июня 2026 года
unit: в миллиардах российских рублей
value: 49 975,0
```

Пока не нужно утверждать, что это какой-то canonical `LOANS.CUSTOMERS.*` construct.

---

# 32. Почему reported observations нужно начинать рано

Они являются проверкой architecture representation-layer.

Когда нужно надежно адресовать сотни конкретных cells, сразу становится видно:

- достаточно ли page locator;
- нужны ли line offsets;
- как хранить multi-level columns;
- как кодировать comparative vintage;
- как хранить source unit;
- что делать с subtotals;
- как фиксировать blank/undisclosed;
- где representation недостаточно структурирована.

До такого пилота можно бесконечно проектировать Markdown и не знать, что действительно необходимо.

---

# 33. Нельзя начинать observation schema с canonical metric

Плохая запись:

```json
{
  "bank": "SBER",
  "metric": "mortgage_loans",
  "date": "2026-06-30",
  "value": 7123
}
```

Она слишком рано уничтожает evidence. Из нее уже непонятно:

- как source назвал показатель;
- gross или net;
- unit;
- perimeter;
- page;
- source column;
- current или comparative vintage;
- reported или derived.

---

# 34. Рекомендуемая source-bound observation

```json
{
  "observation_id": "obs:...",
  "source_report": {
    "path": "russia/.../СБЕР_2026М6_МСФО.md",
    "representation_sha": "..."
  },
  "locator": {
    "page": 5,
    "section_literal": "Промежуточный консолидированный отчет о финансовом положении",
    "row_path_literal": ["Кредиты и авансы клиентам"],
    "column_path_literal": ["30 июня 2026 года"]
  },
  "reported": {
    "value_literal": "49 975,0",
    "unit_literal": "в миллиардах российских рублей",
    "note_literal": "4"
  },
  "status": "REPORTED"
}
```

Это уже полноценный machine-readable evidence object, но в нем почти нет аналитической интерпретации.

---

# 35. Parsed numeric value допустим, но только как явный переход

Источник:

```text
49 975,0
```

Можно получить:

```json
"typed_value": {
  "value": 49975.0,
  "parse_rule": "ru-number-v1"
}
```

То есть исходный literal не исчезает.

---

# 36. Unit conversion тоже не должна быть молчаливой

Сначала:

```json
"unit_literal": "в миллиардах российских рублей"
```

Позже отдельный bridge:

```json
{
  "unit_mapping": "RUB_BILLION",
  "rule": "unit-map-v1"
}
```

---

# 37. Period parsing

Источник:

```text
За шесть месяцев, закончившихся 30 июня 2026 года
```

Сохраняется как literal, затем может быть детерминированно parsed:

```json
{
  "period_kind": "duration",
  "period_start": "2026-01-01",
  "period_end": "2026-06-30"
}
```

Но происхождение parse должно быть видно.

---

# 38. Observation period и source vintage — разные оси

Отчет 6М2026 может сообщать comparative:

```text
31.12.2025 = 100
```

а FY2025 первоначально:

```text
31.12.2025 = 98
```

Оба являются опубликованными observations. Поэтому нельзя иметь ключ только:

```text
entity + metric + date
```

Нужно различать:

```text
observation_period
source_vintage
```

Иначе рестейтменты и реклассификации будут молча перетирать историю.

---

# 39. Missing не равен zero

Observation layer должен уметь различать:

```text
REPORTED
EXPLICIT_ZERO
EXPLICIT_DASH
EXPLICIT_UNDISCLOSED
NOT_APPLICABLE
UNKNOWN
NOT_OBSERVED
```

`NOT_OBSERVED` допустим только когда известно, что соответствующий scope документа полностью обработан.

Отсутствие JSONL record само по себе не означает ни ноль, ни отсутствие disclosure.

---

# 40. Locator: страницы недостаточно

Нужен dual locator.

## Physical locator

```json
{
  "page": 16,
  "representation_sha": "...",
  "line_start_on_page": 12,
  "line_end_on_page": 14
}
```

## Logical locator

```json
{
  "note_literal": "4",
  "table_literal": "Кредиты и авансы клиентам",
  "row_path_literal": ["Физические лица", "Жилищные кредиты"],
  "column_path_literal": ["30 июня 2026", "Валовая балансовая стоимость"]
}
```

Physical говорит **где**, logical — **какая source cell/structure**.

---

# 41. Зачем representation SHA в observation pack

Если Markdown позже исправили, filename остался тем же. Без hash нельзя понять, валиден ли locator.

Поэтому Observation Pack должен быть привязан к конкретной версии representation.

Если SHA изменился:

```text
observation pack = stale until checked/rebuilt
```

---

# 42. Где заканчивается observation и начинается bridge

Простой тест:

- «что именно написал этот source?» → observation;
- «как это соответствует нашему устойчивому экономическому понятию?» → bridge.

Источник:

```text
Жилищные кредиты
```

это source context.

А:

```text
canonical product = MORTGAGE
```

это mapping.

---

# 43. IFRS Accounting Taxonomy: использовать как reference, а не как source replacement

По состоянию на reporting periods 2026 года актуальной остается IFRS Accounting Taxonomy 2025.

Она полезна как:

- reference vocabulary;
- источник standard concepts;
- потенциальный mapping target;
- модель fact/context/unit/dimensions.

Но нельзя предполагать:

```text
каждая строка каждого PDF
→ один IFRS taxonomy concept
```

Причины:

- issuer extensions;
- special-purpose reporting;
- incomplete public disclosure;
- aggregation;
- presentation choices;
- bank-specific structures;
- local disclosure restrictions.

Поэтому IFRS Taxonomy — bridge target, а не средство переписать source semantics.

---

# 44. Native XBRL/iXBRL/XLSX/CSV не надо заставлять идти через Markdown

Если source уже machine-readable:

```text
XBRL/iXBRL → сохранить native
XLSX → сохранить XLSX
CSV → сохранить CSV
XML → сохранить XML
```

Текущий `AGENTS.md` уже закрепляет этот принцип.

Observation layer должен унифицировать **доступ к фактам**, а не физический формат каждого source artifact.

---

# 45. W3C PROV полезен как conceptual model

Не нужно сейчас внедрять RDF/OWL, но модель хорошо ложится на Tabularium:

```text
PDF source              = entity
Markdown representation = entity
conversion              = activity
observation pack        = entity
extraction              = activity
derived metric          = entity
calculation             = activity
```

Так связь:

```text
observation
wasDerivedFrom
representation
```

становится естественной и проверяемой.

---

# 46. Что я бы не делал

## Не создавал `raw/clean/processed`

Слишком неоднозначно.

## Не переводил все таблицы в GFM

Красиво, но растет риск скрытой interpretation.

## Не исправлял source errors

Representation не должна лечить source.

## Не смешивал source observation и canonical metric

Нужен explicit mapping boundary.

## Не делал long CSV primary storage

CSV хорош как build artifact, но беден для provenance.

## Не делал Excel source of truth

Excel — view, не evidence store.

## Не начинал бы с универсальной банковской ontology

Сначала реальные source-bound observations.

---

# 47. Какой pilot выбрать

Нужны принципиально разные документы.

## A. `СБЕР_2026М6_МСФО.md`

- большой полный банковский report;
- сложные note tables;
- Q2 и 6M;
- consolidated perimeter.

## B. `ГАЗПРОМБАНК_2026М6_МСФО.md` или `УРАЛСИБ_2026М6_МСФО.md`

- special-purpose/disclosure-specific wording;
- сложные банковские tables;
- проверка того, что похожие строки не автоматически эквивалентны.

## C. `САМОЛЕТ_2026М6_МСФО.md`

- non-bank IFRS;
- другая структура statements и notes;
- защита от bank-only schema design.

## D. `МСПБАНК_2026М6_МСФО.md` или `ВБРР_2026М6_МСФО.md`

- компактное disclosure;
- native Markdown tables в нынешнем representation;
- проверка legacy-compatible parser.

---

# 48. Что извлекать в первом pilot

Не весь отчет.

Достаточно блоков:

```text
1. Statement of financial position
2. Income statement
3. Один сложный note
4. Один multi-level table
5. Один comparative/restated block
```

Цель pilot — проверить contract, а не получить максимальный coverage.

---

# 49. Observation Pack

Уже существующее исследование `_mw/research/01-base-ideas/tabularium_ifrs_observation_architecture.md` предлагает правильный direction:

```text
one report
→ one Observation Pack
```

Концептуально:

```text
REPORT/
    manifest.json
    observations.jsonl
```

## manifest

```json
{
  "report_id": "SBER_IFRS_2026M6",
  "source_path": ".../СБЕР_2026М6_МСФО.md",
  "source_representation_sha": "...",
  "schema_version": "obs-source-0.1",
  "extraction_status": "PARTIAL"
}
```

## observations.jsonl

Одна строка = одно observation.

Плюсы:

- git-readable;
- streaming;
- independent validation;
- простой concat;
- хороший diff;
- естественная JSON Schema validation.

---

# 50. Но Observation Pack не стоит молча добавлять в production corpus прямо сейчас

Текущий `AGENTS.md` формально описывает production corpus прежде всего как source artifacts и source-faithful representations.

Observation infrastructure пока является development proposal.

Поэтому корректная последовательность:

```text
prototype in _mw/development layer
→ validate semantics
→ decide production ownership
→ explicitly revise AGENTS/README contract
→ only then create production route
```

Это особенно важно, чтобы development research не превратился в архитектурную миграцию по инерции.

---

# 51. Pipeline, которую я считаю целевой

```text
[1] DISCOVER
primary publication found
        ↓
[2] ACQUIRE
download exact source bytes
        ↓
[3] IDENTIFY
URL / filename / SHA / retrieval time
        ↓
[4] REPRESENT
PDF → TMRP Markdown
        ↓
[5] VALIDATE
pages / text / numerics / structure
        ↓
[6] FREEZE
Git commit + representation hash
        ↓
[7] EXTRACT
source-bound observations
        ↓
[8] VALIDATE OBSERVATIONS
schema + locator + literal checks
        ↓
[9] MAP
construct / unit / dimensions
        ↓
[10] DERIVE
explicit formulas only
        ↓
[11] BUILD VIEWS
CSV / Parquet / Excel / Power BI / API
```

---

# 52. Authority каждого слоя

| Layer | Authority |
|---|---|
| Source artifact | publisher |
| Markdown representation | транскрипция Tabularium |
| Reported observation | факт конкретного source vintage |
| Mapping | versioned bridge registry |
| Derived metric | formula + inputs |
| Analytical claim | analysis over evidence chain |

Нижний слой никогда не должен переписывать верхний.

---

# 53. Главная инверсия: красивый Markdown не равен хорошей базе

Для будущей evidence database намного важнее:

```text
stable locator
+ provenance
+ observation schema
```

чем:

```text
pretty Markdown table
```

AI/parser может извлечь точный факт и из layout text, если знает page/row/column/unit/report hash.

И наоборот, идеально оформленная Markdown table без provenance остается слабым evidence object.

---

# 54. Не надо хранить два source representations одной таблицы

Плохая идея:

````markdown
```text
original layout
```

| normalized | table |
|---|---|
...
````

Проблемы:

- duplication;
- divergence;
- неясно, что authoritative;
- doubled diff;
- downstream может случайно читать не тот слой.

Лучше:

```text
canonical source representation
+
separate derived observation layer
```

Если нужен structural view, его можно генерировать как build artifact.

---

# 55. Что фактически должна давать единая representation форма

Не единый внешний вид, а API-подобный contract:

```text
document
contains ordered pages

each page
has stable marker

page content
is source literal

metadata
is outside source literal

editor annotations
are machine-distinguishable

representation
has profile version
```

Это реальная архитектурная ценность.

---

# 56. Что TMRP не должен обещать

Он не должен гарантировать:

```text
все tables семантически распознаны
все headings классифицированы
все footnotes связаны
все lines являются rows
все columns уже определены
```

Это следующий слой.

---

# 57. Сравнение вариантов

| Подход | Fidelity | Machine usability | Semantic risk | Cost | Вывод |
|---|---:|---:|---:|---:|---|
| Только PDF | максимальная визуальная | низкая | низкий | средняя | недостаточно |
| Fenced page transcript | высокая | высокая | низкий | низкая/средняя | **canonical baseline** |
| Все в GFM tables | средняя/высокая | высокая | **высокий** | высокая | не как universal canonical |
| Сразу long CSV | слабый provenance | высокая | очень высокий | средняя | нет |
| Сразу canonical metrics | низкая source fidelity | высокая | **очень высокий** | высокая | нет |
| TMRP + reported observations | **высокая** | **очень высокая** | контролируемый | средняя | **целевой вариант** |

---

# 58. Приоритеты дальнейшей работы

## Приоритет 1 — semantics уровней

```text
source
representation
observation
bridge
derivation
claim
```

## Приоритет 2 — TMRP-1

Небольшой, строгий specification.

## Приоритет 3 — provenance

Особенно:

```text
source SHA
source URL
source filename
page count
representation version
```

## Приоритет 4 — validator

Без него standard останется инструкцией.

## Приоритет 5 — Observation pilot

Здесь появляется настоящая value.

## Приоритет 6 — mapping registry

После source observations.

## Приоритет 7 — derived metrics и analytical views

Последними.

---

# 59. Что делать прямо с текущими 103 файлами

Не запускать массовую перепаковку.

Сначала:

```text
1. inventory
2. representation classification
3. compatibility linter
4. source provenance gaps
5. observation pilot
```

Inventory может автоматически фиксировать:

```text
file
page marker style
fence style
native Markdown headings/tables
page count
file size
encoding
provenance present/missing
```

---

# 60. Compatibility parser

Он должен понимать нынешние variants:

```text
<!-- PAGE 1 -->
<!-- PAGE 1 / 64 -->

```text
...
```

~~~text
...
~~~

native Markdown page
```

Новый стандарт не должен требовать миграции legacy corpus до того, как observation extraction вообще начнет работать.

---

# 61. Когда применять новый profile

Ко всем **новым** PDF после принятия TMRP-1.

Это остановит рост неоднородности.

Legacy corpus можно исправлять opportunistically — при повторном использовании, выявленной ошибке или реальной несовместимости.

---

# 62. Не нужны line-level anchors в каждом Markdown прямо сейчас

Например:

```html
<!-- OBS-ANCHOR:p005:r017 -->
```

на каждой строке засорит evidence-layer.

Пока лучше:

```text
representation SHA
+ page
+ page-local line/character range
+ logical row/column path
```

Если практика покажет, что этого недостаточно, anchor layer можно добавить позже.

---

# 63. Physical PDF page и printed page label нужно различать

Printed page number внутри документа может не совпадать с physical PDF index.

Поэтому `<!-- PAGE N -->` лучше трактовать как физический порядок PDF representation.

Printed page number остается literal source content.

---

# 64. Reporting perimeter не надо слишком рано нормализовать

Источник может писать:

```text
ПАО «...» и его дочерние организации
```

Это perimeter literal.

Bridge позднее может связать его с устойчивым ID группы. Но исходная формулировка должна сохраняться и быть доступна каждому observation.

---

# 65. Special-purpose/disclosure-limited reports требуют особой дисциплины

Если source прямо говорит, что отчетность подготовлена для раскрытия в специальном режиме, это часть identity источника.

Нельзя интерпретировать отсутствие строки как обычное отсутствие IFRS disclosure.

Coverage/completeness должны учитывать nature конкретного source artifact.

---

# 66. Investor presentations — отдельный source artifact

Презентация может содержать:

- adjusted metrics;
- management KPIs;
- rounded values;
- alternative performance measures.

Даже если относится к тому же reporting release:

```text
financial-statement observation
≠ presentation observation
```

Их можно связать на уровне issue/release, но нельзя смешивать без source artifact identity.

---

# 67. Construct ontology нельзя решать через Markdown

Вопрос:

> «кредитный портфель» банка A эквивалентен «кредитам клиентам» банка B?

не относится к representation-layer.

Markdown обязан только гарантировать, что обе source formulations сохранены. Эквивалентность — отдельный bridge.

---

# 68. Роль IFRS taxonomy в будущей архитектуре

Хорошая цепочка:

```text
Source observation
    ↓
issuer-specific mapping
    ↓
IFRS taxonomy concept (where justified)
    ↓
Tabularium analytical construct (where needed)
```

Mapping может быть:

```text
EXACT
CLOSE
BROADER
NARROWER
CONFLICT
UNKNOWN
```

UNKNOWN — нормальное состояние, а не ошибка системы.

---

# 69. Ценность source observations появляется еще до canonical mapping

Уже можно задавать запросы:

```text
покажи все опубликованные значения,
где source label содержит "ипотеч",
по состоянию на 30 июня 2026,
с source locator
```

Это огромная ценность даже без единого universal metric catalog.

После bridge layer можно уже фильтровать только `EXACT` mappings или сознательно включать `CLOSE` с показом различий.

---

# 70. Ответ на вопрос «representation или сразу facts»

**Не выбирать между ними.**

Нужен короткий stabilization pass representation-layer, после чего основное усилие переносится на reported observations.

По смыслу распределение усилий должно быть таким:

```text
небольшая часть — representation contract
основная часть — observation model + extraction + provenance
минимум — cosmetic backfill
```

Чем глубже проект уходит в идеальную верстку, тем быстрее падает отдача.

---

# 71. Конкретный следующий маршрут

## Фаза A — Representation Contract

Оформить `Tabularium Markdown Representation Profile v1` в development-layer.

Он должен описывать:

- metadata;
- pages;
- fences;
- whitespace;
- numeric fidelity;
- annotations;
- legacy compatibility;
- validation.

## Фаза B — Inventory + linter

Не менять файлы. Сначала классифицировать.

Выход:

```text
file
profile
pages
syntax
warnings
```

## Фаза C — Observation pilot

На:

```text
СБЕР_2026М6
ГАЗПРОМБАНК_2026М6 или УРАЛСИБ_2026М6
САМОЛЕТ_2026М6
МСПБАНК_2026М6
```

## Фаза D — Source observation schema v0.1

Без canonical metrics.

## Фаза E — Mapping experiment

Только после устойчивого extraction.

## Фаза F — Production contract adoption

Если pilot работает:

- минимально изменить `AGENTS.md`;
- дополнить `ifrs/README.md`;
- определить production ownership observations;
- version schemas.

---

# 72. Что не нужно делать следующим шагом

Не нужно прямо сейчас:

```text
переконвертировать все 103 файла
перерисовать все таблицы
строить universal bank ontology
строить graph database
создавать десятки пустых directories
писать огромный canonical metric catalog
строить global Power BI stream
```

Все это либо преждевременно, либо зависит от Observation Layer.

---

# 73. Самая сильная часть нынешнего corpus уже существует

Текущий паттерн:

````markdown
<!-- PAGE N -->

```text
...
```
````

я считаю хорошей основой canonical PDF representation.

То есть проект уже находится близко к правильной форме. Задача — не заменить ее, а **формализовать, провенансировать и валидировать**.

---

# 74. Если выбирать только одно улучшение перед observations

Я бы выбрал:

> **source provenance + representation version/hash discipline.**

Без нее downstream fact может быть отлично структурирован, но его связь с конкретной source version останется слабой.

Второе по важности:

> **observation locator.**

Третье:

> **literal никогда не исчезает после parsed/canonical form.**

`"49 975,0"` должен оставаться доступен после появления `49975.0`.

`"в миллиардах российских рублей"` должен оставаться доступен после появления `RUB_BILLION`.

---

# 75. Критерии качества слоев

## Representation-layer

Не «все ли файлы одинаково выглядят», а:

> может ли машина однозначно и воспроизводимо вернуться от observation к месту в опубликованном документе?

## Observation-layer

Не «сколько фактов извлечено», а:

> какая доля имеет однозначный locator, literal value, context, unit, period и status без скрытых semantic assumptions?

## Bridge-layer

Не «заполнен ли общий Excel», а:

> каждое сопоставление имеет явное основание, версию и право остаться UNKNOWN?

---

# 76. Компактный contract TMRP-1

```text
1. PDF publication is represented as UTF-8 Markdown.
2. Every source page has one explicit page marker.
3. Canonical new files use one literal text fence per page.
4. Source-visible text and numeric literals are preserved.
5. No economic normalization occurs in representation.
6. Project metadata is outside source-content blocks.
7. Project annotations are machine-distinguishable.
8. Source identity should include URL/filename/hash when available.
9. Representation profile is versioned.
10. Legacy faithful files remain readable without mandatory migration.
11. Any backfill is revalidated against the primary source.
12. Representation changes invalidate dependent observations until checked.
```

---

# 77. Компактный contract source observation v0.1

Минимально:

```text
observation_id
source_report_id
source_representation_sha

locator.page
locator.row_path_literal
locator.column_path_literal

reported.value_literal
reported.unit_literal
reported.label_literal

status
```

Опционально:

```text
note_literal
table_literal
footnote_literal
period_literal
typed_value
parse_rule
```

Пока не делать обязательными:

```text
canonical_metric_id
canonical_unit
canonical_dimensions
peer_group
analytical_category
```

---

# 78. Форматы по слоям

| Layer | Формат |
|---|---|
| PDF representation | Markdown |
| Native XLSX/CSV/XML/XBRL | исходный формат |
| Observation pack | JSONL |
| Schema | JSON Schema |
| Registries | JSON/YAML/CSV по потребности |
| Derived stream | Parquet/CSV |
| Research notes | Markdown |
| Human workbook | XLSX |
| BI/API views | build artifacts |

Не нужно заставлять один формат выполнять все роли.

---

# 79. Целевая архитектура

```text
                    ┌─────────────────────┐
                    │  PRIMARY PUBLISHER  │
                    │ PDF / XBRL / XLSX   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ SOURCE IDENTITY     │
                    │ URL / SHA / vintage │
                    └──────────┬──────────┘
                               │
                               ▼
                 ┌──────────────────────────┐
                 │ SOURCE REPRESENTATION    │
                 │ TMRP Markdown for PDF    │
                 │ native format otherwise  │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ REPORTED OBSERVATIONS    │
                 │ literal/source-bound     │
                 │ page/row/column locator  │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ BRIDGE / MAPPING         │
                 │ construct / unit / dims  │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ DERIVED OBSERVATIONS     │
                 │ formula + provenance     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ ANALYTICAL VIEWS/CLAIMS  │
                 └──────────────────────────┘
```

---

# 80. Главный asset Tabularium в будущем

Не сами Markdown-файлы и не одна огромная таблица.

Главным asset станет способность разрешить любой используемый факт назад:

```text
claim
→ derivation
→ bridge
→ observation
→ representation
→ source
```

Если эта цепочка работает, архитектура хорошая.

---

# 81. Окончательная рекомендация

1. **Не создавать новый `raw/` каталог.** Текущий Markdown уже является representation-layer.
2. **Формализовать page-oriented fenced-text style как default для новых PDF.**
3. **Не заставлять legacy faithful files немедленно мигрировать.**
4. **Добавить provenance contract:** URL, filename, source SHA-256, page count, representation version.
5. **Сделать linter до массового backfill.**
6. **После этого сразу запустить Observation Pack pilot.**
7. **Первый observation schema делать source-bound, а не canonical-metric-first.**
8. **Literal source values сохранять навсегда рядом с parsed representations.**
9. **Mapping/constructs вынести в отдельный bridge-layer.**
10. **IFRS Taxonomy использовать как reference/mapping target, а не replacement source semantics.**
11. **Native XBRL/XLSX/CSV не конвертировать в Markdown только ради единообразия.**
12. **Derived calculations и analytical claims держать явно ниже evidence-layer.**

Главный ответ в одной фразе:

> **Tabularium сейчас не нужно «очищать» перед извлечением фактов: ему нужно зафиксировать тонкий почти-lossless контракт представления, а затем как можно быстрее перейти к source-bound observations; именно observations, а не идеальная Markdown-верстка, должны стать следующим крупным шагом проекта.**

---

# Приложение A. Минимальный пример TMRP-1

````markdown
---
tabularium_representation_profile: "tmrp-1"
source_media_type: "application/pdf"
source_file_name: "example.pdf"
source_url: null
source_sha256: null
source_page_count: 2
representation:
  method: "pdf-text-layer-assisted"
  review_status: "unreviewed"
---

<!-- PAGE 1 -->

```text
ПАО «Пример»

Промежуточная консолидированная финансовая отчетность

30 июня 2026 года
```

<!-- PAGE 2 -->

```text
Отчет о финансовом положении

в миллионах российских рублей

                            30 июня 2026   31 декабря 2025
Денежные средства                  1 000                900
Кредиты клиентам                   5 000              4 500
```
````

Здесь нет аналитического решения о том, что означает `Кредиты клиентам`. Но source уже пригоден для следующего слоя.

---

# Приложение B. Минимальный source observation

```json
{
  "observation_id": "example:2026m6:p2:loans:20260630",
  "source_report_id": "EXAMPLE_IFRS_2026M6",
  "source_representation_sha": "sha...",
  "locator": {
    "page": 2,
    "row_path_literal": ["Кредиты клиентам"],
    "column_path_literal": ["30 июня 2026"]
  },
  "reported": {
    "label_literal": "Кредиты клиентам",
    "value_literal": "5 000",
    "unit_literal": "в миллионах российских рублей"
  },
  "status": "REPORTED"
}
```

---

# Приложение C. Следующий bridge

```json
{
  "source_observation_id": "example:2026m6:p2:loans:20260630",
  "mapping_rule_id": "EXAMPLE-LOANS-001-v1",
  "mapping_status": "EXACT",
  "construct_id": "CUSTOMER_LOANS",
  "canonical_dimensions": {
    "measurement_scope": "..."
  }
}
```

Это уже не source observation, а explicit bridge.

---

# Приложение D. Материалы исследования

## Актуальный контракт и текущий corpus

Проверены:

- `README.md`
- `AGENTS.md`
- `NOTICE.md`
- `russia/corporate-disclosures/README.md`
- `russia/corporate-disclosures/financial-reporting/README.md`
- `russia/corporate-disclosures/financial-reporting/ifrs/README.md`

Реальные документы, использованные для проверки representation variants:

- `СБЕР_2026М6_МСФО.md`
- `ГАЗПРОМБАНК_2026М6_МСФО.md`
- `САМОЛЕТ_2026М6_МСФО.md`
- `МСПБАНК_2026М6_МСФО.md`
- `ВБРР_2026М6_МСФО.md`
- `УРАЛСИБ_2026М6_МСФО.md`

Development-layer research:

- `_mw/research/01-base-ideas/tabularium_ifrs_observation_architecture.md`
- `_mw/research/01-base-ideas/tabularium_cognitive_database_research.md`

Они использованы как research input, а не как production contract.

## Внешние reference models

- IFRS Foundation — IFRS Accounting Taxonomy; для reporting periods 2026 года продолжает использоваться IFRS Accounting Taxonomy 2025.
- XBRL International — XBRL / Inline XBRL specifications.
- W3C — PROV family of specifications.
- CommonMark — fenced code block semantics.
- GitHub Flavored Markdown — table extension.

---

# Приложение E. Короткий decision record

**Решение:** page-oriented source-faithful Markdown — baseline representation для PDF.  
**Не принимать:** обязательную семантическую GFM-нормализацию всех таблиц.  
**Следующий development target:** reported Observation Pack.  
**Backfill:** selective, source-verified, не косметический.  
**Canonical analytical stream:** build artifact поверх observations/bridges.  
**Граница evidence-layer:** source + representation + source-bound observations.  
**Граница analytical layer:** mapping, derivations и claims — явно отделены и трассируемы.
