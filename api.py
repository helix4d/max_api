"""
  api.py — высокоуровневый клиент для Max Bot API.

  Основной класс: MaxBotAPI.

  Он реализует:
  - авторизацию по access_token;
  - низкоуровневый метод _request (HTTP-запросы к REST API);
  - набор методов-обёрток над основными эндпоинтами:
    /me, /messages, /updates, /chats, /subscriptions, и др.

  Клиент может работать в двух режимах:
  - use_models=False — методы возвращают "сырые" dict/list (как есть из JSON);
  - use_models=True — выбранные методы возвращают dataclasses из max_api.models.
  """

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

import requests

from . import models


DEFAULT_BASE_URL = "https://platform-api.max.ru"


@dataclass
class MaxAPIError(Exception):
      """
      Исключение, описывающее ошибку Max Bot API.

      Это исключение генерируется методом _request, когда API возвращает
      HTTP-статус 4xx или 5xx.

      Атрибуты:
          status_code: HTTP-код ответа (например, 400, 401, 500).
          error_code: Строковый код ошибки из JSON-ответа (поле "code"), если есть.
          message: Текстовое описание ошибки (поле "message"), если есть.
          details: Полный JSON-ответ (словарь) с дополнительной информацией
              или None, если JSON разобрать не удалось.
      """

      status_code: int
      error_code: Optional[str] = None
      message: Optional[str] = None
      details: Optional[Mapping[str, Any]] = None

      def __str__(self) -> str:
          """
          Человекочитаемое представление ошибки, используется при печати исключения.

          Возвращает:
              Строку вида "HTTP <код>: code=<error_code>: <message>".
          """
          parts = [f"HTTP {self.status_code}"]
          if self.error_code:
              parts.append(f"code={self.error_code}")
          if self.message:
              parts.append(self.message)
          return ": ".join(parts)


class MaxBotAPI:
      """
      Клиент Max Bot API.

      Экземпляр этого класса инкапсулирует:
      - access_token, базовый URL, таймаут;
      - объект requests.Session для переиспользования соединений;
      - настройку use_models, определяющую тип возвращаемых данных.

      Основная идея:
      - _request выполняет HTTP-запрос, добавляя access_token и обрабатывая ошибки;
      - публичные методы (get_me, send_message, get_updates и т.п.)
        используют _request и при необходимости преобразуют JSON в модели.
      """

def __init__(
          self,
          access_token: str,
          *,
          base_url: str = DEFAULT_BASE_URL,
          timeout: Optional[float] = 10.0,
          session: Optional[requests.Session] = None,
          use_models: bool = False,
      ) -> None:
          """
          Инициализировать клиент MaxBotAPI.

          Параметры:
              access_token:
                  Токен бота, полученный от MasterBot. Передаётся в каждый запрос
                  в качестве query-параметра access_token.
              base_url:
                  Базовый URL API. По умолчанию: "https://platform-api.max.ru".
              timeout:
                  Значение таймаута (в секундах) для HTTP-запросов по умолчанию.
              session:
                  Необязательный экземпляр requests.Session. Можно передать
                  заранее сконфигурированный объект (например, с прокси или
                  особыми заголовками).
              use_models:
                  Если True, то часть методов будет возвращать dataclasses
                  (models.Message, models.Chat, models.Update и т.п.)
                  вместо "сырых" словарей.
          """
          # Токен доступа бота (строка).
          self._access_token = access_token
          # Базовый URL API без завершающего слеша.
          self._base_url = base_url.rstrip("/")
          # Таймаут запросов (в секундах).
          self._timeout = timeout
          # HTTP-сессия для всех запросов.
          self._session = session or requests.Session()
          # Флаг, определяющий режим возврата данных.
          self._use_models = use_models

@property
      def access_token(self) -> str:
          """
          Текущий access_token.

          Можно использовать для отладки или логирования.
          """
          return self._access_token

      def _build_url(self, path: str) -> str:
          """
          Построить абсолютный URL запроса.

          Параметры:
              path: Путь ресурса (например, "/me" или "messages").

          Возвращает:
              Полный URL, сформированный из base_url и path.
          """
          if not path.startswith("/"):
              path = "/" + path
          return self._base_url + path

      def _should_use_models(self, as_models: Optional[bool]) -> bool:
          """
          Определить, нужно ли возвращать данные как модели (dataclasses).

          Логика:
              - если as_models не None, используется его значение;
              - иначе используется настройка self._use_models (из конструктора).

          Параметры:
              as_models: Явный флаг для конкретного метода (или None).

          Возвращает:
              True, если нужно возвращать модели; False иначе.
          """
          return self._use_models if as_models is None else as_models

      def _request(
          self,
          method: str,
          path: str,
          *,
          params: Optional[Mapping[str, Any]] = None,
          json_body: Optional[Any] = None,
          timeout: Optional[float] = None,
      ) -> Any:
          """
          Низкоуровневый HTTP-запрос к Max Bot API.

          Всегда:
          - добавляет access_token в query-параметры;
          - разбирает JSON-ответ (если Content-Type содержит application/json);
          - при кодах 4xx/5xx выбрасывает MaxAPIError.

          Параметры:
              method:
                  HTTP-метод: "GET", "POST", "PUT", "DELETE", "PATCH" и т.д.
              path:
                  Путь ресурса (например, "/me", "/messages").
              params:
                  Дополнительные query-параметры (dict). Они будут объединены
                  с параметром access_token.
              json_body:
                  Объект, который будет автоматически сериализован в JSON и
                  отправлен в теле запроса.
              timeout:
                  Таймаут конкретного запроса (в секундах). Если None — будет
                  использовано значение self._timeout.

          Возвращает:
              Разобранный JSON (dict/list) или строку, если Content-Type не JSON.
          """
          url = self._build_url(path)

          # Собираем итоговый словарь query-параметров.
          query: Dict[str, Any] = {}
          if params:
              query.update(params)
          # Access token всегда передаём как access_token в query.
          query.setdefault("access_token", self._access_token)

          # Выполняем HTTP-запрос через requests.Session.
          resp = self._session.request(
              method=method.upper(),
              url=url,
              params=query,
              json=json_body,
              timeout=timeout if timeout is not None else self._timeout,
          )

          # Пытаемся разобрать JSON, если заголовок Content-Type это допускает.
          content_type = resp.headers.get("Content-Type", "")
          data: Any
          if "application/json" in content_type:
              try:
                  data = resp.json()
              except ValueError:
                  data = None
          else:
              data = None

          # Обработка ошибок HTTP (4xx/5xx).
          if not resp.ok:
              error_code = None
              message = None
              if isinstance(data, Mapping):
                  error_code = data.get("code")
                  message = data.get("message")
              raise MaxAPIError(
                  status_code=resp.status_code,
                  error_code=error_code,
                  message=message,
                  details=data if isinstance(data, Mapping) else None,
              )

          # Если JSON распарсился — возвращаем его, иначе текст ответа.
          return data if data is not None else resp.text

      # ---------- Бот / информация о себе ----------

      def get_me(self) -> Mapping[str, Any]:
          """
          GET /me — информация о текущем боте.

          Возвращает:
              Сырой словарь (BotInfo) с полями, описывающими бота:
              ID, имя, username, команды и т.д.
          """
          return self._request("GET", "/me")

      # ---------- Сообщения ----------

      def get_messages(
          self,
          *,
          chat_id: Optional[int] = None,
          message_ids: Optional[Iterable[str]] = None,
          from_timestamp: Optional[int] = None,
          to_timestamp: Optional[int] = None,
          count: int = 50,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /messages — получить список сообщений.

          Параметры:
              chat_id:
                  ID чата, из которого нужно получить сообщения.
              message_ids:
                  Итерируемый набор ID сообщений (строки mid). Если указан,
                  фильтрация по времени и count/marker не используется.
              from_timestamp:
                  Начальная граница по времени (Unix time * 1000 в мс).
              to_timestamp:
                  Конечная граница по времени (Unix time * 1000 в мс).
              count:
                  Максимальное количество сообщений (1..100).
              as_models:
                  Если True, возвращаются dataclasses models.Message;
                  если False — "сырые" dict; если None — используется
                  self._use_models.

          Возвращает:
              - при use_models/as_models=False: dict MessageList {"messages": [...]}
              - при use_models/as_models=True:  List[models.Message].
          """
          params: Dict[str, Any] = {"count": count}
          if chat_id is not None:
              params["chat_id"] = chat_id
          if message_ids:
              params["message_ids"] = ",".join(message_ids)
          if from_timestamp is not None:
              params["from"] = from_timestamp
          if to_timestamp is not None:
              params["to"] = to_timestamp

          data = self._request("GET", "/messages", params=params)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw_messages = data.get("messages") or []
              return [models.Message.from_dict(m) for m in raw_messages]

          return data

      def get_message(
          self,
          message_id: str,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /messages/{messageId} — получить одно сообщение по mid.

          Параметры:
              message_id:
                  Строковый идентификатор сообщения (Message.body.mid).
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict (schema Message);
              - при use_models/as_models=True:  models.Message.
          """
          path = f"/messages/{message_id}"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              return models.Message.from_dict(data)

          return data

      def send_message(
          self,
          *,
          chat_id: Optional[int] = None,
          user_id: Optional[int] = None,
          text: Optional[str] = None,
          attachments: Optional[Sequence[Mapping[str, Any]]] = None,
          disable_link_preview: Optional[bool] = None,
          extra: Optional[Mapping[str, Any]] = None,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          POST /messages — отправка сообщения.

          Параметры:
              chat_id:
                  ID чата, в который отправляем сообщение.
              user_id:
                  ID пользователя, которому отправляем личное сообщение.
                  Должен быть указан либо chat_id, либо user_id.
              text:
                  Текст сообщения (может быть None, если только attachments).
              attachments:
                  Список вложений (словарей), соответствующих AttachmentRequest*.
              disable_link_preview:
                  Если True, предпросмотр ссылок отключается.
              extra:
                  Дополнительные поля тела (например, link, format, notify),
                  которые напрямую копируются в JSON.
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict SendMessageResult;
              - при use_models/as_models=True:  models.Message (поле "message").
          """
          if chat_id is None and user_id is None:
              raise ValueError("Нужно указать chat_id или user_id")

          params: Dict[str, Any] = {}
          if user_id is not None:
              params["user_id"] = user_id
          if chat_id is not None:
              params["chat_id"] = chat_id
          if disable_link_preview is not None:
              params["disable_link_preview"] = disable_link_preview

          body: Dict[str, Any] = {}
          if text is not None:
              body["text"] = text
          if attachments is not None:
              body["attachments"] = list(attachments)
          if extra:
              body.update(extra)

          data = self._request("POST", "/messages", params=params, json_body=body)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              msg = data.get("message")
              if isinstance(msg, Mapping):
                  return models.Message.from_dict(msg)

          return data

      def edit_message(
          self,
          message_id: str,
          *,
          text: Optional[str] = None,
          attachments: Optional[Sequence[Mapping[str, Any]]] = None,
          extra: Optional[Mapping[str, Any]] = None,
      ) -> Mapping[str, Any]:
          """
          PUT /messages — редактирование сообщения.

          Параметры:
              message_id:
                  ID сообщения (mid), которое требуется изменить.
              text:
                  Новый текст сообщения (если None — текст не меняется).
              attachments:
                  Новый список вложений (если None — вложения не меняются).
              extra:
                  Дополнительные поля тела запроса.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          params = {"message_id": message_id}
          body: Dict[str, Any] = {}
          if text is not None:
              body["text"] = text
          if attachments is not None:
              body["attachments"] = list(attachments)
          if extra:
              body.update(extra)
          return self._request("PUT", "/messages", params=params, json_body=body)

      def delete_message(self, message_id: str) -> Mapping[str, Any]:
          """
          DELETE /messages — удаление сообщения.

          Параметры:
              message_id:
                  ID сообщения (mid), которое нужно удалить.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          params = {"message_id": message_id}
          return self._request("DELETE", "/messages", params=params)

      # ---------- Обновления (long polling) ----------

      def get_updates(
          self,
          *,
          limit: int = 100,
          timeout: int = 30,
          marker: Optional[int] = None,
          types: Optional[Iterable[str]] = None,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /updates — получение обновлений (long polling).

          Параметры:
              limit:
                  Максимальное количество обновлений в одном ответе (1..1000).
              timeout:
                  Время (в секундах), которое сервер может "долго" держать запрос
                  без ответа, ожидая новые события.
              marker:
                  Маркер "с какого места" продолжить получение событий.
                  Если None, возвращаются новые события с текущего момента.
              types:
                  Список строковых типов обновлений (например,
                  ["message_created", "message_callback"]).
              as_models:
                  Флаг возврата моделей или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict UpdateList;
              - при use_models/as_models=True:  {"updates": List[models.Update], "marker": int | None}.
          """
          params: Dict[str, Any] = {"limit": limit, "timeout": timeout}
          if marker is not None:
              params["marker"] = marker
          if types:
              params["types"] = ",".join(types)

          data = self._request("GET", "/updates", params=params)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw_updates = data.get("updates") or []
              return {
                  "marker": data.get("marker"),
                  "updates": [models.Update.from_dict(u) for u in raw_updates],
              }

          return data

      # ---------- Чаты ----------

      def get_chats(
          self,
          *,
          count: int = 50,
          marker: Optional[int] = None,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats — список чатов, где присутствует бот.

          Параметры:
              count:
                  Максимальное количество чатов в ответе (1..100).
              marker:
                  Маркер, указывающий, откуда продолжить список чатов.
                  Если None, возвращаются чаты "с начала".
              as_models:
                  Флаг возврата моделей или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict ChatList;
              - при use_models/as_models=True:  {"chats": List[models.Chat], "marker": int | None}.
          """
          params: Dict[str, Any] = {"count": count}
          if marker is not None:
              params["marker"] = marker

          data = self._request("GET", "/chats", params=params)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw_chats = data.get("chats") or []
              return {
                  "marker": data.get("marker"),
                  "chats": [models.Chat.from_dict(c) for c in raw_chats],
              }

          return data

      def get_chat(
          self,
          chat_id: int,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatId} — информация о конкретном чате по ID.

          Параметры:
              chat_id:
                  Числовой идентификатор чата.
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict Chat;
              - при use_models/as_models=True:  models.Chat.
          """
          path = f"/chats/{chat_id}"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              return models.Chat.from_dict(data)

          return data

      def get_chat_by_link(
          self,
          chat_link: str,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatLink} — получить чат по короткой ссылке или username.

          Параметры:
              chat_link:
                  Строка вида "@username" или просто "username" / короткий линк.
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict Chat;
              - при use_models/as_models=True:  models.Chat.
          """
          path = f"/chats/{chat_link}"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              return models.Chat.from_dict(data)

          return data

      def get_pinned_message(
          self,
          chat_id: int,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatId}/pin — получить закреплённое сообщение в чате.

          Параметры:
              chat_id:
                  ID чата.
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict GetPinnedMessageResult {"message": {...} | null};
              - при use_models/as_models=True:  models.Message или None.
          """
          path = f"/chats/{chat_id}/pin"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw = data.get("message")
              if raw is None:
                  return None
              if isinstance(raw, Mapping):
                  return models.Message.from_dict(raw)

          return data

      def pin_message(
          self,
          chat_id: int,
          message_id: str,
          *,
          notify: Optional[bool] = None,
      ) -> Mapping[str, Any]:
          """
          PUT /chats/{chatId}/pin — закрепить сообщение в чате.

          Параметры:
              chat_id:
                  ID чата, где нужно закрепить сообщение.
              message_id:
                  ID сообщения (mid), которое нужно закрепить.
              notify:
                  Если True, участникам отправляется уведомление о закреплении.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/pin"
          body: Dict[str, Any] = {"message_id": message_id}
          if notify is not None:
              body["notify"] = notify
          return self._request("PUT", path, json_body=body)

      def unpin_message(
          self,
          chat_id: int,
      ) -> Mapping[str, Any]:
          """
          DELETE /chats/{chatId}/pin — снять закрепление сообщения в чате.

          Параметры:
              chat_id:
                  ID чата.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/pin"
          return self._request("DELETE", path)

      def send_chat_action(
          self,
          chat_id: int,
          action: str,
      ) -> Mapping[str, Any]:
          """
          POST /chats/{chatId}/actions — отправить "действие" в чат.

          Используется, например, для отображения "бот печатает...".

          Параметры:
              chat_id:
                  ID чата.
              action:
                  Строковое значение SenderAction (например, "typing").

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/actions"
          body = {"action": action}
          return self._request("POST", path, json_body=body)

      # ---------- Участники чата ----------

      def get_chat_members(
          self,
          chat_id: int,
          *,
          user_ids: Optional[Iterable[int]] = None,
          marker: Optional[int] = None,
          count: int = 20,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatId}/members — получить список участников чата.

          Параметры:
              chat_id:
                  ID чата.
              user_ids:
                  Необязательный список ID пользователей, для которых нужно
                  получить информацию. Если указан, пагинация по marker/count
                  не используется.
              marker:
                  Маркер постраничной навигации.
              count:
                  Максимальное количество участников в одном ответе (1..100).
              as_models:
                  Флаг возврата моделей или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict ChatMembersList;
              - при use_models/as_models=True:  {"members": List[models.ChatMember], "marker": int | None}.
          """
          params: Dict[str, Any] = {"count": count}
          if marker is not None:
              params["marker"] = marker
          if user_ids:
              params["user_ids"] = ",".join(str(u) for u in user_ids)

          path = f"/chats/{chat_id}/members"
          data = self._request("GET", path, params=params)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw_members = data.get("members") or []
              return {
                  "marker": data.get("marker"),
                  "members": [models.ChatMember.from_dict(m) for m in raw_members],
              }

          return data

      def add_chat_members(
          self,
          chat_id: int,
          user_ids: Iterable[int],
      ) -> Mapping[str, Any]:
          """
          POST /chats/{chatId}/members — добавить участников в чат.

          Параметры:
              chat_id:
                  ID чата.
              user_ids:
                  Итерируемый список ID пользователей, которых нужно добавить.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/members"
          # Тело запроса ожидает объект UserIdsList со списком user_ids.
          body = {"user_ids": list(user_ids)}
          return self._request("POST", path, json_body=body)

      def remove_chat_member(
          self,
          chat_id: int,
          user_id: int,
      ) -> Mapping[str, Any]:
          """
          DELETE /chats/{chatId}/members — удалить участника из чата.

          Параметры:
              chat_id:
                  ID чата.
              user_id:
                  ID пользователя, которого нужно удалить.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/members"
          params = {"user_id": user_id}
          return self._request("DELETE", path, params=params)

      def get_my_membership(
          self,
          chat_id: int,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatId}/members/me — информация о боте как об участнике чата.

          Параметры:
              chat_id:
                  ID чата.
              as_models:
                  Флаг возврата модели или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict ChatMember;
              - при use_models/as_models=True:  models.ChatMember.
          """
          path = f"/chats/{chat_id}/members/me"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              return models.ChatMember.from_dict(data)

          return data

      def leave_chat(
          self,
          chat_id: int,
      ) -> Mapping[str, Any]:
          """
          DELETE /chats/{chatId}/members/me — бот выходит из чата.

          Параметры:
              chat_id:
                  ID чата.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/members/me"
          return self._request("DELETE", path)

      def get_chat_admins(
          self,
          chat_id: int,
          *,
          as_models: Optional[bool] = None,
      ) -> Any:
          """
          GET /chats/{chatId}/members/admins — список админов чата.

          Параметры:
              chat_id:
                  ID чата.
              as_models:
                  Флаг возврата моделей или сырого dict.

          Возвращает:
              - при use_models/as_models=False: dict ChatAdminsList;
              - при use_models/as_models=True:  {"admins": List[models.ChatAdmin], "marker": int | None}.
          """
          path = f"/chats/{chat_id}/members/admins"
          data = self._request("GET", path)

          if self._should_use_models(as_models) and isinstance(data, Mapping):
              raw_admins = data.get("admins") or []
              return {
                  "marker": data.get("marker"),
                  "admins": [models.ChatAdmin.from_dict(a) for a in raw_admins],
              }

          return data

      def set_chat_admins(
          self,
          chat_id: int,
          admins: Iterable[models.ChatAdmin],
      ) -> Mapping[str, Any]:
          """
          PUT /chats/{chatId}/members/admins — установить список админов чата.

          Параметры:
              chat_id:
                  ID чата.
              admins:
                  Итерируемый список объектов ChatAdmin, содержащих user_id и права.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/members/admins"
          body = {"admins": [a.to_dict() for a in admins]}
          return self._request("PUT", path, json_body=body)

      def delete_chat_admin(
          self,
          chat_id: int,
          user_id: int,
      ) -> Mapping[str, Any]:
          """
          DELETE /chats/{chatId}/members/admins/{userId} — снять права администратора.

          Параметры:
              chat_id:
                  ID чата.
              user_id:
                  ID пользователя, которого нужно лишить прав администратора.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          path = f"/chats/{chat_id}/members/admins/{user_id}"
          return self._request("DELETE", path)

      # ---------- Подписки (webhook) ----------

      def get_subscriptions(self) -> Mapping[str, Any]:
          """
          GET /subscriptions — список активных подписок WebHook.

          Возвращает:
              Сырой словарь, соответствующий GetSubscriptionsResult.
          """
          return self._request("GET", "/subscriptions")

      def subscribe(
          self,
          url: str,
          *,
          types: Optional[Iterable[str]] = None,
      ) -> Mapping[str, Any]:
          """
          POST /subscriptions — создать подписку WebHook.

          Параметры:
              url:
                  HTTPS URL обработчика webhook, на который будут приходить обновления.
              types:
                  Необязательный список типов обновлений, которые нужно получать.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          body: Dict[str, Any] = {"url": url}
          if types:
              body["types"] = list(types)
          return self._request("POST", "/subscriptions", json_body=body)

      def unsubscribe(self, url: str) -> Mapping[str, Any]:
          """
          DELETE /subscriptions — удалить подписку WebHook.

          Параметры:
              url:
                  URL, который нужно удалить из списка подписок.

          Возвращает:
              Сырой словарь SuccessResponse.
          """
          params = {"url": url}
          return self._request("DELETE", "/subscriptions", params=params)

      # ---------- Хелперы для inline-клавиатур ----------

      @staticmethod
      def inline_button(
          *,
          type: str,
          text: str,
          **payload_fields: Any,
      ) -> Mapping[str, Any]:
          """
          Построить словарь кнопки для InlineKeyboardAttachment.

          Параметры:
              type:
                  Тип кнопки: "callback", "link", "request_contact",
                  "request_geo_location", "open_app", "message" и т.п.
              text:
                  Текст на кнопке.
              **payload_fields:
                  Дополнительные поля, которые добавляются в кнопку, зависят
                  от типа (например, payload для callback).

          Возвращает:
              Словарь, готовый к использованию в attachments.
          """
          button: Dict[str, Any] = {"type": type, "text": text}
          button.update(payload_fields)
          return button

      @staticmethod
      def inline_keyboard(
          rows: Sequence[Sequence[Mapping[str, Any]]],
      ) -> Mapping[str, Any]:
          """
          Построить вложение InlineKeyboardAttachmentRequest.

          Параметры:
              rows:
                  Последовательность строк клавиатуры, где каждая строка —
                  последовательность кнопок (dict), созданных, например,
                  с помощью inline_button.

          Возвращает:
              Словарь вида:
                  {
                      "type": "inline_keyboard",
                      "payload": {"buttons": [[button1, button2], [button3]]}
                  }
          """
          return {
              "type": "inline_keyboard",
              "payload": {"buttons": [list(row) for row in rows]},
          }
