# AutoCRM — модуль заявок (leads)

Архив содержит только новые и изменённые файлы этапа.

## Куда копировать

Скопируй содержимое архива в корень `autocrm2` с заменой:

- `app/domain/lead_data.py` — новый: телефон и VIN;
- `app/domain/funnel.py` — заменить: переходы новой воронки;
- `app/schemas/lead.py` — заменить;
- `app/repositories/lead.py` — заменить;
- `app/services/lead.py` — заменить;
- `app/api/routes/leads.py` — заменить;
- `tests/conftest.py` — заменить: тесты используют только актуальные модели этапа 2;
- `tests/test_leads.py` — заменить;
- `README_STAGE4.md` — инструкция.

Новая миграция не нужна: таблицы `leads` и `status_history` уже созданы миграцией `0001`.

## API

Все `/leads` требуют Bearer JWT.

- `POST /leads` — создать;
- `GET /leads?status=new&source=telegram&manager_id=1` — список с фильтрами;
- `GET /leads/{id}` — получить одну;
- `PATCH /leads/{id}` — частично обновить;
- `DELETE /leads/{id}` — удалить;
- `PATCH /leads/{id}/status` — сменить статус и добавить `status_history`.

## Примеры Swagger/JSON

Создание:
```json
{
  "name": "Иван",
  "phone": "8 (999) 123-45-67",
  "source": "telegram",
  "car_info": "Lada Vesta, VIN XTA210990Y2765432"
}
```
Ответ содержит телефон `+79991234567` и извлечённый VIN `XTA210990Y2765432`.

Обновление:
```json
{
  "name": "Иван Петров",
  "manager_id": 1
}
```

Смена статуса:
```json
{
  "status": "in_progress"
}
```

Переходы:
`new -> in_progress -> selection -> invoice -> won/lost`.

## Тесты

```bat
pytest -q
```

Ожидаемо после замены старых тестов заявок: `12 passed`.

Тесты этапа проверяют:

1. грязный телефон нормализуется;
2. VIN извлекается из `car_info`;
3. невалидный VIN даёт 422;
4. смена статуса создаёт запись истории;
5. запрещённый прыжок даёт 409;
6. фильтры и PATCH обновления работают.

## Запуск

```bat
set DATABASE_URL=postgresql+psycopg://partsprice:partsprice@localhost:5432/partsprice
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`.
