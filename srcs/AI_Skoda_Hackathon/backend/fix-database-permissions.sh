#!/bin/bash

# Fix Database Permissions Script
# This script fixes PostgreSQL permission issues for the skillbridge_ai database

DB_NAME="skillbridge_ai"
DB_USER="alibiyermekov"

echo "🔧 Fixing database permissions for user: $DB_USER"
echo "📦 Database: $DB_NAME"
echo ""

# Check if database exists
echo "Checking if database exists..."
DB_EXISTS=$(psql -U postgres -lqt | cut -d \| -f 1 | grep -w "$DB_NAME" | wc -l)

if [ $DB_EXISTS -eq 0 ]; then
    echo "❌ Database '$DB_NAME' does not exist. Creating it..."
    createdb -U postgres -O "$DB_USER" "$DB_NAME"
    echo "✅ Database created successfully!"
else
    echo "✅ Database exists."
fi

echo ""
echo "Granting permissions..."

# Grant permissions using psql
psql -U postgres -d postgres << EOF
-- Grant database privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;

-- Connect to the database and grant schema privileges
\c $DB_NAME

-- Grant schema permissions
GRANT ALL ON SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $DB_USER;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $DB_USER;

-- Make the user owner of the database
ALTER DATABASE $DB_NAME OWNER TO $DB_USER;

EOF

echo ""
echo "✅ Permissions granted successfully!"
echo ""
echo "🔄 Now you can run: npm run prisma:migrate"
