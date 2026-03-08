from __future__ import annotations

import asyncio
import logging
import threading
from tkinter import messagebox

from telegram import Bot, Update
from telegram.error import TelegramError
from telegram.ext import Application, CommandHandler

logger = logging.getLogger(__name__)


class TgBot:
    """
    Telegram-бот для отправки результатов бросков.

    Использует long-polling в фоновом потоке для получения chat_id
    и затем отправляет сообщения через отдельные async-задачи.
    """

    GREETING = (
        "Привет! Я бот, подключённый к VTM Calculator.\n\n"
        "Поставьте галочку в интерфейсе приложения, чтобы результаты "
        "бросков отправлялись в этот чат.\n\n"
        "Результаты будут отправляться в тот тред, где вы использовали /start."
    )

    def __init__(self, token: str) -> None:
        self.token = token
        self.chat_id: int | str | None = None
        self.thread_id: int | None = None
        self.is_polling: bool = False
        self._application: Application | None = None

    # ── Polling ────────────────────────────────────────────────────────────────

    def start_polling_in_background(self) -> None:
        """Запускает polling в демон-потоке."""
        self.is_polling = True
        threading.Thread(target=self._run_polling, daemon=True).start()

    def _run_polling(self) -> None:
        self._application = (
            Application.builder()
            .token(self.token)
            .build()
        )
        self._application.add_handler(CommandHandler("start", self._on_start))
        self._application.add_handler(CommandHandler("debug", self._on_debug))
        self._application.run_polling()

    async def _on_start(self, update: Update, context) -> None:  # type: ignore[type-arg]
        self.chat_id = update.effective_chat.id
        self.thread_id = update.message.message_thread_id
        try:
            await context.bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=self.thread_id,
                text=self.GREETING,
            )
        except TelegramError as exc:
            logger.error("Ошибка Telegram при /start: %s", exc)
        finally:
            if self._application:
                self._application.stop_running()
            self.is_polling = False

    async def _on_debug(self, update: Update, context) -> None:  # type: ignore[type-arg]
        chat_id = update.effective_chat.id
        thread_id = update.message.message_thread_id
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                parse_mode="HTML",
                text=f"CHAT ID: <code>{chat_id}</code>",
            )
            await context.bot.send_message(
                chat_id=chat_id,
                message_thread_id=thread_id,
                parse_mode="HTML",
                text=f"THREAD ID: <code>{thread_id}</code>",
            )
        except TelegramError as exc:
            logger.error("Ошибка Telegram при /debug: %s", exc)

    def send_async(self, text: str) -> None:
        """Отправляет сообщение в фоновом потоке; показывает ошибку в GUI."""
        threading.Thread(
            target=self._send_sync,
            args=(text,),
            daemon=True,
        ).start()

    def _send_sync(self, text: str) -> None:
        try:
            asyncio.run(self._send_message(text))
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Ошибка отправки", str(exc))

    async def _send_message(self, text: str) -> None:
        bot = Bot(token=self.token)
        thread_id = int(self.thread_id) if self.thread_id is not None else None
        try:
            await bot.send_message(
                chat_id=self.chat_id,
                message_thread_id=thread_id,
                text=text,
                parse_mode="HTML",
            )
        except TelegramError as exc:
            raise RuntimeError(f"Telegram error: {exc}") from exc
