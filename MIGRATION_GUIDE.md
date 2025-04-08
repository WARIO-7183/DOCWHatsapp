# Migration Guide: MySQL to Supabase (COMPLETED)

> **Note**: This migration has been completed successfully. This guide is kept for reference purposes only.

This guide provides detailed instructions on how to migrate your medical assistant application from MySQL to Supabase.

## Prerequisites

- A Supabase account (sign up at [supabase.com](https://supabase.com) if you don't have one)
- Your existing MySQL database with user data (if you want to migrate existing data)

## Step 1: Create a Supabase Project

1. Log in to your Supabase account
2. Click on "New Project" to create a new project
3. Fill in the project details:
   - Name: `medical_assistant` (or your preferred name)
   - Database Password: Create a secure password
   - Region: Choose the region closest to your users
4. Click "Create New Project" and wait for the project to be created

## Step 2: Get Supabase Credentials

1. Once your project is created, go to the project dashboard
2. Navigate to "Project Settings" > "API"
3. Copy the following values:
   - Project URL (this will be your `SUPABASE_URL`)
   - `anon` public API key (this will be your `SUPABASE_KEY`)

## Step 3: Create the Database Table

1. In your Supabase dashboard, go to "SQL Editor"
2. Create a new query
3. Copy and paste the contents of the `supabase_migration.sql` file
4. Run the query to create the users table and the trigger for updating timestamps

## Step 4: Update Environment Variables

1. Open your `.env` file
2. Replace the MySQL credentials with your Supabase credentials:
   ```
   # Remove these MySQL credentials
   # DB_HOST=localhost
   # DB_USER=root
   # DB_PASSWORD=your_password
   # DB_NAME=medical_assistant
   
   # Add these Supabase credentials
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
3. Save the file

## Step 5: Install Required Packages

1. Install the Supabase Python client:
   ```
   pip install supabase
   ```

## Step 6: Migrate Existing Data (Optional)

If you have existing user data in your MySQL database that you want to migrate to Supabase, follow these steps:

1. Export your MySQL data to a CSV file:
   ```
   mysql -u root -p medical_assistant -e "SELECT * FROM users" > users.csv
   ```

2. In your Supabase dashboard, go to "Table Editor" > "users"
3. Click on "Import Data" and select your CSV file
4. Follow the prompts to map your columns correctly

## Step 7: Test Your Application

1. Run your application to ensure it connects to Supabase correctly
2. Test all database operations (creating users, updating medical history, etc.)
3. Check the logs for any errors

## Troubleshooting

### Connection Issues

- Verify that your Supabase URL and API key are correct
- Check that your application has internet access to reach Supabase
- Ensure your Supabase project is active and not in maintenance mode

### Data Type Issues

- Supabase uses PostgreSQL, which has some differences from MySQL
- If you encounter data type issues, you may need to adjust your schema or data

### Permission Issues

- By default, Supabase tables have Row Level Security (RLS) enabled
- You may need to configure RLS policies to allow your application to access the data
- For development, you can disable RLS for the users table, but for production, you should set up proper policies

## Additional Resources

- [Supabase Documentation](https://supabase.io/docs)
- [Supabase Python Client](https://supabase.io/docs/reference/python/introduction)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/) 