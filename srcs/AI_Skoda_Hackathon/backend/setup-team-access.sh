#!/bin/bash

# Setup Shared Database User for Team Access
# This allows team members to access the database with a password

DB_NAME="skillbridge_ai"
TEAM_USER="skillbridge_team"
DEFAULT_PASSWORD="skillbridge2024"

echo "🔧 Setting up shared database user for team access"
echo ""
echo "📦 Database: $DB_NAME"
echo "👥 Team User: $TEAM_USER"
echo ""

# Prompt for password
read -sp "Enter password for team user (press Enter for default: $DEFAULT_PASSWORD): " USER_PASSWORD
echo ""
USER_PASSWORD=${USER_PASSWORD:-$DEFAULT_PASSWORD}

echo ""
echo "Creating shared user and granting permissions..."

# Create user and grant permissions using psql
psql -U alibiyermekov -d postgres << EOF
-- Create the shared user
CREATE USER $TEAM_USER WITH PASSWORD '$USER_PASSWORD';

-- Grant database privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $TEAM_USER;

-- Make user a superuser (optional, comment out for restricted access)
-- ALTER USER $TEAM_USER WITH SUPERUSER;

EOF

# Connect to the database and grant schema privileges
psql -U alibiyermekov -d $DB_NAME << EOF
-- Grant schema permissions
GRANT ALL ON SCHEMA public TO $TEAM_USER;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $TEAM_USER;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $TEAM_USER;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO $TEAM_USER;

-- Set default privileges for future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $TEAM_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $TEAM_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO $TEAM_USER;

EOF

echo ""
echo "✅ Shared user created successfully!"
echo ""
echo "📋 Share this connection string with your team:"
echo ""
echo "DATABASE_URL=\"postgresql://$TEAM_USER:$USER_PASSWORD@localhost:5432/$DB_NAME?schema=public\""
echo ""
echo "⚠️  Important: Team members need to:"
echo "1. Have PostgreSQL installed locally"
echo "2. Configure pg_hba.conf to allow password authentication"
echo "3. Or use the Docker setup (see docker-compose.yml)"
echo ""
echo "📝 Next steps:"
echo "1. Create .env file in backend folder"
echo "2. Add the connection string above"
echo "3. Run: npm run prisma:migrate"
echo ""
