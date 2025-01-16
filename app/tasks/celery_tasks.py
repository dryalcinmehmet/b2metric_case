import asyncio
from celery import Celery
from datetime import datetime
from sqlalchemy.future import select
from app.models.book_model import BookModel
from app.utils.mail import send_overdue_email
from app.models.patron_model import PatronModel
from app.models.checkout_model import CheckoutModel
from app.core.database import celery_async_session_maker
from celery.schedules import crontab
import logging

celery_app = Celery("library_tasks", broker="redis://redis:6379/0")
celery_app.autodiscover_tasks()
celery_app.conf.update(
    broker_connection_retry_on_startup=True,
)


@celery_app.task(acks_late=True)
def send_overdue_reminders():
    async_session = celery_async_session_maker()

    async def handle_async_query():
        async with async_session() as session:
            try:
                query = (
                    select(
                        CheckoutModel.book_id,
                        BookModel.title,
                        PatronModel.name.label("checked_out_by"),
                        PatronModel.email.label("patron_email"),
                        CheckoutModel.checkout_date,
                        CheckoutModel.due_date,
                    )
                    .join(BookModel, CheckoutModel.book_id == BookModel.id)
                    .join(PatronModel, CheckoutModel.patron_id == PatronModel.id)
                    .filter(CheckoutModel.returned == False)
                    .filter(CheckoutModel.due_date < datetime.now())
                )
                result = await session.execute(query)
                books = result.mappings().all()

                for book in books:
                    send_overdue_email(
                        book["patron_email"],
                        "Overdue Book Reminder",
                        f"Your book  is overdue!",
                    )
                    print(f"Kitap: {book['title']} - Yazar: {book['checked_out_by']}")
            except Exception as e:
                print(e)
            finally:
                await session.close()

    asyncio.run(handle_async_query())


@celery_app.task(acks_late=True)
def generate_weekly_report_reminders():
    async_session = celery_async_session_maker()

    async def handle_async_query():
        async with async_session() as session:
            try:
                query = (
                    select(
                        CheckoutModel.book_id,
                        BookModel.title,
                        PatronModel.name.label("checked_out_by"),
                        PatronModel.email.label("patron_email"),
                        CheckoutModel.checkout_date,
                        CheckoutModel.due_date,
                    )
                    .join(BookModel, CheckoutModel.book_id == BookModel.id)
                    .join(PatronModel, CheckoutModel.patron_id == PatronModel.id)
                    .filter(CheckoutModel.returned == False)
                    .distinct()
                )
                result = await session.execute(query)
                books = result.mappings().all()

                html_table = """
                <table border="1">
                    <thead>
                        <tr>
                            <th>Book ID</th>
                            <th>Title</th>
                            <th>Checked Out By</th>
                            <th>Checkout Date</th>
                            <th>Due Date</th>
                        </tr>
                    </thead>
                    <tbody>
                """

                for book in books:
                    html_table += f"""
                    <tr>
                        <td>{book['book_id']}</td>
                        <td>{book['title']}</td>
                        <td>{book['checked_out_by']}</td>
                        <td>{book['checkout_date'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                        <td>{book['due_date'].strftime('%Y-%m-%d %H:%M:%S')}</td>
                    </tr>
                    """

                # HTML Tablo Kapanışı
                html_table += """
                    </tbody>
                </table>
                """

                for book in books:
                    send_overdue_email(
                        book["patron_email"],
                        "Weekly Report",
                        html_table,
                    )
                    print(f"Weekly Report sent!")
            except Exception as e:
                print(e)
            finally:
                await session.close()

    asyncio.run(handle_async_query())


celery_app.conf.beat_schedule = {
    "send_overdue_reminders": {
        "task": "app.tasks.celery_tasks.send_overdue_reminders",
        "schedule": 60,
    },
    "generate_weekly_report_reminders": {
        "task": "app.tasks.celery_tasks.generate_weekly_report_reminders",
        "schedule": crontab(day_of_week="monday", hour=8, minute=0),
    },
}
