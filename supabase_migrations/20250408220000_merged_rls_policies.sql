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

-- Users access their own files
CREATE POLICY "Users access their own assignment_files"
ON public.assignment_files
FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert their own assignment_files"
ON public.assignment_files
FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update their own assignment_files"
ON public.assignment_files
FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users delete their own assignment_files"
ON public.assignment_files
FOR DELETE USING (auth.uid() = user_id);

-- Authenticated users can read all files (your policy)
CREATE POLICY "Allow read access to authenticated users"
ON public.assignment_files
FOR SELECT
USING (auth.role() = 'authenticated');

-- Instructors/admins can insert (your complex logic)
CREATE POLICY "Allow insert for course instructors/admins"
ON public.assignment_files
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
    UNION ALL
    SELECT 1 FROM instructors i
    JOIN courses c ON c.instructor_id = i.id
    JOIN assignments a ON a.course_id = c.id
    WHERE i.user_id = auth.uid() AND a.id = assignment_id
  )
);

-- =========================
-- assignment_links policies
-- =========================

CREATE POLICY "Admin full access to assignment_links"
ON public.assignment_links
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Users access their own assignment_links"
ON public.assignment_links
FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users insert their own assignment_links"
ON public.assignment_links
FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users update their own assignment_links"
ON public.assignment_links
FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users delete their own assignment_links"
ON public.assignment_links
FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Allow read access to authenticated users"
ON public.assignment_links
FOR SELECT
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow insert for course instructors/admins"
ON public.assignment_links
FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    SELECT 1 FROM instructors i
    JOIN assignments a ON a.course_id = i.course_id
    WHERE i.user_id = auth.uid() AND a.id = assignment_id
  )
);