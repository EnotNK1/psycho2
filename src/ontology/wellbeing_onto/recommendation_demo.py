from __future__ import annotations

import json
import uuid
from pathlib import Path
from datetime import datetime, UTC
from tempfile import TemporaryDirectory

from owlready2 import get_ontology

from .recommender import recommend


MATERIAL_ID_BY_TITLE = {
    # Тесты
    "DASS-21": "bc9f1204-ea5d-40b0-b367-359bf9b2cc21",
    "STAI": "3a9a3c8d-348e-4f0d-aefd-0feaa960ac25",
    "Шкала депрессии Бека": "33d10952-aed7-4a4e-9e5a-dbd01b2f294d",
    "BAT": "ea869ca2-4e8f-4a98-8b13-4fbeedf30539",
    "Шкала проф. апатии": "6c242c64-b8c0-4f5c-877f-91b1c1d3f5af",
    "CMQ": "d7bdba0c-f5ec-410d-9b53-3bfbf20c674a",
    "PSS": "f56b5284-323e-42db-bd74-c80e8a5dc29a",
    "5PFQ": "e89f7acb-cd31-4d27-aadd-24f6c7d52794",
    "Нечеткая модель": "",
    "Индикатор копинг-стратегий": "f45c4528-ce69-4683-822a-91ffc52d55ba",
    "Шкала эмоциональных схем": "c18d71a4-7a8b-4b32-9e2a-3f8e5d6c7b9a",
    "Tracker": "Tracker",

    # Упражнения
    "Трекер настроения": "Tracker_ex",
    "Выявление горячих точек": "5f81cc8b-b057-47cb-96af-a0839d6c0ad9",
    "Как сделать..?": "9bfde30c-0aca-4ed8-abdf-b768b6b8f67f",
    "КПТ-дневник": "4e3f51e9-aad8-4a13-b4b7-d748e472d394",
    "Дневник мыслей": "",
    

    # Теория
    "Основы КПТ": "22cbb105-8857-48de-806d-7242ced60a97",
    "Проф. выгорание": "557d4285-9271-4bd1-bb47-745e8fe79d9d",
    "Стратегии преодоления стресса": "ae2e831a-7a1a-431d-a7b6-17eded8e4c26",
    "Убеждения": "76184343-ef76-408e-92d7-ea1317bcb676",
    "КПТ-дневник (теория)": "56124443-ed76-418c-22a7-ea1317aaa772",
    "Наши эмоции": "22cbb105-8857-48de-806d-7242ced60a98",
    "Релаксация": "8cd36279-61f0-4959-99de-0a642959e08b",
    "Дыхательные техники": "686dd773-7f39-405f-807a-7a6024f982b8",
}

TITLE_BY_MATERIAL_ID = {
    material_id: title
    for title, material_id in MATERIAL_ID_BY_TITLE.items()
    if material_id
}

SCALE_TO_ONTOLOGY_TARGET = {
    ("DASS-21", "Стресс"): "Воспринимаемый стресс",
    ("DASS-21", "Тревожность"): "Тревожность",
    ("DASS-21", "Депрессия"): "Депрессивная симптоматика",

    ("STAI", "Ситуативная"): "Ситуативная",
    ("STAI", "Личностная"): "Личностная",

    ("Шкала депрессии Бека", "Когнитивно-аффективные проявления"): "Когнитивно-аффективные проявления",
    ("Шкала депрессии Бека", "Соматические проявления"): "Соматические проявления",
    ("Шкала депрессии Бека", "Депрессия"): "Депрессивная симптоматика",

    ("BAT", "Истощение"): "Истощение",
    ("BAT", "Дистанцирование"): "Дистанцирование",
    ("BAT", "Когнитивные затруднения"): "Когнитивные затруднения",
    ("BAT", "Эмоциональные затруднения"): "Эмоциональные затруднения",
    ("BAT", "Вторичные симптомы"): "Вторичные симптомы",

    ("Шкала проф. апатии", "Апатичные мысли"): "Апатичные мысли",
    ("Шкала проф. апатии", "Апатичные действия"): "Апатичные действия",

    ("CMQ", "Когнитивные искажения"): "Когнитивные искажения",

    ("PSS", "Стресс"): "Воспринимаемый стресс",
    ("PSS", "Дистресс"): "Дистресс",
    ("PSS", "Совладание"): "Совладание",

    ("5PFQ", "Экстраверсия"): "Экстраверсия",
    ("5PFQ", "Саморегуляция"): "Саморегуляция",
    ("5PFQ", "Привязанность"): "Привязанность",
    ("5PFQ", "Нейротизм"): "Нейротизм",
    ("5PFQ", "Открытость опыту"): "Открытость опыту",

    ("Нечеткая модель", "Склонность к выгоранию"): "Склонность к выгоранию",

    ("Индикатор копинг-стратегий", "Копинги"): "Копинги",

    ("Шкала эмоциональных схем", "Инвалидация"): "Инвалидация",
    ("Шкала эмоциональных схем", "Непонятность"): "Непонятность",
    ("Шкала эмоциональных схем", "Вина и стыд"): "Вина и стыд",
    ("Шкала эмоциональных схем", "Упрощенный взгляд"): "Упрощенный взгляд",
    ("Шкала эмоциональных схем", "Обесценивание"): "Обесценивание",
    ("Шкала эмоциональных схем", "Потеря контроля"): "Потеря контроля",
    ("Шкала эмоциональных схем", "Бесчувственность"): "Бесчувственность",
    ("Шкала эмоциональных схем", "Чрезмерная рациональность"): "Чрезмерная рациональность",
    ("Шкала эмоциональных схем", "Длительность"): "Длительность",
    ("Шкала эмоциональных схем", "Низкий консенсус"): "Низкий консенсус",
    ("Шкала эмоциональных схем", "Руминации"): "Руминации",
    ("Шкала эмоциональных схем", "Непринятие чувств"): "Непринятие чувств",
    ("Шкала эмоциональных схем", "Низкая выраженность чувств"): "Низкая выраженность чувств",
    ("Шкала эмоциональных схем", "Обвинение"): "Обвинение",

    ("Tracker", "Настроение"): "Настроение",
}

TASK_CLASS_TO_RESPONSE_TYPE = {
    "TheoryTask": "theory",
    "TestTask": "test",
    "ExerciseTask": "practice",
}


def load_user_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_material_title_by_input_id(material_id: str) -> str:
    if material_id in TITLE_BY_MATERIAL_ID:
        return TITLE_BY_MATERIAL_ID[material_id]
    return material_id


def get_material_id_by_title(title: str) -> str:
    return MATERIAL_ID_BY_TITLE.get(title, "")


def _labels_of(individual) -> list[str]:
    try:
        return [str(x) for x in getattr(individual, "label", [])]
    except Exception:
        return []


def find_indicator_concept(onto, ru_label: str):
    for ind in onto.IndicatorConcept.instances():
        labels = _labels_of(ind)
        if any(ru_label.lower() == x.lower() for x in labels):
            return ind

    concept = onto.search_one(iri="*#" + ru_label)
    if concept:
        return concept

    for ind in onto.IndicatorConcept.instances():
        if ru_label.lower() in ind.name.lower():
            return ind

    return None


def find_factor_concept(onto, ru_label: str):
    for ind in onto.FactorConcept.instances():
        labels = _labels_of(ind)
        if any(ru_label.lower() == x.lower() for x in labels):
            return ind

    concept = onto.search_one(iri="*#" + ru_label)
    if concept:
        return concept

    for ind in onto.FactorConcept.instances():
        if ru_label.lower() in ind.name.lower():
            return ind

    return None


def find_target_concept(onto, ru_label: str):
    ind = find_indicator_concept(onto, ru_label)
    if ind is not None:
        return ("indicator", ind)

    fac = find_factor_concept(onto, ru_label)
    if fac is not None:
        return ("factor", fac)

    return (None, None)


def normalize_input_to_targets(data: dict) -> list[dict]:
    input_test_id = data["test_id"]
    canonical_test_title = resolve_material_title_by_input_id(input_test_id)

    scale_results = data.get("scale_results", [])
    normalized = []

    for item in scale_results:
        scale_title = item["scale_title"]
        score = float(item["score"])

        key = (canonical_test_title, scale_title)
        target_label = SCALE_TO_ONTOLOGY_TARGET.get(key)

        if target_label is None:
            continue

        normalized.append({
            "target_label": target_label,
            "value": score,
        })

    return normalized


def create_observations_from_payload(onto, data: dict, user_name: str):
    User = onto.User
    Observation = onto.Observation

    user = onto.search_one(iri="*#" + user_name)
    if user is None:
        user = User(user_name)
        user.label = [f"Пользователь ({user_name})"]

    created = []

    input_test_id = data.get("test_id", "unknown_test")
    canonical_test_title = resolve_material_title_by_input_id(input_test_id)

    normalized_targets = normalize_input_to_targets(data)

    for obs_data in normalized_targets:
        target_label = obs_data["target_label"]
        value = float(obs_data["value"])

        target_kind, concept = find_target_concept(onto, target_label)

        if concept is None:
            continue

        obs_name = (
            f"obs_{user_name}_{concept.name}_"
            f"{datetime.now(UTC).strftime('%H%M%S%f')}"
        )

        obs = Observation(obs_name)
        obs.observationValue = [value]
        obs.observationTime = [datetime.now(UTC)]
        obs.observationSource = [canonical_test_title]

        if target_kind == "indicator":
            obs.aboutIndicator = [concept]
        elif target_kind == "factor":
            obs.aboutFactor = [concept]
        else:
            continue

        obs.observedBy = [user]
        user.hasObservation.append(obs)

        created.append(obs)

    return user, created


def create_observations_from_json(onto, data: dict, user_name: str):
    return create_observations_from_payload(onto, data, user_name)


def _infer_response_type(rec):
    try:
        tasks = list(getattr(rec, "recommendsTask", []))
    except Exception:
        tasks = []

    if not tasks:
        return "practice"

    task = tasks[0]

    try:
        for cls in task.is_a:
            name = getattr(cls, "name", "")
            if name in TASK_CLASS_TO_RESPONSE_TYPE:
                return TASK_CLASS_TO_RESPONSE_TYPE[name]
    except Exception:
        pass

    return "practice"


def _get_material_id_or_empty(task):
    title = _get_task_title(task)
    return get_material_id_by_title(title)


def _get_task_title(task):
    labels = _labels_of(task)
    if labels:
        return labels[0]
    return getattr(task, "name", "")


def build_output_json(onto, user):
    recs = list(getattr(user, "hasRecommendation", []))
    result = []
    seen = set()

    for rec in recs:
        tasks = list(getattr(rec, "recommendsTask", []))
        task = tasks[0] if tasks else None

        if task is None:
            continue

        item = {
            "type": _infer_response_type(rec),
            "material_id": _get_material_id_or_empty(task),
        }

        dedupe_key = (item["type"], item["material_id"], _get_task_title(task))
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        result.append(item)

    return result


def save_output_json(path: str, payload):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def generate_recommendations_from_payload(
    payload: dict,
    ontology_path: str = "data/ontologies/wellbeing_app_demo_rules.owl",
    user_name: str | None = None,
):
    request_user_name = user_name or f"user_api_{uuid.uuid4().hex[:12]}"

    with TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        runtime_owl_path = tmpdir_path / "result.owl"

        onto = get_ontology(ontology_path).load()

        user, obs = create_observations_from_payload(
            onto=onto,
            data=payload,
            user_name=request_user_name,
        )

        if not obs:
            return []

        onto.save(file=str(runtime_owl_path))

        recommend(
            app_owl_path=str(runtime_owl_path),
            out_owl_path=str(runtime_owl_path),
            user_name=user.name,
        )

        onto = get_ontology(str(runtime_owl_path)).load()
        user = onto.search_one(iri="*#" + user.name)

        if user is None:
            return []

        return build_output_json(onto, user)


def run_demo(
    ontology_path: str,
    json_path: str,
    user_name: str = "user_json_demo",
    out_json_path: str = "recommendations.json",
):
    data = load_user_json(json_path)

    payload = generate_recommendations_from_payload(
        payload=data,
        ontology_path=ontology_path,
        user_name=user_name,
    )

    save_output_json(out_json_path, payload)


if __name__ == "__main__":
    run_demo(
        ontology_path="data/ontologies/wellbeing_app_demo_rules.owl",
        json_path="user_data.json",
        user_name="user_json_demo",
        out_json_path="recommendations.json",
    )