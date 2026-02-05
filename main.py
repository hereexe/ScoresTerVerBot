from __future__ import annotations

import asyncio
import logging
import sys
from contextlib import suppress


async def main() -> None:
    """Application entrypoint."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stdout,
    )

    log = logging.getLogger("ScoresTerVerBot")

    try:
        from aiogram import Bot, Dispatcher
        from aiogram.client.default import DefaultBotProperties
        from aiogram.enums import ParseMode
        from aiogram.fsm.storage.memory import MemoryStorage
    except ModuleNotFoundError as e:
        log.error("Missing dependency: %s", e.name)
        log.error("Install requirements: python -m pip install -r requirements.txt")
        raise SystemExit(1) from e

    try:
        from bot.config import load_settings
        from bot.db import connect, ensure_indexes
        from bot.handlers import setup_router
    except ModuleNotFoundError as e:
        log.error("Missing project module: %s", e.name)
        raise SystemExit(1) from e

    try:
        settings = load_settings()
    except Exception as e:
        log.error("Configuration error: %s", e)
        log.error("Copy `.env.example` -> `.env` and set BOT_TOKEN / MONGODB_URI.")
        raise SystemExit(2) from e

    try:
        db = await connect(settings.mongodb_uri, settings.db_name)
        await ensure_indexes(db)
    except Exception:
        log.exception("MongoDB connection failed. Check MONGODB_URI and that MongoDB is running.")
        raise SystemExit(3)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(setup_router())

    try:
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            db=db,
            settings=settings,
        )
    finally:
        with suppress(Exception):
            db.close()
        with suppress(Exception):
            await bot.session.close()


def _entrypoint() -> None:
    """Sync entrypoint wrapper."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    _entrypoint()
