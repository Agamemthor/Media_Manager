-- sql/init.sql

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
    file_id SERIAL PRIMARY KEY,
    folder_id INTEGER REFERENCES media_folders(folder_id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_size_kb INTEGER,
    UNIQUE (folder_id, file_name)
);

CREATE TABLE IF NOT EXISTS Parameters (
    Parameter_Name VARCHAR(100) PRIMARY KEY,
    Parameter_Value VARCHAR(500)
);

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
