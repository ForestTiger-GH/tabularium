# Концепция количественного слоя банковских показателей в Tabularium

## 1. Общий вывод

Если расширить контур на РСБУ/регуляторную отчетность и разрешить производные показатели с полностью открытой, прозрачной и исторически устойчивой формулой, пространство показателей существенно расширяется.

РСБУ в ряде задач удобнее МСФО: формы 0409806 и 0409807 стандартизированы Банком России, а формы 0409808 и 0409813 дают капитал, RWA и обязательные нормативы в жестко заданной регуляторной геометрии.

Практически можно построить порядка **100–150 устойчивых показателей на банк**, а вместе с дополнительными структурами, темпами, мостами IFRS↔RAS и алгоритмическими рядами — более **200 рядов на банк**.

Ключевой принцип:

> **Формула показателя может быть постоянной, а mapping от конкретной версии отчетной формы к формуле должен версионироваться.**

---

## 2. Основные ограничения

### 2.1. РСБУ дает единые формы, но не полностью механическую классификацию

Публикуемая форма 0409806 стандартизирована, однако отдельные статьи могут включать реклассификацию по экономической сущности. Поэтому totals и крупные статьи обладают высокой надежностью, а часть детализаций требует сохранения пояснений банка.

### 2.2. Исторические формы меняются

Экономический показатель может оставаться постоянным, а строка формы, код или состав раскрытия — меняться.

Поэтому canonical object должен быть экономическим:

```text
operating_expenses
```

а не:

```text
row_21_form_0409807
```

Mapping должен иметь:

```text
valid_from
valid_to
source_form
source_line
mapping_version
```

### 2.3. `X`, `неприменимо`, отсутствие и ноль — разные состояния

Нельзя превращать скрытое или нераскрытое значение в `0`.

Следует различать:

```text
REPORTED
UNDISCLOSED
NOT_APPLICABLE
UNKNOWN
ZERO
```

---

# 3. Прямые показатели РСБУ

## 3.1. Баланс 0409806

Из формы можно собирать практически без интерпретации:

### Масштаб

- активы;
- обязательства;
- источники собственных средств.

### Ликвидные и банковские активы

- денежные средства;
- средства в Банке России;
- обязательные резервы;
- средства в кредитных организациях.

### Финансовые активы

- финансовые активы по справедливой стоимости через прибыль или убыток;
- чистая ссудная задолженность по амортизированной стоимости;
- финансовые активы по справедливой стоимости через прочий совокупный доход;
- ценные бумаги и иные финансовые активы по амортизированной стоимости;
- инвестиции в дочерние и зависимые организации.

### Фондирование

- средства Банка России;
- средства клиентов;
- средства кредитных организаций;
- средства клиентов, не являющихся кредитными организациями;
- вклады физических лиц и ИП;
- выпущенные долговые ценные бумаги;
- субординированный долг.

### Капитал

- уставный капитал;
- эмиссионный доход;
- резервный фонд;
- переоценки;
- бессрочные/субординированные инструменты в капитале;
- неиспользованная прибыль;
- всего источников собственных средств.

### Внебаланс

- безотзывные обязательства;
- гарантии и поручительства;
- условные обязательства.

---

# 4. Прямые показатели ОФР РСБУ

Форма 0409807 особенно удобна для унификации.

Можно хранить:

```text
interest_income_total
interest_income_banks
interest_income_nonbank_clients
interest_income_securities

interest_expense_total
interest_expense_banks
interest_expense_nonbank_clients
interest_expense_issued_securities

net_interest_income

reserve_change_loans
reserve_change_interest_receivable

net_interest_income_after_reserves

trading_income_fvpl
trading_income_fvoci
trading_income_amortized_cost
fx_result
metals_result
dividend_income

fee_income
fee_expense

reserve_change_fvoci_securities
reserve_change_ac_securities
reserve_change_other

other_operating_income

net_income_before_opex
operating_expenses
profit_before_tax
income_tax
profit_continuing
profit_discontinued
net_profit

oci
total_financial_result
```

Это существенно более однородный межбанковский P&L, чем неоднородные МСФО-презентации.

---

# 5. Производные показатели динамики

Для stock-показателей:

```text
qoq_growth
yoy_growth
ytd_growth
1y_growth
3y_cagr
5y_cagr
```

Для накопленных потоков:

```text
Q1 = 3M
Q2 = 6M - 3M
Q3 = 9M - 6M
Q4 = FY - 9M
```

Только при одинаковой методике, единице и периметре.

После этого:

```text
TTM = Q_t + Q_t-1 + Q_t-2 + Q_t-3
```

Для profitability ratios предпочтительно использовать TTM как основной вариант, а annualized YTD — как дополнительный.

---

# 6. Структура активов

Можно автоматически считать:

```text
loans_to_assets =
net_loans / assets
```

```text
cash_to_assets =
cash / assets
```

```text
cbr_funds_assets_share =
funds_at_cbr / assets
```

```text
interbank_assets_share =
due_from_banks / assets
```

```text
fvpl_assets_share =
fvpl_assets / assets
```

```text
fvoci_assets_share =
fvoci_assets / assets
```

```text
ac_securities_share =
ac_securities / assets
```

```text
accounting_equity_ratio =
accounting_equity / assets
```

```text
liabilities_to_assets =
liabilities / assets
```

```text
offbalance_commitments_to_assets =
irrevocable_commitments / assets
```

```text
guarantees_to_assets =
guarantees / assets
```

Можно строить механическую декомпозицию изменения активов:

```text
Δassets =
Δcash +
ΔCBR +
Δinterbank +
ΔFVPL +
Δloans +
ΔFVOCI +
ΔAC_securities +
...
```

---

# 7. Структура фондирования

Из РСБУ можно считать:

```text
customer_funding_share =
customer_funds / liabilities
```

```text
nonbank_customer_funding_share =
nonbank_customer_funds / liabilities
```

```text
retail_share_of_nonbank_funding =
household_and_IP_funds /
nonbank_customer_funds
```

```text
corporate_other_nonbank_share =
(nonbank_customer_funds - household_and_IP_funds) /
nonbank_customer_funds
```

```text
bank_funding_share =
bank_funds / liabilities
```

```text
cbr_funding_share =
CBR_funding / liabilities
```

```text
market_debt_funding_share =
issued_debt / liabilities
```

```text
subordinated_funding_share =
subordinated_debt / liabilities
```

Можно ввести прозрачный агрегат:

```text
wholesale_funding_share =
(CBR funding
 + bank funding
 + issued debt
 + subordinated debt)
/
liabilities
```

---

# 8. Loans-to-deposits и funding gap

Лучше задавать точное название:

```text
net_loans_to_nonbank_customer_funds =
net_loan_debt /
nonbank_customer_funds
```

Также:

```text
funding_gap =
net_loans - nonbank_customer_funds
```

```text
funding_gap_to_assets =
funding_gap / assets
```

---

# 9. ROA и ROE

Можно построить собственные стандартные показатели.

```text
ROA_TTM =
TTM net profit /
average assets
```

```text
ROE_TTM =
TTM net profit /
average accounting equity
```

Для МСФО можно разделять:

```text
ROE_total_equity
ROE_attributable_equity
```

с соответствующим profit numerator.

Для средней величины необходимо хранить:

```text
average_method
```

Например:

```text
two_point_average
quarterly_average
monthly_chronological_average
```

Если впоследствии добавить месячную форму 101, можно перейти к более качественным средним хронологическим значениям.

---

# 10. Собственная NIM

Вместо reported NIM можно считать:

```text
tabularium_net_interest_margin_on_assets =
TTM NII /
average total assets
```

Желательно использовать явное имя:

```text
tabularium.ras.nii_to_avg_assets.v1
```

Так показатель не смешивается с NIM банков или официальным ПД5 Банка России.

---

# 11. Доходность кредитов и стоимость фондирования

Можно считать прозрачные proxy:

```text
client_loan_income_yield_proxy =
interest_income_from_nonbank_client_loans /
average net_loan_debt
```

```text
customer_funding_cost_proxy =
interest_expense_on_nonbank_customer_funds /
average nonbank_customer_funds
```

```text
issued_debt_cost_proxy =
interest_expense_on_issued_securities /
average issued_debt
```

```text
simple_customer_spread_proxy =
client_loan_income_yield_proxy
-
customer_funding_cost_proxy
```

Это надежные формулы, но imperfect economic proxies. Их следует так и маркировать.

---

# 12. Собственный CIR

Из формы 0409807 можно восстановить pre-provision operating income.

Например:

```text
PPOP =
net_income_before_opex
-
loan_reserve_change
-
fvoci_reserve_change
-
ac_securities_reserve_change
-
other_reserve_change
```

При этом знак резервов должен быть нормализован.

После этого:

```text
Tabularium_CIR_RAS =
operating_expenses /
PPOP
```

Это единый CIR Tabularium, а не reported CIR банка.

---

# 13. Декомпозиция ROA

Можно создать аддитивный мост:

```text
NII / avg assets
+
net fees / avg assets
+
trading_and_other_income / avg assets
-
credit_loss_charge / avg assets
-
opex / avg assets
-
tax / avg assets
=
ROA
```

Отдельные показатели:

```text
interest_contribution_to_roa
fee_contribution_to_roa
trading_contribution_to_roa
other_income_contribution_to_roa
credit_cost_drag_to_roa
opex_drag_to_roa
tax_drag_to_roa
```

---

# 14. Core revenue

Можно определить:

```text
core_revenue =
NII + net_fee_income
```

Из него:

```text
core_revenue_to_opex =
core_revenue / operating_expenses
```

Также:

```text
nii_share_of_preprovision_income
net_fee_share_of_preprovision_income
other_income_share_of_preprovision_income
```

```text
profit_conversion =
net_profit / PPOP
```

---

# 15. Operating leverage

```text
operating_leverage =
growth(PPOP) - growth(OPEX)
```

Дополнительно:

```text
ΔPPOP
ΔOPEX
ΔPBT
```

---

# 16. Кредитный риск по МСФО

Если раскрыты gross exposures и ECL:

```text
total_ecl_coverage =
ECL allowance /
gross loans
```

```text
stage1_share =
Stage1 gross /
gross loans
```

```text
stage2_share =
Stage2 gross /
gross loans
```

```text
stage3_share =
Stage3 gross /
gross loans
```

Покрытие:

```text
stage1_coverage =
Stage1 ECL /
Stage1 gross
```

```text
stage2_coverage =
Stage2 ECL /
Stage2 gross
```

```text
stage3_coverage =
Stage3 ECL /
Stage3 gross
```

Также:

```text
uncovered_stage3 =
Stage3 gross - Stage3 ECL
```

```text
uncovered_stage3_to_equity =
uncovered_stage3 /
equity
```

---

# 17. Стандартизованный CoR

Только если можно выделить именно customer-loan ECL charge:

```text
Tabularium_CoR_IFRS =
TTM customer-loan ECL charge /
average gross customer loans
```

Если numerator смешивает customer loans, securities, interbank или off-balance, показатель не рассчитывается.

---

# 18. Write-off metrics

При наличии раскрытия:

```text
writeoff_rate =
TTM writeoffs /
average gross loans
```

```text
writeoffs_to_ecl =
TTM writeoffs /
average ECL stock
```

```text
recoveries_to_writeoffs =
recoveries /
writeoffs
```

---

# 19. Risk migration

Можно считать:

```text
ΔStage2_share
ΔStage3_share
```

Дополнительный аналитический proxy:

```text
stage2_to_stage3_pressure_proxy =
ΔStage3_share - ΔStage2_share
```

Последний следует относить к advanced derived layer.

---

# 20. Регуляторный капитал

Из 0409808 можно собирать:

```text
basic_capital
core_capital
supplementary_capital
total_regulatory_capital
RWA
N1.1
N1.2
N1.0
```

Производные:

```text
rwa_density =
RWA /
total_assets
```

```text
regulatory_capital_to_assets =
regulatory_capital /
assets
```

```text
regulatory_to_accounting_capital =
regulatory_capital /
accounting_equity
```

```text
tier2_dependence =
(total_capital - core_capital) /
total_capital
```

```text
core_capital_share =
core_capital /
total_regulatory_capital
```

---

# 21. Capital headroom

Если нормативные требования хранятся как параметры с `effective_from/effective_to`:

```text
N1_0_headroom_pp =
actual_N1_0 - required_N1_0
```

Можно перевести запас в денежную величину:

```text
excess_total_capital_rub =
(actual_N1_0 - required_N1_0)
× RWA_N1_0 / 100
```

Аналогично:

```text
excess_basic_capital
excess_core_capital
```

---

# 22. Capital generation

```text
regulatory_capital_growth
RWA_growth
```

```text
capital_growth_minus_rwa_growth
```

```text
earnings_to_rwa =
TTM net_profit /
average RWA
```

```text
PPOP_to_RWA =
TTM PPOP /
average RWA
```

---

# 23. ROE decomposition

Классическая identity:

```text
ROE =
ROA × financial_leverage
```

где:

```text
financial_leverage =
average_assets /
average_equity
```

Это дает механическое объяснение высокого ROE через:

- доходность активов;
- leverage;
- сочетание факторов.

---

# 24. Ликвидность

Из 0409813 можно хранить прямые нормативы:

```text
N2
N3
N4
```

При наличии раскрытия:

```text
N26/N27
N28/N29
regulatory_leverage
```

Производные:

```text
N2_headroom
N3_headroom
N4_headroom
LCR_headroom
NSFR_headroom
```

---

# 25. Простые liquidity proxies

Можно определить:

```text
primary_liquidity_assets =
cash
+ funds_at_CBR
+ due_from_banks
```

```text
primary_liquidity_share =
primary_liquidity_assets /
assets
```

Это следует называть именно proxy.

---

# 26. Внебалансовый риск

```text
offbalance_credit_exposure =
irrevocable_commitments
+ guarantees
```

Далее:

```text
offbalance_to_assets
offbalance_to_equity
offbalance_to_customer_funds
```

---

# 27. Концентрация структуры

Можно использовать HHI по заранее утвержденным buckets.

Для фондирования:

```text
CBR
banks
retail customers
other nonbank customers
issued debt
subordinated funding
other liabilities
```

```text
funding_HHI =
Σ share_i²
```

Аналогично:

```text
asset_mix_HHI
```

Это относится к mapped deterministic indicators, поскольку классификация buckets задается нами.

---

# 28. Дивиденды и retention

Из формы 0409810 при наличии раскрытия:

```text
dividends_paid
```

Производные:

```text
payout_ratio =
dividends /
prior_period_profit
```

```text
retention_ratio =
1 - payout_ratio
```

```text
internal_capital_generation =
retained_profit /
beginning_equity
```

---

# 29. Рыночные доли

При наличии секторного denominator можно считать:

```text
asset_market_share
loan_market_share
corporate_loan_share
retail_loan_share
household_funding_share
corporate_funding_share
profit_share
```

Изменение доли:

```text
market_share_change_pp
```

Вклад в рост рынка:

```text
contribution_to_market_growth =
Δbank /
Δmarket
```

---

# 30. Growth gap к рынку

```text
growth_gap_to_market =
bank_growth - market_growth
```

Например:

```text
corporate_loan_growth_gap
retail_loan_growth_gap
funding_growth_gap
```

---

# 31. IFRS ↔ RAS bridge

Это отдельный уникальный слой.

По stock-показателям:

```text
group_asset_uplift =
IFRS_group_assets /
RAS_bank_assets - 1
```

```text
group_equity_uplift
group_loan_uplift
group_customer_funds_uplift
```

По flows:

```text
IFRS_RAS_profit_difference
IFRS_RAS_NII_difference
```

Эту разницу нельзя автоматически называть «вкладом дочерних обществ», поскольку присутствуют:

- консолидационные различия;
- perimeter differences;
- IFRS/RAS recognition differences;
- fair-value differences.

Корректная трактовка:

> отличие group lens от legal-entity lens.

---

# 32. Accounting ↔ Regulatory capital bridge

Можно хранить:

```text
RAS accounting equity
IFRS equity
regulatory basic capital
regulatory core capital
regulatory total capital
```

Производные:

```text
reg_cap_minus_accounting_equity
reg_cap_to_accounting_equity
IFRS_equity_to_reg_cap
```

---

# 33. IFRS ↔ RAS profitability bridge

Можно рассчитывать параллельно:

```text
IFRS_ROA
RAS_ROA

IFRS_ROE
RAS_ROE

IFRS_NII_to_assets
RAS_NII_to_assets
```

и:

```text
IFRS_minus_RAS_ROA
IFRS_minus_RAS_ROE
```

Это observation of difference, а не causal attribution.

---

# 34. Месячный слой формы 101

В перспективе форма 0409101 может дать месячные stocks и более качественные average denominators.

Это позволит:

- считать monthly average balances;
- строить более устойчивые ROA/ROE/NIM proxies;
- делать ранние оценки квартальных результатов;
- анализировать внутриквартальную динамику.

Но текущая публичная детализация формы 101 ограничена. Ее следует использовать как supplementary high-frequency layer.

---

# 35. Более широкий регуляторный набор

В методиках Банка России используются семейства показателей:

### Качество активов

- качество ссуд;
- риск потерь;
- просроченные ссуды;
- резервы;
- крупные кредитные риски.

### Доходность

- прибыльность активов;
- прибыльность капитала;
- структура расходов;
- чистая процентная маржа;
- чистый кредитный спред.

### Ликвидность

- краткосрочная ликвидность;
- Н2;
- Н3;
- зависимость от межбанковского рынка;
- концентрация крупных кредиторов;
- структура небанковских ссуд.

Часть официальных коэффициентов требует форм, которые публично раскрываются ограниченно. Поэтому собственные proxy нельзя выдавать за официальный показатель Банка России.

---

# 36. Модельные и статистические показатели

При накоплении 3–5 лет истории можно добавить отдельный model layer.

## Волатильность

```text
earnings_volatility_3y =
stdev(quarterly ROA over 12 quarters)
```

```text
capital_ratio_volatility
loan_growth_volatility
funding_growth_volatility
```

## Банковский Z-score

```text
Z-score =
(average_ROA + average_equity_to_assets)
/
stdev(ROA)
```

С обязательным указанием окна:

```text
bank_zscore_5y_v1
```

## Drawdown

```text
max_drawdown_N1_0
max_drawdown_ROE
max_drawdown_equity
```

## Чувствительность

```text
NII_sensitivity_to_key_rate
loan_growth_sensitivity_to_key_rate
deposit_growth_sensitivity_to_key_rate
```

Regression/beta indicators должны храниться отдельно от deterministic layer, поскольку зависят от:

- окна;
- лагов;
- спецификации;
- sample definition.

---

# 37. Классы показателей

Рекомендуемая классификация:

| Class | Смысл | Пример |
|---|---|---|
| `R` | Reported | assets, NII, Stage 3, N1.0 |
| `D1` | Deterministic | loans/assets, ROA, retail funding share |
| `D2` | Mapped deterministic | CIR, standardized CoR, wholesale funding |
| `M` | Model | Z-score, rate beta, volatility |

Это позволяет не смешивать reported и derived observations.

---

# 38. Рекомендуемый первый banking dataset

Ориентир:

| Блок | Количество показателей |
|---|---:|
| Масштаб и структура баланса | 15–20 |
| Loan/funding mix | 15–20 |
| P&L и income mix | 15–20 |
| Profitability / efficiency | 10–15 |
| IFRS credit risk | 10–20 |
| Regulatory capital / RWA | 10–15 |
| Liquidity / normatives | 5–10 |
| Market share / growth | 10–20 |
| IFRS↔RAS bridges | 5–10 |

Итого: примерно **80–100 показателей для первого полноценного слоя**, с возможностью расширения выше 150.

---

# 39. Минимальная идентичность observation

Каждая observation должна иметь:

```text
entity
perimeter
lens
metric_id
period
value
unit
source
status
```

Для производного показателя дополнительно:

```text
formula_id
formula_version
input_observation_ids
mapping_version
```

---

# 40. Архитектурная модель

Вместо таблицы готовых KPI лучше строить количественный engine:

```text
REPORTED OBSERVATIONS
        ↓
STANDARD MAPPINGS
        ↓
DETERMINISTIC FORMULAS
        ↓
DERIVED OBSERVATIONS
        ↓
OPTIONAL MODELS
```

Это позволяет из одних и тех же первичных данных воспроизводимо рассчитывать:

```text
ROA
ROE
CIR
NII/assets
CoR
RWA density
capital headroom
funding structure
market share
growth contribution
IFRS/RAS bridge
```

и пересчитывать многолетнюю историю единой версией формулы.

---

# 41. Главный принцип исторической устойчивости

Следует разделять:

```text
metric definition
```

и:

```text
source mapping
```

Пример:

```text
metric_id: operating_expenses
formula_version: 1
```

может оставаться неизменным много лет.

При этом mapping:

```text
0409807 / version A / row X
0409807 / version B / row Y
```

может меняться.

Исторический ряд считается непрерывным только при доказанном semantic bridge.

Похожее название строки само по себе доказательством непрерывности не является.
