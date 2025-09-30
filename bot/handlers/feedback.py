from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from app.models import Demand
from asgiref.sync import sync_to_async
from authentication.models import User

from bot.const import FEEDBACK_

router = Router()

class DemandState(StatesGroup):
    waiting_for_text = State()

@router.message(F.text == FEEDBACK_)
async def start_demand(message, state: FSMContext):
    await message.answer("✍️ Please enter your request:")
    await state.set_state(DemandState.waiting_for_text)

@router.message(DemandState.waiting_for_text)
async def process_demand(message, state: FSMContext):
    user = await User.objects.aget(telegram_id=message.from_user.id)
    await Demand.objects.acreate(user=user, main_text=message.text)
    await message.answer("✅ Your feedback has been saved.")
    await state.clear()
