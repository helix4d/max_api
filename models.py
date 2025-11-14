"""
  Модели (dataclasses), описывающие основные сущности Max Bot API.

  Цель этого модуля —
  дать типизированные Python-объекты вместо "сырых" словарей JSON,
  которые возвращает API. Для каждой сущности есть:

  - dataclass с полями, соответствующими схеме swagger;
  - метод `from_dict` для преобразования из JSON (dict);
  - метод `to_dict` для обратного преобразования в JSON-совместимый dict.

  Эти модели используются в MaxBotAPI, когда клиент настроен с use_models=True.
  """

  from __future__ import annotations

  from dataclasses import dataclass, field
  from typing import Any, Dict, List, Mapping, Optional


  # ========== Пользователи ==========


  @dataclass
  class User:
      """
      Пользователь (schema User).

      Эта модель описывает любого пользователя Max (как обычного, так и бота).

      Атрибуты:
          user_id: Уникальный числовой идентификатор пользователя в системе Max.
          first_name: Имя пользователя (обязательное поле).
          last_name: Фамилия пользователя. Может быть None, если не указана.
          username: Публичный username (короткий логин) или None,
              если пользователь не установил себе username.
          is_bot: True, если этот пользователь является ботом.
          last_activity_time: Время последней активности пользователя в Max
              в формате Unix time (миллисекунды).
          name: Удобное "собранное" имя (обычно first_name + last_name),
              может быть None.
      """

      user_id: int
      first_name: str
      last_name: Optional[str]
      username: Optional[str]
      is_bot: bool
      last_activity_time: int
      name: Optional[str] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "User":
          """
          Создать объект User из словаря JSON.

          Параметры:
              data: Словарь, полученный из ответа API (schema User).

          Возвращает:
              Экземпляр User.
          """
          return cls(
              user_id=data["user_id"],
              first_name=data["first_name"],
              last_name=data.get("last_name"),
              username=data.get("username"),
              is_bot=data["is_bot"],
              last_activity_time=data["last_activity_time"],
              name=data.get("name"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать объект User обратно в словарь JSON-совместимого вида.

          Возвращает:
              Словарь с ключами, соответствующими схеме User.
          """
          return {
              "user_id": self.user_id,
              "first_name": self.first_name,
              "last_name": self.last_name,
              "username": self.username,
              "is_bot": self.is_bot,
              "last_activity_time": self.last_activity_time,
              "name": self.name,
          }


  @dataclass
  class UserWithPhoto(User):
      """
      Пользователь с информацией об аватаре (schema UserWithPhoto).

      Это расширение User, которое добавляет поля, связанные
      с публичным профилем и фотографиями.

      Дополнительные атрибуты:
          description: Описание пользователя (био). Может быть None.
          avatar_url: URL аватарки (иконка).
          full_avatar_url: URL большого изображения аватарки.
      """

      description: Optional[str] = None
      avatar_url: Optional[str] = None
      full_avatar_url: Optional[str] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "UserWithPhoto":
          """
          Создать UserWithPhoto из словаря JSON.

          Параметры:
              data: Словарь с полями User + UserWithPhoto.

          Возвращает:
              Экземпляр UserWithPhoto.
          """
          base = User.from_dict(data)
          return cls(
              # разворачиваем базовый словарь, чтобы не дублировать код
              **base.to_dict(),
              description=data.get("description"),
              avatar_url=data.get("avatar_url"),
              full_avatar_url=data.get("full_avatar_url"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать UserWithPhoto в словарь JSON-совместимого вида.

          Возвращает:
              Словарь со всеми полями User + UserWithPhoto.
          """
          d = super().to_dict()
          d.update(
              {
                  "description": self.description,
                  "avatar_url": self.avatar_url,
                  "full_avatar_url": self.full_avatar_url,
              }
          )
          return d


  # ========== Получатель сообщения ==========


  @dataclass
  class Recipient:
      """
      Получатель сообщения (schema Recipient).

      Recipient описывает, куда направлено сообщение:
      в конкретный чат или конкретному пользователю.

      Атрибуты:
          chat_id: ID чата, в который направлено сообщение, либо None.
          chat_type: Тип чата (значение enum ChatType, например "chat" или "dialog").
          user_id: ID пользователя, если сообщение направлено пользователю (для диалога),
              либо None.
      """

      chat_id: Optional[int]
      chat_type: str
      user_id: Optional[int]

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "Recipient":
          """
          Создать Recipient из словаря JSON.

          Параметры:
              data: Словарь с полями schema Recipient.

          Возвращает:
              Экземпляр Recipient.
          """
          return cls(
              chat_id=data.get("chat_id"),
              chat_type=data["chat_type"],
              user_id=data.get("user_id"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать Recipient в словарь JSON-совместимого вида.

          Возвращает:
              Словарь с ключами chat_id, chat_type, user_id.
          """
          return {
              "chat_id": self.chat_id,
              "chat_type": self.chat_type,
              "user_id": self.user_id,
          }


  # ========== Вложения ==========


  @dataclass
  class Attachment:
      """
      Базовое вложение сообщения (schema Attachment).

      Это абстракция над всеми типами вложений (фото, видео, файл, локация,
      inline-клавиатура и т.д.). В swagger за конкретный тип отвечает поле `type`
      и discriminator.

      Атрибуты:
          type: Строковый тип вложения (image, video, file, location,
              inline_keyboard, share, sticker и т.п.).
          payload: Содержимое вложения (обычно вложенный объект с полями
              конкретного типа; хранится как dict, так как структура зависит
              от типа вложения).
      """

      type: str
      payload: Optional[Mapping[str, Any]] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "Attachment":
          """
          Создать Attachment из словаря JSON.

          Параметры:
              data: Словарь с полями type и payload (если есть).

          Возвращает:
              Экземпляр Attachment.
          """
          return cls(type=data["type"], payload=data.get("payload"))

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать Attachment в словарь JSON-совместимого вида.

          Возвращает:
              Словарь, пригодный для отправки в API.
          """
          d: Dict[str, Any] = {"type": self.type}
          if self.payload is not None:
              d["payload"] = self.payload
          return d


  @dataclass
  class LocationAttachment(Attachment):
      """
      Вложение с геолокацией (schema LocationAttachment/LocationAttachmentRequest).

      Это частный случай Attachment, в payload которого ожидаются координаты.

      Дополнительные атрибуты:
          latitude: Широта.
          longitude: Долгота.
      """

      latitude: float = 0.0
      longitude: float = 0.0

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "LocationAttachment":
          """
          Создать LocationAttachment из словаря JSON.

          Параметры:
              data: Словарь Attachment, в котором payload содержит latitude/longitude.

          Возвращает:
              Экземпляр LocationAttachment.
          """
          payload = data.get("payload") or {}
          return cls(
              type=data["type"],
              payload=payload,
              latitude=payload.get("latitude", 0.0),
              longitude=payload.get("longitude", 0.0),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать LocationAttachment в словарь JSON-совместимого вида.

          Возвращает:
              Словарь, содержащий type и payload с координатами.
          """
          payload = dict(self.payload or {})
          payload["latitude"] = self.latitude
          payload["longitude"] = self.longitude
          return {"type": self.type, "payload": payload}


  # ========== Доп. сущности сообщений ==========


  @dataclass
  class MessageStat:
      """
      Статистика сообщения (schema MessageStat).

      Атрибуты:
          views: Количество просмотров (или аналогичная метрика).
      """

      views: int

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "MessageStat":
          """
          Создать MessageStat из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema MessageStat.

          Возвращает:
              Экземпляр MessageStat.
          """
          return cls(views=data["views"])

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать MessageStat в словарь JSON-совместимого вида.
          """
          return {"views": self.views}


  @dataclass
  class MessageBody:
      """
      Тело сообщения (schema MessageBody).

      Атрибуты:
          mid: Внутренний ID сообщения (строка).
          seq: Порядковый номер сообщения в чате.
          text: Текст сообщения (может быть None, если только вложения).
          attachments: Список вложений сообщения.
          markup: Список элементов разметки текста (например, bold, italic),
              если используется форматированный текст. Хранится как список dict.
      """

      mid: str
      seq: int
      text: Optional[str]
      attachments: List[Attachment]
      markup: Optional[List[Mapping[str, Any]]] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "MessageBody":
          """
          Создать MessageBody из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema MessageBody.

          Возвращает:
              Экземпляр MessageBody.
          """
          attachments_raw = data.get("attachments") or []
          attachments = [Attachment.from_dict(a) for a in attachments_raw]
          return cls(
              mid=data["mid"],
              seq=data["seq"],
              text=data.get("text"),
              attachments=attachments,
              markup=data.get("markup"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать MessageBody в словарь JSON-совместимого вида.
          """
          return {
              "mid": self.mid,
              "seq": self.seq,
              "text": self.text,
              "attachments": [a.to_dict() for a in self.attachments],
              "markup": self.markup,
          }


  @dataclass
  class NewMessageBody:
      """
      Тело нового сообщения (schema NewMessageBody).

      Используется при отправке сообщения через API.

      Атрибуты:
          text: Текст сообщения (может быть None, если только вложения).
          attachments: Список вложений (Attachment), которые нужно отправить.
          link: Ссылка на другое сообщение (NewMessageLink) — например, для ответа.
          notify: Нужно ли отправлять уведомление участникам (`True` по умолчанию).
          format: Объект формата текста (TextFormat), если используется
              форматирование, хранится как dict.
      """

      text: Optional[str] = None
      attachments: List[Attachment] = field(default_factory=list)
      link: Optional[Mapping[str, Any]] = None
      notify: bool = True
      format: Optional[Mapping[str, Any]] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "NewMessageBody":
          """
          Создать NewMessageBody из словаря JSON (например, если вы читаете
          сохранённую конфигурацию сообщения).

          Параметры:
              data: Словарь, соответствующий schema NewMessageBody.

          Возвращает:
              Экземпляр NewMessageBody.
          """
          attachments_raw = data.get("attachments") or []
          attachments = [Attachment.from_dict(a) for a in attachments_raw]
          return cls(
              text=data.get("text"),
              attachments=attachments,
              link=data.get("link"),
              notify=data.get("notify", True),
              format=data.get("format"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать NewMessageBody в словарь JSON-совместимого вида
          для отправки в API.
          """
          return {
              "text": self.text,
              "attachments": [a.to_dict() for a in self.attachments],
              "link": self.link,
              "notify": self.notify,
              "format": self.format,
          }


  @dataclass
  class LinkedMessage:
      """
      Связанное сообщение (schema LinkedMessage).

      Используется для описания "родительского" сообщения для пересылки,
      цитирования и т.п.

      Атрибуты:
          type: Тип связи (значение MessageLinkType — например, "reply").
          sender: Пользователь, который отправил исходное сообщение (User),
              либо None, если не задан.
          chat_id: ID чата, где было исходное сообщение.
          message: Тело исходного сообщения (MessageBody).
      """

      type: str
      sender: Optional[User]
      chat_id: int
      message: MessageBody

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "LinkedMessage":
          """
          Создать LinkedMessage из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema LinkedMessage.

          Возвращает:
              Экземпляр LinkedMessage.
          """
          sender_raw = data.get("sender")
          sender = User.from_dict(sender_raw) if isinstance(sender_raw, Mapping) else None
          return cls(
              type=data["type"],
              sender=sender,
              chat_id=data["chat_id"],
              message=MessageBody.from_dict(data["message"]),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать LinkedMessage в словарь JSON-совместимого вида.
          """
          return {
              "type": self.type,
              "sender": self.sender.to_dict() if self.sender else None,
              "chat_id": self.chat_id,
              "message": self.message.to_dict(),
          }


  # ========== Message ==========


  @dataclass
  class Message:
      """
      Сообщение в чате (schema Message).

      Атрибуты:
          recipient: Получатель сообщения (Recipient).
          body: Тело сообщения (MessageBody).
          timestamp: Время отправки сообщения в Unix time (миллисекунды).
          sender: Отправитель сообщения (User) или None.
          link: Связанное сообщение (LinkedMessage), если это ответ/пересылка.
          stat: Статистика сообщения (MessageStat) или None.
          url: Публичная URL-ссылка на сообщение, если есть.
      """

      recipient: Recipient
      body: MessageBody
      timestamp: int

      sender: Optional[User] = None
      link: Optional[LinkedMessage] = None
      stat: Optional[MessageStat] = None
      url: Optional[str] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "Message":
          """
          Создать Message из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema Message.

          Возвращает:
              Экземпляр Message.
          """
          sender_raw = data.get("sender")
          link_raw = data.get("link")
          stat_raw = data.get("stat")

          sender = User.from_dict(sender_raw) if isinstance(sender_raw, Mapping) else None
          link = LinkedMessage.from_dict(link_raw) if isinstance(link_raw, Mapping) else None
          stat = MessageStat.from_dict(stat_raw) if isinstance(stat_raw, Mapping) else None

          return cls(
              recipient=Recipient.from_dict(data["recipient"]),
              body=MessageBody.from_dict(data["body"]),
              timestamp=data["timestamp"],
              sender=sender,
              link=link,
              stat=stat,
              url=data.get("url"),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать Message в словарь JSON-совместимого вида.
          """
          return {
              "sender": self.sender.to_dict() if self.sender else None,
              "recipient": self.recipient.to_dict(),
              "timestamp": self.timestamp,
              "link": self.link.to_dict() if self.link else None,
              "body": self.body.to_dict(),
              "stat": self.stat.to_dict() if self.stat else None,
              "url": self.url,
          }


  # ========== Chat ==========


  @dataclass
  class Chat:
      """
      Чат (schema Chat).

      Описывает как личные диалоги, так и групповые чаты/каналы.

      Обязательные атрибуты:
          chat_id: Уникальный ID чата.
          type: Тип чата (значение ChatType, например "chat" или "dialog").
          status: Статус чата (ChatStatus: active, removed, left, closed).
          title: Название чата (может быть None для диалога).
          last_event_time: Время последнего события в чате (Unix time, ms).
          participants_count: Количество участников в чате.
          icon: Объект с информацией о иконке (Image) или None.
          is_public: Флаг публичности (True/False).
          description: Описание чата (может быть None).

      Дополнительные атрибуты:
          owner_id: ID владельца чата или None.
          participants: Словарь {строковый ключ: user_id}, если список участников
              частично включён в объект.
          link: Короткая ссылка на чат (username/ссылка).
          dialog_with_user: Пользователь, с которым ведётся диалог (UserWithPhoto),
              актуально для личных чатов.
          chat_message_id: ID сообщения, создавшего этот чат (например, для
              "чатов по сообщениям") или None.
          pinned_message: Закреплённое сообщение (Message) или None.
      """

      chat_id: int
      type: str
      status: str
      title: Optional[str]
      last_event_time: int
      participants_count: int
      icon: Optional[Mapping[str, Any]]
      is_public: bool
      description: Optional[str]

      owner_id: Optional[int] = None
      participants: Optional[Dict[str, int]] = None
      link: Optional[str] = None
      dialog_with_user: Optional[UserWithPhoto] = None
      chat_message_id: Optional[str] = None
      pinned_message: Optional[Message] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "Chat":
          """
          Создать Chat из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema Chat.

          Возвращает:
              Экземпляр Chat.
          """
          participants = data.get("participants")
          if participants is not None:
              participants = dict(participants)

          dialog_raw = data.get("dialog_with_user")
          dialog = (
              UserWithPhoto.from_dict(dialog_raw)
              if isinstance(dialog_raw, Mapping)
              else None
          )

          pinned_raw = data.get("pinned_message")
          pinned = Message.from_dict(pinned_raw) if isinstance(pinned_raw, Mapping) else None

          return cls(
              chat_id=data["chat_id"],
              type=data["type"],
              status=data["status"],
              title=data.get("title"),
              last_event_time=data["last_event_time"],
              participants_count=data["participants_count"],
              icon=data.get("icon"),
              is_public=data["is_public"],
              description=data.get("description"),
              owner_id=data.get("owner_id"),
              participants=participants,
              link=data.get("link"),
              dialog_with_user=dialog,
              chat_message_id=data.get("chat_message_id"),
              pinned_message=pinned,
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать Chat в словарь JSON-совместимого вида.
          """
          return {
              "chat_id": self.chat_id,
              "type": self.type,
              "status": self.status,
              "title": self.title,
              "last_event_time": self.last_event_time,
              "participants_count": self.participants_count,
              "icon": self.icon,
              "is_public": self.is_public,
              "description": self.description,
              "owner_id": self.owner_id,
              "participants": self.participants,
              "link": self.link,
              "dialog_with_user": self.dialog_with_user.to_dict()
              if self.dialog_with_user
              else None,
              "chat_message_id": self.chat_message_id,
              "pinned_message": self.pinned_message.to_dict()
              if self.pinned_message
              else None,
          }


  # ========== Участники и админы чата ==========


  @dataclass
  class ChatMember(UserWithPhoto):
      """
      Участник чата (schema ChatMember).

      Наследует все поля UserWithPhoto и добавляет
      информацию о статусе пользователя именно в данном чате.

      Дополнительные атрибуты:
          last_access_time: Время последнего просмотра чата этим пользователем
              (Unix time, ms).
          is_owner: True, если пользователь — владелец чата.
          is_admin: True, если пользователь — администратор чата.
          join_time: Время вступления пользователя в чат (Unix time, ms).
          permissions: Список строк с правами (ChatAdminPermission),
              например "read_all_messages", "add_remove_members".
      """

      last_access_time: int
      is_owner: bool
      is_admin: bool
      join_time: int
      permissions: Optional[List[str]] = None

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "ChatMember":
          """
          Создать ChatMember из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema ChatMember.

          Возвращает:
              Экземпляр ChatMember.
          """
          base = UserWithPhoto.from_dict(data)
          return cls(
              **base.to_dict(),
              last_access_time=data["last_access_time"],
              is_owner=data["is_owner"],
              is_admin=data["is_admin"],
              join_time=data["join_time"],
              permissions=list(data["permissions"]) if data.get("permissions") is not None else None,
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать ChatMember в словарь JSON-совместимого вида.
          """
          d = super().to_dict()
          d.update(
              {
                  "last_access_time": self.last_access_time,
                  "is_owner": self.is_owner,
                  "is_admin": self.is_admin,
                  "join_time": self.join_time,
                  "permissions": self.permissions,
              }
          )
          return d


  @dataclass
  class ChatAdmin:
      """
      Админ чата (schema ChatAdmin / ChatAdminsList).

      Эта модель используется для операций с администраторами чата.

      Атрибуты:
          user_id: ID пользователя-администратора.
          permissions: Список строковых прав (ChatAdminPermission).
      """

      user_id: int
      permissions: List[str]

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "ChatAdmin":
          """
          Создать ChatAdmin из словаря JSON.

          Параметры:
              data: Словарь с полями user_id и permissions.

          Возвращает:
              Экземпляр ChatAdmin.
          """
          return cls(
              user_id=data["user_id"],
              permissions=list(data.get("permissions") or []),
          )

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать ChatAdmin в словарь JSON-совместимого вида.
          """
          return {"user_id": self.user_id, "permissions": self.permissions}


  # ========== Update ==========


  @dataclass
  class Update:
      """
      Обновление (schema Update).

      Это базовый тип для всех событий, приходящих через /updates (long polling)
      или через webhook.

      Атрибуты:
          update_type: Строковый тип события (например, "message_created",
              "message_callback", "bot_added" и т.д.).
          timestamp: Время события (Unix time, ms).
          payload: Остальные поля события, зависят от конкретного типа.
              Хранятся в виде словаря.
      """

      update_type: str
      timestamp: int
      payload: Dict[str, Any] = field(default_factory=dict)

      @classmethod
      def from_dict(cls, data: Mapping[str, Any]) -> "Update":
          """
          Создать Update из словаря JSON.

          Параметры:
              data: Словарь, соответствующий schema Update или одному из
                  производных типов.

          Возвращает:
              Экземпляр Update.
          """
          update_type = data["update_type"]
          timestamp = data["timestamp"]
          # Все поля, кроме служебных, складываем в payload
          payload = {k: v for k, v in data.items() if k not in ("update_type", "timestamp")}
          return cls(update_type=update_type, timestamp=timestamp, payload=payload)

      def to_dict(self) -> Dict[str, Any]:
          """
          Преобразовать Update в словарь JSON-совместимого вида.
          """
          data = dict(self.payload)
          data["update_type"] = self.update_type
          data["timestamp"] = self.timestamp
          return data
