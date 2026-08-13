# Черновики Linear-issue: лестница эндгейма IV → UHV (Arc C)

> Team: **Skuf-addon**. Все — статус **Backlog**, майлстоун «Эндгейм / поздняя игра».
> Нумерация SKU-64+ (последний существующий — SKU-63). Финал переиспользует существующие SKU-40/41/43/44 как под-задачи Эры 9.
> Формат готов к созданию через Linear MCP (`create_issue`). Приоритеты: эры выше = ниже приоритет (Low), кроме гигиены-замыкания орфанов.

---

## ⚠️ СТЕК ИДЕНТИЧНОСТИ ТИЛЬТА (аудит §13.3, V1+V3+A+V4) — делать ДО эндгейм-лестницы

> Симуляция (roadmap §13): Тильт = пассивный +EU/t налог. Первый вариант (катастрофа+вайб-скидка) = GTNH pollution с мемом. Принят **стек-переворот**: тильт становится **соблазном** (игрок сам хочет гнать ради бонуса), а не угрозой. 4 слоя, порядок реализации V1→V3→A→V4. Эндгейм §12 строить НЕЛЬЗЯ до этого (зависимость Б1).

### SKU-80 (новый) · СЛОЙ V1 «Соблазн» — тильт даёт бонус (ядро риск/награда)
**Priority:** High (P0 идентичности)
**Description:** высокий тильт через `recipeModifier` даёт **бонус** (скорость/выход/шанс редких побочек), не только +EU/t штраф (§17.3 «Пот», C12 «Прайм»). Игрок сам гонит тильт ради дорогих ресурсов. Баланс: бонус перекрывает цену только при управляемом риске; за порогом — растёт шанс катастрофы (SKU-23). Числа — config (SKU-11).
**DoD:** разгон линии в высокий тильт даёт измеримую выгоду; игрок делает осознанную ставку, а не терпит налог.
**Blocks:** SKU-81, SKU-23-как-провал.

### SKU-81 (новый) · СЛОЙ V3 «Режимы линии» — LineMode как интерфейс к ядру
**Priority:** High (P0 идентичности)
**Description:** `LineMode { UGAR, POT, NE_POTEEM, POHUI }` (§17.1) — режим на каждой линии/контроллере, `@Persisted/@DescSynced`, переключение через UI. Меняет `recipeModifier` (скорость/EU/потери/бонус) и профиль роста тильта. Угар=дёшево/криво/потери; Пот=быстро/хрупко/бонус; Не потеем=фасад; Похуй=стабильно/медленно.
**Почему критично:** повторяющийся выбор на КАЖДОМ тире — прямой ответ на «выше = рескин». Идентичность встроена в каждый тир.
**DoD:** игрок ставит режим линии, поведение измеримо меняется; работает на всех тирах.
**Depends:** SKU-80.

### SKU-23 (существует, переприоритет Todo→**P0/High**) · СЛОЙ A «Катастрофа» = честный провал ставки
**Description (переформулировать):** «Горящий пукан» при 100% тильта — плавятся конденсаторы/горят кабели → `burnt_capacitor`/`burnt_cable_debris`, ручной ремонт (SKU-24, §19.4). Теперь это **downside добровольного риска** (игрок сам гнал в «Пот»), а не наказание. Ощущается честно.
**DoD:** катастрофа срабатывает как следствие ставки игрока; `ticksAtMaxTilt` ведёт к событию.
**Depends:** SKU-80 (иначе провал наказывает за то, чего игрок не выбирал).

### SKU-82 (новый) · СЛОЙ V4 «Голос Артура» — Observer реагирует на тильт
**Priority:** Medium (P0 идентичности, дёшево — observer уже built)
**Description:** связать пакет `observer/` + observer-service/BogA с тильт-событиями. Артур глумится над фасадом «Не потеем», эскалирует комментарии при росте тильта/ставок, реагирует на катастрофу, тихо поздравляет в финале. Делает мемы живыми/реактивными вместо статичных имён.
**DoD:** ≥3 контекстных реакции Артура на состояния тильта; работает при запущенном observer-service.
**Depends:** SKU-80 (нужны события ставок/тильта).

### SKU-15 (существует, переприоритет Backlog→**P0/High**) · Вайб как ПОТОЛОК РИСКА
**Description (переформулировать под стек):** вайб через `recipeModifier` **поднимает потолок безопасного тильта** — позволяет гнать выше/дольше без катастрофы (не «обезболивающее», а инструмент бОльшей ставки). C02: вайб не декоративный.
**DoD:** вайб измеримо расширяет безопасную зону риска; связка с SKU-80.

### SKU-78 (новый) · Сауна как «разрешение на бОльшую жадность»
**Priority:** Medium
**Description:** пересмотреть баланс Сауны: окупается тем, что **разрешает гнать тильт выше/дольше безопасно** (больше выгоды от V1), а не экономией EU/t. Тогда игрок строит её чтобы БОЛЬШЕ рисковать, а не чтобы терпеть. Config (SKU-11).
**Depends:** SKU-80, SKU-23.

### V2 «Ложь» (сокрытие информации, §17.4) — ОТЛОЖЕНО
Опциональная фаза максимальной уникальности (машина показывает «0% пота», правда только через диагностику). Дорого: mixin/HUD (§31.5), риск фрустрации. НЕ в P0 — отдельным issue когда/если возьмёмся.

---

## Эра 6 — LuV «Меметический Коллайдер»

> **Зависимость Б1 (аудит §13.4):** все SKU-64…73 зависят от стека идентичности §13.3 — **SKU-80 (V1 соблазн) + SKU-81 (V3 режимы) + SKU-15 (вайб-потолок) + SKU-23 (катастрофа)**. Начинать эндгейм-код только после них.

### SKU-79 (новый, Изм. C) · Рецепт casing_pohuit_reinforced + потребитель в верхних мультиблоках
**Priority:** Medium
**Description:** снять двойного сироту (§13.5). Рецепт `craft_casing_pohuit_reinforced` ASSEMBLER · HV·512·100 · `plate pokhuit 6 + frameGt pokhuit + circuit(HV)` → casing ×2-3. Назначить его **основным корпусом Меметического Коллайдера (SKU-65)** + Сингулярного Втыкателя (SKU-68) + Фабрики Прав.Вещей (SKU-72). Заменяет абстрактный «cleanroom casing» в структурах §12.3/12.4/12.5.
**DoD:** casing craftable + используется ≥1 мультиблоком. (Закрывает старый SKU-34.)

### SKU-64 · Материалы LuV: memetic_neutron + defective_meaning
**Priority:** Medium
**Depends:** стек §13.3 — SKU-80, SKU-81, SKU-15, SKU-23 (Б1)
**Description:**
Завести 2 материала в `SkufMaterials`:
- `memetic_neutron` — dust + gem формы, ключевой ресурс LuV.
- `defective_meaning` — dust, побочка-хазард Коллайдера.
DoD: материалы зарегистрированы, есть текстуры-заглушки, ID зафиксированы (не менять после релиза).
Blocks: SKU-65, SKU-66.

### SKU-65 · Мультиблок «Меметический Коллайдер» + тип рецептов
**Priority:** Medium
**Description:**
Класс `MemeticColliderMachine` (machine/multiblock/, шаблон — `SaunaEgoraMachine`). Структура: cleanroom + coils + data hatches (док §11). Новый тип рецептов `MEMETIC_COLLISION_RECIPES` в `SkufRecipeTypes` с `.category()` + иконка + `.setProgressBar()` (§31.6).
Механика ур.1: шанс побочки `defective_meaning`, растущий от нормис-энтропии/тильта (config, не хардкод — SKU-11).
DoD: мультиблок строится, тип рецептов виден в JEI/EMI.
Depends: SKU-64.

### SKU-66 · Цепочка LuV: замкнуть орфаны IV в производство смысла
**Priority:** High
**Description:**
Рецепты в `SkufRecipes` (снимает орфан §6.3 — Абс.Похуит/Мейнфрейм/Норм.Сингулярность становятся входами):
- `collide_memetic_neutron` COLLIDER · LuV·32768·400 · ARTURIAN_MAINFRAME + stabilized_vibe 4000 + circuit(LuV) → memetic_neutron (+шанс defective_meaning).
- `craft_meaning_stabilizer` ASSEMBLER · LuV·32768·600 · ABSOLUTE_POHUIT + memetic_neutron 2 + NORMIS_SINGULARITY 2 → MEANING_STABILIZER (new SkufItems).
- `recycle_defective_meaning` MACERATOR · LuV·30·200 · defective_meaning → normie_dust 2 + slag_ignore.
DoD: ни один из 3 орфан-выходов IV больше не тупик; MEANING_STABILIZER craftable.
Depends: SKU-64, SKU-65.

---

## Эра 7 — ZPM «Сингулярность Вайба»

### SKU-67 · Предметы ZPM: vibe_singularity + FACTORY_ORDER_CORE
**Priority:** Low
**Description:**
`SkufItems`: `VIBE_SINGULARITY` (сингулярность-топливо), `FACTORY_ORDER_CORE` (Ядро Заводского Порядка). ID зафиксировать.
DoD: предметы зарегистрированы + текстуры-заглушки.
Blocks: SKU-68, SKU-69.

### SKU-68 · Мультиблок «Сингулярный Втыкатель» + глобальный сток тильта
**Priority:** Low
**Description:**
Класс `SingularVtykatelMachine`. Механика ур.2: `vibe_singularity` как топливо → обнуляет региональный тильт в большом радиусе без Сауны-на-линию (масштаб planet vs EV-локальная Сауна). `@Persisted/@DescSynced`, `ITickSubscription` 20–40 тиков, радиус/скорость стока — config.
DoD: втыкатель строится, гасит тильт в радиусе при наличии топлива.
Depends: SKU-67.

### SKU-69 · Цепочка ZPM
**Priority:** Low
**Description:**
- `compress_vibe_singularity` VTYKATEL · ZPM·131072·800 · stabilized_vibe 16000 + MEANING_STABILIZER + condensed_sweat 4000 → VIBE_SINGULARITY.
- `craft_factory_order_core` ASSEMBLER · ZPM·131072·600 · correct_matter gem 4 + VIBE_SINGULARITY + honest_steel plate 8 → FACTORY_ORDER_CORE.
DoD: обе цепочки замкнуты, вход = выход LuV.
Depends: SKU-67, SKU-68.

---

## Эра 8 — UV «Уральское Сердце / Финальная Фабрика»

### SKU-70 · Блок casing_proval_concrete (+ потребитель chelyabinsk_shale)
**Priority:** Medium
**Description:**
Блок-корпус `casing_proval_concrete` в `SkufBlocks`. Рецепт `craft_proval_concrete` MIXER · HV·512·100 · chelyabinsk_shale dust 4 + honest_steel dust + concrete → casing.
**Побочная ценность:** закрывает орфан-вход `chelyabinsk_shale` (§6.4) — первый массовый потребитель. Можно вынести отдельно и сделать раньше остальной Эры 8.
DoD: casing craftable, chelyabinsk_shale больше не орфан.

### SKU-71 · Предметы UV: URAL_HEART + FINAL_FACTORY_FRAME
**Priority:** Low
**Description:**
`SkufItems`: `URAL_HEART` (ядро), `FINAL_FACTORY_FRAME` (каркас).
- `craft_ural_heart` ASSEMBLER · UV·524288·800 · ural_isotope dust 16 + FACTORY_ORDER_CORE + correct_matter gem 8 → URAL_HEART.
- `craft_final_factory_frame` ASSEMBLER · UV·524288·1200 · URAL_HEART + casing_proval_concrete 64 + frameGt pokhuit 8 → FINAL_FACTORY_FRAME.
DoD: оба craftable, вход = выход ZPM + casing.
Depends: SKU-70, SKU-69.

### SKU-72 · Мультиблок «Фабрика Правильных Вещей» (15×15×15) + обращение энтропии
**Priority:** Low
**Description:**
Класс `PravilnyeVeshiFabrikaMachine`, структура 15×15×15 с URAL_HEART. Механика: превращает «нормисный конец» (normie_dust/defective_meaning массово) обратно в correct_matter — обращение энтропии. Дорого по EU, требует FACTORY_ORDER_CORE активным.
DoD: фабрика строится и работает; пик производственной цепочки.
Depends: SKU-71.

---

## Эра 9 — UHV «Деревенский Покой» (ФИНАЛ)

### SKU-40 (существует, переопределить как Эра-9) · item_derevenskiy_pokoy_singularity + финальный рецепт
**Priority:** Low → поднять при подходе к релизу эндгейма
**Description (обновить):**
`SkufItems`: `END_STABILIZER` (Стабилизатор Конца), `DEREVENSKIY_POKOY_SINGULARITY`.
- `craft_end_stabilizer` ASSEMBLER · UHV·2097152·1200 · ABSOLUTE_POHUIT + memetic_neutron 4 + FINAL_FACTORY_FRAME → END_STABILIZER.
- `craft_derevenskiy_pokoy` PGT_GATE · UHV·2097152·2400 · END_STABILIZER + FACTORY_ORDER_CORE 4 + VIBE_SINGULARITY 8 + stabilized_vibe 64000 + гейт-условия → DEREVENSKIY_POKOY_SINGULARITY.
Depends: SKU-72, SKU-73.

### SKU-41 (существует) · Мультиблок pgt_gate «Врата Деревенского Покоя»
**Priority:** Low
**Description:** класс `PgtGateMachine` (каркас как SKUFIZATOR). Хостит финальный рецепт. Активация → триггер датапак-телепорта.

### SKU-73 · Гейт-условия финала (проверка мультиблока, не ингредиенты)
**Priority:** Low
**Description:**
Проверки перед запуском `craft_derevenskiy_pokoy` (§10.3, реш. №10):
- рядом стабильная Сауна Егора; построен/«очищен» Челябинский Провал;
- нулевой активный тильт ключевых линий; ни одного активного «Ваще похуй».
Реализация: проверка структуры/трейтов в recipeModifier (§31.3), не входные предметы.
Depends: механики тильта (SKU-22/23), Сауна (SKU-37), Провал (SKU-30).

### SKU-43 (существует) · ПГТ: биом-датапак + ачивка + трофей
### SKU-44 (существует) · Финальный квест + тихий финал
> Оба остаются как есть — теперь у них есть предмет-ключ (SKU-40) и врата (SKU-41), на которые они завязаны.

---

## Сквозные

### SKU-74 · FTB Quests: главы LuV→UHV + непрерывная спина до финала (Monifactory-style)
**Priority:** Medium
**Description:**
Довести квестбук до эндгейма с «перетеканием» эр как в Monifactory — непрерывная item-гейт спина, без checkmark-разрывов (см. roadmap §12.10).
Механизм: FTB `dependencies` = поле `deps_keys` в `scripts/generate_ftbquests.py` (уже так сшиты Steam→…→Sauna).
Работа в генераторе:
1. `q(...)` для новых предметов (капстоуны + промежуточные), `deps_keys` на капстоун прошлой главы.
2. 4 новых кортежа в `CHAPTERS`: `luv`(6), `zpm`(7), `uv`(8), `uhv`(9).
3. Заменить 3 checkmark-заглушки `e_singularity/e_gate/e_pgt` на item-гейты.
Спина (каждый узел = 1 item-квест):
`ARTURIAN_MAINFRAME → MEANING_STABILIZER → FACTORY_ORDER_CORE → FINAL_FACTORY_FRAME → END_STABILIZER → DEREVENSKIY_POKOY → ачивка ПГТ`.
Проекция глав:
- `luv` капстоун `MEANING_STABILIZER`, dep `ARTURIAN_MAINFRAME`
- `zpm` капстоун `FACTORY_ORDER_CORE`, dep `MEANING_STABILIZER`
- `uv` капстоун `FINAL_FACTORY_FRAME`, dep `FACTORY_ORDER_CORE`
- `uhv` (финал) капстоун `DEREVENSKIY_POKOY_SINGULARITY`, dep `FINAL_FACTORY_FRAME`
Тексты финала — концепт §10.6 / §26.
DoD: от Steam до Деревенского Покоя проходится одной непрерывной цепочкой зависимостей; ни одного `type: "checkmark"`-разрыва в спине.
Depends: контент эр 6–9 (SKU-64…73) — квесты гейтят реальные предметы.

### SKU-75 · Схемы/кабели/материалы-проводники LuV→UHV
**Priority:** Low
**Description:** пере-открыть/расширить SKU-61 (EV+ схемы) до UHV: проводниковый материал на LuV/ZPM/UV, dodik-схемы circuit tier ≥ LuV. Иначе рецепты верхних тиров не собрать (нет схем нужного уровня).

### SKU-76 · Config-баланс верхних тиров (расширение SKU-11)
**Priority:** Low
**Description:** все числа эр 6–9 (EU/t, длительности, шанс defective_meaning, радиус стока vibe_singularity, пороги гейта финала) — в config GTCEu, не хардкод.

### SKU-77 · Перегенерить дерево крафтов (D1/SKU-58) под лестницу
**Priority:** Low
**Description:** после реализации эр 6–9 обновить дерево крафтов — добавились 5 тиров и ~8 новых предметов/материалов.
