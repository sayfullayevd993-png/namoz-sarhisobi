from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus
from app.config import settings

class ChannelSubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        channel_id = settings.REQUIRED_CHANNEL_ID
        if not channel_id:
            return await handler(event, data)

        bot = data["bot"]
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
            # Start va tekshirish komandalari o'tkaziladi
            if event.text and (event.text.startswith("/start") or event.text.startswith("/help")):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            if event.data == "check_subscription":
                pass
            else:
                pass

        if not user_id or user_id in settings.admin_id_list:
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                return await handler(event, data)
        except Exception:
            # Agar bot kanalda admin bo'lmasa yoki xato bo'lsa, o'tkazib yuborish
            return await handler(event, data)

        # A'zo bo'lmagan bo'lsa
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga a'zo bo'lish", url=settings.REQUIRED_CHANNEL_URL or "https://t.me/")],
            [InlineKeyboardButton(text="🔄 Tekshirish", callback_data="check_subscription")]
        ])

        msg_text = (
            "⚠️ <b>Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'lishingiz lozim.</b>\n\n"
            "Kanalga a'zo bo'lgach, «Tekshirish» tugmasini bosing:"
        )

        if isinstance(event, Message):
            await event.answer(msg_text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(msg_text, reply_markup=kb)
            await event.answer("Avval kanalga a'zo bo'ling!", show_alert=True)
            
        return None
