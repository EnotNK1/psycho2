from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Iterable
from collections import deque

from owlready2 import get_ontology, Thing, ObjectProperty, DataProperty


@dataclass(frozen=True)
class RecommendResult:
    in_path: Path
    out_path: Path
    user_name: str
    observations_used: int
    recommendations_created: int


DEFAULT_LOW = 0.33
DEFAULT_HIGH = 0.66

POSITIVE_INDICATORS = {
    "Nastroenie",
    "Sovladanie",
}

THRESHOLD_RULES = {
    "Воспринимаемый стресс": {"threshold": 10.0, "direction": "gte"},
    "Дистресс": {"threshold": 5.0, "direction": "gte"},
    "Совладание": {"threshold": 5.0, "direction": "gte"},
    "Тревога": {"threshold": 5.0, "direction": "gte"},
    "Тревожность": {"threshold": 5.0, "direction": "gte"},
    "Ситуативная": {"threshold": 30.0, "direction": "gte"},
    "Ситуативная тревожность": {"threshold": 30.0, "direction": "gte"},
    "Личностная": {"threshold": 30.0, "direction": "gte"},
    "Личностная тревожность": {"threshold": 30.0, "direction": "gte"},
    "Депрессивная симптоматика": {"threshold": 7.0, "direction": "gte"},
    "Депрессия": {"threshold": 10.0, "direction": "gte"},
    "Выгорание": {"threshold": 1.6, "direction": "gte"},
    "Истощение": {"threshold": 1.75, "direction": "gte"},
    "Дистанцирование": {"threshold": 1.2, "direction": "gte"},
    "Внутреннее дистанцирование": {"threshold": 1.2, "direction": "gte"},
    "Эмоциональные затруднения": {"threshold": 1.2, "direction": "gte"},
    "Когнитивные затруднения": {"threshold": 1.8, "direction": "gte"},
    "Вторичные симптомы": {"threshold": 1.7, "direction": "gte"},
    "Настроение": {"threshold": 50.0, "direction": "lte"},
    "Инвалидация": {"threshold": 3.0, "direction": "gte"},
    "Непонятность": {"threshold": 3.0, "direction": "gte"},
    "Вина и стыд": {"threshold": 3.0, "direction": "gte"},
    "Упрощенный взгляд": {"threshold": 3.0, "direction": "gte"},
    "Обесценивание": {"threshold": 3.0, "direction": "gte"},
    "Потеря контроля": {"threshold": 3.0, "direction": "gte"},
    "Бесчувственность": {"threshold": 3.0, "direction": "gte"},
    "Чрезмерная рациональность": {"threshold": 3.0, "direction": "gte"},
    "Длительность": {"threshold": 3.0, "direction": "gte"},
    "Низкий консенсус": {"threshold": 3.0, "direction": "gte"},
    "Руминации": {"threshold": 3.0, "direction": "gte"},
    "Непринятие чувств": {"threshold": 3.0, "direction": "gte"},
    "Низкая выраженность чувств": {"threshold": 3.0, "direction": "gte"},
    "Обвинение": {"threshold": 3.0, "direction": "gte"},
}

SOURCE_ALIASES = {
    "tracker": {"tracker", "трекер настроения"},
    "stai": {"stai", "трекер настроения"},
    "dass-21": {"dass-21", "трекер настроения"},
    "pss": {"pss", "трекер настроения"},
    "bat": {"bat", "трекер настроения"},
    "cmq": {"cmq", "трекер настроения"},
    "5pfq": {"5pfq", "трекер настроения"},
    "шкала депрессии бека": {"шкала депрессии бека", "трекер настроения"},
    "шкала проф. апатии": {"шкала проф. апатии", "трекер настроения"},
    "шкала эмоциональных схем": {"шкала эмоциональных схем", "трекер настроения"},
    "нечеткая модель": {"нечеткая модель", "нечёткая модель", "трекер настроения"},
    "индикатор копинг-стратегий": {"индикатор копинг-стратегий", "трекер настроения"},
    "кпт-дневник": {"кпт-дневник", "трекер настроения"},
    "дневник мыслей": {"дневник мыслей", "трекер настроения"},
    "релаксация": {"релаксация", "трекер настроения"},
    "дыхательные техники": {"дыхательные техники", "трекер настроения"},
    "выявление горячих точек": {"выявление горячих точек", "трекер настроения"},
    "как сделать..?": {"как сделать..?", "как сделать", "трекер настроения"},
}

GRAPH_FORWARD_PROPS = {
    "Includes",
    "Moderates",
}

ALLOWED_EXTRA_EDGES = {
    ("Настроение", "Influences_reverse", "Чувства"),
    ("Чувства", "ManifestsIn_reverse", "Эмоции"),
    ("Чувства", "is_a_down", "Тревога"),
    ("Тревога", "Includes_reverse", "Тревожность"),
    ("Эмоциональные схемы", "Moderates", "Эмоции"),
    ("Ситуативная", "is_a", "Тревожность"),
    ("Личностная", "is_a", "Тревожность"),
    ("Тревожность", "Includes", "Тревога"),
    ("Тревога", "is_a", "Чувства"),
}

NON_STOP_START_CONCEPTS = {
    "Настроение",
    "Ситуативная",
    "Личностная"
}

DISALLOWED_TARGETS_BY_START = {
    "Настроение": {"Тревога"},
}

DEPTH_WEIGHTS = {
    0: 1.00,
    1: 0.90,
    2: 0.80,
    3: 0.70,
    4: 0.60,
}


def _ensure_class(onto, name: str, parent):
    existing = getattr(onto, name, None)
    if existing is not None:
        return existing
    with onto:
        return type(name, (parent,), {})


def _ensure_objprop(onto, name: str, domain=None, range_=None):
    existing = getattr(onto, name, None)
    if existing is not None:
        return existing
    with onto:
        prop = type(name, (ObjectProperty,), {})
        if domain is not None:
            prop.domain = domain
        if range_ is not None:
            prop.range = range_
    return prop


def _ensure_dataprop(onto, name: str, domain=None, range_=None):
    existing = getattr(onto, name, None)
    if existing is not None:
        return existing
    with onto:
        prop = type(name, (DataProperty,), {})
        if domain is not None:
            prop.domain = domain
        if range_ is not None:
            prop.range = range_
    return prop


def _label(entity) -> str:
    try:
        lab = list(getattr(entity, "label", []))
        if lab:
            return str(lab[0])
    except Exception:
        pass
    try:
        return entity.name
    except Exception:
        return "Unnamed"


def _norm_text(s: str) -> str:
    return (s or "").strip().lower()


def _parse_origin_class_name(origin_iri: Optional[str]) -> Optional[str]:
    if not origin_iri:
        return None
    if "#" in origin_iri:
        return origin_iri.split("#", 1)[1]
    return None


def _resolve_threshold_rule(concept_label: str):
    return THRESHOLD_RULES.get(concept_label)


def _binary_severity_from_threshold(raw_value: float, concept_label: str):
    rule = _resolve_threshold_rule(concept_label)
    if rule is None:
        return None

    threshold = float(rule["threshold"])
    direction = rule["direction"]

    if direction == "gte":
        is_high = raw_value >= threshold
        ratio = raw_value / threshold if threshold > 0 else 0.0
    else:
        is_high = raw_value <= threshold
        ratio = threshold / raw_value if raw_value > 0 else 1.0

    problem_score = max(0.0, min(1.0, ratio))
    severity = "high" if is_high else "low"
    return severity, problem_score


def _severity_from_value(problem_score: float, low: float, high: float) -> str:
    if problem_score < low:
        return "low"
    if problem_score < high:
        return "medium"
    return "high"


def _problem_score(indicator_class_name: str, raw_value: float) -> float:
    v = max(0.0, min(1.0, float(raw_value)))
    if indicator_class_name in POSITIVE_INDICATORS:
        return 1.0 - v
    return v


def _iter_individuals(onto, cls) -> Iterable:
    try:
        return list(cls.instances())
    except Exception:
        return []


def _find_individual(onto, name: str):
    return onto.search_one(iri="*#" + name)


def _get_first_dataprop(ind, prop_name: str) -> Optional[str]:
    try:
        vals = list(getattr(ind, prop_name, []))
        if vals:
            return str(vals[0])
    except Exception:
        pass
    return None


def _get_first_float(ind, prop_name: str) -> Optional[float]:
    try:
        vals = list(getattr(ind, prop_name, []))
        if vals:
            return float(vals[0])
    except Exception:
        pass
    return None


def _ensure_schema_for_reasoning(onto):
    Observation = getattr(onto, "Observation")
    Recommendation = getattr(onto, "Recommendation")

    with onto:
        SeverityLevel = _ensure_class(onto, "SeverityLevel", Thing)
        Low = getattr(onto, "SeverityLow", None) or SeverityLevel("SeverityLow")
        Medium = getattr(onto, "SeverityMedium", None) or SeverityLevel("SeverityMedium")
        High = getattr(onto, "SeverityHigh", None) or SeverityLevel("SeverityHigh")
        Low.label = ["Low"]
        Medium.label = ["Medium"]
        High.label = ["High"]

        hasSeverity = _ensure_objprop(onto, "hasSeverity", domain=[Observation], range_=[SeverityLevel])
        computedProblemScore = _ensure_dataprop(onto, "computedProblemScore", domain=[Observation], range_=[float])
        explanationJson = _ensure_dataprop(onto, "explanationJson", domain=[Recommendation], range_=[str])

    return {
        "SeverityLow": Low,
        "SeverityMedium": Medium,
        "SeverityHigh": High,
        "hasSeverity": hasSeverity,
        "computedProblemScore": computedProblemScore,
        "explanationJson": explanationJson,
    }


def _annotate_observation_severity(onto, obs, low: float, high: float) -> Tuple[str, float, Optional[object], str]:
    schema = _ensure_schema_for_reasoning(onto)

    raw_val = _get_first_float(obs, "observationValue")
    if raw_val is None:
        raw_val = 0.0

    concept = None
    concept_kind = None

    try:
        v = list(getattr(obs, "aboutIndicator", []))
        if v:
            concept = v[0]
            concept_kind = "indicator"
    except Exception:
        pass

    if concept is None:
        try:
            v = list(getattr(obs, "aboutFactor", []))
            if v:
                concept = v[0]
                concept_kind = "factor"
        except Exception:
            pass

    origin_iri = _get_first_dataprop(concept, "originClassIri") if concept is not None else None
    concept_class_name = _parse_origin_class_name(origin_iri) or (concept.name if concept is not None else "Unknown")
    concept_label = _label(concept) if concept is not None else concept_class_name

    binary = _binary_severity_from_threshold(float(raw_val), concept_label)
    if binary is not None:
        sev, pscore = binary
    else:
        if concept_kind == "indicator":
            pscore = _problem_score(concept_class_name, float(raw_val))
        else:
            pscore = max(0.0, min(1.0, float(raw_val)))
        sev = "high" if pscore >= high else "low"

    obs.computedProblemScore = [pscore]
    if sev == "low":
        obs.hasSeverity = [schema["SeverityLow"]]
    elif sev == "medium":
        obs.hasSeverity = [schema["SeverityMedium"]]
    else:
        obs.hasSeverity = [schema["SeverityHigh"]]

    return sev, pscore, concept, concept_class_name


def _load_rules(onto):
    Rule = getattr(onto, "Rule", None)
    if Rule is None:
        return []

    rules = []
    for r in list(_iter_individuals(onto, Rule)):
        try:
            ind = None
            fac = None

            v = list(getattr(r, "ruleForIndicator", []))
            if v:
                ind = v[0]

            v = list(getattr(r, "ruleForFactor", []))
            if v:
                fac = v[0]

            ms = None
            v = list(getattr(r, "ruleMinSeverity", []))
            if v:
                ms = v[0]

            task = None
            v = list(getattr(r, "ruleRecommendsTask", []))
            if v:
                task = v[0]

            w = _get_first_float(r, "ruleWeight")
            if w is None:
                w = 1.0

            why = _get_first_dataprop(r, "ruleWhy") or "Правило"
            swrl = _get_first_dataprop(r, "ruleSWRL")

            if task is None or ms is None:
                continue

            min_sev_name = ms.name if hasattr(ms, "name") else ""
            if "High" in min_sev_name:
                min_sev_value = "high"
            else:
                min_sev_value = "low"

            rules.append({
                "rule": r,
                "forIndicator": ind,
                "forFactor": fac,
                "minSeverityValue": min_sev_value,
                "task": task,
                "weight": float(w),
                "why": why,
                "swrl": swrl,
            })
        except Exception:
            continue
    return rules


def _subclasses_of(onto, parent_cls):
    result = []
    for c in onto.classes():
        if c is parent_cls:
            continue
        try:
            if parent_cls in list(getattr(c, "is_a", [])):
                result.append(c)
        except Exception:
            continue
    return result


def _is_allowed_extra_edge(from_cls, relation: str, to_cls) -> bool:
    return (_label(from_cls), relation, _label(to_cls)) in ALLOWED_EXTRA_EDGES


def _origin_class_from_concept(onto, concept):
    if concept is None:
        return None

    origin_iri = _get_first_dataprop(concept, "originClassIri")
    if not origin_iri:
        return None

    try:
        return onto.search_one(iri=origin_iri)
    except Exception:
        return None


def _concepts_by_origin_class(onto):
    result = {}
    for cls_name in ("IndicatorConcept", "FactorConcept"):
        cls = getattr(onto, cls_name, None)
        if cls is None:
            continue

        for ind in _iter_individuals(onto, cls):
            iri = _get_first_dataprop(ind, "originClassIri")
            local = _parse_origin_class_name(iri)
            if local:
                result.setdefault(local, []).append(ind)
    return result


def _class_neighbors_forward(onto, cls):
    result = []

    try:
        for ax in list(getattr(cls, "is_a", [])):
            if hasattr(ax, "name"):
                result.append(("is_a", ax))
            else:
                prop = getattr(ax, "property", None)
                target = getattr(ax, "value", None)
                prop_name = getattr(prop, "name", None)
                if target is not None and prop_name in GRAPH_FORWARD_PROPS:
                    result.append((prop_name, target))
    except Exception:
        pass

    for child in _subclasses_of(onto, cls):
        if _is_allowed_extra_edge(cls, "is_a_down", child):
            result.append(("is_a_down", child))

    for candidate in onto.classes():
        try:
            for ax in list(getattr(candidate, "is_a", [])):
                prop = getattr(ax, "property", None)
                target = getattr(ax, "value", None)
                prop_name = getattr(prop, "name", None)
                if target is cls and prop_name is not None:
                    rel = f"{prop_name}_reverse"
                    if _is_allowed_extra_edge(cls, rel, candidate):
                        result.append((rel, candidate))
        except Exception:
            continue

    return result


def _task_kind(task) -> str:
    try:
        for cls in task.is_a:
            name = getattr(cls, "name", "")
            if name == "TheoryTask":
                return "theory"
            if name == "TestTask":
                return "test"
            if name == "ExerciseTask":
                return "practice"
    except Exception:
        pass
    return "unknown"


def _source_test_label_for_observation(obs) -> Optional[str]:
    try:
        vals = list(getattr(obs, "observationSource", []))
        if vals:
            return str(vals[0])
    except Exception:
        pass
    return None


def _same_material_as_source(task, source_label: Optional[str]) -> bool:
    if not source_label:
        return False

    src = _norm_text(source_label)
    aliases = SOURCE_ALIASES.get(src, {src})

    task_candidates = {
        _norm_text(_label(task)),
        _norm_text(getattr(task, "name", "")),
    }

    return not aliases.isdisjoint(task_candidates)


def _collect_all_tasks(onto):
    TherapeuticTask = getattr(onto, "TherapeuticTask", None)
    if TherapeuticTask is None:
        return []
    return list(_iter_individuals(onto, TherapeuticTask))


def _tasks_targeting_concept(all_tasks, concept):
    result = []
    for task in all_tasks:
        try:
            if concept in list(getattr(task, "targetsIndicator", [])):
                result.append(task)
                continue
        except Exception:
            pass

        try:
            if concept in list(getattr(task, "targetsFactor", [])):
                result.append(task)
                continue
        except Exception:
            pass
    return result


def _collect_candidates_for_observation(
    onto,
    obs,
    concept,
    pscore: float,
    severity: str,
    max_depth: int = 4,
):
    all_tasks = _collect_all_tasks(onto)
    concept_map = _concepts_by_origin_class(onto)
    source_test_label = _source_test_label_for_observation(obs)

    start_cls = _origin_class_from_concept(onto, concept)
    start_label = _label(concept) if concept is not None else ""
    if start_cls is None:
        return []

    candidates = []
    q = deque()
    q.append((start_cls, 0, []))
    seen_states = set()

    while q:
        cls, depth, path = q.popleft()
        cls_name = getattr(cls, "name", None)
        if not cls_name:
            continue

        path_key = tuple((p["from_name"], p["relation"], p["to_name"]) for p in path)
        state_key = (cls_name, depth, path_key)
        if state_key in seen_states:
            continue
        seen_states.add(state_key)

        found_material_on_this_branch = False
        target_concepts = concept_map.get(cls_name, [])

        for target_concept in target_concepts:
            blocked_targets = DISALLOWED_TARGETS_BY_START.get(start_label, set())
            if _label(target_concept) in blocked_targets:
                continue
            
            tasks = _tasks_targeting_concept(all_tasks, target_concept)

            for task in tasks:
                if _same_material_as_source(task, source_test_label):
                    continue

                task_label = _label(task)
                kind = _task_kind(task)
                depth_weight = DEPTH_WEIGHTS.get(depth, 0.5)

                kind_bonus = {
                    "practice": 0.15,
                    "theory": 0.08,
                    "test": 0.00,
                }.get(kind, 0.0)

                score = pscore * depth_weight + kind_bonus

                exp = {
                    "source": "graph_traversal",
                    "concept": concept.name if concept is not None else "",
                    "concept_label": _label(concept) if concept is not None else "",
                    "expanded_to_class": cls_name,
                    "expanded_to_concept": target_concept.name,
                    "expanded_to_label": _label(target_concept),
                    "depth": depth,
                    "path": path,
                    "severity": severity,
                    "problem_score": round(pscore, 4),
                    "observation": obs.name,
                    "task": task.name,
                    "task_label": task_label,
                    "task_kind": kind,
                }

                candidates.append((score, task, obs, None, exp))
                found_material_on_this_branch = True

        if found_material_on_this_branch and start_label not in NON_STOP_START_CONCEPTS:
            continue

        if depth >= max_depth:
            continue

        for rel_name, nxt in _class_neighbors_forward(onto, cls):
            nxt_name = getattr(nxt, "name", None)
            if not nxt_name:
                continue

            step = {
                "from": _label(cls),
                "from_name": cls_name,
                "relation": rel_name,
                "to": _label(nxt),
                "to_name": nxt_name,
            }
            q.append((nxt, depth + 1, list(path) + [step]))

    return candidates


def recommend(
    app_owl_path: str,
    out_owl_path: str,
    user_name: str,
    low: float = DEFAULT_LOW,
    high: float = DEFAULT_HIGH,
    min_severity: str = "high",
    top_k: int = 50,
    traversal_max_depth: int = 4,
) -> RecommendResult:
    in_path = Path(app_owl_path)
    out_path = Path(out_owl_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    onto = get_ontology(str(in_path)).load()

    User = getattr(onto, "User")
    Recommendation = getattr(onto, "Recommendation")

    Rule = getattr(onto, "Rule", None)
    if Rule is None:
        Rule = _ensure_class(onto, "Rule", Thing)

    derivedFromRule = getattr(onto, "derivedFromRule", None)
    if derivedFromRule is None:
        derivedFromRule = _ensure_objprop(onto, "derivedFromRule", domain=[Recommendation], range_=[Rule])

    hasRecommendation = getattr(onto, "hasRecommendation", None)
    if hasRecommendation is None:
        hasRecommendation = _ensure_objprop(onto, "hasRecommendation", domain=[User], range_=[Recommendation])

    recommendationText = getattr(onto, "recommendationText", None)
    recommendationScore = getattr(onto, "recommendationScore", None)

    _ensure_schema_for_reasoning(onto)

    user = _find_individual(onto, user_name)
    if user is None:
        raise RuntimeError(f"Не найден пользователь '{user_name}'.")

    observations = list(getattr(user, "hasObservation", []))
    rules = _load_rules(onto)

    sev_order = {"low": 0, "high": 1}
    min_level = sev_order.get(min_severity, 1)

    best_candidates = {}

    for obs in observations:
        sev, pscore, concept, _ = _annotate_observation_severity(onto, obs, low=low, high=high)

        if sev_order[sev] < min_level:
            continue
        if concept is None:
            continue

        for rr in rules:
            rule_min = rr.get("minSeverityValue", "high")
            if rule_min not in sev_order:
                rule_min = "high"
            if sev_order[sev] < sev_order[rule_min]:
                continue

            match = False
            if rr["forIndicator"] is not None and rr["forIndicator"] == concept:
                match = True
            if rr["forFactor"] is not None and rr["forFactor"] == concept:
                match = True

            if not match:
                continue

            task = rr["task"]
            if _same_material_as_source(task, _source_test_label_for_observation(obs)):
                continue

            score = pscore * float(rr["weight"])

            exp = {
                "source": "direct_rule",
                "rule_individual": rr["rule"].name,
                "rule_why": rr["why"],
                "rule_swrl": rr["swrl"],
                "concept": concept.name,
                "concept_label": _label(concept),
                "severity": sev,
                "problem_score": round(pscore, 4),
                "observation": obs.name,
                "task": task.name,
                "task_label": _label(task),
                "task_kind": _task_kind(task),
                "path": [],
            }

            key = (task.name, obs.name, "direct_rule")
            if key not in best_candidates or score > best_candidates[key][0]:
                best_candidates[key] = (score, task, rr["rule"], exp, obs)

        fb = _collect_candidates_for_observation(
            onto=onto,
            obs=obs,
            concept=concept,
            pscore=pscore,
            severity=sev,
            max_depth=traversal_max_depth,
        )

        for score, task, obs_obj, rule_obj, exp in fb:
            key = (task.name, obs_obj.name, "graph_traversal")
            if key not in best_candidates or score > best_candidates[key][0]:
                best_candidates[key] = (score, task, rule_obj, exp, obs_obj)

    candidates_list = list(best_candidates.values())
    candidates_list.sort(key=lambda x: x[0], reverse=True)
    candidates_list = candidates_list[:max(1, int(top_k))]

    created = 0
    seen_recommendations = set()

    for score, task, rule_obj, exp, obs in candidates_list:
        rec_key = (task.name, exp.get("source", "unknown"), obs.name)
        if rec_key in seen_recommendations:
            continue
        seen_recommendations.add(rec_key)

        rec_name = f"rec_{user.name}_{task.name}_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
        rec = Recommendation(rec_name)
        rec.label = [f"Рекомендация: {_label(task)}"]

        rec.recommendationFor = [user]
        rec.recommendsTask = [task]
        rec.triggeredBy = [obs]

        if rule_obj is not None:
            try:
                rec.derivedFromRule = [rule_obj]
            except Exception:
                pass

        user.hasRecommendation.append(rec)

        if exp.get("source") == "direct_rule":
            text = (
                f"Уровень '{exp['severity']}' для '{exp['concept_label']}' "
                f"(score={exp['problem_score']}). "
                f"Рекомендуем: '{exp['task_label']}'. Причина: {exp['rule_why']}"
            )
        else:
            path_parts = []
            for step in exp.get("path", []):
                path_parts.append(f"{step['from']} --{step['relation']}--> {step['to']}")
            path_str = " | ".join(path_parts) if path_parts else "прямое совпадение"

            text = (
                f"Уровень '{exp['severity']}' для '{exp['concept_label']}' "
                f"(score={exp['problem_score']}). "
                f"Через путь: {path_str}. "
                f"Найдена рекомендация: '{exp['task_label']}'."
            )

        if recommendationText is not None:
            rec.recommendationText = [text]
        if recommendationScore is not None:
            rec.recommendationScore = [float(score)]

        rec.explanationJson = [json.dumps(exp, ensure_ascii=False)]
        created += 1

    onto.save(file=str(out_path), format="rdfxml")

    return RecommendResult(
        in_path=in_path,
        out_path=out_path,
        user_name=user.name,
        observations_used=len(observations),
        recommendations_created=created,
    )