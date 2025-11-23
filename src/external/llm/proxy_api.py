import json
from logging import Logger
from typing import List, Optional

import requests
from src.core.config import Settings


class ProxyAPI:
    def __init__(self, config: Settings, logger: Logger):
        self.logger = logger
        self.api_key = config.LLM_PROXY_API_KEY
        self.model = config.LLM_MODEL
        self.timeout = config.LLM_REQUEST_TIMEOUT
        self.base_url = config.LLM_PROXY_BASE_URL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def send_message(self, message: str) -> Optional[List[str]]:
        try:
            payload = {
                "model": self.model,  # твоя модель
                "input": message,  # весь промпт одним блоком
                "temperature": 0.0,  # строгое, детерминированное поведение
                "top_p": 1.0,
                "max_output_tokens": 400,  # ограничение на ответ
            }
            self.logger.debug(
                f"Отправка запроса к ProxyAPI: {json.dumps(payload, ensure_ascii=False)[:100]}..."
            )
            response = requests.post(
                self.base_url, headers=self.headers, json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            response_data = response.json()
            self.logger.debug(
                f"Получен ответ от ProxyAPI: {json.dumps(response_data, ensure_ascii=False)[:200]}..."
            )

            if response_data:
                text = response_data["output"][0]["content"][0]["text"]
                options = json.loads(text)
                self.logger.debug(f"Ответ LLM: {options}")
                return options

            self.logger.error(
                f"Не удалось извлечь текст из ответа API. Полный ответ: {json.dumps(response_data, ensure_ascii=False)}"
            )
            return None

        except requests.exceptions.HTTPError as e:
            self.logger.error(f"HTTP ошибка при запросе к ProxyAPI: {str(e)}")
            if e.response is not None:
                self.logger.error(f"Тело ответа с ошибкой: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Ошибка сети при запросе к ProxyAPI: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Ошибка декодирования JSON ответа: {str(e)}")
            return None
        except Exception as e:
            self.logger.exception(f"Неожиданная ошибка при работе с ProxyAPI: {str(e)}")
            return None
