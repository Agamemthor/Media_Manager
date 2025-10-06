### Media Manager
The app consists of a local user interface in python, and a postgresql database which needs to be run with docker-compose. 

#### Project status: 
This project is currently in development - ugly stuff to be honest, but it works haha! No guarantees though. Vibe coding is a blessing and a curse.

#### Project goals
To develop an app which manages media on disk and creates a configurable multimedia slideshow thingy app. Also gain experience with python, postgresql and docker-compose. 

#### Installation steps
- Todo: requirements.txt
- run 'docker-compose up --build' to deploy docker
- run app.py

#### Postgres
The container hosting Postgres automatically creates tables on its init. Some information is automatically inserted in the parameters table.The table Media_Types has a record inserted for each file type associated with the media type.  
Possibly temporary: pgadmin to check the database. http://localhost:5050/browser/, u: your@email.com, p: yourpassword

#### Multimedia manager 
- Todo: open database from .env file
- 
- User interface to browse files and folders similar to a file explorer.
- Connection to the Postgres database running in the container. Certain parameters will be saved and loaded from there, as well as user created metadata on files and folders. 
- The app recursively loops over all files in the rootfolder directory, and for files of specific mediatypes, saves file and folder metadata in the database.
- The treeview is generated for the files and folders in the dataframe, respecting folder hierarchy. 
- The treeview can be interacted with using a context menu
- Todo: when scanning a folder of higher hierarchy, existing folders need to be checked if their parent is null. If true, we update it with the new parent_id

#### Multimedia Slideshow
- Todo: Configurable grid, from one single piece of media to i.e. a 2x4 grid.
- During a slideshow, a cell in a grid plays a predefined collection of media
- Todo: Possible configuration also include merging cells together (i.e. span >1)
- Todo: Can be used windowed and fullscreen (ideally borderless/menubarless fullscreen)
- Media is resized to fit their grid's size to fit, respecting aspect ratio

#### notes
if there are no existing media files in the database, the user is asked for a rootfolder and scanning starts. 
if there is data in the db, this is loaded automatically 
mediafolder and mediafiles will be presented in a treeview, along with a media viewer.
collection treeview is only shown when a collection is present. 
