-- Enable RLS on all relevant tables
ALTER TABLE public.assignment_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignment_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignment_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.assignment_progress ENABLE ROW LEVEL SECURITY;

-- =========================
-- assignment_files policies
-- =========================

-- Admins full access
CREATE POLICY "Admin full access to assignment_files"
ON public.assignment_files
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

-- Users can access their own files
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

-- =========================
-- assignment_submissions policies
-- =========================

CREATE POLICY "Admin full access to assignment_submissions"
ON public.assignment_submissions
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Users access their own assignment_submissions"
ON public.assignment_submissions
FOR SELECT USING (auth.uid() = student_id);
CREATE POLICY "Users insert their own assignment_submissions"
ON public.assignment_submissions
FOR INSERT WITH CHECK (auth.uid() = student_id);
CREATE POLICY "Users update their own assignment_submissions"
ON public.assignment_submissions
FOR UPDATE USING (auth.uid() = student_id);
CREATE POLICY "Users delete their own assignment_submissions"
ON public.assignment_submissions
FOR DELETE USING (auth.uid() = student_id);

-- =========================
-- course_progress policies
-- =========================

CREATE POLICY "Admin full access to course_progress"
ON public.course_progress
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Users access their own course_progress"
ON public.course_progress
FOR SELECT USING (auth.uid() = student_id);
CREATE POLICY "Users insert their own course_progress"
ON public.course_progress
FOR INSERT WITH CHECK (auth.uid() = student_id);
CREATE POLICY "Users update their own course_progress"
ON public.course_progress
FOR UPDATE USING (auth.uid() = student_id);
CREATE POLICY "Users delete their own course_progress"
ON public.course_progress
FOR DELETE USING (auth.uid() = student_id);

-- =========================
-- assignment_progress policies
-- =========================

CREATE POLICY "Admin full access to assignment_progress"
ON public.assignment_progress
FOR ALL
USING (auth.jwt() ->> 'role' = 'admin');

CREATE POLICY "Users access their own assignment_progress"
ON public.assignment_progress
FOR SELECT USING (auth.uid() = student_id);
CREATE POLICY "Users insert their own assignment_progress"
ON public.assignment_progress
FOR INSERT WITH CHECK (auth.uid() = student_id);
CREATE POLICY "Users update their own assignment_progress"
ON public.assignment_progress
FOR UPDATE USING (auth.uid() = student_id);
CREATE POLICY "Users delete their own assignment_progress"
ON public.assignment_progress
FOR DELETE USING (auth.uid() = student_id);