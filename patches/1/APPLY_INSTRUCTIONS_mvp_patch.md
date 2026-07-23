# Как применить патч `mvp_circuits_cables_orphans.patch`

Базовый коммит: `7f42c4c` (main). Применять с чистой ветки.

```bash
git checkout main
git checkout -b feat/mvp-circuits-cables-orphans
git apply --check mvp_circuits_cables_orphans.patch   # проверка
git am < mvp_circuits_cables_orphans.patch            # применить с коммитом
# или без коммита:  git apply mvp_circuits_cables_orphans.patch

./gradlew spotlessApply
./gradlew runData      # сгенерить рецепты-датапак
./gradlew build        # У МЕНЯ В ПЕСОЧНИЦЕ НЕТ JDK — собери и проверь у себя!
```

> ⚠️ Я не смог скомпилировать (в песочнице нет JDK). Код выверен по API GTCEu 7.4.0,
> но **обязательно собери `./gradlew build` и запусти `runData`** — если что-то не так,
> кинь лог, поправлю за минуту.

---

## Что внутри (11 файлов)

### Материалы (`SkufMaterials.java`)
- `honestSteel` → +`cableProperties(LV, 2A, loss2)` → авто-генерятся `wireGtSingle`/`cableGtSingle` (LV-кабель).
- `pokhuit` → +`cableProperties(MV, 2A, loss2)` (MV-кабель).
- **НОВЫЙ** `crystallizedDodikSweat` (gem, SHINY, HV) → +`cableProperties(HV, 4A, loss2)` (HV-кабель).
  Текстуры кабеля/провода GTCEu рисует сам по iconSet — рисовать не надо.

### Предметы (`SkufItems.java`) — 3 каскадные схемы
- `DODIK_BOARD` (LV) → `LYUDSKAYA_BOARD` (MV, ест Додик) → `ZAPIZDOSH_MAINFRAME` (HV, ест Людскую).
- Текстуры — **плейсхолдеры** (16×16, я нарисовал заглушки). Замени артом, когда будет.

### Рецепты (`SkufRecipes.java`)
- `circuitsChain()` — крафт 3 схем (каскад LV→MV→HV).
- `machineCrafting()` — **12 рецептов**: LV/MV/HV-сборка для всех 4 машин
  (Normis Filtration, CNC, Pot Distillery, Vibe Stabilizer). Вместо «бесплатного»
  `circuitMeta` теперь тир-схема + тир-кабель. EU/t и материалы растут по тиру.
- `craft_pukan_core` — **вариант B**: ранний ASSEMBLER-источник `PUKAN_CORE` (MV)
  → Скуфизатор собирается в MVP, софт-лока нет.
- `mvpOrphanFixes()`:
  - `condense_sweat` — источник `condensed_sweat` (центрифуга, концентрат пота).
  - `crystallize_dodik_sweat` — источник HV-проводника из `condensed_sweat` + `correct_matter`.
  - `scrub_ugar_gas` — приёмник `ugar_gas` (был дед-энд) → обратно в `puff_smoke`.
- `pravilnaya_vesh` и `myposhko` теперь едят `LYUDSKAYA_BOARD` (а не `circuitMeta`).
- **Дедуп**: удалён `correct_matter_electrolysis` (ELECTROLYZER). Канон Жижняк→Правильная
  материя = **POT_DISTILLERY** (по Roadmap).

### lang (en_us / ru_ru) + модели предметов — добавлены для 3 схем и нового материала.

---

## Что СОЗНАТЕЛЬНО НЕ трогал (по Roadmap — это эры 3–4, не баги)
`charred_developer_circuit`, `melted_capacitor`, `burnt_cable_debris` (дроп «Горящего пукана», Э3),
`slag_ignore` (побочка «Ваще похуй», Э3), `technical_tears`, `warm_vibe_steam` (Сауна, Э4),
`diluted_sweat`/`coolant_of_denial` (Э4). Их «приёмники»-рецепты уже есть — ждут свои машины.

`hidden_sweat` оставил без рецептов: режимы тильта косметические (не потребляют его),
потребителя нет → источник создал бы новый дед-энд. Вернёмся, если введём «цену режимов».

## Числа баланса
Стартовые (EU/t, длительности) из §4а Roadmap. Всё тюнится; если ratio покажется кривым на тесте — скажи, перекину.
