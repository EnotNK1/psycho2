# Схема Compas

Таблицы: users, inquiry, user_inquiry, applications, clients, test, question, answer_choice, scale, borders, test_result, scale_result.

```mermaid
erDiagram
    users ||--o{ applications : sends_or_receives
    users ||--o{ clients : client_or_psychologist
    users ||--o{ user_inquiry : tags
    inquiry ||--o{ user_inquiry : tags
    users ||--o{ test_result : completes
    test ||--o{ test_result : attempts
    test ||--o{ question : questions
    test ||--o{ scale : scales
    scale ||--o{ borders : categories
    test_result ||--o{ scale_result : scores
    scale ||--o{ scale_result : scored_by
```

`question.answer_choice` содержит UUID вариантов из `answer_choice` в массиве PostgreSQL, как в исходном проекте. Это не FK-связь: целостность массива проверяется приложением и тестами каталога.

Порядок вопросов — `number`, порядок шкал — `position`. При первичном заполнении порядок шкал берётся из исходного `scale_info.json`, в котором расположены результаты соответствующих формул. ID исходных тестов, шкал, вопросов и вариантов сохранены.

Одна активная связь clients соответствует паре (client_id, mentor_id); уникальность пары обеспечена БД. Пара заявки (client_id, manager_id) тоже уникальна. Результаты многократных прохождений имеют разные test_result.id; их история не удаляется при группировке карточек.

Индексы начальной миграции покрывают поиск истории, шкал прохождения, клиентов психолога, входящих заявок и вопросов теста. Эффективность на больших данных необходимо замерять через EXPLAIN ANALYZE, а не выводить из наличия индекса.
