ArthurTech / skufaddon — full project archive (v0.9.1-dev.1)
=============================================================

ЧТО НОВОГО в 0.9.1
------------------
1) EMI: добавлены переводы тегов gtceu (circuits/batteries по тирам, tools/crafting_*,
   chemical_bath_washable и т.д.) в en_us+ru_ru — пропадают «Untranslated tag» warning'и в EMI.
2) Текстуры: сгенерированы иконки для 13 предметов, у которых их не было
   (с рофло-отсылками на концепцию): melted_capacitor, burnt_cable_debris,
   charred_developer_circuit, item_myposhko_script, item_egor_core,
   item_correct_matter_microcapsule, item_lyrika_v_padike, item_antizoomer_core,
   item_correct_developer_schematic, item_normis_singularity, item_absolute_pohuit,
   item_arturian_mainframe, item_derevenskiy_pokoy_singularity.
   (Блоки/машины рендерятся через рендерер GTCEu — у них текстуры уже есть.)

СОДЕРЖИМОЕ
----------
arturtech/   — чистый исходник аддона (40 .java, текстуры+модели предметов,
                build.gradle с dev-зависимостями FTB Quests, run.sh/run.bat).
dist/         — skufaddon-0.9.1-dev.1.jar + ArthurTech_PGT_datapack.zip + ArthurTech_FTBQuests.zip
docs/         — дизайн-док, роадмап, план тестирования, список играбельного, NPC-outline.

КАК ЗАПУСТИТЬ (dev)
------------------
JDK 17 или 21. В папке arthurtech/: run.bat (Windows) или ./run.sh → «1 Play».
Первый запуск долгий (качает Forge/MC/GTCEu + FTB).

FTB QUESTS / PGT
----------------
Книга квестов из dist/ArthurTech_FTBQuests.zip → распаковать в config/ftbquests/quests/.
Датапак PGT из dist/ArthurTech_PGT_datapack.zip → в saves/<мир>/datapacks/.

Сборка вручную:  ./gradlew build  → build/libs/skufaddon-0.9.1-dev.1.jar
