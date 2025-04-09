-- Create assignment_files table
CREATE TABLE IF NOT EXISTS public.assignment_files (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id uuid NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    file_name text NOT NULL,
    file_path text NOT NULL,
    mime_type text,
    size bigint,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Create assignment_links table
CREATE TABLE IF NOT EXISTS public.assignment_links (
    id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
    assignment_id uuid NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    url text NOT NULL,
    title text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_assignment_files_assignment_id ON public.assignment_files(assignment_id);
CREATE INDEX IF NOT EXISTS idx_assignment_links_assignment_id ON public.assignment_links(assignment_id);

-- Add trigger for updated_at timestamps
CREATE OR REPLACE FUNCTION update_modified_column() 
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assignment_files_modtime 
BEFORE UPDATE ON public.assignment_files 
FOR EACH ROW EXECUTE FUNCTION update_modified_column();

CREATE TRIGGER update_assignment_links_modtime 
BEFORE UPDATE ON public.assignment_links 
FOR EACH ROW EXECUTE FUNCTION update_modified_column();