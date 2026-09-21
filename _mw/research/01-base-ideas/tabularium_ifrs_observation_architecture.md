# Архитектура квартальной МСФО-рабочей книги: Observation Pack → поток → представления

## 1. Ключевой вывод

Не следует строить прямой конвейер:

```text
МСФО → Excel
```

и даже:

```text
МСФО → long CSV
```

Более устойчивой является трёх- и фактически пятислойная архитектура:

```text
МСФО в Tabularium
→ пакет атомарных наблюдений конкретного отчёта
→ реестр и mapping
→ детерминированный long stream
→ производные представления / Excel / Power BI / Python
```

Главный принцип:

> потоковая grid-таблица не должна быть первичным продуктом ИИ. Она должна автоматически собираться из более атомарного машиночитаемого слоя.

Это снижает риск тихих семантических ошибок и разделяет:
- извлечение из источника;
- интерпретацию;
- унификацию;
- сборку данных;
- аналитическое представление.

---

## 2. Почему прямой переход `МСФО → long table` опасен

Строка длинной таблицы может выглядеть просто:

| entity | metric | date | value |
|---|---|---|---:|
| SBER | retail_mortgage_loans | 2026-06-30 | 10 500 |

Но за этой строкой скрыты решения:

- группа это или отдельный банк;
- gross или net;
- амортизированная стоимость или весь портфель;
- значение на дату или поток за период;
- исходная единица;
- текущий период или comparative;
- reported или derived;
- из какой страницы, примечания, строки и колонки взято значение;
- напрямую ли сообщено значение или собрано из компонентов.

Если ИИ одновременно должен:
1. извлечь число;
2. понять семантику;
3. привести к общему словарю;
4. определить периметр;
5. сформировать ряд;
6. положить всё в общую БД,

то наиболее опасными становятся не числовые, а семантические ошибки.

Поэтому нужен самостоятельный слой между source и stream.

---

# 3. Observation Pack

Предлагаемый базовый объект:

> **один МСФО-материал → один пакет наблюдений**

Например:

```text
SBER_2026M6_IFRS/
    manifest.json
    observations.jsonl
```

В более развитой версии:

```text
SBER_2026M6_IFRS/
    manifest.json
    observations.jsonl
    coverage.jsonl
```

`observations.jsonl` содержит только то, что извлечено из конкретного источника.

Он не должен:
- содержать остальные банки;
- строить peer comparison;
- считать темпы роста;
- формировать Excel;
- нормализовать весь банковский сектор;
- производить аналитические выводы.

ИИ получает ограниченную задачу:

> для одного отчёта выписать атомарные наблюдения по фиксированному контракту.

---

# 4. Почему JSONL

Для канонического Observation Pack оптимален JSON Lines.

Каждая строка является самостоятельным JSON-объектом.

Это позволяет:

- валидировать каждую запись независимо;
- локализовать ошибку;
- добавлять данные блоками;
- объединять файлы простой конкатенацией;
- удобно читать данные построчно в Python;
- не ломать весь файл одной синтаксической ошибкой в конце.

Рекомендуемое разделение форматов:

| Формат | Роль |
|---|---|
| Markdown | первичный source-faithful Tabularium |
| JSONL | канонический машинный Observation Pack |
| JSON Schema | формальный контракт записи |
| CSV | экспорт long table |
| Parquet | быстрый аналитический кэш |
| XLSX | человеческая рабочая книга |
| Pivot / сводные | представления |

YAML удобен для небольших реестров и mapping rules, но менее предпочтителен как массовый production-формат наблюдений.

CSV слишком беден для первичного слоя, поскольку provenance, source path и измерения требуют вложенной структуры.

Parquet удобен для аналитики, но бинарный формат не подходит как основной Git-readable source of truth.

---

# 5. Одновременно сохранять source и canonical

Нельзя хранить только:

```json
{
  "metric_id": "retail_mortgage_loans",
  "value": 100
}
```

Это слишком далеко от источника.

Запись должна сохранять две связанные части:

```text
SOURCE OBSERVATION
        ↓ explicit binding
CANONICAL OBSERVATION
```

Концептуальный пример:

```json
{
  "observation_id": "obs_...",

  "source_report_id": "SBER_IFRS_2026M6",

  "source": {
    "page": 18,
    "note": "4",
    "table": "Кредиты и авансы клиентам",
    "row_path": [
      "Физические лица",
      "Жилищные кредиты"
    ],
    "column_path": [
      "30 июня 2026",
      "Валовая балансовая стоимость"
    ],
    "reported_label": "Жилищные кредиты",
    "value_literal": "7 123 456",
    "unit_literal": "млн руб."
  },

  "observation": {
    "period_kind": "instant",
    "period_end": "2026-06-30",
    "numeric_value": 7123456,
    "value_status": "REPORTED"
  },

  "binding": {
    "metric_id": "LOAN.RETAIL.MORTGAGE",
    "gross_net": "GROSS",
    "measurement": "AMORTIZED_COST",
    "stage": "ALL",
    "mapping_status": "EXACT",
    "mapping_rule_id": "SBER-LOANS-017"
  }
}
```

Смысл:

- `source` отвечает на вопрос: **что именно было опубликовано**;
- `observation` фиксирует само наблюдаемое значение;
- `binding` отвечает на вопрос: **как это наблюдение связано с нашей системой показателей**.

Это соответствует цепочке:

```text
source
→ representation
→ observation
→ bridge
→ analytical claim
```

---

# 6. Source locator должен быть точным

Одной страницы недостаточно.

Для таблицы:

|  | Stage 1 | Stage 2 | Stage 3 | Итого |
|---|---:|---:|---:|---:|
| Ипотека | … | … | … | … |
| Потребительские | … | … | … | … |

одно значение должно разрешаться примерно так:

```text
page = 21
note = 4
table = credit quality
row_path = retail / mortgage
column_path = stage 2 / gross
```

Это позволяет однозначно вернуть observation к исходной клетке.

Простая ссылка вроде:

```text
см. примечание 4
```

для такого слоя недостаточна.

---

# 7. Extraction unit должен быть ограниченным

Даже JSONL не решит проблему, если дать ИИ задачу:

> обработай 100 страниц и выдай 900 observations.

Надёжнее работать блоками:

```text
отчёт
↓
примечание
↓
таблица / логический блок
↓
атомарные observations
```

Например:

1. Statement of financial position;
2. Note 4 — Loans — composition;
3. Note 4 — Loans — Stage 1/2/3;
4. Note 4 — Loans — sector structure;
5. Note 7 — Customer funds;
6. и т.д.

Каждый блок можно валидировать отдельно.

После этого JSONL-файлы объединяются детерминированно.

---

# 8. JSON Schema как обязательный контракт

Для Observation Pack необходим строгий schema-layer.

Например:

```text
schemas/
    observation.schema.json
    manifest.schema.json
```

JSON Schema должен фиксировать:

- обязательные поля;
- типы;
- разрешённые enum;
- формат дат;
- допустимые статусы;
- структуру source locator;
- структуру period;
- допустимое устройство binding;
- правила для reported / derived / missing.

Например, невозможно будет случайно записать:

```text
status = "probably missing"
```

если допустимы только:

```text
REPORTED
EXPLICIT_ZERO
EXPLICIT_UNDISCLOSED
NOT_APPLICABLE
UNKNOWN
```

Это снижает энтропию машинного слоя.

---

# 9. Mapping registry

ИИ не должен каждый квартал заново решать:

> строка «Жилищные кредиты» соответствует нашему `LOAN.RETAIL.MORTGAGE` или нет?

Большая часть банковской отчётности достаточно устойчива.

Поэтому нужен отдельный mapping registry.

Пример:

```text
SBER
Note 4
"Жилищные кредиты"
+
gross carrying amount
→
LOAN.RETAIL.MORTGAGE
gross_net = GROSS
```

Правило получает стабильный ID:

```text
SBER-LOANS-017
```

В следующем квартале ИИ не изобретает mapping, а применяет существующее правило.

Если раскрытие изменилось:

```text
MAPPING_NOT_RESOLVED
```

и изменение уходит на отдельную проверку.

---

# 10. Mapping должен версионироваться

Экономический показатель должен быть устойчивым:

```text
metric_id = LOAN.RETAIL.MORTGAGE
```

Mapping может меняться:

```text
SBER-LOANS-017-v1
valid_to = 2027-12-31
```

и затем:

```text
SBER-LOANS-017-v2
valid_from = 2028-01-01
```

Это соответствует принципу:

> стабильной должна быть экономическая конструкция, а связь с конкретной версией формы/раскрытия должна иметь свою версию.

---

# 11. Long stream не редактируется вручную

Глобальная потоковая таблица должна быть исключительно build artifact.

Пример полей:

| observation_id | entity | perimeter | metric_id | period | basis | dimensions | value | unit | status | report | locator |
|---|---|---|---|---|---|---|---|---:|---|---|---|---|

Но человек или ИИ не должен заполнять её напрямую.

Python делает:

```text
find all observations.jsonl
→ validate
→ concatenate
→ resolve registries
→ flatten canonical dimensions
→ create long table
```

Если long table удалена, она просто пересобирается.

---

# 12. Observation period и source vintage — разные оси

Это обязательно надо заложить сразу.

Предположим, отчёт 6М2026 сообщает comparative:

```text
31.12.2025 = 80
```

а первоначальная отчётность FY2025 сообщала:

```text
31.12.2025 = 79
```

Возможно, значение было реклассифицировано.

Нельзя иметь ключ:

```text
entity + metric + 2025-12-31
```

иначе одно значение затрёт другое.

Нужны как минимум:

```text
observation_period = 2025-12-31
source_vintage = SBER_IFRS_2025M12
```

и:

```text
observation_period = 2025-12-31
source_vintage = SBER_IFRS_2026M6
```

Это два разных наблюдения одного экономического периода.

После этого можно строить представления:

- as originally reported;
- latest restated vintage.

---

# 13. Периоды потоков

Для flow-показателей одной даты недостаточно.

Нужно различать:

```text
Q2
6M YTD
derived Q2 = 6M - 3M
```

Поэтому period object должен содержать:

```text
period_kind
period_start
period_end
period_basis
```

Например:

```text
period_kind = duration
period_start = 2026-01-01
period_end = 2026-06-30
period_basis = YTD
```

и отдельно:

```text
period_kind = duration
period_start = 2026-04-01
period_end = 2026-06-30
period_basis = QUARTER
```

Если квартал рассчитан как разность накопленных периодов:

```text
observation_class = DERIVED
formula_id = YTD_DIFFERENCE
```

и он уже не относится к source observations.

---

# 14. Статусы отсутствия

Excel может визуально показывать крестик.

Но в машинном слое крестик не должен существовать как семантика.

Нужно различать:

| Машинное состояние | Смысл | Excel |
|---|---|---|
| `REPORTED` | источник дал значение | число |
| `EXPLICIT_ZERO` | источник сообщил 0 | 0 |
| `EXPLICIT_UNDISCLOSED` | источник явно скрыл значение | × |
| `NOT_APPLICABLE` | показатель неприменим | × |
| `UNKNOWN` | значение/семантика неразрешимы | × / контроль |
| `NOT_OBSERVED` | в полном обработанном отчёте наблюдение отсутствует | × |
| пакет не завершён | мы ещё не знаем | пусто |

Ключевой принцип:

> отсутствие записи в JSONL само по себе не означает отсутствия раскрытия.

Чтобы автоматически ставить `×`, система должна знать:

```text
extraction_status = COMPLETE
```

для соответствующего отчёта.

---

# 15. Manifest

Каждый Observation Pack должен иметь `manifest.json`.

Концептуально:

```json
{
  "report_id": "SBER_IFRS_2026M6",
  "source_path": ".../СБЕР_2026М6_МСФО.md",

  "entity_id": "SBER",
  "perimeter_id": "SBER_GROUP",

  "reporting_date": "2026-06-30",
  "report_type": "IFRS_INTERIM",

  "source_commit": "...",
  "source_sha": "...",

  "schema_version": "OBS-001",
  "mapping_version": "...",

  "extraction_status": "COMPLETE"
}
```

Особенно важен `source_sha`.

Если исходная Markdown-транскрипция изменилась, система может автоматически определить:

```text
source SHA changed
```

и потребовать повторную проверку extraction pack.

---

# 16. Уровень атомарности

Оптимальный уровень атомарности:

> одна опубликованная величина = одно observation.

Например:

|  | Stage 1 | Stage 2 | Stage 3 |
|---|---:|---:|---:|
| Ипотека | 100 | 10 | 5 |

превращается в три наблюдения:

```text
mortgage / stage1 = 100
mortgage / stage2 = 10
mortgage / stage3 = 5
```

Но при этом сохраняется исходная иерархия строки и колонки.

Не стоит упаковывать всё в один объект:

```text
Mortgage = {100, 10, 5}
```

потому что тогда атомарность теряется.

---

# 17. Sparse dimensions

Не следует проектировать long stream с десятками обязательных dimension columns.

Лучше хранить sparse dimensions:

```json
"dimensions": {
  "client_type": "RETAIL",
  "product": "MORTGAGE",
  "stage": "STAGE_2"
}
```

Для другого наблюдения:

```json
"dimensions": {
  "client_type": "CORPORATE",
  "industry": "AGRICULTURE",
  "currency": "RUB"
}
```

Это позволяет моделировать настоящий многомерный куб без тысяч пустых полей.

Compiler при необходимости разворачивает зарегистрированные dimensions в столбцы.

---

# 18. Source dimensions и canonical dimensions

Для сохранения source-faithful semantics полезно разделять:

```text
source_dimensions
```

и:

```text
canonical_dimensions
```

Например источник пишет:

> «Жилищные кредиты физическим лицам»

Тогда:

```text
source_dimensions:
    client_category = "Физические лица"
    product_category = "Жилищные кредиты"
```

а mapping создаёт:

```text
canonical_dimensions:
    client_type = RETAIL
    product = MORTGAGE
```

Если классификация позже изменится, можно перемаппировать корпус без повторного извлечения PDF/Markdown.

---

# 19. Пять самостоятельных уровней

Архитектура:

## A. Source corpus

Tabularium Markdown.

## B. Observation Pack

То, что конкретно было опубликовано в конкретном отчёте.

## C. Registry / Mapping

Связь source observations с устойчивым словарём.

## D. Observation Stream

Единая длинная таблица по всем объектам и периодам.

## E. Views

- Excel;
- pivot;
- презентационные таблицы;
- Power BI;
- Python;
- аналитические расчёты.

D и E должны быть полностью пересобираемыми.

A–C являются воспроизводимой основой.

---

# 20. Где физически хранить observation layer

Текущий контракт Tabularium определяет основной corpus как source-faithful первичные публикации.

Поэтому без отдельного архитектурного решения не следует складывать `observations.jsonl` прямо рядом с:

```text
СБЕР_2026М6_МСФО.md
```

Это фактически изменило бы контракт corpus.

`_mw` тоже не должен автоматически становиться постоянным product-layer: сейчас это workspace исследований и разработки.

Для первой версии более безопасен отдельный downstream-репозиторий, условно:

```text
ForestTiger-GH/tabularium-banking-observations
```

или:

```text
ForestTiger-GH/banking-ifrs-workbook
```

Пример структуры:

```text
schemas/
    observation.schema.json
    manifest.schema.json

registry/
    entities.yaml
    metrics.yaml
    dimensions.yaml
    statuses.yaml

mappings/
    sber.yaml
    vtb.yaml
    gazprombank.yaml
    ...

packs/
    2026/
        SBER_2026M3/
            manifest.json
            observations.jsonl
        SBER_2026M6/
            manifest.json
            observations.jsonl
        VTB_2026M6/
            ...

build/
    build_long.py
    validate.py
    build_workbook.py

dist/
    observations.csv
    observations.parquet
    banking_ifrs_workbook.xlsx
```

`dist/` может вообще не быть каноническим и пересобираться автоматически.

---

# 21. Google Colab

Google Colab в такой архитектуре не должен понимать бухгалтерский текст.

Его роль:

```text
git clone
↓
scan packs/**/observations.jsonl
↓
JSON Schema validation
↓
pandas.concat
↓
mapping validation
↓
long dataframe
↓
pivot_table
↓
xlsx
```

То есть Colab становится компилятором, а не аналитиком.

---

# 22. Excel как производное представление

В Excel может существовать лист:

```text
DATA
```

с длинным потоком.

Поверх него:

- Кредиты;
- Средства;
- Баланс;
- Доходы;
- Риск;
- Капитал;
- Ликвидность;
- Внебаланс;
- специальные KPI.

Эти листы могут строиться:

- сводными таблицами;
- формулами;
- Python-генерацией;
- Power Query;
- отдельным build script.

Если другой департамент дальше ведёт Excel вручную, его книгу можно сравнивать с regenerated workbook, собранным из observation layer.

---

# 23. Двухступенчатая проверка

Вместо:

```text
PDF/MD ↔ огромный Excel
```

получаем:

```text
МСФО ↔ Observation Pack
```

Это проверка extraction.

И отдельно:

```text
Observation Pack
→ stream
→ workbook
```

Это детерминированный программный pipeline.

Во второй части ИИ не нужен.

Если там появляется ошибка, это обычная программная ошибка, которую можно исправить один раз.

---

# 24. Как должен работать следующий квартал

Для нового отчёта ИИ получает:

```text
новый МСФО
+
предыдущий Observation Pack
+
действующий mapping данного банка
```

Задача:

> извлечь новый период по действующему контракту; использовать существующие mappings; отдельно перечислить новые, исчезнувшие или изменившиеся раскрытия.

Это гораздо надёжнее, чем каждый квартал заново интерпретировать банк с нуля.

---

# 25. Долгосрочный эффект

После нескольких кварталов появится архив:

```text
2026Q1 packs
2026Q2 packs
2026Q3 packs
...
2028Q4 packs
```

Один observation layer сможет использоваться для:

- Excel;
- Python;
- Power BI;
- графиков;
- презентаций;
- автоматических проверок;
- peer-анализа;
- прогнозных моделей;
- ИИ-агентов.

Любое аналитическое значение сможет разрешаться обратно:

```text
аналитическая цифра
→ stream row
→ observation
→ source row / source column
→ page
→ конкретный IFRS Markdown
```

---

# 26. Итоговая рекомендуемая архитектура

```text
Tabularium IFRS Markdown
        ↓
source-bound JSONL Observation Pack
        ↓
versioned registries + mapping
        ↓
validated canonical observation stream
        ↓
derived calculations
        ↓
Excel / pivot / Power BI / Python / presentation tables
```

Каноническими поддерживаемыми объектами должны быть:

1. Observation Packs;
2. entity registry;
3. metric registry;
4. dimension registry;
5. status registry;
6. mapping rules;
7. JSON Schema;
8. build scripts.

А:

- long CSV;
- Parquet;
- Excel;
- сводные;
- аналитические таблицы

следует рассматривать как производные сборочные продукты.

---

# 27. Следующий архитектурный шаг

До проектирования финального Excel имеет смысл взять три принципиально разных объекта, например:

- Сбер;
- Банк ДОМ.РФ;
- Т-Технологии / Т-Банк;

и на реальных МСФО 6М2026 спроектировать первую версию:

```text
OBS-001
```

То есть определить точный контракт одной observation:

- identity;
- source report;
- source locator;
- entity;
- perimeter;
- value literal;
- numeric value;
- unit;
- status;
- period;
- source vintage;
- source dimensions;
- canonical dimensions;
- mapping status;
- mapping rule;
- schema version;
- uncertainty / unresolved state.

Если три столь разных типа отчётности укладываются в один контракт без насилия над source semantics, такой слой, вероятно, сможет стать устойчивым основанием всей банковской МСФО-рабочей книги.
