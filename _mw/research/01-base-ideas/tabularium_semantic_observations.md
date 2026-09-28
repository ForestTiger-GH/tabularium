# Semantic Observations для Tabularium: крупные корпоративные факты из МСФО, годовых отчётов и отчетов эмитента

## 1. Ключевой вывод

Для Tabularium не стоит пытаться извлекать из корпоративных документов вообще все возможные «семантические факты».

На первом этапе нужен существенно более узкий и сильный слой:

> **корпоративные факты верхнего уровня, которые способны изменить понимание того, что представляет собой компания, чем она владеет, куда движется, от чего зависит и какие у неё возникли крупные ограничения или обязательства.**

Это должны быть не пафосные формулировки, не маркетинговые эпитеты и не мелкие операционные детали, а существенные события, состояния и отношения корпоративного масштаба.

В этом смысле финансовая и корпоративная отчетность является источником не только чисел, но и структурируемых смысловых наблюдений.

---

## 2. Два параллельных класса наблюдений

Для будущего observation-layer Tabularium полезно различать два принципиально разных класса наблюдений.

### Numeric observation

```text
Сбер
→ ипотечные кредиты
→ 7 123 млрд руб.
```

### Semantic observation

```text
Компания
→ acquired
→ Компания X

Компания
→ classified
→ Business Y as held for sale

Компания
→ ceased
→ Business Z

Компания
→ breached
→ covenant X

Компания
→ plans
→ construction of Plant A

Компания
→ controls
→ Subsidiary B
```

Второй класс правильнее трактовать не просто как «факты», а как:

> **reported assertions / semantic observations**

Это принципиально важно, потому что разные формулировки источника могут иметь разный эпистемический статус.

Например:

```text
Компания приобрела X.
```

не равно:

```text
Руководство планирует приобрести X.
```

не равно:

```text
Руководство ожидает приобретение X.
```

не равно:

```text
Невозможность приобрести X является риском.
```

Во всех случаях источник что-то утверждает, но это разные типы наблюдений.

---

# 3. Приоритетные классы semantic observations

## 3.1. Периметр бизнеса и контроль

Это один из самых ценных классов корпоративных фактов.

Можно извлекать:

| Семантический факт | Пример |
|---|---|
| Контроль | `A controls B` |
| Материнская компания | `B is subsidiary of A` |
| Существенная дочерняя организация | `A has material subsidiary B` |
| Совместное предприятие | `A has joint venture B` |
| Ассоциированная компания | `A has associate B` |
| Приобретение контроля | `A acquired control of B` |
| Потеря контроля | `A lost control of B` |
| Изменение доли участия | `A changed interest in B` |
| Включение в периметр консолидации | `B entered consolidation perimeter` |
| Выход из периметра консолидации | `B exited consolidation perimeter` |
| Реорганизация | merger / spin-off / consolidation / demerger |

Этот слой позволяет строить воспроизводимый **corporate graph** по vintages.

Особенно полезные источники:

- примечания МСФО;
- IFRS 3 disclosures;
- IFRS 12 disclosures;
- годовые отчеты;
- отчеты эмитента;
- сообщения о существенных фактах;
- transaction materials.

---

## 3.2. Крупные изменения периметра: приобретения, продажи, закрытия

Следующий ключевой класс — события, меняющие фактический состав бизнеса.

Примеры:

```text
2025-04-17
Company A
disposed_of
Company B
```

```text
2025-09-30
Company A
classified
Business C
as held_for_sale
```

Базовые типы:

```text
acquisition
disposal
held_for_sale
discontinued_operation
loss_of_control
merger
demerger
spin_off
liquidation
restructuring
```

Это особенно ценно для восстановления долгосрочной корпоративной истории.

---

## 3.3. Крупные проекты и изменение производственной архитектуры

Для промышленных, инфраструктурных, сырьевых, транспортных и девелоперских компаний это один из важнейших смысловых слоев.

Примеры:

```text
Company
commissioned
Plant X
```

```text
Company
suspended
Project Y
```

```text
Company
approved
construction of Facility Z
```

```text
Company
closed
Production Site A
```

Для проекта важно фиксировать не просто его существование, но и статус.

Рекомендуемые состояния:

```text
announced
approved
committed
under_construction
commissioned
operational
suspended
cancelled
disposed
closed
```

Это позволяет строить историю:

```text
announced
→ approved
→ construction
→ commissioned
→ operational
```

или:

```text
announced
→ construction
→ suspended
→ cancelled
```

---

## 3.4. Стратегические решения и крупные обязательства

Здесь необходимо жестко фильтровать корпоративную риторику.

Фразы вроде:

> «Мы продолжим укреплять лидерство, обеспечивая устойчивый рост за счет инновационных решений»

не должны становиться semantic observations.

Полезны только утверждения с достаточно конкретной структурой:

```text
ACTION
+
OBJECT
+
STATUS / INTENT
```

Желательно также:

```text
TIME / HORIZON
```

Примеры пригодных наблюдений:

```text
Company
plans_to_exit
Business X
```

```text
Company
committed_to_build
Plant Y
```

```text
Company
targets
Production capacity Z by 2030
```

```text
Company
plans_to_expand_into
Market A
```

Потенциальные predicates:

```text
plans
committed_to
targets
enters
exits
expands_into
reduces
builds
closes
transforms
```

Но их необходимо хранить вместе с эпистемическим статусом.

---

## 3.5. Бизнес-модель и фактический контур деятельности

Полезный относительно стабильный слой:

```text
company operates_segment Retail
company operates_segment Corporate
company produces Product A
company provides_service Service B
company operates_in Geography C
```

Особенно полезны:

- operating segments;
- основные продукты и услуги;
- ключевые географии;
- существенные рынки;
- типы бизнеса;
- значимые производственные цепочки.

Важно:

> изменение состава сегментов по отчетным периодам само по себе является набором наблюдений.

Например:

```text
2022: A / B / C
2024: A / B / D
2026: A / D
```

А вывод:

> «бизнес-модель компании изменилась»

уже является analytical claim и не относится к evidence-layer.

---

## 3.6. Критические зависимости компании

Не следует извлекать каждого поставщика, клиента или контрагента.

Интересны только зависимости корпоративного масштаба:

```text
material_customer
material_supplier
key_distributor
key_financing_provider
critical_license
critical_concession
critical_resource
critical_contract
```

Можно строить:

```text
company
→ depends_on
→ customer / supplier / lender / license / concession / contract
```

Особенно ценны:

- крупнейшие клиенты;
- существенные поставщики;
- существенные дебиторы;
- существенные кредиторы;
- ключевые лицензии;
- концессии;
- критические ресурсы;
- инфраструктурные зависимости;
- существенные договоры.

В перспективе это дает второй граф поверх ownership graph:

> **corporate dependency graph**

---

## 3.7. Финансирование и существенные договорные ограничения

Числовое наблюдение:

```text
Debt = 800 bn
```

не заменяет семантическое раскрытие:

```text
Company
entered_into
syndicated credit agreement
```

```text
Loan
secured_by
Asset X
```

```text
Company
provided_guarantee_for
Subsidiary Y
```

```text
Loan
subject_to
Covenant Z
```

```text
Company
breached
Covenant Z
```

```text
Lender
waived
Covenant breach
```

```text
Debt
refinanced_by
New facility
```

Приоритетные типы:

```text
entered_financing
issued_debt
refinanced
pledged
guaranteed
subject_to_covenant
breached_covenant
received_waiver
defaulted
accelerated
restructured_debt
```

Это описывает уже не просто размер долга, а **условия существования компании в капитальной структуре**.

---

## 3.8. Юридические и регуляторные события

Не нужен реестр каждого мелкого спора.

Нужны только события корпоративного масштаба:

```text
material_litigation
regulatory_investigation
material_fine
license_granted
license_revoked
concession_awarded
concession_terminated
sanctions_restriction
regulatory_prohibition
asset_freeze
```

Правильная source-faithful запись:

```text
source states:
    litigation X exists
    claimant = ...
    status = ...
    claimed_amount = ...
```

Неправильная:

```text
lawsuit_risk = HIGH
```

Оценка `HIGH` уже является аналитической интерпретацией.

---

## 3.9. Financial distress и «красные события»

Этот класс стоит выделить особо.

Примеры:

```text
going_concern_material_uncertainty
default
covenant_breach
debt_restructuring
emergency_financing
material_impairment
restructuring_program
bankruptcy_proceeding
liquidation_plan
```

Если источник сообщает о:

```text
going_concern_material_uncertainty
```

это один из наиболее существенных semantic observations всего корпуса.

То же касается impairment.

Важно хранить не только сумму impairment, но и:

```text
asset / CGU
→ impaired
```

плюс причину, если источник её прямо сообщает.

---

## 3.10. Contingencies и крупные обязательства

Еще один важный класс:

```text
contingent_liability
material_commitment
guarantee
restoration_obligation
purchase_commitment
capital_commitment
legal_obligation
```

Не каждое условное обязательство должно попадать в верхний слой, но материальные обязательства компании — должны.

---

# 4. События после отчетной даты

`subsequent_event` лучше не делать самостоятельным экономическим типом события.

Это должен быть **temporal qualifier**.

Например:

```yaml
event_type: acquisition
event_date: 2026-07-15
observation_period_end: 2026-06-30
reported_as: subsequent_event
```

Таким образом одно и то же экономическое событие не получает отдельную сущность только из-за того, что оно произошло после отчетной даты.

Раздел `Events after the reporting period` особенно ценен, потому что там часто раскрываются:

- новые заимствования;
- облигационные выпуски;
- приобретения;
- продажи;
- дивиденды;
- реструктуризации;
- решения совета директоров;
- крупные инвестиционные события.

Для semantic extraction этот раздел должен иметь высокий приоритет.

---

# 5. Первое ядро semantic layer

Первоначальный слой можно ограничить примерно следующими семействами:

| Семейство | Примеры predicates | Приоритет |
|---|---|---:|
| Control & perimeter | controls, subsidiary_of, associate_of, joint_venture_with, gained_control, lost_control | ★★★★★ |
| M&A / disposal | acquired, disposed_of, merged_with, spun_off, classified_held_for_sale | ★★★★★ |
| Business structure | operates_segment, operates_in, produces, provides_service | ★★★★☆ |
| Major projects | approved, started, commissioned, suspended, cancelled, closed | ★★★★★ |
| Strategy / commitments | plans, committed_to, targets, exits, expands_into | ★★★★☆ |
| Critical dependencies | depends_on_customer, depends_on_supplier, depends_on_license, material_counterparty | ★★★★☆ |
| Funding & constraints | entered_financing, pledged, guaranteed, covenant, breach, default, waiver, refinanced | ★★★★★ |
| Legal / regulatory | subject_to_litigation, sanctioned, licensed, restricted, investigated | ★★★★☆ |
| Distress / restructuring | going_concern_uncertainty, impaired, restructured, bankruptcy, liquidation | ★★★★★ |
| Contingencies | contingent_liability, commitment, guarantee, restoration_obligation | ★★★★☆ |

Главная идея:

> начинать не с сотен мелких semantic predicates, а с нескольких десятков сильных predicates корпоративного масштаба.

---

# 6. Source assertion и semantic observation нельзя смешивать

Фраза «извлекать без преобразований» требует точного разделения уровней.

Пусть источник пишет:

> «В апреле Группа приобрела 75% долей ООО „Ромашка“ и получила контроль над обществом».

Минимальный source-bound объект:

```text
SOURCE ASSERTION

"В апреле Группа приобрела 75% долей ООО «Ромашка»
и получила контроль над обществом."
```

Рядом можно создать semantic observation:

```yaml
assertion:
  subject_literal: "Группа"
  predicate: acquired_control_of
  object_literal: 'ООО "Ромашка"'
  modality: actual
  status: completed
```

Но привязка:

```text
ООО "Ромашка"
→ canonical entity ID
```

или:

```text
acquired_control_of
→ canonical predicate ontology
```

уже является отдельным bridge / binding.

Поэтому правильная цепочка:

```text
source
→ representation
→ source assertion
→ semantic observation
→ canonical binding
→ derivation
→ analytical claim
```

Это соответствует базовой эпистемической архитектуре Tabularium.

---

# 7. Modality — обязательное поле

Одного predicate недостаточно.

Необходимо хранить **эпистемический статус утверждения**.

Рекомендуемый минимум:

| Modality | Смысл |
|---|---|
| `actual` | событие произошло / состояние существует |
| `committed` | компания приняла обязательство |
| `planned` | заявленный план |
| `target` | заявленная цель |
| `expected` | ожидание менеджмента |
| `possible` | возможное событие |
| `contingent` | зависит от условия |
| `risk` | источник описывает риск |
| `management_attribution` | объяснение причины менеджментом |

Например:

> «Компания закроет завод»

не должно превращаться в:

```text
plant_closed = true
```

Правильно:

```yaml
predicate: close
modality: planned
```

Позже источник может сообщить:

```yaml
predicate: close
modality: actual
```

И только выше evidence-layer можно построить связь:

```text
plan
→ execution
```

---

# 8. Статусы события и состояния

Помимо modality полезно отделять status.

Например:

```text
announced
approved
committed
in_progress
completed
suspended
cancelled
terminated
expired
unknown
```

Для проектов:

```text
announced
→ approved
→ under_construction
→ commissioned
→ operational
```

Для M&A:

```text
announced
→ signed
→ regulatory_approval
→ completed
```

Для сделки, которая не состоялась:

```text
announced
→ signed
→ terminated
```

Это намного информативнее, чем просто наличие слова `acquisition`.

---

# 9. Materiality

Semantic layer не должен превращаться в свалку фактов.

Полезно разделить:

```text
source_materiality
```

и:

```text
tabularium_selection
```

### source_materiality

Хранит только то, что прямо следует из источника:

```text
material
significant
key
major
principal
```

если источник сам это говорит.

### tabularium_selection

Отражает только факт включения observation в верхний semantic layer.

Не следует автоматически присваивать:

```text
materiality = HIGH
```

если это не квалификация источника.

---

# 10. Temporal model

Для semantic observations одной отчетной даты недостаточно.

Минимально полезны:

```text
event_date
effective_date
period_start
period_end
publication_date
source_vintage
```

Например:

```yaml
event:
  type: acquisition
  event_date: 2026-07-15

source:
  reporting_period_end: 2026-06-30
  publication_date: 2026-08-20
  reported_as: subsequent_event
```

Так сохраняется различие между:

- когда событие произошло;
- к какому отчетному периоду относится документ;
- когда информация была опубликована;
- в каком source vintage она появилась.

---

# 11. Возможная структура записи

Концептуальный пример:

```yaml
semantic_observation:
  observation_id: obs_sem_...

  source_report_id: COMPANY_IFRS_2026M6

  source:
    page: 87
    section: "Events after the reporting period"
    paragraph: 3
    assertion_literal: >
      In July 2026 the Group completed the acquisition
      of a 75% interest in Company X and obtained control.

  subject:
    literal: "the Group"

  predicate:
    source_meaning: "completed the acquisition and obtained control"

  object:
    literal: "Company X"

  event:
    type: acquisition
    status: completed
    modality: actual
    event_date: 2026-07-15

  source_materiality:
    literal: null

  binding:
    subject_entity_id: null
    object_entity_id: null
    canonical_predicate: null
    mapping_status: UNMAPPED
```

Ключевой принцип:

> semantic observation должен быть полезен даже до canonical mapping.

---

# 12. Что не следует включать в первое поколение

На первом этапе не стоит превращать в semantic observations:

- маркетинговые эпитеты;
- «лидер», «уникальный», «инновационный», «лучший»;
- награды;
- благотворительность;
- общие ESG-декларации;
- неконкретные кадровые заявления;
- общие слова о клиентском опыте;
- корпоративные ценности;
- общие заявления о цифровизации;
- каждую продуктовую новинку;
- каждое изменение тарифов;
- каждого контрагента;
- каждый судебный иск;
- каждый локальный проект;
- мелкие кадровые перестановки;
- описание обычной текущей деятельности.

Пример нежелательного факта:

```text
Company is an innovative leader
```

Пример пригодного факта:

```text
Company approved construction of Plant X
```

---

# 13. Что это даст Tabularium

Числовой слой отвечает:

> **Сколько?**

Semantic layer отвечает:

> **Что произошло с самой компанией?**

Вместе можно получить:

```text
company
→ ownership
→ businesses
→ material subsidiaries
→ segments
→ critical relationships
→ strategic commitments
→ projects
→ acquisitions
→ disposals
→ financing
→ collateral
→ covenants
→ litigation
→ regulation
→ restructuring
→ distress
→ subsequent events
```

В результате для компании можно построить не просто набор отчетов и не только таблицу чисел, а:

> **машиночитаемую корпоративную биографию, где каждое утверждение разрешается обратно до конкретного фрагмента первичного источника.**

---

# 14. Производные продукты поверх semantic layer

Сам semantic layer остается evidence-layer.

Но поверх него можно строить:

```text
plans
→ execution
```

```text
targets
→ outcomes
```

```text
announced M&A
→ completed M&A
```

```text
projects
→ commissioning
```

```text
strategy
→ capital allocation
```

```text
business perimeter
→ historical changes
```

```text
dependency
→ concentration risk analysis
```

```text
covenant
→ breach
→ waiver
→ refinancing
```

```text
impairment
→ disposal
→ exit
```

Это уже derivation / analytical layer.

---

# 15. Рекомендуемый первый scope

Первое поколение semantic extraction стоит ограничить примерно 10–15 крупными классами:

1. контроль и периметр;
2. приобретения;
3. продажи;
4. реорганизации;
5. крупные проекты;
6. стратегические обязательства;
7. сегменты и крупные бизнес-направления;
8. критические зависимости;
9. существенное финансирование;
10. залоги, гарантии и ковенанты;
11. дефолты и нарушения;
12. существенные юридические и регуляторные события;
13. restructuring / distress;
14. крупные contingencies;
15. события после отчетной даты.

Это уже способно дать чрезвычайно сильный слой данных без преждевременной универсализации.

---

# 16. Архитектурный вывод

Для Tabularium разумно развивать два комплементарных observation-layer:

```text
NUMERIC OBSERVATIONS
+
SEMANTIC OBSERVATIONS
```

При этом оба должны подчиняться одинаковым принципам:

```text
source-faithful
source-bound
traceable
versioned
modality-aware
status-aware
no silent normalization
no analytical conclusions in evidence-layer
```

И единая эпистемическая цепочка может выглядеть так:

```text
source
→ representation
→ observation
→ semantic / dimensional binding
→ derivation / bridge
→ analytical claim
```

Главный принцип:

> **Tabularium должен хранить не только числа, которые компания сообщила, но и крупные события, состояния и отношения, которые сама компания или иной первичный источник прямо зафиксировал.**

Но Tabularium не должен самостоятельно превращать эти наблюдения в оценки вроде:

```text
good acquisition
failed strategy
high risk
strong competitive advantage
successful project
```

Такие выводы принадлежат уже аналитическому слою.

---

# 17. Опорные стандарты и источники

Исследовательская рамка опирается, в частности, на следующие классы раскрытий:

- IFRS 3 — Business Combinations;
- IFRS 5 — Non-current Assets Held for Sale and Discontinued Operations;
- IFRS 8 — Operating Segments;
- IFRS 12 — Disclosure of Interests in Other Entities;
- IAS 1 — Presentation of Financial Statements;
- IAS 10 — Events after the Reporting Period;
- IAS 34 — Interim Financial Reporting;
- IAS 36 — Impairment of Assets;
- IAS 37 — Provisions, Contingent Liabilities and Contingent Assets;
- IFRS Practice Statement 1 — Management Commentary;
- IFRS Accounting Taxonomy narrative concepts;
- SEC Form 8-K event taxonomy;
- российские отчеты эмитента и нормативные требования Банка России.

Полезные ссылки:

- https://www.ifrs.org/issued-standards/list-of-standards/ifrs-3-business-combinations/
- https://www.ifrs.org/issued-standards/list-of-standards/ifrs-5-non-current-assets-held-for-sale-and-discontinued-operations/
- https://www.ifrs.org/issued-standards/list-of-standards/ifrs-8-operating-segments/
- https://www.ifrs.org/issued-standards/list-of-standards/ifrs-12-disclosure-of-interests-in-other-entities/
- https://www.ifrs.org/issued-standards/list-of-standards/ias-10-events-after-the-reporting-period/
- https://www.ifrs.org/issued-standards/list-of-standards/ias-36-impairment-of-assets/
- https://www.ifrs.org/issued-standards/list-of-standards/ias-37-provisions-contingent-liabilities-and-contingent-assets/
- https://www.ifrs.org/issued-standards/list-of-standards/management-commentary-practice-statement-1/
- https://media.ifrs.org/versioned_iti_full.html
- https://www.sec.gov/
- https://www.cbr.ru/
