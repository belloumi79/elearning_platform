# Student Registration Endpoint Implementation Plan

## Overview
Implement an endpoint to register student users with email and password in the e-learning platform.

## Current Architecture Analysis
- **Authentication**: Uses Supabase Auth for user management
- **Database**: Supabase PostgreSQL with tables: `admins`, `students`, `instructors`
- **Backend**: Flask application with service layer pattern
- **Existing Auth**: Login endpoint exists, but no signup for students

## Database Schema (students table)
```sql
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id), -- nullable initially
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Implementation Steps

### 1. Create Student Signup Function in auth_service.py
**Function**: `signup_student(email, password, name=None, phone=None)`

**Logic**:
1. Create user in Supabase Auth using `supabase.auth.admin.create_user()`
2. Extract the user ID from the created auth user
3. Create student record in `students` table with the auth user_id
4. Return user data and tokens

**Parameters**:
- `email` (required): Student's email address
- `password` (required): Student's password
- `name` (optional): Student's full name
- `phone` (optional): Student's phone number

**Returns**:
- Success: User data with access/refresh tokens
- Error: Appropriate error messages for validation failures

### 2. Add Signup Route in auth.py
**Route**: `POST /api/v1/auth/signup`

**Request Body**:
```json
{
  "email": "student@example.com",
  "password": "securepassword123",
  "name": "John Doe",
  "phone": "+1234567890"
}
```

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "refresh_token": "refresh_token_here",
  "token_type": "bearer",
  "user": {
    "id": "user_id",
    "email": "student@example.com",
    "name": "John Doe",
    "role": "student",
    "profile_type": "student"
  }
}
```

### 3. Error Handling
- Email already exists
- Invalid email format
- Weak password
- Missing required fields
- Database connection issues

### 4. Security Considerations
- Password validation (minimum length, complexity)
- Email format validation
- Rate limiting (consider implementing)
- Input sanitization

## API Documentation
Update API_DOCUMENTATION.md with the new endpoint specification.

## Testing
- Unit tests for the signup function
- Integration tests for the endpoint
- Test edge cases (duplicate email, invalid data)

## Files to Modify
1. `app/services/auth_service.py` - Add `signup_student()` function
2. `app/routes/auth.py` - Add `/signup` route
3. `API_DOCUMENTATION.md` - Document the new endpoint

## Dependencies
- Existing Supabase client setup
- JWT service for token generation
- Existing error handling patterns