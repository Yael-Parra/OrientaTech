# OrientaTech Database

This module contains all necessary components for working with the OrientaTech project database.

## Database Structure

The database includes the following tables:

### 1. `users` - Users
- `id` - Primary key
- `email` - Unique email
- `password_hash` - Hashed password
- `is_active` - Account activity status
- `is_verified` - Email verification status
- `created_at` - Creation date
- `updated_at` - Last update date
- `last_login` - Last login date

### 2. `user_personal_info` - Personal Information
- `id` - Primary key
- `user_id` - User reference (FK)
- `full_name` - Full name
- `date_of_birth` - Date of birth
- `gender` - Gender
- `location` - Location
- `education_level` - Education level
- `previous_experience` - Previous experience
- `area_of_interest` - Area of interest
- `main_skills` - Main skills
- `digital_level` - Digital literacy level
- `resume_path` - Resume file path
- `resume_embedding` - Resume vector embedding
- `updated_at` - Last update date

### 3. `employment_platforms` - Employment Platforms
- `id` - Primary key
- `name` - Platform name
- `type` - Platform type
- `url` - Platform URL
- `description` - Description
- `country` - Country
- `category` - Category
- `validated` - Validation status
- `registered_at` - Registration date

### 4. `reviews` - Reviews
- `id` - Primary key
- `user_id` - User reference (FK)
- `platform_id` - Platform reference (FK)
- `is_platform_review` - Whether it's a platform review
- `review_type` - Review type
- `rating` - Rating (1-5)
- `comment` - Comment
- `created_at` - Creation date
- `visible` - Review visibility

## Module Files

- `db_connection.py` - Database connection functions
- `create_database.py` - Database creation
- `init_extensions.py` - Extensions initialization (pgvector)
- `db_tables_creation.py` - All tables creation
- `init_database.py` - Complete database initialization

## Usage

### Complete database initialization

```bash
python init_database.py
```

### Individual components

```python
from database import (
    create_database,
    init_pgvector_extension,
    create_all_tables,
    connect,
    disconnect
)

# Database creation
create_database()

# Extensions initialization
init_pgvector_extension()

# Tables creation
create_all_tables()

# Database connection
conn = connect()
# ... database operations
disconnect(conn)
```

## Requirements

Make sure you have all dependencies installed from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Features

- Uses `pgvector` extension for vector data operations
- Automatic `updated_at` field updates when records are modified
- Indexes for query optimization
