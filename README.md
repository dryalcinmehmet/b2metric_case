If you operation system is Debian follow the instructions.

🟧🟨 sudo apt-get update

🟧🟨 sudo apt install make

If you operation system is MacOS follow the instructions.

🟧🟨 brew install make

Run FastAPI project on Docker:

First try to make command:  

🟧🟨 make help

If you see colorful informations then you can run this:

🟧🟨 make dev

It will run projects with docker-compose.


🟣 Fast API Page: http://0.0.0.0:8000

🟣 Fast API: OpenAPI Documents Page: http://0.0.0.0:8000/api/docs


🟣 You can find Postman collection in app folder as "B2Metric.postman_collection.json" for using REST endpoints.
🟣 After run "make dev" command Makefile is gonna starting docker-compose commands.

Celery Tasks:

    🟧🟨 send_overdue_reminders -> It runs every minute.
    
    🟧🟨 generate_weekly_report_reminders -> It runs every week on Monday at 08:00.

Best Regards
