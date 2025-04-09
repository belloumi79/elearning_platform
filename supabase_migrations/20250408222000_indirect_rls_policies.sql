-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Allow read access to authenticated users" ON assignment_files;
DROP POLICY IF EXISTS "Allow insert for course instructors/admins" ON assignment_files;
DROP POLICY IF EXISTS "Allow read access to authenticated users" ON assignment_links;
DROP POLICY IF EXISTS "Allow insert for course instructors/admins" ON assignment_links;

-- Enable RLS (safe if already enabled)
ALTER TABLE public.assignment_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignment_links ENABLE ROW LEVEL SECURITY;

-- =========================
-- assignment_files policies
-- =========================

-- Admins full access (JWT claim)
CREATE POLICY "Admin full access to assignment_files"
ON public.assignment_files
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

-- Authenticated users can read all files
CREATE POLICY "Allow read access to authenticated users"
ON public.assignment_files
FOR SELECT
USING (auth.role() = 'authenticated');

-- Instructors can access files linked to their courses
CREATE POLICY "Instructors access assignment_files for their courses"
ON public.assignment_files
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM instructors i
    JOIN courses c ON c.instructor_id = i.id
    JOIN assignments a ON a.course_id = c.id
    WHERE a.id = assignment_files.assignment_id
      AND i.user_id = auth.uid()
  )
);

-- Students can access files linked to their assignments (if needed, adjust logic)
CREATE POLICY "Students access assignment_files for their assignments"
ON public.assignment_files
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM assignment_submissions s
    WHERE s.assignment_id = assignment_files.assignment_id
      AND s.student_id = auth.uid()
  )
);

-- Instructors/admins can insert files for their courses
CREATE POLICY "Allow insert for course instructors/admins"
ON public.assignment_files
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    SELECT 1 FROM instructors i
    JOIN courses c ON c.instructor_id = i.id
    JOIN assignments a ON a.course_id = c.id
    WHERE a.id = assignment_id
      AND i.user_id = auth.uid()
  )
);

-- =========================
-- assignment_links policies
-- =========================

CREATE POLICY "Admin full access to assignment_links"
ON public.assignment_links
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Allow read access to authenticated users"
ON public.assignment_links
FOR SELECT
USING (auth.role() = 'authenticated');

CREATE POLICY "Instructors access assignment_links for their courses"
ON public.assignment_links
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM instructors i
    JOIN courses c ON c.instructor_id = i.id
    JOIN assignments a ON a.course_id = c.id
    WHERE a.id = assignment_links.assignment_id
      AND i.user_id = auth.uid()
  )
);

CREATE POLICY "Students access assignment_links for their assignments"
ON public.assignment_links
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM assignment_submissions s
    WHERE s.assignment_id = assignment_links.assignment_id
      AND s.student_id = auth.uid()
  )
);

CREATE POLICY "Allow insert for course instructors/admins"
ON public.assignment_links
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    SELECT 1 FROM instructors i
    JOIN assignments a ON a.course_id = i.course_id
    WHERE a.id = assignment_id
      AND i.user_id = auth.uid()
  )
);