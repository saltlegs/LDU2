# Deploying the database
1. Install PostgreSQL
1. Create a database: `createdb ldu2`
    - On Linux, if command returns `role "[username]" does not exist`, run `su postgres -c "createuser --superuser [username]"` and try again
1. Create guilds schema: `psql -f path/to/schema.sql ldu2`
