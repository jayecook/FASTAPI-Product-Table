# Inventory / Product Table 

Added:
- Admin login
- User login
- Password hashing
- Session-based authentication
- Admin-only add, edit, delete, and email alerts
- User view-only access
- Register page

Default accounts for testing the template:
- Admin: admin@example.com / Admin123!
- User: user@example.com / User123!

## Local Docker or to use on VS Studio Code
docker compose down -v
docker compose up --build

Open http://localhost:5000 on your browser once build has been successfully completed.

## Important
Because the users are created by schema.sql, run `docker compose down -v` once before rebuilding so the new users table and starter accounts are refreshed.
