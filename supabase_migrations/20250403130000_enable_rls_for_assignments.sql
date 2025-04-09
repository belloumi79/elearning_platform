-- Enable Row Level Security
ALTER TABLE assignment_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE assignment_links ENABLE ROW LEVEL SECURITY;

-- Create read access policy
CREATE POLICY "Allow read access to authenticated users" 
ON assignment_files FOR SELECT 
USING (auth.role() = 'authenticated');

-- Create insert policy for admins/instructors  
CREATE POLICY "Allow insert for course instructors/admins"
ON assignment_files FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    -- Admin check
    SELECT 1 FROM admins WHERE user_id = auth.uid()
    UNION ALL
    -- Instructor check for the assignment's course
    SELECT 1 FROM instructors i
    JOIN courses c ON c.instructor_id = i.id
    JOIN assignments a ON a.course_id = c.id
    WHERE i.user_id = auth.uid() AND a.id = assignment_id
  )
);

-- Similar policies for assignment_links
CREATE POLICY "Allow read access to authenticated users"
ON assignment_links FOR SELECT
USING (auth.role() = 'authenticated');

CREATE POLICY "Allow insert for course instructors/admins" 
ON assignment_links FOR INSERT
WITH CHECK (
  EXISTS (
    SELECT 1 FROM admins WHERE user_id = auth.uid()
  ) OR EXISTS (
    SELECT 1 FROM instructors i
    JOIN assignments a ON a.course_id = i.course_id
    WHERE i.user_id = auth.uid() AND a.id = assignment_id
  )
);