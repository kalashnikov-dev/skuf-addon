#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Monifactory-style FTB Quests datapack (Minecraft 1.20.1 Forge) for ArthurTech / SkufAddon.

Features:
  - Deterministic MD5-based hex IDs (preserves player progress across updates)
  - Monifactory chapter groups (Main Progression vs Special Mechanics)
  - Visual hierarchy: shape (hexagon/gear/square/circle) and size (2.0d/1.8d/1.5d/1.0d)
  - Cross-chapter quest links (quest_links) connecting capstones to next tier entrances
  - Structured 3-part descriptions (&b[Цель], &7[Крафт], &o«Лоровый юмор»)
  - Auto-syncing to run/config/ftbquests/quests and run/saves/*/ftbquests/quests
"""

import os, sys, io, hashlib, shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT = os.path.join(os.path.dirname(__file__), "..", "quests")
QDIR = os.path.join(OUT, "config", "ftbquests", "quests")
CDIR = os.path.join(QDIR, "chapters")
MID = "skufaddon"

# Deterministic ID generation
def det_id(seed: str) -> str:
    return hashlib.md5(seed.encode("utf-8")).hexdigest()[:16].upper()

def esc(s): return s.replace("\\", "\\\\").replace('"', '\\"')
def s_str(s): return '"' + esc(s) + '"'
def s_desc(lines): return "[" + ", ".join(s_str(l) for l in lines) + "]"

# Builders
def t_item(item_id, count=1): return {"k": "item", "item": item_id, "count": count}
def t_tag(tag, count=1):      return {"k": "tag",  "tag": tag,   "count": count}
def t_fluid(fluid_id, mb=1000): return {"k": "fluid", "fluid": fluid_id, "amount": mb}
def t_check():                return {"k": "check"}
def r_item(item_id, count=1): return {"k": "item", "item": item_id, "count": count}
def r_xp(x):                  return {"k": "xp",   "xp": x}

def _full(iid): return iid if ":" in iid else f"{MID}:{iid}"

def emit_task(t, quest_key, idx):
    tid = det_id(f"task:{quest_key}:{idx}")
    o = ["\t\t{", f'\t\t\tid: "{tid}"']
    if t["k"] == "item":
        if t["count"] == 1:
            o += ['\t\t\titem: "%s"' % _full(t["item"]), '\t\t\ttype: "item"']
        else:
            o += ['\t\t\tcount: %dL' % t["count"],
                  '\t\t\titem: { Count: 1, id: "%s" }' % _full(t["item"]),
                  '\t\t\ttype: "item"']
    elif t["k"] == "tag":
        o += ['\t\t\tcount: %dL' % t["count"],
              '\t\t\titem: { Count: 1, id: "itemfilters:tag", tag: { value: "%s" } }' % t["tag"],
              '\t\t\ttype: "item"']
    elif t["k"] == "fluid":
        o += ['\t\t\tamount: %dL' % t["amount"],
              '\t\t\tfluid: "%s"' % _full(t["fluid"]),
              '\t\t\ttype: "fluid"']
    else:
        o += ['\t\t\ttype: "checkmark"']
    o.append("\t\t}")
    return "\n".join(o)

def emit_reward(r, quest_key, idx):
    rid = det_id(f"reward:{quest_key}:{idx}")
    o = ["\t\t{", f'\t\t\tid: "{rid}"']
    if r["k"] == "item":
        if r["count"] == 1:
            o += ['\t\t\titem: "%s"' % _full(r["item"]), '\t\t\ttype: "item"']
        else:
            o += ['\t\t\tcount: %d' % r["count"],
                  '\t\t\titem: { Count: 1, id: "%s" }' % _full(r["item"]),
                  '\t\t\ttype: "item"']
    else:
        o += ['\t\t\ttype: "xp"', f'\t\t\txp: {r["xp"]}']
    o.append("\t\t}")
    return "\n".join(o)

def emit_quest(q, quest_key):
    qid = q["id"]
    o = ["\t{", f'\t\tid: "{qid}"', f'\t\ttitle: {s_str(q["title"])}']
    if q.get("subtitle"):
        o.append(f'\t\tsubtitle: {s_str(q["subtitle"])}')
    if q.get("icon"):
        o.append('\t\ticon: "%s"' % _full(q["icon"]))
    shape = q.get("shape", "circle")
    size = q.get("size", 1.0)
    o += [f'\t\tx: {q["x"]:.1f}d', f'\t\ty: {q["y"]:.1f}d', f'\t\tshape: "{shape}"', f'\t\tsize: {size:.1f}d']
    if q.get("desc"):
        o.append(f'\t\tdescription: {s_desc(q["desc"])}')
    if q.get("deps"):
        o.append('\t\tdependencies: [%s]' % " ".join(f'"{d}"' for d in q["deps"]))
    o.append("\t\ttasks: [")
    o.append("\n".join(emit_task(t, quest_key, i) for i, t in enumerate(q["tasks"])))
    o.append("\t\t]")
    if q.get("rewards"):
        o.append("\t\trewards: [")
        o.append("\n".join(emit_reward(r, quest_key, i) for i, r in enumerate(q["rewards"])))
        o.append("\t\t]")
    o.append("\t}")
    return "\n".join(o)

def emit_quest_link(link_key, linked_quest_id, x, y, shape="hexagon", size=1.5):
    lid = det_id(f"link:{link_key}")
    return "\n".join([
        "\t\t{",
        f'\t\t\tid: "{lid}"',
        f'\t\t\tlinked_quest: "{linked_quest_id}"',
        f'\t\t\tshape: "{shape}"',
        f'\t\t\tsize: {size:.1f}d',
        f'\t\t\tx: {x:.1f}d',
        f'\t\t\ty: {y:.1f}d',
        "\t\t}"
    ])

def emit_chapter(filename, title, icon, order, group_id, quests, links=None):
    cid = det_id(f"chapter:{filename}")
    b = ["{", "\tdefault_hide_dependency_lines: false", '\tdefault_quest_shape: ""',
         f'\tfilename: "{filename}"', f'\tgroup: "{group_id}"',
         '\ticon: "%s"' % _full(icon), f'\tid: "{cid}"', "\timages: [ ]",
         f'\torder_index: {order}', f'\ttitle: {s_str(title)}']
    
    if links:
        b.append("\tquest_links: [")
        b.append(",\n".join(emit_quest_link(k, lq, x, y, sh, sz) for k, lq, x, y, sh, sz in links))
        b.append("\t]")
    else:
        b.append("\tquest_links: [ ]")

    b.append("\tquests: [")
    b.append(",\n".join(emit_quest(Q[k], k) for k in quests))
    b += ["\t]", "}"]
    return "\n".join(b)

# ---------------------------------------------------------------------------
Q = {}
def q(key, **kw):
    kw["id"] = det_id(f"quest:{key}")
    Q[key] = kw
    return kw

GROUP_MAIN = det_id("group:main_progression")
GROUP_MECH = det_id("group:special_mechanics")

# ============================ CHAPTER 1: Steam ============================
q("c1_skufit", title="1.1 · Скуфит из Земли", subtitle="Первый металл Урала", icon="skufit_ingot",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Найти жилу скуфитовой руды.",
        "&7[Крафт]: Копай на глубине в жилах skufit_vein.",
        "&o«Урал не даёт даром. Первые шаги сквозь руду.»"],
  tasks=[t_tag("forge:ores/skufit", 8)], rewards=[r_xp(20)])

q("c1_normie", title="1.2 · Пыль Нормиса", subtitle="Органический катализатор", icon="normie_dust",
  shape="circle", size=1.0, x=-2.5, y=2.0,
  desc=["&b[Цель]: Добыть первую нормисную пыль.",
        "&7[Крафт]: Измельчай плоть или фильтруй отходы.",
        "&o«Из органики выжимаем катализатор заводов.»"],
  tasks=[t_tag("forge:dusts/normie_dust", 4)], rewards=[r_xp(20)], deps_keys=["c1_skufit"])

q("c1_sweat", title="1.3 · Скуфий Пот", subtitle="Жидкий ресурс разработки", icon="sweat",
  shape="circle", size=1.0, x=2.5, y=2.0,
  desc=["&b[Цель]: Собрать первую ведро пота.",
        "&7[Крафт]: Выделяется в фильтрах и миксерах.",
        "&o«Пот и труд всё перетрут.»"],
  tasks=[t_fluid("sweat", 1000)], rewards=[r_xp(20)], deps_keys=["c1_skufit"])

q("c1_skufit_ingot", title="1.4 · Скуфитовый Слиток", subtitle="Основа сплавов", icon="skufit_ingot",
  shape="square", size=1.2, x=0, y=3.0,
  desc=["&b[Цель]: Переплавить руду в чистые слитки.",
        "&7[Крафт]: Печь или плавильня.",
        "&o«Чистый скуфит готовит почву для стали.»"],
  tasks=[t_tag("forge:ingots/skufit", 2)], rewards=[r_xp(30)], deps_keys=["c1_skufit"])

q("c1_steel", title="1.5 · Честная Сталь (Steam Capstone)", subtitle="Капстоун паровой эры", icon="honest_steel_ingot",
  shape="hexagon", size=1.8, x=0, y=5.5,
  desc=["&b[Цель]: Получить Честную Сталь.",
        "&7[Крафт]: Скуфит + нормисная пыль в сплавильне.",
        "&o«Капстоун паровой эры. Пропуск в LV!»"],
  tasks=[t_tag("forge:ingots/honest_steel", 4)], rewards=[r_xp(50)], deps_keys=["c1_skufit_ingot", "c1_normie"])

# ============================ CHAPTER 2: LV ============================
q("c2_hull", title="2.1 · Обугленный Корпус LV", subtitle="Вход в эру электричества", icon="lv_smoldering_pukan",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать первый LV корпус.",
        "&7[Крафт]: 8 плит стали + кабель.",
        "&o«Корпус дымит, но держит напряжение LV.»"],
  tasks=[t_item("lv_smoldering_pukan", 1)], rewards=[r_xp(50)], deps_keys=["c1_steel"])

q("c2_cnc", title="2.2 · LV ЧПУ Станок", subtitle="Точная обработка деталей", icon="lv_cnc",
  shape="gear", size=1.5, x=-2.5, y=2.5,
  desc=["&b[Цель]: Собрать ЧПУ станок.",
        "&7[Крафт]: Корпус + схема + фреза.",
        "&o«Автоматизирует фрезеровку спиц и резцов.»"],
  tasks=[t_item("lv_cnc", 1)], rewards=[r_xp(60)], deps_keys=["c2_hull"])

q("c2_bit", title="2.3 · ЧПУ Резец & Фреза", subtitle="Расходник станков", icon="cnc_cutter",
  shape="circle", size=1.0, x=-4.5, y=2.5,
  desc=["&b[Цель]: Выточить фрезу на ЧПУ.",
        "&7[Крафт]: Пруток стали на ЧПУ станке.",
        "&o«Лезвие режет заготовки без пощады.»"],
  tasks=[t_item("cnc_cutter", 1)], rewards=[r_xp(40)], deps_keys=["c2_cnc"])

q("c2_filter", title="2.4 · LV Фильтр Нормиса", subtitle="Очистка компонентов", icon="lv_filtration",
  shape="gear", size=1.5, x=2.5, y=2.5,
  desc=["&b[Цель]: Собрать элекро-фильтр.",
        "&7[Крафт]: Корпус + фильтр сетка.",
        "&o«Фильтрует тонкую фракцию пылей.»"],
  tasks=[t_item("lv_filtration", 1)], rewards=[r_xp(60)], deps_keys=["c2_hull"])

q("c2_distill", title="2.5 · LV Дистиллятор Пота", subtitle="Фракционирование", icon="lv_distillery",
  shape="gear", size=1.5, x=2.5, y=5.0,
  desc=["&b[Цель]: Перегонка жижняка.",
        "&7[Крафт]: Корпус + труба + нагреватель.",
        "&o«Выделяет материю из жижи.»"],
  tasks=[t_item("lv_distillery", 1)], rewards=[r_xp(60)], deps_keys=["c2_filter"])

q("c2_jizhnyak", title="2.6 · Жижняк", subtitle="Жидкий полупродукт", icon="zhizhnyak",
  shape="square", size=1.2, x=0, y=3.5,
  desc=["&b[Цель]: Замиксить Жижняк.",
        "&7[Крафт]: Нормисная пыль + пот + дым.",
        "&o«Густая субстанция для химических реакций.»"],
  tasks=[t_fluid("zhizhnyak", 1000)], rewards=[r_xp(50)], deps_keys=["c2_hull"])

q("c2_matter", title="2.7 · Правильная Материя", subtitle="Эссенция правильности", icon="correct_matter_gem",
  shape="circle", size=1.2, x=0, y=6.0,
  desc=["&b[Цель]: Выкристаллизовать правильную материю.",
        "&7[Крафт]: Дистилляция жижняка ➔ Автоклав.",
        "&o«Чистейший кристаллоид правильности.»"],
  tasks=[t_tag("forge:gems/correct_matter", 2)], rewards=[r_xp(80)], deps_keys=["c2_jizhnyak", "c2_distill"])

q("c2_dodik1", title="2.8 · Схема Додика I (LV Capstone)", subtitle="Капстоун LV-эры", icon="dodik_circuit_1",
  shape="hexagon", size=1.8, x=0, y=8.5,
  desc=["&b[Цель]: Собрать микросхему Додика I.",
        "&7[Крафт]: Химреактор: плиты + пот + схема.",
        "&o«Первый полноценный процессор. Открывает MV!»"],
  tasks=[t_item("dodik_circuit_1", 1)], rewards=[r_xp(100)], deps_keys=["c2_matter", "c2_bit"])

# ============================ CHAPTER 3: MV ============================
q("c3_dodik2", title="3.1 · Схема Додика II", subtitle="Сердце MV вычислений", icon="dodik_circuit_2",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать плату Додика II.",
        "&7[Крафт]: 2x dodik_1 + плиты похуита.",
        "&o«Удваивает вычислительный похуизм в MV.»"],
  tasks=[t_item("dodik_circuit_2", 1)], rewards=[r_xp(120)], deps_keys=["c2_dodik1"])

q("c3_skufizator", title="3.2 · Скуфизатор (Мультиблок)", subtitle="Каталитический конвертер", icon="skufizator",
  shape="gear", size=1.5, x=-2.5, y=2.5,
  desc=["&b[Цель]: Построить мультиблок Скуфизатор.",
        "&7[Крафт]: Ассемблер: скрипт Мыпошко + правильные вещи.",
        "&o«Удваивает выход похуита из скуфита.»"],
  tasks=[t_item("skufizator", 1)], rewards=[r_xp(150)], deps_keys=["c3_dodik2"])

q("c3_pokhuit", title="3.3 · Рафинированный Похуит", subtitle="Инертный эндгейм сплав", icon="pokhuit_ingot",
  shape="square", size=1.2, x=-2.5, y=5.0,
  desc=["&b[Цель]: Получить слиток Похуита.",
        "&7[Крафт]: Скуфитор: слиток скуфита + пот.",
        "&o«Абсолютно инертный материал.»"],
  tasks=[t_tag("forge:ingots/pokhuit", 4)], rewards=[r_xp(100)], deps_keys=["c3_skufizator"])

q("c3_stab", title="3.4 · Стабилизатор Вайба", subtitle="Гармонизатор", icon="mv_vibe_stabilizer",
  shape="gear", size=1.5, x=2.5, y=2.5,
  desc=["&b[Цель]: Собрать Стабилизатор Вайба.",
        "&7[Крафт]: MV корпус + схема Додика II.",
        "&o«Удерживает колебания вайба под контролем.»"],
  tasks=[t_item("mv_vibe_stabilizer", 1)], rewards=[r_xp(150)], deps_keys=["c3_dodik2"])

q("c3_isotope", title="3.5 · Уральский Изотоп", subtitle="Тяжёлый концентрат", icon="ural_isotope_dust",
  shape="circle", size=1.0, x=2.5, y=5.0,
  desc=["&b[Цель]: Выделит Уральский Изотоп.",
        "&7[Крафт]: Центрифугирование жижняка.",
        "&o«Высокоэнергетический компонент эндгейма.»"],
  tasks=[t_tag("forge:dusts/ural_isotope", 4)], rewards=[r_xp(100)], deps_keys=["c3_stab"])

q("c3_myposhko", title="3.6 · Скрипт Мыпошко", subtitle="Программный алгоритм", icon="myposhko_script",
  shape="circle", size=1.2, x=-1.0, y=7.0,
  desc=["&b[Цель]: Написать скрипт Мыпошко.",
        "&7[Крафт]: Ассемблер: нормисная пыль + вайб.",
        "&o«Скрипт оптимизирует производственный цикл.»"],
  tasks=[t_item("myposhko_script", 1)], rewards=[r_xp(100)], deps_keys=["c3_pokhuit"])

q("c3_vesh", title="3.7 · Правильная Вещь (MV Capstone)", subtitle="Капстоун MV-эры", icon="pravilnaya_vesh",
  shape="hexagon", size=1.8, x=0, y=9.0,
  desc=["&b[Цель]: Создать Правильную Вещь.",
        "&7[Крафт]: Ассемблер: gem + плиты + вайб + dodik_2.",
        "&o«Символ эталона MV. Открывает путь в HV!»"],
  tasks=[t_item("pravilnaya_vesh", 1)], rewards=[r_xp(200)], deps_keys=["c3_myposhko", "c3_isotope"])

# ============================ CHAPTER 4: HV ============================
q("c4_dodik3", title="4.1 · Схема Додика III", subtitle="Процессор высокой плотности", icon="dodik_circuit_3",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать процессор Додика III.",
        "&7[Крафт]: 2x dodik_2 + плиты кристаллизованного пота.",
        "&o«Флагманский процессор HV-эры.»"],
  tasks=[t_item("dodik_circuit_3", 1)], rewards=[r_xp(250)], deps_keys=["c3_vesh"])

q("c4_cap", title="4.2 · Высоковольтный Конденсатор", subtitle="Накопитель энергии", icon="capacitor",
  shape="circle", size=1.0, x=-2.5, y=2.5,
  desc=["&b[Цель]: Собрать конденсатор.",
        "&7[Крафт]: Плиты стали + похуит.",
        "&o«Накапливает разряд. При перегрузке горит.»"],
  tasks=[t_item("capacitor", 1)], rewards=[r_xp(100)], deps_keys=["c4_dodik3"])

q("c4_monitor", title="4.3 · Разбитый Монитор", subtitle="Разгневанный разработчик", icon="broken_monitor_block",
  shape="gear", size=1.5, x=-2.5, y=5.0,
  desc=["&b[Цель]: Сокрушить монитор.",
        "&7[Крафт]: Сожги конденсатор в печи ➔ Блок монитора.",
        "&o«Следствие сожжённого дедлайна.»"],
  tasks=[t_item("broken_monitor_block", 1)], rewards=[r_xp(150)], deps_keys=["c4_cap"])

q("c4_charred", title="4.4 · Обугленная Схема", subtitle="Остатки дедлайна", icon="charred_developer_circuit",
  shape="circle", size=1.0, x=2.5, y=2.5,
  desc=["&b[Цель]: Спасти обугленную схему.",
        "&7[Крафт]: Ассемблер: dodik_2 + шлак-игнор.",
        "&o«Схема подгорела, но всё ещё работает.»"],
  tasks=[t_item("charred_developer_circuit", 1)], rewards=[r_xp(150)], deps_keys=["c4_dodik3"])

q("c4_demo", title="4.5 · Рабочее ДЕМО", subtitle="Продукт к релизу", icon="demo",
  shape="square", size=1.2, x=2.5, y=5.0,
  desc=["&b[Цель]: Собрать ДЕМО версию.",
        "&7[Крафт]: Обугленная схема + скрипт + пыль.",
        "&o«Готово к депрекации на прод.»"],
  tasks=[t_item("demo", 1)], rewards=[r_xp(200)], deps_keys=["c4_charred"])

q("c4_razbor", title="4.6 · Разбор Геймплея (Мультиблок)", subtitle="Аналитический комплекс", icon="razbor_geympleya",
  shape="gear", size=1.5, x=0, y=4.5,
  desc=["&b[Цель]: Собрать Разбор Геймплея.",
        "&7[Крафт]: Ассемблер: DEMO + скрипт Мыпошко.",
        "&o«Разбирает геймплей на технические слёзы.»"],
  tasks=[t_item("razbor_geympleya", 1)], rewards=[r_xp(300)], deps_keys=["c4_monitor", "c4_demo"])

q("c4_tears", title="4.7 · Технические Слёзы (HV Capstone)", subtitle="Капстоун HV-эры", icon="technical_tears_dust",
  shape="hexagon", size=1.8, x=0, y=7.5,
  desc=["&b[Цель]: Выделить Технические Слёзы.",
        "&7[Крафт]: Прогони нормисную сингулярность через Разбор.",
        "&o«Капстоун HV. Открывает Сауну Егора!»"],
  tasks=[t_tag("forge:dusts/technical_tears", 1)], rewards=[r_xp(350)], deps_keys=["c4_razbor"])

# ============================ CHAPTER 5: Sauna ============================
q("c5_sauna", title="5.1 · Ядро Сауны Егора", subtitle="Сердце теплообменника", icon="egor_core",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать Ядро Егора.",
        "&7[Крафт]: Ассемблер: 2 gem + 4 плиты стали + вайб.",
        "&o«Управляет мощными тепловыми потоками.»"],
  tasks=[t_item("egor_core", 1)], rewards=[r_xp(300)], deps_keys=["c4_tears"])

q("c5_egor", title="5.2 · Сауна Егора (Мультиблок)", subtitle="Термальный гигант", icon="sauna_egora",
  shape="gear", size=1.5, x=-2.5, y=2.5,
  desc=["&b[Цель]: Возвести Сауну Егора.",
        "&7[Крафт]: Ядро + 2 правильные вещи + рамы похуита.",
        "&o«Жаркая парилка для загородных жидкостей.»"],
  tasks=[t_item("sauna_egora", 1)], rewards=[r_xp(400)], deps_keys=["c5_sauna"])

q("c5_dense", title="5.3 · Плотный Жижняк", subtitle="Сверхгустой концентрат", icon="dense_jizhnyak_dust",
  shape="circle", size=1.0, x=2.5, y=2.5,
  desc=["&b[Цель]: Получить плотный жижняк.",
        "&7[Крафт]: Сепарация жижняка (2000) в центрифуге.",
        "&o«Густота достигает предела.»"],
  tasks=[t_tag("forge:dusts/dense_jizhnyak", 2)], rewards=[r_xp(200)], deps_keys=["c5_sauna"])

q("c5_shale", title="5.4 · Челябинский Сланец", subtitle="Минерал рафинирования", icon="chelyabinsk_shale_dust",
  shape="circle", size=1.0, x=2.5, y=5.0,
  desc=["&b[Цель]: Добыть Челябинский Сланец.",
        "&7[Крафт]: Копай суровые челябинские жилы.",
        "&o«Каменный компонент для сжатия бетона.»"],
  tasks=[t_tag("forge:ores/chelyabinsk_shale", 4)], rewards=[r_xp(200)], deps_keys=["c5_dense"])

q("c5_coolant", title="5.5 · Запрещённый Хладагент (Sauna Capstone)", subtitle="Капстоун EV-эры", icon="coolant_of_denial_fluid",
  shape="hexagon", size=1.8, x=0, y=6.0,
  desc=["&b[Цель]: Свартить Хладагент Отрицания.",
        "&7[Крафт]: Химия: слёзы + похуит + вода.",
        "&o«Охлаждает самые горячие пуканы эндгейма.»"],
  tasks=[t_fluid("coolant_of_denial", 1000)], rewards=[r_xp(500)], deps_keys=["c5_egor", "c5_shale"])

# ============================ CHAPTER 6: Endgame ============================
q("e_main", title="6.1 · Главный Фрейм Артура", subtitle="Вычислитель Похуизма", icon="arturian_mainframe",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать Mainframe Артура.",
        "&7[Крафт]: 8 плит стали + 4 gem + скрипт + вайб.",
        "&o«Главный мозг эндгейм автоматики.»"],
  tasks=[t_item("arturian_mainframe", 1)], rewards=[r_xp(600)], deps_keys=["c5_coolant"])

q("e_pohuit", title="6.2 · Абсолютный Похуизм", subtitle="Высшая инертность", icon="absolute_pohuit",
  shape="square", size=1.2, x=-2.5, y=2.5,
  desc=["&b[Цель]: Сплавить Absolute Pohuit.",
        "&7[Крафт]: Правильная вещь + изотоп + антизумер-ядро.",
        "&o«Полное равнодушие к законам физики.»"],
  tasks=[t_item("absolute_pohuit", 1)], rewards=[r_xp(700)], deps_keys=["e_main"])

q("e_micro", title="6.3 · Микрокапсула Материи", subtitle="Герметичный контейнер", icon="correct_matter_microcapsule",
  shape="circle", size=1.0, x=2.5, y=2.5,
  desc=["&b[Цель]: Запечатать капсулу.",
        "&7[Крафт]: Gem + плотная жижа + благородный газ.",
        "&o«Хранит стабильную материю.»"],
  tasks=[t_item("correct_matter_microcapsule", 1)], rewards=[r_xp(500)], deps_keys=["e_main"])

q("e_anti", title="6.4 · Антизумерное Ядро", subtitle="Защитный модуль", icon="antizoomer_core",
  shape="gear", size=1.5, x=-2.5, y=5.0,
  desc=["&b[Цель]: Собрать антизумерное ядро.",
        "&7[Крафт]: Gem + плиты + изотоп.",
        "&o«Блокирует клиповое мышление.»"],
  tasks=[t_item("antizoomer_core", 1)], rewards=[r_xp(600)], deps_keys=["e_pohuit"])

q("e_schem", title="6.5 · Схема Разработчика", subtitle="Архитектурный чертёж", icon="correct_developer_schematic",
  shape="circle", size=1.0, x=2.5, y=5.0,
  desc=["&b[Цель]: Начертить правильную схему.",
        "&7[Крафт]: Обугленная схема + gem + вайб.",
        "&o«Идеальный чертёж без багов.»"],
  tasks=[t_item("correct_developer_schematic", 1)], rewards=[r_xp(600)], deps_keys=["e_micro"])

q("e_singfrag", title="6.6 · Сингулярность Нормиса (Endgame Capstone)", subtitle="Капстоун Абсолютного Похуизма", icon="normis_singularity",
  shape="hexagon", size=1.8, x=0, y=6.0,
  desc=["&b[Цель]: Сжать Сингулярность Нормиса.",
        "&7[Крафт]: 16 нормисной пыли + 4 шлак-игнора.",
        "&o«Капстоун эндгейма. Открывает LuV!»"],
  tasks=[t_item("normis_singularity", 1)], rewards=[r_xp(800)], deps_keys=["e_anti", "e_schem"])

# ============================ CHAPTER 7: LuV ============================
q("luv_collider", title="7.1 · Усиленный Похуитовый Корпус", subtitle="Вход в LuV эру", icon="casing_pohuit_reinforced",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Собрать усиленный корпус.",
        "&7[Крафт]: 6 плит похуита + фрейм + Людская плата.",
        "&o«Выдерживает колоссальные меметические нагрузки.»"],
  tasks=[t_item("casing_pohuit_reinforced", 1)], rewards=[r_xp(600)], deps_keys=["e_singfrag"])

q("luv_neutron", title="7.2 · Меметический Нейтрон", subtitle="Субатомный смысл", icon="memetic_neutron_dust",
  shape="gear", size=1.5, x=-2.5, y=2.5,
  desc=["&b[Цель]: Синтезировать меметический нейтрон.",
        "&7[Крафт]: Меметический Коллайдер: столкновение смыслов.",
        "&o«Фиолетовый кристаллоид фундаментальной логики.»"],
  tasks=[t_item("memetic_neutron_dust", 1)], rewards=[r_xp(700)], deps_keys=["luv_collider"])

q("luv_defective", title="7.3 · Дефектный Смысл", subtitle="Побочный продукт распада", icon="defective_meaning_dust",
  shape="gear", size=1.5, x=2.5, y=2.5,
  desc=["&b[Цель]: Отсепарировать дефектный смысл.",
        "&7[Крафт]: Центрифуга: 2x defective_meaning ➔ normie_dust + slag_ignore.",
        "&o«Опасные отходы сепарируются на полезный шлак.»"],
  tasks=[t_item("defective_meaning_dust", 1)], rewards=[r_xp(700)], deps_keys=["luv_collider"])

q("luv_stabilizer", title="7.4 · Стабилизатор Смысла (LuV Capstone)", subtitle="Капстоун LuV-эры", icon="absolute_pohuit",
  shape="hexagon", size=1.8, x=0, y=5.5,
  desc=["&b[Цель]: Собрать Стабилизатор Смысла.",
        "&7[Крафт]: ABSOLUTE_POHUIT + memetic_neutron + NORMIS_SINGULARITY.",
        "&o«Капстоун LuV. Смысл зафиксирован навечно!»"],
  tasks=[t_item("absolute_pohuit", 1)], rewards=[r_xp(1000)], deps_keys=["luv_neutron", "luv_defective"])

# ============================ CHAPTER 8: ZPM ============================
q("zpm_vtykatel", title="8.1 · Сингулярный Втыкатель", subtitle="Вход в ZPM эру", icon="vibe_singularity",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Построить Сингулярный Втыкатель.",
        "&7[Крафт]: Мультиблок сжатия вайба ZPM класса.",
        "&o«Гасит тильт и прессует вайб в точку.»"],
  tasks=[t_item("vibe_singularity", 1)], rewards=[r_xp(800)], deps_keys=["luv_stabilizer"])

q("zpm_singularity", title="8.2 · Сингулярность Вайба", subtitle="Астральный сгусток", icon="vibe_singularity",
  shape="gear", size=1.5, x=-2.5, y=2.5,
  desc=["&b[Цель]: Сжать Сингулярность Вайба.",
        "&7[Крафт]: Автоклав: 16B вайба + 4B пота + 2x correct_matter.",
        "&o«Сияющий астральный шар чистейшего настроения.»"],
  tasks=[t_item("vibe_singularity", 1)], rewards=[r_xp(900)], deps_keys=["zpm_vtykatel"])

q("zpm_core", title="8.3 · Ядро Заводского Порядка (ZPM Capstone)", subtitle="Капстоун ZPM-эры", icon="factory_order_core",
  shape="hexagon", size=1.8, x=0, y=5.5,
  desc=["&b[Цель]: Собрать Ядро Заводского Порядка.",
        "&7[Крафт]: Ассемблер: vibe_singularity + correct_matter + dodik_3.",
        "&o«Капстоун ZPM. Идеальный фабричный порядок!»"],
  tasks=[t_item("factory_order_core", 1)], rewards=[r_xp(1200)], deps_keys=["zpm_singularity"])

# ============================ CHAPTER 9: UV ============================
q("uv_concrete", title="9.1 · Провальный Бетон", subtitle="Вход в UV эру", icon="casing_proval_concrete",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Замешать Провальный Бетон.",
        "&7[Крафт]: Миксер: челябинский сланец + сталь + бетон.",
        "&o«Сверхпрочный блочный каркас для мегафабрик.»"],
  tasks=[t_item("casing_proval_concrete", 1)], rewards=[r_xp(1000)], deps_keys=["zpm_core"])

q("uv_frame", title="9.2 · Каркас Финальной Фабрики (UV Capstone)", subtitle="Капстоун UV-эры", icon="casing_proval_concrete",
  shape="hexagon", size=1.8, x=0, y=4.5,
  desc=["&b[Цель]: Построить Каркас Фабрики 15x15x15.",
        "&7[Крафт]: Провальный бетон + правильная вещь.",
        "&o«Капстоун UV. Остов величайшего завода!»"],
  tasks=[t_item("casing_proval_concrete", 1)], rewards=[r_xp(1500)], deps_keys=["uv_concrete"])

# ============================ CHAPTER 10: UHV ============================
q("uhv_gate", title="10.1 · Врата Деревенского Покоя", subtitle="Вход в финал UHV", icon="arturian_mainframe",
  shape="hexagon", size=2.0, x=0, y=0,
  desc=["&b[Цель]: Открыть Врата Деревенского Покоя.",
        "&7[Крафт]: Главный Фрейм Артура + Ядро Порядка.",
        "&o«Портал в мирную жизнь без багов и тильта.»"],
  tasks=[t_item("arturian_mainframe", 1)], rewards=[r_xp(2000)], deps_keys=["uv_frame"])

q("uhv_final", title="10.2 · Деревенский Покой (ФИНАЛ)", subtitle="Финишный капстоун ArthurTech", icon="normis_singularity",
  shape="hexagon", size=2.5, x=0, y=5.0,
  desc=["&b[Цель]: Достичь Деревенского Покоя.",
        "&7[Крафт]: Врата Покоя ➔ Сингулярность Нормиса.",
        "&o«Победа! Вы полностью прошли ArthurTech: Правильные Вещи!»"],
  tasks=[t_item("normis_singularity", 1)], rewards=[r_xp(5000)], deps_keys=["uhv_gate"])

# Resolve deps_keys
for key, quest in Q.items():
    dk = quest.pop("deps_keys", None)
    if dk:
        quest["deps"] = [Q[k]["id"] for k in dk]

# CHAPTERS definition
CHAPTERS = [
    ("steam",   "1 · Грязный двор (Steam)",            "skufit_ingot",
     ["c1_skufit", "c1_normie", "c1_sweat", "c1_skufit_ingot", "c1_steel"], None),
    ("lv",      "2 · ЧПУ-станкчанин (LV)",             "dodik_circuit_1",
     ["c2_hull", "c2_cnc", "c2_bit", "c2_filter", "c2_distill", "c2_jizhnyak", "c2_matter", "c2_dodik1"],
     [("link_c1_steel", Q["c1_steel"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("mv",      "3 · Разрабская неоднозначность (MV)",  "dodik_circuit_2",
     ["c3_dodik2", "c3_skufizator", "c3_pokhuit", "c3_stab", "c3_isotope", "c3_myposhko", "c3_vesh"],
     [("link_c2_dodik1", Q["c2_dodik1"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("hv",      "4 · Разбор Геймплея (HV)",             "dodik_circuit_3",
     ["c4_dodik3", "c4_cap", "c4_monitor", "c4_charred", "c4_demo", "c4_razbor", "c4_tears"],
     [("link_c3_vesh", Q["c3_vesh"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("sauna",   "5 · Сауна и Челябинск (HV/EV)",        "egor_core",
     ["c5_sauna", "c5_egor", "c5_dense", "c5_shale", "c5_coolant"],
     [("link_c4_tears", Q["c4_tears"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("endgame", "6 · Абсолютный Похуизм (эндгейм)",     "arturian_mainframe",
     ["e_main", "e_pohuit", "e_micro", "e_anti", "e_schem", "e_singfrag"],
     [("link_c5_coolant", Q["c5_coolant"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("luv",     "7 · Распадение Смысла (LuV)",         "casing_pohuit_reinforced",
     ["luv_collider", "luv_neutron", "luv_defective", "luv_stabilizer"],
     [("link_e_singfrag", Q["e_singfrag"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("zpm",     "8 · Сингулярный Порядок (ZPM)",       "vibe_singularity",
     ["zpm_vtykatel", "zpm_singularity", "zpm_core"],
     [("link_luv_stabilizer", Q["luv_stabilizer"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("uv",      "9 · Обращение Энтропии (UV)",          "casing_proval_concrete",
     ["uv_concrete", "uv_frame"],
     [("link_zpm_core", Q["zpm_core"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
    ("uhv",     "10 · Деревенский Покой (UHV)",        "normis_singularity",
     ["uhv_gate", "uhv_final"],
     [("link_uv_frame", Q["uv_frame"]["id"], 0.0, -2.5, "hexagon", 1.5)]),
]

# Write SNBT files
os.makedirs(CDIR, exist_ok=True)

# Write data.snbt
with open(os.path.join(QDIR, "data.snbt"), "w", encoding="utf-8") as f:
    f.write("""{
	default_autoclaim_rewards: "disabled"
	default_consume_items: false
	default_quest_disable_jei: false
	default_quest_shape: "circle"
	default_reward_team: false
	detection_delay: 20
	disable_gui: false
	drop_book_on_death: false
	drop_loot_crates: false
	emergency_items_cooldown: 300
	grid_scale: 0.5d
	hide_excluded_quests: false
	lock_message: ""
	loot_crate_no_drop: { boss: 0, monster: 600, passive: 4000 }
	pause_game: false
	progression_mode: "flexible"
	show_lock_icons: true
	title: "ArthurTech: Правильные Вещи"
	version: 13
}
""")

# Write chapter_groups.snbt
with open(os.path.join(QDIR, "chapter_groups.snbt"), "w", encoding="utf-8") as f:
    f.write(f"""{{
	chapter_groups: [
		{{ id: "{GROUP_MAIN}", title: "Основная Прогрессия (Main Progression)" }}
		{{ id: "{GROUP_MECH}", title: "Спец-структуры и Механики (Special Mechanics)" }}
	]
}}
""")

# Write chapters
for order, (fn, title, icon, keys, links) in enumerate(CHAPTERS):
    text = emit_chapter(fn, title, icon, order, GROUP_MAIN, keys, links)
    with open(os.path.join(CDIR, fn + ".snbt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

# Sync to run/config/ftbquests/quests
RUN_QDIR = os.path.join(os.path.dirname(__file__), "..", "run", "config", "ftbquests", "quests")
if os.path.exists(os.path.dirname(RUN_QDIR)):
    if os.path.exists(RUN_QDIR):
        shutil.rmtree(RUN_QDIR)
    shutil.copytree(QDIR, RUN_QDIR)
    print("Synced to run dir:", os.path.abspath(RUN_QDIR))

# Sync to run/saves/*/ftbquests/quests and reset stale player progress files
SAVES_DIR = os.path.join(os.path.dirname(__file__), "..", "run", "saves")
if os.path.exists(SAVES_DIR):
    for w in os.listdir(SAVES_DIR):
        w_path = os.path.join(SAVES_DIR, w)
        if os.path.isdir(w_path):
            ftb_dir = os.path.join(w_path, "ftbquests")
            target_q = os.path.join(ftb_dir, "quests")
            os.makedirs(ftb_dir, exist_ok=True)
            if os.path.exists(target_q):
                shutil.rmtree(target_q)
            shutil.copytree(QDIR, target_q)
            # Remove stale player progress SNBT files to avoid old quest ID mismatch exceptions
            for item in os.listdir(ftb_dir):
                if item.endswith(".snbt") and item != "data.snbt":
                    try:
                        os.remove(os.path.join(ftb_dir, item))
                    except Exception:
                        pass
    print("Synced to all world saves in:", os.path.abspath(SAVES_DIR))

print("Generated:", os.path.abspath(QDIR))
print("Chapters:", ", ".join(c[0] for c in CHAPTERS))
print("Quests total:", len(Q))
