-- Create tables
CREATE TABLE IF NOT EXISTS Media_Types (
    Media_Type_ID SERIAL PRIMARY KEY,
    Media_Type_Description VARCHAR(50) NOT NULL,
    Media_Type_Extension VARCHAR(10) NOT NULL,
    UNIQUE (Media_Type_Description, Media_Type_Extension)  -- Add this line
);

-- Folders table with explicit ID and parent relationship
CREATE TABLE media_folders (
    folder_id INTEGER PRIMARY KEY,
    folder_path TEXT UNIQUE NOT NULL,
    parent_folder_id INTEGER REFERENCES media_folders(folder_id) ON DELETE CASCADE
);

-- Files table with foreign key to folders
CREATE TABLE media_files (
    media_file_id SERIAL PRIMARY KEY,
    folder_id INTEGER REFERENCES media_folders(folder_id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_extension TEXT NOT NULL,
    file_size_kb INTEGER,
    folder_path TEXT,
    UNIQUE (folder_id, file_name)
);

CREATE TABLE IF NOT EXISTS Parameters (
    Parameter_Name VARCHAR(100) PRIMARY KEY,
    Parameter_Value VARCHAR(500)
);


CREATE OR REPLACE VIEW Media_Files_Extended AS
SELECT
    mf.File_ID, mf.File_Name, mf.File_Extension, mf.File_Size_KB, mf.Media_Height, mf.Media_Width,
    mf.Folder_ID, mfd.Folder_Path,
    mty.Media_Type_Description
FROM Media_Files mf
JOIN Media_Folders mfd ON mf.Folder_ID = mfd.Folder_ID
JOIN Media_Types mty ON mf.File_Extension = mty.Media_Type_Extension;

-- Insert default media types 
INSERT INTO Media_Types (Media_Type_Description, Media_Type_Extension)
VALUES
    -- Images
    ('image', '.jpg'),   -- JPEG Image
    ('image', '.jpeg'),  -- JPEG Image (alternative extension)
    ('image', '.png'),   -- Portable Network Graphics
    ('image', '.webp'),  -- WebP Image
    ('image', '.tiff'),  -- Tagged Image File Format
    ('image', '.tif'),   -- TIFF (alternative extension)
    ('image', '.bmp'),   -- Bitmap Image
    ('image', '.svg'),   -- Scalable Vector Graphics
    ('image', '.heic'),  -- High Efficiency Image Format
    ('image', '.heif'),  -- High Efficiency Image Format (alternative)
    ('image', '.avif'),  -- AV1 Image File Format

    -- Videos
    ('video', '.mp4'),   -- MPEG-4 Video
    ('video', '.mov'),   -- QuickTime Movie
    ('video', '.avi'),   -- Audio Video Interleave
    ('video', '.mkv'),   -- Matroska Video
    ('video', '.flv'),   -- Flash Video
    ('video', '.wmv'),   -- Windows Media Video
    ('video', '.webm'),  -- WebM Video
    ('video', '.mpeg'),  -- MPEG Video
    ('video', '.mpg'),   -- MPEG Video (alternative extension)
    ('video', '.3gp'),   -- 3GPP Video
    ('video', '.ts'),    -- MPEG Transport Stream

    -- GIFs (treated separately since they're technically images but often used for animations)
    ('gif', '.gif'),     -- Graphics Interchange Format
    ('gif', '.gifv')     -- GIF Video (rare, but sometimes used)
ON CONFLICT (Media_Type_Description, Media_Type_Extension) DO NOTHING;

-- Insert default parameters if needed
INSERT INTO Parameters (Parameter_Name, Parameter_Value)
VALUES ('rootfolder', NULL)
ON CONFLICT (Parameter_Name) DO NOTHING;

CREATE OR REPLACE VIEW folder_hierarchy AS
WITH RECURSIVE folder_tree AS (
    -- Base case: root folders (no parent)
    SELECT
        folder_id,
        folder_path,
        parent_folder_id,
        0 AS level,
        ARRAY[folder_path]::TEXT[] AS path_parts
    FROM media_folders
    WHERE parent_folder_id IS NULL

    UNION ALL

    -- Recursive case: child folders
    SELECT
        f.folder_id,
        f.folder_path,
        f.parent_folder_id,
        ft.level + 1,
        ft.path_parts || f.folder_path
    FROM media_folders f
    JOIN folder_tree ft ON f.parent_folder_id = ft.folder_id
)
SELECT * FROM folder_tree
ORDER BY path_parts;
