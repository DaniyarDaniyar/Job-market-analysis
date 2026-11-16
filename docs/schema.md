# ER-диаграмма и нормализация

```mermaid
erDiagram
    COMPANIES ||--o{ JOBS : posts
    LOCATIONS ||--o{ JOBS : located_in
    ROLES ||--o{ JOBS : classifies
    JOBS ||--o{ JOB_SKILLS : mentions
    SKILLS ||--o{ JOB_SKILLS : mentioned_in
    COMPANIES {
        INTEGER company_id PK
        TEXT source_key UK
        TEXT name
    }
    LOCATIONS {
        INTEGER location_id PK
        TEXT name UK
    }
    ROLES {
        INTEGER role_id PK
        TEXT name UK
    }
    JOBS {
        INTEGER job_id PK
        INTEGER company_id FK
        INTEGER location_id FK
        INTEGER role_id FK
        TEXT title
        TEXT posted_date
        REAL salary_usd
        TEXT experience
        TEXT work_type
        INTEGER remote
        REAL views
        REAL applies
        INTEGER description_length
    }
    SKILLS {
        INTEGER skill_id PK
        TEXT name UK
    }
    JOB_SKILLS {
        INTEGER job_id PK,FK
        INTEGER skill_id PK,FK
    }
```

Справочники компаний, локаций, ролей и навыков вынесены из фактов вакансий.
Каждый неключевой атрибут зависит от ключа своей таблицы. Составной ключ
`job_skills(job_id, skill_id)` исключает повторный учёт навыка в вакансии.
`source_key` компании: исходный company_id, иначе точное имя; разные исходные
ID могут иметь одинаковые имена. Неизвестные компании объединены в Unknown.
Роль — результат классификации заголовка правилами, а не метка работодателя.
Текст локации не геокодируется. Исходные описания остаются в CSV; база
содержит извлечённые навыки и длину текста. В Parquet хранится денормализованная
аналитическая витрина для быстрых расчётов Pandas.

При загрузке включён `PRAGMA foreign_keys=ON`, после загрузки выполняется
`PRAGMA foreign_key_check`. Построение идёт во временные файлы; итоговая база
заменяется только после успешной обработки CSV.
