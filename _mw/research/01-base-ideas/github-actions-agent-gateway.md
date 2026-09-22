# GitHub Actions как сенсорный слой и шлюз для агентной исследовательской системы

GitHub Actions можно рассматривать не просто как CI/CD или «бесплатный cron», а как постоянно работающий сенсорный слой вокруг исследовательских репозиториев.

Его сильная сторона — регулярно превращать нестабильный внешний интернет в стабильные, адресуемые и версионируемые факты, которые затем могут читать агенты без повторного поиска.

В пределе архитектура может выглядеть так:

```text
                ВНЕШНИЙ ИНТЕРНЕТ
                       │
        ┌──────────────┼──────────────┐
        │              │              │
       ЦБ            MOEX          сайты СМИ
        │              │              │
        └──────────────┼──────────────┘
                       ▼
               GitHub Actions
           discovery / fetch / diff
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        raw evidence        event / inbox
             │                   │
             │                   ▼
             │                 АГЕНТ
             │           classify / extract
             │                   │
             └──────────┬────────┘
                        ▼
                    Tabularium
                        │
              source observations
                        │
                        ▼
                derivation layer
                        │
                        ▼
                     АГЕНТЫ
```

## 1. Почему это сильнее, чем агенту каждый раз самому искать в интернете

Обычная исследовательская работа агента часто выглядит так:

```text
получить задачу
→ понять, где искать
→ найти сайт
→ найти нужную страницу
→ скачать файл
→ понять структуру
→ проверить дату
→ возможно снова найти то же самое
→ только потом анализировать
```

Если Actions заранее выполняет первые шаги, агент начинает уже с:

```text
открыть GitHub
→ profiles / catalog / inbox
→ взять уже найденный source
→ работать
```

GitHub становится своего рода памятью внешнего мира:

```text
URL когда-то существовал
+ вот когда мы его увидели
+ вот что он тогда отдавал
+ вот SHA-256
+ вот HTTP metadata
+ вот какой release это был
+ вот что изменилось с прошлого наблюдения
```

Особенно хорошо это сочетается с эпистемической цепочкой:

```text
source
→ representation
→ observation
→ derivation / bridge
→ analytical claim
```

GitHub Actions особенно полезен на первых трёх уровнях.

## 2. «Умный поиск» в первую очередь не требует ИИ

Самый надёжный интеллект для автоматического сбора — часто не LLM, а набор детерминированных методов.

Можно искать не сам документ, а сигнал изменения:

```text
RSS / Atom
sitemap.xml
release calendar
API updated_time
ETag
Last-Modified
список ссылок на странице
новый идентификатор публикации
новое имя файла
изменение content hash
```

Только если сигнал изменился, выполняется загрузка:

```text
скачать source
→ проверить
→ сохранить
```

Например:

```text
09:00
Actions получает список пресс-релизов MOEX

старый набор:
A
B
C

новый:
A
B
C
D

→ fetch только D
```

Если на следующем запуске список не изменился, новых файлов и commits не появляется.

## 3. Fingerprinting

Для страницы или файла можно рассчитывать несколько отпечатков:

```text
raw_sha256
normalized_html_sha256
main_content_sha256
link_set_sha256
```

Это позволяет отличать технические изменения страницы от смысловых.

Например:

```text
raw HTML changed       = yes
main content changed   = no
```

может означать изменение cookie banner, tracking-параметров или технического блока.

А:

```text
URL тот же
title тот же
main_content_sha256 изменился
```

уже означает, что издатель изменил ранее опубликованный материал.

Для финансовых и статистических источников это особенно ценно.

## 4. Revision tracking

Для статистики важно отслеживать не только новые точки, но и пересмотр старых.

Пример:

```text
вчера:
2026-06 = 100
2026-07 = 105
2026-08 = 107

сегодня API:
2026-06 = 100
2026-07 = 104
2026-08 = 107
2026-09 = 109
```

Правильный collector должен выделить:

```text
NEW:
2026-09 = 109

REVISION:
2026-07
105 → 104
```

Это позволяет знать не только текущее значение, но и когда источник пересмотрел старое наблюдение.

## 5. Банк России как первый полигон

Банк России удобен тем, что значительная часть данных доступна через официальные структурированные интерфейсы.

Вместо scraping можно использовать:

- официальный статистический REST API;
- XML-интерфейсы для курсов валют;
- web-service интерфейсы;
- официальный календарь выпуска статистики.

Это позволяет строить calendar-aware collectors.

Например:

```text
в четверг после публикации
→ проверить international reserves

в рабочий день вечером
→ забрать FX / RUONIA

в день решения ЦБ после публикации
→ проверить key rate
```

То есть не нужно бессмысленно опрашивать сайт каждые несколько минут.

## 6. Базовый автоматический набор временных рядов

В качестве первого живого блока можно собирать:

| Семейство | Частота | Источник | Автоматизация |
|---|---|---|---|
| Ключевая ставка | изменение / день | ЦБ | полная |
| USD/RUB, EUR/RUB, CNY/RUB | день | ЦБ | полная |
| RUONIA | день | ЦБ | полная |
| Международные резервы | неделя | ЦБ | полная |
| Денежная база | неделя | ЦБ | полная |
| Инфляционные показатели | месяц / прочее | ЦБ | высокая |
| Денежная масса | месяц | ЦБ | высокая |
| Ставки банков | месяц | ЦБ | высокая |
| Корпоративное и розничное кредитование | месяц | ЦБ | высокая |
| Средства населения и юрлиц | месяц | ЦБ | высокая |
| MOEX trading statistics | день / месяц | MOEX | высокая |

Это может стать первым полностью автоматическим «живым» фрагментом Tabularium.

## 7. reported и derived нельзя смешивать

Если ЦБ публикует ежедневный курс:

```text
01.09  82.10
02.09  81.95
...
30.09  84.20
```

это source observations.

Если затем рассчитывается:

```text
Средний USD/RUB за сентябрь = 83.17
```

то это уже derived observation, если сам источник такое значение не публиковал.

Поэтому полезно сохранять жёсткую границу:

```text
reported ≠ derived
```

Tabularium остаётся evidence layer.

## 8. Отдельный derivation layer

Средние, темпы роста и другие расчёты всё равно полезны, но их лучше хранить отдельно.

Например:

```text
Tabularium
    │
    │ reported observations
    ▼
Derivation layer
    │
    ├── monthly average FX
    ├── end-of-month FX
    ├── average key rate
    ├── YoY
    ├── MoM
    ├── rolling averages
    └── bridges
```

Каждый derived observation должен содержать как минимум:

```text
value
unit
period
formula
input observations
source commit/version
calculation code version
calculated_at
```

Тогда результат можно разрешить обратно до исходных наблюдений и формулы.

## 9. Derivation layer тоже можно автоматизировать

Например:

```text
02:00
source collector:
получил новые daily FX
→ commit в Tabularium

02:10
derivation workflow:
увидел изменение source series
→ пересчитал affected periods
→ проверил formula/tests
→ commit derived dataset
```

Агент утром получает сразу:

```text
official daily observations
+
monthly averages
+
quarter averages
+
end-of-period
+
revision history
```

без нового запроса к исходному сайту.

## 10. Отдельный raw/news observatory

Обычные вторичные новости лучше не смешивать с Tabularium.

Можно завести отдельный репозиторий вида:

```text
web-observatory
```

или:

```text
news-observatory
```

Его смысл — не просто «база новостей», а исторический наблюдатель публичного веба.

Он может регулярно смотреть:

```text
index page
RSS
sitemap
search page
specific section
```

и при обнаружении нового URL записывать manifest:

```text
source_domain
source_url
discovered_at
published_at
title
http_status
content_type
etag
last_modified
sha256
```

При допустимости можно сохранять raw HTML; иначе — только metadata и сигналы изменений.

## 11. Авторские права и raw HTML

Полные статьи СМИ обычно защищены авторским правом.

Поэтому публичный репозиторий, зеркалирующий тысячи материалов СМИ целиком, требует отдельной проверки условий использования и прав.

Для официальных первичных источников ситуация обычно проще, но тоже требует соблюдения их условий.

Для media/news источников безопаснее рассматривать:

```text
URL
metadata
timestamp
hash
structure
change signals
```

как основной публичный слой.

## 12. JS-сайты

GitHub Actions может запускать headless browser:

```text
Chromium
Playwright
Selenium
```

Workflow может:

```text
открыть страницу
→ дождаться JS
→ получить resulting DOM
→ обнаружить network endpoints
→ сохранить screenshot при необходимости
```

Но часто после первого анализа выясняется, что UI просто обращается к внутреннему JSON API, после чего браузер больше не нужен.

## 13. Уровни «умного поиска»

Полезно строить автоматизацию ступенчато.

Самый дешёвый уровень:

```text
URL pattern detection
regex
filename pattern
date parsing
link-set diff
HTML selectors
JSON schema
```

Далее:

```text
source-specific classifier
document type inference
series recognition
period detection
entity extraction
```

Ещё выше:

```text
document similarity
near-duplicate detection
previous-release comparison
schema drift detection
revision detection
```

И только затем:

```text
LLM classification
LLM extraction
LLM semantic analysis
```

LLM лучше использовать верхним этажом, а не первым инструментом crawler.

## 14. Near-duplicate detection

Для обнаружения почти одинаковых документов можно использовать:

```text
SimHash
MinHash
n-gram similarity
TF-IDF cosine
```

Например два разных URL могут содержать почти один и тот же пресс-релиз.

Если similarity очень высокая, система может классифицировать второй документ как probable duplicate без вызова LLM.

## 15. Полнотекстовый поиск

До embeddings можно построить обычный поисковый индекс:

```text
documents
→ tokenizer
→ inverted index
→ BM25
```

И искать по всему корпусу:

```text
"ипотечное кредитование"
"средства физических лиц"
"прогноз чистой процентной маржи"
```

Actions может автоматически пересобирать индекс после каждого изменения.

Статический интерфейс можно публиковать через GitHub Pages.

## 16. Embeddings как отдельная поисковая инфраструктура

Embeddings тоже возможны:

```text
source
→ chunks
→ embeddings
→ semantic index
```

Но это уже отдельная representation layer.

Для provenance нужно хранить:

```text
model
model version
chunking
embedding date
vector dimension
```

Embeddings не являются evidence и не должны смешиваться с первичными наблюдениями.

## 17. Event queue для агентов

Одна из самых сильных идей — превратить discovery в очередь событий.

Actions обнаруживает новую публикацию и создаёт, например:

```text
events/2026/09/23/...
```

с машинным event:

```text
event_type: new_publication
source: bank-of-russia
url: ...
discovered_at: ...
content_sha256: ...
suggested_route: ...
status: pending
```

Агент начинает не с поиска в интернете, а с:

```text
events/pending/
```

После обработки event получает статус:

```text
processed
```

и ссылку на конечный artifact.

## 18. Разделение труда между Actions и агентом

GitHub Actions хорош в:

```text
регулярно проверять
помнить предыдущее состояние
сравнивать
не пропускать новые URL
фиксировать изменения
```

Агент хорош в:

```text
прочитать
понять
структурировать
сопоставить
решить неоднозначность
```

Поэтому правильная схема:

```text
GitHub Actions:
наблюдать постоянно

Agent:
думать тогда, когда есть событие
```

а не заставлять агента каждый раз заново обходить интернет.

## 19. Ожидаемые публикации

Можно хранить расписания источников.

Например:

```text
CBR international reserves:
frequency = weekly
weekday = Thursday
expected_after = 16:00
```

Если к ожидаемому времени публикация появилась:

```text
status = observed
```

Если нет:

```text
status = expected_but_not_observed
```

Можно создать событие:

```text
SOURCE_DELAY
```

Это сохраняет различие:

```text
missing ≠ zero
missing ≠ not applicable
missing ≠ source did not publish
```

## 20. Исчезновение источника

Если вчера URL отдавал:

```text
HTTP 200
```

а сегодня:

```text
404
```

система может сохранить:

```text
source_available = false
first_failure_at = ...
previous_sha256 = ...
```

Для долговременного корпуса это важная часть provenance.

## 21. Schema drift и методологические изменения

Collector должен проверять не только значения, но и структуру источника.

Например:

```text
unit:
million RUB
```

внезапно стало:

```text
billion RUB
```

или:

```text
periodicity:
monthly
```

стало:

```text
quarterly
```

В таком случае правильное действие:

```text
SCHEMA_DRIFT
```

а не автоматическое продолжение старой серии.

То же относится к:

```text
measure_id changed
classification changed
column disappeared
new category appeared
```

## 22. Cross-source validation

Если один и тот же показатель публикуется через несколько официальных representation:

```text
API ЦБ
XLSX ЦБ
HTML таблица ЦБ
```

можно автоматически проверить:

```text
API value == XLSX value?
```

Если значения совпадают:

```text
validation = consistent
```

Если нет:

```text
CONFLICT
```

При этом никакое исходное значение не исправляется.

## 23. Git как журнал изменений

Каждый автоматический commit уже создаёт версионную историю.

Но внутри provenance всё равно желательно хранить:

```text
source_url
source_published_at
retrieved_at
content_sha256
content_type
etag
last_modified
collector_version
```

Потому что:

```text
Git commit time
```

и:

```text
source observation time
```

— разные понятия.

## 24. Workflow artifacts

Workflow artifacts лучше использовать для временных операционных результатов:

```text
debug
screenshots
temporary browser dumps
validation reports
logs
```

А долговечный evidence — сохранять в Git или другом постоянном хранилище.

То есть:

```text
artifact = operational by-product

repository = durable corpus
```

## 25. Cross-repository workflows

Несколько репозиториев могут образовывать pipeline.

Например:

```text
web-observatory
       │
       │ detected new CBR release
       ▼
repository_dispatch
       │
       ▼
tabularium workflow
```

или:

```text
Tabularium updated
       │
       ▼
derivation repo
       │
       ▼
recalculate affected series
```

Для cross-repository операций нужна правильно ограниченная авторизация.

## 26. Семантические слои системы

Полезно разделить архитектуру минимум на три слоя:

```text
I. WEB / SOURCE OBSERVATION
   "что появилось во внешнем мире?"

II. TABULARIUM
    "что утверждает первичный источник?"

III. DERIVATION
     "что воспроизводимо следует из observations?"
```

И уже поверх:

```text
IV. AGENT / ANALYTICAL LAYER
    "что это значит?"
```

## 27. Роль news/web observatory

Новостной репозиторий лучше понимать не как «архив статей», а как:

> public-source change observatory.

Он фиксирует:

```text
страница появилась
страница исчезла
страница изменилась
новая ссылка
новая публикация
новый PDF
новый API response
```

После этого материал можно классифицировать:

```text
PRIMARY_PUBLICATION
SECONDARY_NEWS
COMMENTARY
UNKNOWN
```

Первичный материал потенциально маршрутизируется в Tabularium.

## 28. «Живой» Tabularium

Tabularium может со временем сочетать:

```text
static archive
+
live bridges
+
automatic collectors
+
agent ingestion
```

Разные серии могут иметь разные степени автоматизации:

```text
полностью автоматическая
```

или:

```text
Actions обнаруживает
→ agent оформляет
```

или:

```text
полностью ручная
```

Не обязательно автоматизировать всё одинаково.

## 29. Предлагаемый порядок развития

### Этап 1 — структурированные ряды ЦБ

Взять 5–10 наиболее надёжных официальных серий:

```text
ключевая ставка
USD/RUB
EUR/RUB
CNY/RUB
RUONIA
международные резервы
денежная база
несколько банковских агрегатов
инфляционный показатель
```

Для каждой:

```text
canonical API
→ automated fetch
→ provenance
→ revision detection
→ source-faithful storage / bridge
```

### Этап 2 — публикационные watchers

```text
MOEX
CBR releases
Rosstat releases
Minfin
corporate disclosures
```

Actions:

```text
detects
fetches
hashes
queues
```

### Этап 3 — web/news observatory

```text
RSS
sitemaps
HTML
change detection
near duplicates
```

### Этап 4 — agent inbox

Агенты получают уже готовую очередь новых источников вместо самостоятельного discovery.

### Этап 5 — derived machine layer

```text
валютные средние
средние ставки
росты
rolling values
bridges
```

с воспроизводимыми формулами и provenance.

## 30. Итоговая идея

В развитой системе агент, отвечая на вопрос вроде:

> «как менялись средства физлиц при снижении ставки и укреплении рубля?»

уже имеет:

```text
Tabularium:
official key rate
official FX
official CPI
official deposits
official lending

Derivation:
monthly average key rate
monthly average USD/RUB
MoM / YoY
quarter averages
EOP values

News observatory:
what happened around those dates
```

И всё это автоматически поддерживается до последнего закрытого периода.

Тогда агент начинает работу не с Google, а с **машиночитаемого исторического состояния мира**.

GitHub Actions в такой архитектуре — уже не просто автоматизация GitHub, а **инфраструктура памяти для агентной исследовательской системы**.
