-- Create tables for e-learning platform

-- Enable Row Level Security for all tables

-- Admins table
CREATE TABLE IF NOT EXISTS admins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Students table  
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NULL REFERENCES auth.users(id), -- Made user_id nullable
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Instructors table
CREATE TABLE IF NOT EXISTS instructors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NULL REFERENCES auth.users(id), -- Made nullable
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger to update user_id when auth user is created
CREATE OR REPLACE FUNCTION set_instructor_user_id()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_id IS NULL THEN
        NEW.user_id := (SELECT id FROM auth.users WHERE email = NEW.email LIMIT 1);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_set_instructor_user_id
BEFORE UPDATE ON instructors
FOR EACH ROW
EXECUTE FUNCTION set_instructor_user_id();

-- Update RLS policy to allow NULL user_id during creation
CREATE POLICY instructor_null_user_id ON instructors
    FOR INSERT TO authenticated
    WITH CHECK (user_id IS NULL OR user_id = auth.uid());

-- Courses table
CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    description TEXT,
    instructor_id UUID NOT NULL REFERENCES instructors(id),
    price DECIMAL(10,2) NOT NULL,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Enrollments table (student-course relationship)
CREATE TABLE IF NOT EXISTS enrollments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status TEXT NOT NULL DEFAULT 'active',
    course_title TEXT NOT NULL,
    UNIQUE (student_id, course_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_instructors_email ON instructors(email);
CREATE INDEX IF NOT EXISTS idx_courses_instructor ON courses(instructor_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS idx_enrollments_course ON enrollments(course_id);

-- Enable Row Level Security and set policies
ALTER TABLE admins ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE instructors ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;

-- Admin policies (only admins can access)
CREATE POLICY admin_all ON admins TO authenticated USING (true);
CREATE POLICY admin_manage_students ON students TO authenticated USING (auth.role() = 'admin');
CREATE POLICY admin_manage_instructors ON instructors TO authenticated USING (auth.role() = 'admin');
CREATE POLICY admin_manage_courses ON courses TO authenticated USING (auth.role() = 'admin');
CREATE POLICY admin_manage_enrollments ON enrollments TO authenticated USING (auth.role() = 'admin');

-- Student policies (students can view their own data)
CREATE POLICY student_view_self ON students FOR SELECT USING (user_id = auth.uid());
CREATE POLICY student_view_own_enrollments ON enrollments FOR SELECT USING (student_id = (SELECT id FROM students WHERE user_id = auth.uid()));

-- Instructor policies (instructors can manage their courses)
CREATE POLICY instructor_manage_own_courses ON courses FOR ALL USING (instructor_id = (SELECT id FROM instructors WHERE user_id = auth.uid()));
CREATE POLICY instructor_view_own_students ON enrollments FOR SELECT USING (course_id IN (SELECT id FROM courses WHERE instructor_id = (SELECT id FROM instructors WHERE user_id = auth.uid())));
