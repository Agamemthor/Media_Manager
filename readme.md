#### Project goals

To develop an app which manages media on disk and creates a configurable multimedia slideshow thingy app. Also gain experience with python, postgresql and docker-compose. 

#### Architecture

The app consists of a user interface developed in python, and a postgresql database. I'd like to host the postgres database using a docker-compose script. I'm open to ideas on how to launch everything. I'm using visual studio code to develop, it could be launched from there.

#### Postgres

The container hosting Postgres should automatically create certain tables and views if they do not exist yet at launch. The ddl's for the tables and views are saved next to the docker-compose file. Some information is automatically inserted in the parameters table using .sql file(s) after it has been created.

The table Media_Types has a record inserted for each file type associated with the media type.  

- Media_Type_ID: automatically generated ID
- Media_Type_Description: image, video, gif
- Media_Type_Extension: file extensions of the media type (i.e. .jpg for image, .mp4 for video)

The table Media_Folders consists of:

- Folder_ID: automatically generated ID
- Folder_Path

The table Media_Files:

- File_ID: automatically generated ID
- Folder_ID
- File_Name
- File_Extension
- File_Size_KB
- Media_Height
- Media_Width

The view Media_Files_Extended takes media_files and joins the info from Media_Folders and Media_Types. 

#### Multimedia manager 

- User interface to browse files and folders similar to a file explorer. We'll refer to this UI element as the foldertree.
- Connection to the Postgres database running in the container. Certain parameters will be saved and loaded from there, as well as user created metadata on files and folders. 
- When opening the user interface and the parameter 'rootfolder' has not been defined yet,   the user is prompted to select a 'root'  folder with a dialogue. This folder should be saved in a 'parameters' key-value table.
- After the rootfolder has been defined, the system checks whether there is any user loaded metadata. If not, prompts the user and asks if they want to scan all files and subfolders in the selected rootfolder. 
- If the user says ok to scanning all files and subfolders, the system recursively loops over all files in the rootfolder directory, and for files of specific mediatypes, creates a dataframe with their filename, file extension, and folder. If the media supports it and it does not cause a performance problem, other parameters may be saved as well.
- This data is saved in the database. There's a table with all distinct folders, and a table with files referencing the folder table. 
- If on startup this data of files and tables existed and had data in the database, it is automatically loaded into a dataframe instead using the view Media_Files_Extended. 
- The treeview is generated for the files and folders in the dataframe, respecting folder hierarchy. Additional columns in the treeview show attributes of the elements, such as file size and media type.
- Right clicking an item in the treeview opens a menu. One of the options in the menu should be 'show in folder', opening the operating system's file explorer and navigating to the file or folder

#### Multimedia Slideshow

- Configurable grid, from one single piece of media to i.e. a 2x4 grid.
- During a slideshow, a cell in a grid plays a predefined collection of media
- Some grid cells can be merged to fit the media's aspect ratio.
- Can be used windowed and fullscreen (ideally borderless/menubarless fullscreen)
- Media is resized to fit their grid's size to fit, while not adjusting the aspect ratio