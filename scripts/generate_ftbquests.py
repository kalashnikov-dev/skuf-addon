#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a COMPLETE FTB Quests datapack (Minecraft 1.20.1 Forge) for ArthurTech / SkufAddon.

Every quest task references a REAL id taken from SkufRecipes.java / SkufItems / SkufMaterials
(git 6e48f37). Nothing aspirational except the final 3 endgame quests (singularity / gate /
PGT), which are marked LOCKED because the code for them doesn't exist yet.

Coverage (all craftable today):
  ores -> skufit / pokhuit / chelyabinsk_shale
  filtration: water->sweat, rotten_flesh->normie_dust(+sweat)
  bootstrap: macerator rotten_flesh->normie_dust ; centrifuge normie->puff_smoke
  honest_steel alloy ; jizhnyak (mixer) ; correct_matter (distillery+autoclave)
  ural_isotope (centrifuge) ; condensed_sweat ; crystallized_dodik_sweat
  hulls smoldering_pukan LV/MV/HV ; 4 machines x3 tiers (cnc/filtration/distillery/vibe)
  circuits dodik_1/2/3 ; cnc_bit/cnc_cutter ; pravilnaya_vesh ; stabilized_vibe ; pokhuit refine
  recycling: capacitor->burnt->repair ; burnt_cable_debris loop
  myposhko_script ; comfort technical_tears
  sauna: egor_core -> SAUNA_EGORA multiblock ; warm_vibe_steam ; coolant_of_denial
  gameplay breakdown: capacitor -> broken_monitor_block -> charred_circuit -> demo
                      -> RAZBOR_GEYMPLAYA multiblock -> technical_tears (fluid/dust)
  endgame components: dense_jizhnyak, padik_noble_gas, normis_singularity, antizoomer_core,
                      correct_developer_schematic, absolute_pohuit, correct_matter_microcapsule,
                      arturian_mainframe
  LOCKED (not in code): derevenskiy_pokoy singularity, pgt_gate, PGT dimension.

Referencing rules:
  - our items      -> "skufaddon:<id>"                 (verified)
  - our machines   -> "skufaddon:<tier>_<base>"        (lv_/mv_/hv_)
  - our multiblocks -> "skufaddon:<id>"  (sauna_egora, razbor_geympleya)
  - our hull       -> "skufaddon:<tier>_smoldering_pukan"
  - GTCEu material item -> forge tag via itemfilters:tag  (forge:dusts/<m>, ingots, gems, plates)
  - GTCEu material block/frame -> "skufaddon:<m>_block" / "skufaddon:<m>_frame"
  - fluids / tilt / entropy -> checkmark placeholder (convert to fluid/stat task in editor)
"""

import os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Tracked datapack source lives in <repo>/quests/ (committed for the PR).
# Copy quests/config/ftbquests/quests/* into run/config/ftbquests/quests/ to test in-game.
OUT = os.path.join(os.path.dirname(__file__), "..", "quests")
QDIR = os.path.join(OUT, "config", "ftbquests", "quests")
CDIR = os.path.join(QDIR, "chapters")
MID = "skufaddon"

_counters = {"Q": 0, "T": 0, "R": 0, "C": 0}
def new_id(kind):
    _counters[kind] += 1
    pn = {"Q": "A", "T": "7", "R": "2", "C": "5"}[kind]
    return pn + f"{_counters[kind]:015X}"

def esc(s): return s.replace("\\", "\\\\").replace('"', '\\"')
def s_str(s): return '"' + esc(s) + '"'
def s_desc(lines): return "[" + ", ".join(s_str(l) for l in lines) + "]"

# task/reward builders -------------------------------------------------------
def t_item(item_id, count=1): return {"k": "item", "item": item_id, "count": count}
def t_tag(tag, count=1):      return {"k": "tag",  "tag": tag,   "count": count}
def t_fluid(fluid_id, mb=1000): return {"k": "fluid", "fluid": fluid_id, "amount": mb}
def t_check():                return {"k": "check"}
def r_item(item_id, count=1): return {"k": "item", "item": item_id, "count": count}
def r_xp(x):                  return {"k": "xp",   "xp": x}

def _full(iid): return iid if ":" in iid else f"{MID}:{iid}"

def emit_task(t):
    # FTB Quests 1.20.1 SNBT. Item stacks MUST carry Count (a bare `{ id }` with no
    # Count deserializes as an empty stack → renders as AIR). Match Monifactory format.
    tid = new_id("T")
    o = ["\t\t{", f'\t\t\tid: "{tid}"']
    if t["k"] == "item":
        # bare-string form for count==1, compound with count: NL otherwise
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

def emit_reward(r):
    rid = new_id("R")
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

def emit_quest(q):
    o = ["\t{", f'\t\tid: "{q["id"]}"', f'\t\ttitle: {s_str(q["title"])}']
    if q.get("icon"):
        o.append('\t\ticon: "%s"' % _full(q["icon"]))
    o += [f'\t\tx: {q["x"]:.1f}d', f'\t\ty: {q["y"]:.1f}d', '\t\tshape: "circle"']
    if q.get("desc"):
        o.append(f'\t\tdescription: {s_desc(q["desc"])}')
    if q.get("deps"):
        o.append('\t\tdependencies: [%s]' % " ".join(f'"{d}"' for d in q["deps"]))
    o.append("\t\ttasks: [")
    o.append("\n".join(emit_task(t) for t in q["tasks"]))
    o.append("\t\t]")
    if q.get("rewards"):
        o.append("\t\trewards: [")
        o.append("\n".join(emit_reward(r) for r in q["rewards"]))
        o.append("\t\t]")
    o.append("\t}")
    return "\n".join(o)

def emit_chapter(filename, title, icon, order, quests):
    cid = new_id("C")
    b = ["{", "\tdefault_hide_dependency_lines: false", '\tdefault_quest_shape: ""',
         f'\tfilename: "{filename}"', '\tgroup: ""',
         '\ticon: "%s"' % _full(icon), f'\tid: "{cid}"', "\timages: [ ]",
         f'\torder_index: {order}', f'\ttitle: {s_str(title)}', "\tquest_links: [ ]", "\tquests: ["]
    b.append("\n".join(emit_quest(q) for q in quests))
    b += ["\t]", "}"]
    return "\n".join(b)

# ---------------------------------------------------------------------------
Q = {}
def q(key, **kw):
    kw["id"] = new_id("Q"); Q[key] = kw; return kw

# ============================ CHAPTER 1: Grязный двор (Steam/старт) =========
q("c1_skufit", title="Скуфит из земли", icon="skufit_ingot", x=0, y=0,
  desc=["&7Урал не даёт даром. Найди жилу скуфита и накопай руды.",
        "&8(жилы skufit_vein / pokhuit_vein на глубине)"],
  tasks=[t_tag("forge:ores/skufit", 8)], rewards=[r_xp(20)])
q("c1_flesh", title="Мусор — это ресурс", icon="minecraft:rotten_flesh", x=1.5, y=0,
  desc=["&7Гнилая плоть — сырьё для нормисной пыли.",
        "&aBootstrap починен: мацератор даёт первую пыль без завода."],
  tasks=[t_item("minecraft:rotten_flesh", 8)], rewards=[r_xp(10)])
q("c1_normie", title="Отдели нормисное", icon="normie_dust_dust", x=1.5, y=1.5,
  desc=["&7Прогони плоть через мацератор (или фильтр) → нормисная пыль.",
        "«Очисти мысли от лишнего. Даже если сам пока не чистый.»"],
  tasks=[t_tag("forge:dusts/normie_dust", 4)], rewards=[r_xp(20)],
  deps_keys=["c1_flesh"])
q("c1_skufit_ingot", title="Первый слиток", icon="skufit_ingot", x=0, y=1.5,
  desc=["&7Переплавь скуфит в слиток — основа всего металла."],
  tasks=[t_tag("forge:ingots/skufit", 2)], rewards=[r_xp(20)],
  deps_keys=["c1_skufit"])
q("c1_steel", title="Честная сталь", icon="honest_steel_ingot", x=0.75, y=3,
  desc=["&7Скуфит + нормисная пыль в сплавильне → &fчестная сталь&7.",
        "«Не бывает чистого металла из грязных рук. Но твоя — честная.»"],
  tasks=[t_tag("forge:ingots/honest_steel", 4)], rewards=[r_xp(40)],
  deps_keys=["c1_normie", "c1_skufit_ingot"])
q("c1_sweat", title="Пот не льётся сам", icon="sweat_bucket", x=3, y=1.5,
  desc=["&7Фильтр Нормиса: вода → пот (медленно). Или плоть → пыль + пот.",
        "«Постой, потей, жди.»"],
  tasks=[t_fluid("sweat", 1000)], rewards=[r_xp(20)], deps_keys=["c1_normie"])

# ============================ CHAPTER 2: ЧПУ-станкчанин (LV) ================
q("c2_hull", title="Тлеющий пукан (корпус LV)", icon="lv_smoldering_pukan", x=0, y=0,
  desc=["&7Корпус всех машин: 8 плит честной стали + кабель, крафт в сетке.",
        "«Он уже тлеет. Как и ты.»"],
  tasks=[t_item("lv_smoldering_pukan", 1)], rewards=[r_xp(30)], deps_keys=["c1_steel"])
q("c2_dodik1", title="Плата дятла (LV)", icon="dodik_circuit_1", x=1.5, y=0,
  desc=["&7Химреактор: 2 плиты стали + пот + схема(1) → dodik_circuit_1.",
        "«Схема кривая, как её сборщик. Но ток проводит.»"],
  tasks=[t_item("dodik_circuit_1", 2)], rewards=[r_item("dodik_circuit_1", 1), r_xp(30)],
  deps_keys=["c2_hull"])
q("c2_cnc", title="Первый станок", icon="cnc_bit", x=0.75, y=1.5,
  desc=["&7Собери &fLV ЧПУ-станок&7 (корпус + схема + кабель + фреза).",
        "«Настоящий человек делает станок, чтобы станок страдал вместо него.»"],
  tasks=[t_item("lv_cnc_machine", 1)], rewards=[r_item("cnc_bit", 2), r_xp(40)],
  deps_keys=["c2_dodik1"])
q("c2_filter", title="Фильтр под напряжением", icon="lv_normis_filtration_machine", x=2.5, y=1.5,
  desc=["&7Собери &fLV Фильтр Нормиса&7 — электрическая очистка пыли."],
  tasks=[t_item("lv_normis_filtration_machine", 1)], rewards=[r_xp(40)],
  deps_keys=["c2_dodik1"])
q("c2_bit", title="Фрезы и резцы", icon="cnc_cutter", x=0.75, y=3,
  desc=["&7На ЧПУ точи &fcnc_bit&7 из прутка, затем собирай &fcnc_cutter&7."],
  tasks=[t_item("cnc_bit", 4), t_item("cnc_cutter", 1)], rewards=[r_xp(40)],
  deps_keys=["c2_cnc"])
q("c2_distill", title="Дистилляция пота", icon="lv_pot_distillery", x=4, y=1.5,
  desc=["&7Собери &fLV Дистиллятор пота&7. Жижняк → правильная материя."],
  tasks=[t_item("lv_pot_distillery", 1)], rewards=[r_xp(40)], deps_keys=["c2_dodik1"])
q("c2_jizhnyak", title="Первая жижа", icon="jizhnyak_bucket", x=4, y=3,
  desc=["&7Миксер: нормисная пыль + пот + пых-дым → &fжижняк&7.",
        "«Мир не обязан быть удобным.»"],
  tasks=[t_fluid("jizhnyak", 1000)], rewards=[r_xp(30)], deps_keys=["c2_distill"])
q("c2_matter", title="Правильная материя", icon="correct_matter_gem", x=4, y=4.5,
  desc=["&7Дистиллируй жижняк → &fcorrect_matter&7 (dust), затем автоклав → gem.",
        "«Концентрированная мудрость.»"],
  tasks=[t_tag("forge:gems/correct_matter", 2)], rewards=[r_xp(60)], deps_keys=["c2_jizhnyak"])

# ============================ CHAPTER 3: Разрабская неоднозначность (MV) ====
q("c3_dodik2", title="Людская плата (MV)", icon="dodik_circuit_2", x=0, y=0,
  desc=["&72x dodik_1 + 2 плиты похуита + схема(2) → dodik_circuit_2."],
  tasks=[t_item("dodik_circuit_2", 2)], rewards=[r_xp(60)], deps_keys=["c2_dodik1"])
q("c3_skufizator", title="Скуфизатор", icon="skufizator", x=4, y=1.5,
  desc=["&7Собери мультиблок &fСкуфизатор&7 (ассемблер: скрипт Мыпошко + 2 правильные вещи + жижняк-лосс 2000).",
        "«Скуфизация — это когда ты наконец перестал делать вид, что скуфита достаточно.»"],
  tasks=[t_item("skufizator", 1)], rewards=[r_xp(120)], deps_keys=["c3_vesh", "c3_myposhko"])
q("c3_pokhuit", title="Похуит из скуфита", icon="pokhuit_ingot", x=4, y=3,
  desc=["&7Скуфизатор (SKUFIZATION): слиток скуфита + пот 250 → &f2× похуит&7.",
        "«Дешёвая ферма похуита прямо из скуфита. Философия в промышленных масштабах.»"],
  tasks=[t_tag("forge:ingots/pokhuit", 4)], rewards=[r_xp(60)], deps_keys=["c3_skufizator"])
q("c3_stab", title="Стабилизируй вайб", icon="mv_vibe_stabilizer", x=0.75, y=1.5,
  desc=["&7Собери &fMV Стабилизатор вайба&7. correct_matter + пот → stabilized_vibe.",
        "«Хаос вокруг? Просто стабилизируй вайб.»"],
  tasks=[t_item("mv_vibe_stabilizer", 1)], rewards=[r_xp(60)], deps_keys=["c3_dodik2"])
q("c3_isotope", title="Уральский изотоп", icon="ural_isotope_dust", x=2.5, y=1.5,
  desc=["&7Центрифуга: жижняк → &fural_isotope&7 (+ пот).",
        "«Радиация не прощает, но платит за смелость.»"],
  tasks=[t_tag("forge:dusts/ural_isotope", 4)], rewards=[r_xp(80)], deps_keys=["c3_dodik2"])
q("c3_vesh", title="Правильная Вещь", icon="pravilnaya_vesh", x=0.75, y=3,
  desc=["&7Ассемблер: 2 gem correct_matter + плиты + резец + вайб + dodik_2 → &fPRAVILNAYA VESH&7.",
        "«Ты не знаешь, зачем она. Но чувствуешь: без неё дальше нельзя.»"],
  tasks=[t_item("pravilnaya_vesh", 1)], rewards=[r_xp(120)], deps_keys=["c3_stab", "c2_matter"])
q("c3_myposhko", title="Скрипт Мыпошко", icon="myposhko_script", x=2.5, y=3,
  desc=["&7Ассемблер: нормисная пыль + gem + вайб + dodik_2 → &fmyposhko_script&7."],
  tasks=[t_item("myposhko_script", 1)], rewards=[r_xp(80)], deps_keys=["c3_stab"])

# ============================ CHAPTER 4: Разбор Геймплея (HV) ===============
q("c4_dodik3", title="Запиздош-мейнфрейм (HV)", icon="dodik_circuit_3", x=0, y=0,
  desc=["&72x dodik_2 + 2 плиты кристаллизованного дожик-пота + схема(3) → dodik_circuit_3."],
  tasks=[t_item("dodik_circuit_3", 2)], rewards=[r_xp(100)], deps_keys=["c3_dodik2"])
q("c4_cap", title="Конденсатор", icon="capacitor", x=1.5, y=0,
  desc=["&7Ассемблер: плиты стали + похуит → &fcapacitor&7. Сгорит — будет burnt_capacitor."],
  tasks=[t_item("capacitor", 1)], rewards=[r_xp(60)], deps_keys=["c3_pokhuit"])
q("c4_monitor", title="Разбитый монитор", icon="block_broken_monitor", x=1.5, y=1.5,
  desc=["&7Сожги конденсатор в дуговой печи → burnt_capacitor → собери &fблок разбитого монитора&7.",
        "«12 таких — и получится терминал правды.»"],
  tasks=[t_item("block_broken_monitor", 4)], rewards=[r_xp(80)], deps_keys=["c4_cap"])
q("c4_charred", title="Обугленная схема", icon="charred_developer_circuit", x=0, y=1.5,
  desc=["&7Ассемблер: dodik_2 + шлак-игнор + вайб → &fcharred_developer_circuit&7."],
  tasks=[t_item("charred_developer_circuit", 1)], rewards=[r_xp(80)], deps_keys=["c4_dodik3"])
q("c4_demo", title="Демка", icon="demo", x=0.75, y=3,
  desc=["&7Обугленная схема + скрипт Мыпошко + пыль + вайб → &fDEMO&7.",
        "«То, что ты показываешь. Не то, что работает.»"],
  tasks=[t_item("demo", 1)], rewards=[r_xp(100)], deps_keys=["c4_charred", "c3_myposhko"])
q("c4_razbor", title="Разбор Геймплея", icon="razbor_geympleya", x=0.75, y=4.5,
  desc=["&7Собери мультиблок &fРазбор Геймплея&7 (ассемблер: DEMO + скрипт Мыпошко +",
        "2× обугленная схема + 4× обгоревший кабель + пых-дым 2000).",
        "«Для просмотра демок и девочек в Twitch. Мониторы уже разбиты заранее — экономит время.»"],
  tasks=[t_item("razbor_geympleya", 1)], rewards=[r_xp(200)], deps_keys=["c4_monitor", "c4_demo"])
q("c4_tears", title="Технические слёзы", icon="technical_tears_dust", x=2.5, y=4.5,
  desc=["&7Прогони &f2× нормисную сингулярность&7 через Разбор → technical_tears 1000 (fluid),",
        "высуши в центрифуге → dust.",
        "«Тут ты и понял, сколько было спрятано.»"],
  tasks=[t_tag("forge:dusts/technical_tears", 1)], rewards=[r_xp(120)], deps_keys=["c4_razbor"])

# ============================ CHAPTER 5: Сауна и Челябинск (HV/EV) ==========
q("c5_dense", title="Плотная жижа", icon="jizhnyak_bucket", x=0, y=0,
  desc=["&7Центрифуга: жижняк(2000) → &fdense_jizhnyak&7 + zhizhnyak_loss.",
        "«Густая правда оседает на дне.»"],
  tasks=[t_fluid("dense_jizhnyak", 1000)], rewards=[r_xp(80)], deps_keys=["c4_dodik3"])
q("c5_shale", title="Челябинский сланец", icon="chelyabinsk_shale_dust", x=1.5, y=0,
  desc=["&7Накопай &fchelyabinsk_shale&7 — нужен для рафинирования похуита."],
  tasks=[t_tag("forge:ores/chelyabinsk_shale", 4)], rewards=[r_xp(60)], deps_keys=["c3_isotope"])
q("c5_egor", title="Ядро Егора", icon="egor_core", x=0.75, y=1.5,
  desc=["&7Ассемблер: 2 gem correct_matter + 4 плиты стали + вайб → &fegor_core&7."],
  tasks=[t_item("egor_core", 1)], rewards=[r_xp(150)], deps_keys=["c5_dense"])
q("c5_sauna", title="Сауна Егора", icon="sauna_egora", x=0.75, y=3,
  desc=["&7Собери мультиблок &fСауна Егора&7 (ядро + 2 правильные вещи + рамы похуита).",
        "«Большим машинам нужен отдых. Егор попарит — тильт спадёт.»"],
  tasks=[t_item("sauna_egora", 1)], rewards=[r_xp(300)], deps_keys=["c5_egor"])
q("c5_coolant", title="Хладагент отрицания", icon="stabilized_vibe_bucket", x=2.5, y=1.5,
  desc=["&7Химия: technical_tears + похуит + вода → &fcoolant_of_denial&7.",
        "«Остужает не проблему, а разговор о ней.»"],
  tasks=[t_fluid("coolant_of_denial", 1000)], rewards=[r_xp(120)], deps_keys=["c5_dense"])

# ============================ CHAPTER 6: Абсолютный Похуизм (эндгейм) =======
q("e_singfrag", title="Нормисная Сингулярность", icon="normis_singularity", x=-1.5, y=0,
  desc=["&7Ассемблер: 16 нормисной пыли + 4 шлак-игнора → &fnormis_singularity&7.",
        "«Сгусток всего, что ты игнорировал.»"],
  tasks=[t_item("normis_singularity", 1)], rewards=[r_xp(200)], deps_keys=["c5_sauna"])
q("e_anti", title="Антизумерное ядро", icon="antizoomer_core", x=1.5, y=0,
  desc=["&7Ассемблер: gem correct_matter + плиты + изотоп → &fantizoomer_core&7.",
        "«Боялся зумеров? Теперь они боятся тебя.»"],
  tasks=[t_item("antizoomer_core", 1)], rewards=[r_xp(200)], deps_keys=["c5_shale"])
q("e_schem", title="Правильная схема разраба", icon="correct_developer_schematic", x=0, y=1.5,
  desc=["&7Обугленная схема + gem correct_matter + вайб → &fcorrect_developer_schematic&7."],
  tasks=[t_item("correct_developer_schematic", 1)], rewards=[r_xp(200)],
  deps_keys=["e_anti"])
q("e_pohuit", title="Абсолютный Похуит", icon="absolute_pohuit", x=0, y=3,
  desc=["&7Правильная вещь + изотоп + антизумер-ядро + схема разраба + вайб → &fABSOLUTE POHUIT&7.",
        "«Высший индустриальный дзен.»"],
  tasks=[t_item("absolute_pohuit", 1)], rewards=[r_xp(400)], deps_keys=["e_schem", "e_singfrag"])
q("e_micro", title="Микрокапсула правильной материи", icon="correct_matter_microcapsule", x=2.5, y=1.5,
  desc=["&7Химия: gem + плотная жижа + padik_noble_gas → &fmicrocapsule&7."],
  tasks=[t_item("correct_matter_microcapsule", 1)], rewards=[r_xp(200)], deps_keys=["e_anti"])
q("e_main", title="Arthurian Mainframe", icon="arturian_mainframe", x=0, y=4.5,
  desc=["&78 плит стали + 4 gem correct_matter + скрипт Мыпошко + вайб → &fARTURIAN MAINFRAME&7.",
        "«Теперь Артур говорит через твои машины. Готов ли ты его слушать?»"],
  tasks=[t_item("arturian_mainframe", 1)], rewards=[r_xp(500)], deps_keys=["e_pohuit"])
# --- locked (not in code yet) ---
q("e_singularity", title="&c[🔒] Сингулярность «Деревенский Покой»", icon="absolute_pohuit", x=0, y=6,
  desc=["&7Собрать всё в одну Сингулярность — право уйти.",
        "&c[НЕ В КОДЕ] Финальный предмет + рецепт ещё не реализованы (Фаза 3).",
        "&8Держать заблокированным до сборки финала (roadmap §10)."],
  tasks=[t_check()], rewards=[r_xp(1000)], deps_keys=["e_main"])
q("e_gate", title="&c[🔒] Врата ПГТ", icon="arturian_mainframe", x=0, y=7.5,
  desc=["&7«Ты построил завод, который мог всё. Теперь докажи, что можешь его выключить.»",
        "&c[НЕ В КОДЕ] Мультиблок pgt_gate ещё не реализован."],
  tasks=[t_check()], rewards=[r_xp(1000)], deps_keys=["e_singularity"])
q("e_pgt", title="&c[🔒] Деревенский Покой (финал)", icon="normis_singularity", x=0, y=9,
  desc=["&7GregTech довёл тебя до предела. ArthurTech разрешает уйти.",
        "&c[НЕ В КОДЕ] Измерение ПГТ = датапак модпака."],
  tasks=[t_check()], rewards=[r_xp(2000)], deps_keys=["e_gate"])

# resolve deps_keys -> id lists ---------------------------------------------
for key, quest in Q.items():
    dk = quest.pop("deps_keys", None)
    if dk:
        quest["deps"] = [Q[k]["id"] for k in dk]

CHAPTERS = [
    ("steam",   "1 · Грязный двор (Steam)",            "skufit_ingot",
     ["c1_skufit", "c1_flesh", "c1_normie", "c1_skufit_ingot", "c1_steel", "c1_sweat"]),
    ("lv",      "2 · ЧПУ-станкчанин (LV)",             "dodik_circuit_1",
     ["c2_hull", "c2_dodik1", "c2_cnc", "c2_filter", "c2_bit", "c2_distill", "c2_jizhnyak", "c2_matter"]),
    ("mv",      "3 · Разрабская неоднозначность (MV)",  "dodik_circuit_2",
     ["c3_dodik2", "c3_stab", "c3_isotope", "c3_vesh", "c3_myposhko", "c3_skufizator", "c3_pokhuit"]),
    ("hv",      "4 · Разбор Геймплея (HV)",             "dodik_circuit_3",
     ["c4_dodik3", "c4_cap", "c4_monitor", "c4_charred", "c4_demo", "c4_razbor", "c4_tears"]),
    ("sauna",   "5 · Сауна и Челябинск (HV/EV)",        "egor_core",
     ["c5_dense", "c5_shale", "c5_egor", "c5_sauna", "c5_coolant"]),
    ("endgame", "6 · Абсолютный Похуизм (эндгейм)",     "arturian_mainframe",
     ["e_singfrag", "e_anti", "e_schem", "e_pohuit", "e_micro", "e_main",
      "e_singularity", "e_gate", "e_pgt"]),
]

# write ----------------------------------------------------------------------
os.makedirs(CDIR, exist_ok=True)
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
with open(os.path.join(QDIR, "chapter_groups.snbt"), "w", encoding="utf-8") as f:
    f.write("{\n\tchapter_groups: [ ]\n}\n")
for order, (fn, title, icon, keys) in enumerate(CHAPTERS):
    text = emit_chapter(fn, title, icon, order, [Q[k] for k in keys])
    with open(os.path.join(CDIR, fn + ".snbt"), "w", encoding="utf-8") as f:
        f.write(text + "\n")

print("Generated:", os.path.abspath(QDIR))
print("Chapters:", ", ".join(c[0] for c in CHAPTERS))
print("Quests total:", len(Q))
