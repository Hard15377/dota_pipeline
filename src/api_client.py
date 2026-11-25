from pathlib import Path
from typing import Any
import time
import pandas as pd
import requests


DEFAULT_API_URL = "https://api.opendota.com/api/publicMatches"
DEFAULT_RAW_PATH = Path("data/raw_data.csv")
DEFAULT_TARGET_RECORDS = 200


def fetch_matches(
    less_than_match_id: int | None = None,
    url: str = DEFAULT_API_URL,
    attempts: int = 3,
    timeout: int = 10,
    retry_delay: int = 5,
) -> list[dict[str, Any]]:
    """Запрашивает одну страницу публичных матчей из OpenDota API с ретраями."""
    params: dict[str, int] = {}
    if less_than_match_id is not None:
        params["less_than_match_id"] = less_than_match_id

    for attempt in range(1, attempts + 1):
        print(f"Попытка {attempt} из {attempts}...")
        try:
            response = requests.get(url, params=params, timeout=timeout)
            response.raise_for_status()

            payload = response.json()
            if not isinstance(payload, list):
                print("Неожиданный формат ответа от API: ожидался список записей.")
                return []

            print(f"Запрос успешно выполнен. Получено в пачке: {len(payload)}")
            return payload

        except requests.exceptions.RequestException as exc:
            print(f"Ошибка запроса на попытке {attempt}: {exc}")

        if attempt < attempts:
            time.sleep(retry_delay)

    print("Все попытки запроса к API оказались неудачными.")
    return []


def collect_unique_matches(
    target: int = DEFAULT_TARGET_RECORDS,
    url: str = DEFAULT_API_URL,
    max_pages: int = 15,
    request_pause: float = 1.0,
) -> list[dict[str, Any]]:
    """
    Собирает минимум `target` уникальных матчей через пагинацию по `less_than_match_id`.
    """
    unique_matches: dict[int, dict[str, Any]] = {}
    cursor_match_id: int | None = None
    pages_fetched = 0

    while len(unique_matches) < target and pages_fetched < max_pages:
        batch = fetch_matches(less_than_match_id=cursor_match_id, url=url)
        pages_fetched += 1

        if not batch:
            print("Пачка пустая, пагинация остановлена.")
            break

        added_in_batch = 0
        min_match_id_in_batch: int | None = None

        for match in batch:
            match_id = match.get("match_id")
            if match_id is None:
                continue

            match_id_int = int(match_id)
            if min_match_id_in_batch is None or match_id_int < min_match_id_in_batch:
                min_match_id_in_batch = match_id_int

            if match_id_int not in unique_matches:
                unique_matches[match_id_int] = match
                added_in_batch += 1

        print(
            f"Страница {pages_fetched}: добавлено новых={added_in_batch}, "
            f"всего уникальных={len(unique_matches)}/{target}"
        )

        if min_match_id_in_batch is None or min_match_id_in_batch == cursor_match_id:
            print("Курсор match_id не сдвинулся, пагинация остановлена.")
            break

        cursor_match_id = min_match_id_in_batch

        if len(unique_matches) < target:
            time.sleep(request_pause)

    records = list(unique_matches.values())
    if len(records) < target:
        print(
            f"Внимание: собрано {len(records)} записей из запрошенных {target}."
        )
    return records


def save_raw_matches(
    matches: list[dict[str, Any]],
    output_path: Path = DEFAULT_RAW_PATH,
) -> Path:
    """Сохраняет сырые данные до очистки в CSV и возвращает путь к файлу."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_raw = pd.DataFrame(matches)
    df_raw.to_csv(output_path, index=False)
    print(f"Сырые данные сохранены в {output_path} (строк: {len(df_raw)})")
    return output_path


def collect_and_save_matches(
    target: int = DEFAULT_TARGET_RECORDS,
    output_path: Path = DEFAULT_RAW_PATH,
) -> list[dict[str, Any]]:
    """Основная точка входа модуля сбора данных."""
    matches = collect_unique_matches(target=target)
    if matches:
        save_raw_matches(matches, output_path)
    return matches


if __name__ == "__main__":
    collected = collect_and_save_matches(target=DEFAULT_TARGET_RECORDS)
    print(f"Итоговое количество уникальных записей: {len(collected)}")