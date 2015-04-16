#import pymel.core as core
from pymel.core import windows, system, general, language
from subprocess import call
import os, glob, time, shutil

#Define global variables
makes = ("Fiat","Datsun","Kia","Nissan","Mitsubishi","VW","Hyundai","Mercedes","Unknown")


#Function allows for a shell command to be executed, or else it times out
def waitfor(command, timeout):
    """call shell-command and either return its output or kill it
    if it doesn't normally exit within timeout seconds and return None"""
    import subprocess, datetime, time, signal
    start = datetime.datetime.now()
    process = subprocess.Popen(command, shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    while process.poll() is None:
        time.sleep(0.2)
        now = datetime.datetime.now()
        if (now - start).seconds > timeout:
            os.kill(process.pid, signal.SIGKILL)
            os.waitpid(-1, os.WNOHANG)
            return None

def openFinderDirectory(_dir):
    if (os.path.isdir(_dir)):
        call(["open", "-R", _dir])
    else:
        print(_dir + " could not be found.")

#A storage class for project information
class Project():
    def __init__(self):
        #The long path to the project
        self.directory=""
        #The name of the project, usually derived from the path
        self.name=""
        #The numbered name of the project.  This is so we can access the rest of the project info
        #From the array by pulling the number off the front of it
        self.numname=""
        #The make of the car this project is for
        self.make=""
        #The 1st level directories the project contains, generally stuff like "01_Mangement" and "02_Modeling" and such
        #Stored in pairs, long path first, then name.  Ex. self.internalDirectories[0] = [path/to/internal/directory,directory]
        self.internalDirectories=[]
        #Modeling components, if found.  If none are found, will simply return None
        #Otherwise, they're stored in pairs.  Long path first, then part name, then numbered part name.
        #Ex self.modelingComponents[0]=[path/to/part, part, numbered part]
        self.modelingComponents=[]

def findProjectDirectories(levels, startDirs, foldersToFind):
    #Recursively searches through levels of directories and returns a list of all of them
    if (levels>0):
        #The current level we're searching
        index=0
        #Initialize the starting directory to search from.  This is effectively level 1
        currentDirs=startDirs
        #The overall list of projects
        projectsList=[]
        #The total project count, so we can number the project as we create them
        projectsCount = 0
        #While the index is less than the number of levels we're searching through, repeat the next function
        while (index<levels):
            nextDirs = []
            #Iterate through the search directories and find all the directories within them
            for searchDir in currentDirs:
                print("Searching " + searchDir + " for project folders...")
                #Create a new project variable.  This is where we'll assign the necessary variables
                #That we'll eventually be saving.
                new_project = None
                #print("Searching " + searchDir + " ...")
                #Glob all the files into an array
                dirs = glob.glob(searchDir+"*")
                #Iterate through the list to see if any of them are the directories we're looking for
                #The underscore is so we dont hide the built in Python dir function
                for _dir in dirs:
                    #If the path is a directory
                    if os.path.isdir(_dir):
                        #Iterate through the list of folders we're comparing with
                        for compare in foldersToFind:
                            #print("Comparing " + compare + " with " + _dir.split("/")[-1] + " ...")
                            #If the string is found in the project, add our current search directory to the project list
                            if (compare in _dir.split("/")[-1]):
                                if new_project==None:
                                    projectsCount+=1
                                    #print("Initializing project " + searchDir[:-1].split("/")[-1])
                                    new_project=Project()
                                    new_project.directory = searchDir
                                    new_project.name = searchDir[:-1].split("/")[-1]
                                    new_project.numname = str(projectsCount) + ": " + new_project.name
                                    #Try and locate the make of the car for this project
                                    for make in makes:
                                        if make in new_project.directory:
                                            new_project.make=make
                                            break
                                    else:
                                        new_project.make="Unknown"
                                new_project.internalDirectories.append((_dir, _dir.split("/")[-1]))
                                #Now, a special case occurs if we find a modeling folder, since we also
                                #Want to compile a list of modeling components.  So its time to dive deeper.
                                if (compare=="Modeling"):
                                    for i in glob.glob(_dir+"/*"):
                                        if "Components" in i:
                                            #Now that we've successfully located the components folder, if there
                                            #Is one, set our usual index variable so we can number things, then
                                            #Iterate through the directories and pull the names from em
                                            index=0
                                            for l in glob.glob(i+"/*"):
                                                if os.path.isdir(l) and not os.path.split(l)[1].startswith("_"):
                                                    new_project.modelingComponents.append((l, l.split("/")[-1], str(index + 1)+ ": " + l.split("/")[-1]))
                                                    index+=1
                                #print("Adding project " + new_project.name + " to list, breaking loop...")
                        else:
                            #If the loop doesnt break, add that directory to the next level of searchdirs
                            #print("Directory " + _dir + " is not a required folder, adding it to next level of search dirs")
                            #print("    Adding " + _dir + " to the next level of search directories.")
                            nextDirs.append(_dir)
                else:
                    #If no new project was created, then none of the required directories were found
                    #Therefore the current searchDir is not a project
                    if new_project!=None:
                        #Otherwise, add the new project to the list
                        projectsList.append(new_project)
                        #new_project.createProjectInfoFile(projectFolder)
            else:
                #Once the loop is finished, add one to the index, and also replace the next level search directory list with a
                #New one comprised only of the directories that this loop found.  If that makes any sense, hooray
                index+=1
                currentDirs=[]
                #print("\n\nNext level of search dirs:")
                [currentDirs.append(_dir+"/") for _dir in nextDirs]
        else:
            print("\n\n**Final Projects List**")
            for x in projectsList:
                print(x.name)
            #[print(str(x.name)) for x in projectsList]
            return projectsList
#The class for the file saving script, so that I can contain all the variables without having to use globals
#Also its just more neat.
class fileSaver():
    #Init all the necessary things, like the GUI, the variables, and then populate the appropriate lists
    #Also load user settings if necessary.  Load the user settings after the lists have been populated
    #Otherwise problems might arise.
    def __init__(self):
        waitfor("""osascript -e 'mount volume "afp://xserve1._afpovertcp._tcp.local/Client_Projects"'""", 30)
        waitfor("""osascript -e 'mount volume "afp://xserve1._afpovertcp._tcp.local/bto-secure"'""", 30)
        
        if windows.window("fileSaver_GUI", exists=True):
            windows.deleteUI("fileSaver_GUI")
        if windows.window("loadingWindow", exists=True):
            windows.deleteUI("loadingWindow")
        if windows.window("fileSaver_SaveGUI", exists = True):
            windows.deleteUI("fileSaver_SaveGUI")
            
        windows.window("loadingWindow", h = 20, sizeable=False, t = "Loading Projects")
        windows.columnLayout()
        windows.separator(h=20)

        windows.rowLayout(nc = 3)
        windows.separator(w=10, st = "none")
        windows.text(l = "One moment, finding projects...")
        windows.separator(w=10, st = "none")
        windows.setParent(u = True)
        windows.separator(h=20)
        windows.showWindow("loadingWindow")
        #time.sleep(0.1)
        self.initializeVars()
        windows.deleteUI("loadingWindow")
        self.GUI()
        self.loadSettings()
    
    def overrideSaveFunction(self):
        override = '''
        global proc FileMenu_SaveItem()
        {
            python("f.saveFile(0)");
        }
        
        global proc SaveSceneAs()
        {
            python("f.saveFile(0)");
        }
        
        global proc IncrementAndSave()
        {
            python("f.saveFile(0)");
        }
        
        global proc NewScene()
        {
            confirmDialog -title "Restart Maya" -message "If you want to create a new scene independently of the file structure script, please restart Maya." -button "Dismiss";
        }
        
        global proc OpenScene()
        {
            confirmDialog -title "Restart Maya" -message "If you want to open a scene independently of the file structure script, please restart Maya." -button "Dismiss";
        }
        
        global proc doOpenFile(string $file)
        {
            confirmDialog -title "Restart Maya" -message "If you want to open a scene independently of the file structure script, please restart Maya." -button "Dismiss";
        }
        '''
        language.mel.eval(override)
    
    #Initialize all necessary variables
    def initializeVars(self):
        #The global projects list
        self.projects = findProjectDirectories(3, ["/Volumes/Client_Projects/","/Volumes/bto-secure/"], ["Modeling",])
        self.filterCheckboxes = []
        self.username = "default"
    
    def loadProjectFiles(self, pathToProjects):
        #print("Loading project files...")
        #Create the path to the list on the server from the two variables
        #path = os.path.join(pathToProjects)
        #If the file is found
        if os.path.isdir(pathToProjects):
            #print("Path to projects is valid, globbing projects...")
            #Open the file
            project_files=glob.glob(pathToProjects+"*")
            #Create a new array for all the directories
            #This is the variable we'll return when this function is done
            projects = []
            #Iterate through the project list file and read each line
            if len(project_files)>0:
                for index, proj in enumerate(project_files):
                    _newProject = self.loadProjectFile(proj)
                    _newProject.numname = str(index+1)+": "+_newProject.name
                    projects.append(_newProject)
            return(projects)
    
    def populateProjectsList(self, _filter=[]):
        #This is where we populate our drop down menu.  So its just GUI stuff
        #Get all the current menu items for the project drop down menu, if there are any
        menuItems = windows.optionMenu("projectOptionMenu", q = True, ill = True)
        #If theres at least one, delete it.  In the future, this will have to be replaced by a more
        #Elegant function that simply checks each one against the new list being added and only
        #Adds new ones when necessary and deletes old ones, rather than rebuilding the entire menu
        if len(menuItems)>0:
            windows.deleteUI(menuItems)
        #If the list of projects actually has something in it...
        if len(self.projects)>0:
            #...iterate through the projects and create a menu option for each one.
            for project in self.projects:
                if len(_filter)>0:
                    for f in _filter:
                        if project.make == f:
                            windows.menuItem(l = project.numname, p = "projectOptionMenu")
                            break
                else:
                    windows.menuItem(l = project.numname, p = "projectOptionMenu")

            if len(windows.optionMenu("projectOptionMenu", q = True, ill = True))==0:
                windows.menuItem(l = "None", p = "projectOptionMenu")
            else:
                self.populatePartsList()
        else:
            #If no projects are found, just add a None menu option.
            windows.menuItem(l = "None", p = "projectOptionMenu")
    
    def populatePartsList(self):
        #First query whether or not we have a valid project selected.  Otherwise theres no point
        #in trying to query the parts list, since its derivative of the project directory
        if windows.optionMenu("projectOptionMenu", q = True, v = True)=="None":
            #Delete all menu items and create a "None" item if there is none
            [windows.deleteUI(x) for x in windows.optionMenu("partOptionMenu", q = True, ill = True)]
            windows.menuItem(l = "None", p = "partOptionMenu")
        else:
            project = self.getSelectedProject()
            #Delete all the menu items in the part option menu dropdown
            [windows.deleteUI(x) for x in windows.optionMenu("partOptionMenu", q = True, ill = True)]
            if len(project.modelingComponents)>0:
                [windows.menuItem(l = component[2], p = "partOptionMenu") for component in project.modelingComponents]
            else:
                windows.menuItem(l = "None", p = "partOptionMenu")

    def loadFile(self, type=0):
        project = self.getSelectedProject()
        if project!="None":
            if windows.optionMenu("partOptionMenu", q=True, v=True)!="None":
                part_index = int(windows.optionMenu("partOptionMenu", q=True, v=True).split(":")[0]) - 1
                part_directory = project.modelingComponents[part_index][0]
                #part_name = project.modelingComponents[part_index][1]
                
                working_dir = os.path.join(part_directory, "Working")
                #publish_dir = os.path.join(part_directory, "Publish")
                latest_file=None

                if os.path.isdir(working_dir)==False:
                    print("No working files for this model found.")
                else:
                    if type==0:
                        files = glob.glob(working_dir+"/*")
                        if len(files)>0:
                            highest_num=0
                            for file in files:
                                if os.path.isfile(file):
                                    filenum = int(os.path.split(file)[1].split(".")[0][-3:])
                                    if filenum>highest_num:
                                        highest_num = filenum
                                        latest_file = file
                            else:
                                if latest_file==None:
                                    print("No working files found that match the save format")
                        else:
                            print("No working files found in the working directory")
                            
                #print("Saving file: " + file_name)
                if latest_file!=None:
                    #changes_list = system.dgmodified()
                    if system.dgmodified()==None:
                        system.openFile(latest_file, f = True)
                    else:
                        if windows.confirmDialog(title = "Unsaved Changes in Scene", message = "There are unsaved changes in the scene.  Would you like to proceed anyways?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                            system.openFile(latest_file, f = True)
    
    def saveFile(self, type=0):
        #So this function needs to look into the proper component folder (if it exists), find the Working folder (if it exists, if not make it)
        #Then save an iteration of this file.
        project = self.getSelectedProject()
        if project!="None":
            if windows.optionMenu("partOptionMenu", q=True, v=True)!="None":
                part_index = int(windows.optionMenu("partOptionMenu", q=True, v=True).split(":")[0]) - 1
                part_directory, part_name, part_numname = project.modelingComponents[part_index]
                if os.path.isdir(part_directory):
                    #part_name = project.modelingComponents[part_index][1]
                    
                    working_dir = os.path.join(part_directory, "Working")
                    qa_dir = os.path.join(part_directory, "QA")
                    publish_dir = os.path.join(part_directory, "Publish")
                    
                    if os.path.isdir(working_dir)==False:
                        os.makedirs(working_dir)
                    if os.path.isdir(qa_dir)==False:
                        os.makedirs(qa_dir)
                    if os.path.isdir(publish_dir)==False:
                        os.makedirs(publish_dir)
                    
                    #If save type is 0 (which is a regular work file incremental save)
                    #Save format: part_modeler_v001.mb
                    if type==0:
                        if self.username!="":
                            files = glob.glob(working_dir+"/*")
                            if len(files)>0:
                                highest_num=0
                                for file in files:
                                    if os.path.isfile(file):
                                        filenum = int(os.path.split(file)[1].split(".")[0][-3:])
                                        if filenum>highest_num:
                                            highest_num = filenum
                                else:
                                    highest_num+=1
                                    num = ("0"*max(0,3-len(str(highest_num)))+str(highest_num))
                                    print("Num: " + num)
                            else:
                                num = "001"
                            
                            if num=="001":
                                if windows.confirmDialog(title = "Save Part File?", message = "Save the first version of this part? You will not be prompted when saving new versions after this.", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                                    file_name = os.path.join(working_dir , part_name + "_" + self.username + "_" + "v" + num + ".mb")
                                    system.saveAs(file_name)
                            else:
                                file_name = os.path.join(working_dir , part_name + "_" + self.username + "_" + "v" + num + ".mb")
                                system.saveAs(file_name)
                        else:
                            windows.confirmDialog(title="No username entered.", message="Please enter a valid username to save with.",button="Dismiss")
                    
                    #If the save file is type 1, its a publish attempt 
                    elif type==1:
                        if windows.confirmDialog(title = "Publish File", message = "Publish this scene file?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                            file_name = os.path.join(publish_dir, part_name + "_publish.mb")
                            if os.path.isfile(file_name):
                                ctime = os.path.getctime(file_name)
                                moveFolder = os.path.join(publish_dir,"_old",time.strftime("%b%d_%Y %H-%M-%S",time.localtime(ctime)))
                                if not os.path.isdir(moveFolder):
                                    os.makedirs(moveFolder)
                                shutil.move(file_name, moveFolder)
                            #Save the current file, then move on to cleaning up this file in preparation for publishing
                            current_filename = system.sceneName()
                            system.saveAs(current_filename)
                            #Clean up all references
                            reference_files = []
                            references = general.ls(type = "reference")
                            if len(references)>0:
                                for reference in references:
                                    if "sharedReferenceNode"!=reference:
                                        reference_files.append(system.referenceQuery(reference, filename=True))
                                else:
                                    for file in reference_files:
                                        system.FileReference(pathOrRefNode = file).remove()
                            general.select(clear = True)
                            general.select(general.ls(geometry = True))
                            layerName = os.path.split(system.sceneName())[1].split("_")[0].replace(" ", "_")
                            general.createDisplayLayer(name = layerName)
                            system.saveAs(file_name)
                            system.openFile(current_filename, f = True)
                    #If its type 2, its a QA submit
                    elif type==2:
                        if windows.confirmDialog(title = "Submit for QA", message = "Submit this scene file for QA?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                            _time = time.strftime("%b%d_%Y_%H-%M-%S", time.localtime(time.time()))
                            file_name = os.path.join(qa_dir, part_name + "_%s_%s.mb"%(self.username,_time))
                            _files = glob.glob(qa_dir+"/*.mb")
                            if len(_files)>0:
                                found=False
                                for i in _files:
                                    if file_name == i:
                                        found=True
                                        if windows.confirmDialog(title = "Overwrite?", message = "A QA file with this name already exists.  Overwrite it?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes': 
                                            current_filename = system.sceneName()
                                            system.saveAs(file_name)
                                            system.saveAs(current_filename)
                                            
                                    else:
                                        _folder = os.path.join(qa_dir,os.path.split(i)[1].split(".")[0])
                                        os.makedirs(_folder)
                                        shutil.move(i, _folder)
                                else:
                                    if found==False:
                                        current_filename = system.sceneName()
                                        system.saveAs(file_name)
                                        system.saveAs(current_filename)
                            else:
                                current_filename = system.sceneName()
                                system.saveAs(file_name)
                                system.saveAs(current_filename)
                else:
                    windows.confirmDialog(title = "Part Not Found", message = "The selected part folder cannot be found.", button=["Dismiss"])
    
    def saveSettings(self):
        #Save the user settings so when they reopen the script, it loads back the values they had
        #When they closed it.  The settings file is found in the user's Documents folder under
        #maya/settings/, which isn't actually a default directory so we might have to create it
        if os.path.isdir(os.path.join(os.path.expanduser("~"),"Documents/maya/settings"))==False:
            os.makedirs(os.path.join(os.path.expanduser("~"),"Documents/maya/settings"))
        file = open(os.path.join(os.path.expanduser("~"),"Documents/maya/settings/filepublishsettings"), "w+")
        file.write(self.username + "\n")
        #Get project number:
        if windows.optionMenu("projectOptionMenu", q = True, v = True)!="None":
            project_number = int(windows.optionMenu("projectOptionMenu", q = True, v = True).split(":")[0]) - 1
            project = self.projects[project_number]
            #Write project name to file
            file.write(project.name + "\n")
            #Next write the current part display name
            if windows.optionMenu("partOptionMenu",q = True, v = True)!="None":
                part_number = int(windows.optionMenu("partOptionMenu",q = True, v = True).split(":")[0]) - 1
                file.write(project.modelingComponents[part_number][1] + "\n")
            else:
                file.write("None\n")
            #Save the current filter
        else:
            #Else, if there is no project selected somehow, just write "None" for both project and part
            file.write("None\nNone\n")
        #file.write(str(windows.optionMenu("filterMakeMenu",q = True, v = True)) + "\n")
        file.close()
    
    def loadSettings(self):
        #print("\n\nInitializing project save and publish script.\nChecking for settings file...")
        if os.path.isfile(os.path.join(os.path.expanduser("~"),"Documents/maya/settings/filepublishsettings")):
            file = open(os.path.join(os.path.expanduser("~"),"Documents/maya/settings/filepublishsettings"), "r")
            self.username = file.readline().replace("\n", "")
            windows.textFieldGrp("usernameEntry", e = True, tx = self.username)
            project_name =  file.readline().replace("\n","")
            part_name = file.readline().replace("\n","")
            #filter = file.readline().replace("\n","")
            file.close()
            
            if filter in makes:
                windows.optionMenu("filterMakeMenu", e = True, v = filter)
            self.populateProjectsList([])
        
            for project in self.projects:
                if project.name == project_name:
                    #print("    Project successfully loaded, looking for part now...")
                    windows.optionMenu("projectOptionMenu", e = True, v = project.numname)
                    self.populatePartsList()
                    for part in project.modelingComponents:
                        #print("    Checking " + part_name + " against " + part[1])
                        if part_name == part[1]:
                            windows.optionMenu("partOptionMenu", e = True, v = part[2])
                            if windows.confirmDialog(title = "Load previous scene?",message= "Do you want to automatically load the last scene you were working on?", button=["Yes","No"], defaultButton = "Yes", cancelButton = "No", dismissString="No")=="Yes":
                                self.loadFile()
                            return
                    else:
                        return
            else:
                self.populatePartsList()#self.getFilters())
        else:
            self.populateProjectsList(self.getFilters())
    
    def openProjectFolder(self):
        if windows.optionMenu("projectOptionMenu", q = True, v = True)!="None":
            project_number = int(windows.optionMenu("projectOptionMenu", q = True, v = True).split(":")[0]) - 1
            _dir = self.projects[project_number].directory
            print(_dir)
            #if "Client_Projects" in _dir:
            #    waitfor("""osascript -e 'mount volume "afp://xserve1._afpovertcp._tcp.local/Client_Projects"'""", 30)
            if (os.path.isdir(_dir)):
                call(["open", "-R", _dir])
            else:
                windows.confirmDialog(title = "Project Not Found", message = "The selected project folder cannot be found.", button=["Dismiss"])
    
    def openPartFolder(self):
        if windows.optionMenu("projectOptionMenu", q = True, v = True)!="None":
            project = self.getSelectedProject()
            if windows.optionMenu("partOptionMenu", q=True, v=True)!="None":
                part_num = int(windows.optionMenu("partOptionMenu", q = True, v = True).split(":")[0]) - 1
                part_dir = project.modelingComponents[part_num][0]
                if (os.path.isdir(part_dir)):
                    call(["open", "-R", part_dir])
                else:
                    windows.confirmDialog(title = "Part Not Found", message = "The selected part folder cannot be found.", button=["Dismiss"])
    
    def getFilters(self):
        returnFilters = []
        for i in self.filterCheckboxes:
            if windows.checkBox(i, q = True, v = True):
                returnFilters.append(windows.checkBox(i, q = True, l = True))
                print ("Filter: " + returnFilters[-1])
        return returnFilters
#        return windows.optionMenu("filterMakeMenu", q = True, v = True)
    
    def getSelectedProject(self):
        if windows.optionMenu("projectOptionMenu", q=True, v=True)!="None":
            return self.projects[int(windows.optionMenu("projectOptionMenu", q=True, v=True).split(":")[0]) -1]
        else:
            return "None"
    
    def setUserName(self):
        self.username = windows.textFieldGrp("usernameEntry", q = True, tx = True)
        print(self.username)
        self.saveSettings()
    
    def GUI(self):
        #Create the UI
        #Define all custom commands for the buttons and dropdown menus
        def refreshButtonCommand(event):
            self.projects = findProjectDirectories(3, ["/Volumes/Client_Projects/","/Volumes/bto-secure/"], ["Modeling",])
            self.populateProjectsList(self.getFilters())
            self.loadSettings()
        
        def projectOptionMenuChangeCommand(event):
            self.populatePartsList()
            self.saveSettings()
            
        def filterMakeMenuChangeCommand(event):
            self.populateProjectsList(self.getFilters())
            self.saveSettings()
        
        overall_width = 400
        
        windows.window("fileSaver_GUI", t = "OEM Modeling",w = overall_width, h=150, sizeable=False)
        windows.columnLayout()
        
        windows.separator(h = 5, style = "none")
        windows.rowLayout(nc = 3)
        windows.separator(w = 5, style = "none")
        windows.columnLayout()
        ###
        ###
        ###
        ''''''
        windows.frameLayout(l = "User Settings",w = overall_width, cl = False, cll = True)
        windows.textFieldGrp("usernameEntry", l = "User", cw2 = [overall_width*0.16667, 5*(overall_width*0.16667)], cc = lambda x: self.setUserName())
        windows.setParent(u = True)
        ''''''        
        windows.separator(w = overall_width, h = 20, style = "in")
        ''''''
        windows.frameLayout(l = "Projects",w = overall_width, cl = False, cll = True)
        windows.columnLayout("Project Settings")
        windows.optionMenu("projectOptionMenu", l = "Project: ", w = overall_width,cc = projectOptionMenuChangeCommand)
        windows.rowLayout(nc = 2)
        windows.button("navigateToProjectButton", l = "Open Finder Window", w = overall_width*0.5, h = 18, command = lambda event: self.openProjectFolder())
        windows.button("refreshProjectsButton", l = "Refresh List", w = overall_width*0.5, h = 18, command = refreshButtonCommand)
        windows.setParent(u = True)
        
        windows.text(l = "Filters:")
        self.filterCheckboxes = []
        windows.rowColumnLayout(nc = 3, columnWidth = [(1, 0.3333*overall_width), (2, 0.3333*overall_width), (3, 0.3333*overall_width)])
        for k in makes:
            self.filterCheckboxes.append(windows.checkBox(l = k, w = 100, cc = filterMakeMenuChangeCommand))
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.setParent(u = True)
        ''''''
        windows.separator(w = overall_width, h = 20, style = "in")
        ''''''
        windows.frameLayout(l = "Parts",w = overall_width, cl = False, cll = True)
        windows.columnLayout("Part Actions")
        
        def partChangeCommand():
            self.saveSettings()
            self.loadFile()
        
        windows.optionMenu("partOptionMenu", l = "Selected Part: ", w = overall_width, cc = lambda event: partChangeCommand())
        windows.rowLayout(nc = 2)
        #windows.button("loadButton", l = "Load Selected Part", w = overall_width*0.5, h=18, c = lambda event: self.loadFile())
        windows.button("openPartFolderButton", l = "Open Part Folder", w = overall_width, h = 18, c = lambda event: self.openPartFolder())
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.setParent(u = True)
        ''''''
        windows.separator(w = 5, style = "none")
        windows.setParent(u = True)
        windows.separator(h = 5, style = "none")
        
        windows.setParent(u = True)
        
        #
        # Save window
        #
        
        windows.window("fileSaver_SaveGUI", t = "Save Options", sizeable = False)
        windows.columnLayout()
        windows.separator(h = 5, style = "none")
        windows.rowLayout(nc = 3)
        windows.separator(w = 5, style = "none")
        
        windows.frameLayout(l = "Save Options",w = 300, cl = False, cll = True)
        windows.rowLayout(nc = 2)
        windows.button("saveQAButton", l = "Submit for QA", w = 150, h=25, c = lambda event: self.saveFile(2))
        windows.button("publishButton", l = "Publish Part", w = 150, h = 25,c = lambda event: self.saveFile(1))
        windows.setParent(u = True)
        windows.button("saveButton", l = "Save Work in Progress", w = 300, h=50, c = lambda event: self.saveFile())
        windows.setParent(u = True)
        
        windows.separator(w = 5, style = "none")
        windows.setParent(u = True)
        windows.separator(h = 5, style = "none")
        windows.setParent(u = True)
        
        windows.setParent(u = True)
        
        ###
        ###ADD MORE LAYOUTS HERE TO ADD THEM TO THE TAB LAYOUT
        ###
        
        
        windows.showWindow("fileSaver_GUI")
        windows.showWindow("fileSaver_SaveGUI")