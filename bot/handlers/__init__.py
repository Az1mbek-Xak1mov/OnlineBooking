from . import auth, booking, feedback, start


def register_all_handlers(dp):
    dp.include_router(start.router)
    dp.include_router(auth.router)
    dp.include_router(booking.router)
    dp.include_router(feedback.router)
