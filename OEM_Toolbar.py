#import pymel.core as core
import pymel.core
from pymel.core import windows, system, general, language
from subprocess import call
import os, glob, time, shutil
#import checkModeling

#Define global variables
makes = ("Fiat","Datsun","Kia","Nissan","Mitsubishi","VW","Hyundai","Mercedes","Unknown")

#Function allows for a shell command to be executed, or else it times out
#Not written by me
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

#Reverse enumerate function
def reverse_enumerate(list):
    return zip( reversed(range(len(list))), reversed(list) )

#Opens a window at the specified directory
def openFinderDirectory(_dir):
    if (os.path.isdir(_dir)):
        call(["open", "-R", _dir])
        return
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
        #In the future this should  be converted into a list of objects with the appropriate attributes
        self.modelingComponents=[]
        self.componentsFolder=""

#I didn't want to use os.walk, so, I made this instead
def findProjectDirectories(levels, startDirs, foldersToFind):
    #Recursively searches through levels of directories and returns a list of all of them
    if (levels>0):
        #The current level we're searching
        search_index=0
        #Initialize the starting directory to search from.  This is effectively level 1
        currentDirs=startDirs
        #The overall list of projects
        projectsList=[]
        #The total project count, so we can number the project as we create them
        projectsCount = 0
        #While the index is less than the number of levels we're searching through, repeat the next function
        while search_index <levels:
            print("Index: %s, Levels: %s"%(search_index, levels))
            nextDirs = []
            #Iterate through the search directories and find all the directories within them
            for searchDir in currentDirs:
                print("Searching " + searchDir + " for project folders...")
                #Create a new project variable.  This is where we'll assign the necessary variables
                #That we'll eventually be saving.
                new_project = None
                #Glob all the files into an array
                dirs = glob.glob(searchDir+"*")
                #Iterate through the list to see if any of them are the directories we're looking for
                #The underscore is so we dont hide the built in Python dir function
                for _dir in dirs:
                    #If the path is a directory
                    if os.path.isdir(_dir):
                        #Iterate through the list of folders we're comparing with
                        for compare in foldersToFind:
                            #If the string is found in the project, add our current search directory to the project list
                            if (compare in _dir.split("/")[-1]):
                                if new_project==None:
                                    projectsCount+=1
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
                                            new_project.componentsFolder = "%s/"%(i)
                                            for l in glob.glob(i+"/*"):
                                                if os.path.isdir(l) and not os.path.split(l)[1].startswith("_"):
                                                    new_project.modelingComponents.append((l, l.split("/")[-1], str(index + 1)+ ": " + l.split("/")[-1]))
                                                    index+=1
                        else:
                            #If the loop doesnt break, add that directory to the next level of searchdirs
                            nextDirs.append(_dir)
                else:
                    #If no new project was created, then none of the required directories were found
                    #Therefore the current searchDir is not a project
                    if new_project!=None:
                        #Otherwise, add the new project to the list
                        projectsList.append(new_project)
            else:
                #Once the loop is finished, add one to the index, and also replace the next level search directory list with a
                #New one comprised only of the directories that this loop found.  If that makes any sense, hooray
                currentDirs=[]
                [currentDirs.append(_dir+"/") for _dir in nextDirs]
                print("Current Dirs for next level: %s"%(str(currentDirs)))
                search_index+=1
                print("Index: %s"%(search_index))
        else:
            print("\n\n**Final Projects List**")
            for x in projectsList:
                print(x.name)
            return projectsList

class OEMToolbar():
    #The main toolbar class for all the windows and such that modelers can use
    #In the future the individual modules could probably become their own classes
    def __init__(self):
        if windows.confirmDialog(title = "Run OEM Toolbar?", message = "This script will engage locks on the save and load functions.  If you are working on something separate, please save it.  Are you sure you'd like to run the script?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
            #Init all the necessary things, like the GUI, the variables, and then populate the appropriate lists
            #Also load user settings if necessary.  Load the user settings after the lists have been populated
            #Otherwise problems might arise.
            #waitfor("""osascript -e 'mount volume "afp://xserve1._afpovertcp._tcp.local/Client_Projects"'""", 30)
            #waitfor("""osascript -e 'mount volume "afp://xserve1._afpovertcp._tcp.local/bto-secure"'""", 30)
            
            #Clear all windows that already exist with these names
            if windows.window("OEMToolbar_Settings", exists=True):
                windows.deleteUI("OEMToolbar_Settings")
            if windows.window("loadingWindow", exists=True):
                windows.deleteUI("loadingWindow")
            if windows.window("OEMToolbar_SaveGUI", exists = True):
                windows.deleteUI("OEMToolbar_SaveGUI")
            if windows.window("OEMToolbar_Toolbar", exists = True):
                windows.deleteUI("OEMToolbar_Toolbar")
            if windows.window("OEMToolbar_ReferencePanel", exists = True):
                windows.deleteUI("OEMToolbar_ReferencePanel")
            
            #Clear the window preference for the loading window
            if windows.windowPref("loadingWindow", exists=True):
                windows.windowPref("loadingWindow", remove=True)
            
            #Show the loading window
            self.OEM_LoadingWindow_GUI()
            #Initialize the vars while the loading window is up
            #Finding the projects takes a while, so at least the user will know something is happening
            self.initializeVars()
            #Once the variables have been created, remove the loading window and initialize the toolbar GUI
            windows.deleteUI("loadingWindow")
            self.OEMToolbar_GUI()
            #Finally, load the settings from the preference file, if it exists
            #This should be converted to a JSON file at some point
            self.loadSettings()
            self.overrideSaveFunction()
    
    def selectNewProject(self, index):
        #Select a new project from the master project list by index
        #The only reason this needs to be a function is so that selecting
        #A new part is handled automatically, since the new project might
        #Have a different amount of parts, or no parts at all
        self.selectedProject = int(index)
        #Make sure we've selected a valid project.  This check should never fire if things are handled properly
        #if self.getSelectedProject()!=None:
            #Make sure this project has at least one part
            #if len(self.getSelectedProject().modelingComponents)>0:
                #If it does, assign the currently selected part to the first part in the list
                #self.selectedPart = 0
                #return
        #If we never made it to assigning the part correctly, set it to None
        self.selectedPart = None

    def showSettingsPanel(self):
        #If the Settings panel exists, delete it and rebuild it
        if windows.window("OEMToolbar_Settings", exists=True):
            windows.deleteUI("OEMToolbar_Settings")
        self.OEM_SettingsPanel_GUI()
    
    def showSavingPanel(self):
        #If the Saving panel exists, delete it and rebuild it
        if windows.window("OEMToolbar_SaveGUI", exists=True):
            windows.deleteUI("OEMToolbar_SaveGUI")
        self.OEM_SavingPanel_GUI()
        
    def showReferencePanel(self):
        #If the Part Reference panel exists, delete it and rebuild it
        if windows.window("OEMToolbar_ReferencePanel", exists = True):
            windows.deleteUI("OEMToolbar_ReferencePanel")
        self.OEM_ReferencePanel_GUI()
            
    def overrideSaveFunction(self):
        #This command is run when the script is called, it overrides all the ways the user can mess things up by loading
        #different scenes or saving them with alternate names
        override = '''
        global proc FileMenu_SaveItem()
        {python("f.saveFile(0)");}
        
        global proc SaveSceneAs()
        {python("f.saveFile(0)");}
        
        global proc IncrementAndSave()
        {python("f.saveFile(0)");}
        
        global proc NewScene()
        {confirmDialog -title "Restart Maya" -message "If you want to create a new scene independently of the file structure script, please restart Maya." -button "Dismiss";}
        
        global proc OpenScene()
        {confirmDialog -title "Restart Maya" -message "If you want to open a scene independently of the file structure script, please restart Maya." -button "Dismiss";}
        
        global proc doOpenFile(string $file)
        {confirmDialog -title "Restart Maya" -message "If you want to open a scene independently of the file structure script, please restart Maya." -button "Dismiss";}
        
        global proc openRecentFile(string $arg1, string $arg2)
        {confirmDialog -title "Restart Maya" -message "If you want to open a scene independently of the file structure script, please restart Maya." -button "Dismiss";}
        '''
        language.mel.eval(override)
    
    def initializeVars(self):
        #Initialize necessary variables
        
        #Load a list of projects using the above recursive project finding function
        self.projects = findProjectDirectories(3, ["/Volumes/Client_Projects/","/Volumes/bto-secure/"], ["Modeling",])
        #The filters we currently have checked or not
        self.filterCheckboxes = []
        #The name of the current user
        self.username = ""
        #Current project
        self.selectedProject=None
        #Currently selected part in the project
        self.selectedPart=None
        #Currently selected part versions
        self.selectedPartVersions = []
    
    #Load a new file
    def loadFile(self, index, type=0):
        #Attempts a load of different file types
        #Right now there's only one, type 0, which is a working file for modelers
        #In the future there will be support for loading and working with QA files, and clay complete files for scene assembly
        try:
            #If we have a valid project selected...
            if self.getSelectedProject()!=None:
                #If we have a valid part selected...
                if index!=None:
                    #Retrieve the directory for the selected part from the components array
                    #In the future, the parts should be stored as a class rather than an obtuse multi-dimensional array
                    part_directory = self.getSelectedProject().modelingComponents[index][0]
                    #Append the "Working" folder onto the part directory
                    working_dir = os.path.join(part_directory, "Working")
                    #Set the latest file name
                    latest_file=None
                    
                    #If load type is 0, then its a working file load attempt
                    if type==0:
                        #If the working directory is not valid, do nothing
                        if os.path.isdir(working_dir)==False:
                            print("No working directory for this model found.")
                        else:
                            #Get all the files inside the working dir, which should all be mb files with a specific format
                            files = glob.glob(working_dir+"/*.mb")
                            #If theres at least one file in there...
                            if len(files)>0:
                                #Set the highest number found in the incremental saves
                                highest_num=0
                                #Iterate through the files and see if we can find a higher version number than 0
                                for file in files:
                                    #Make sure its a file.  This is a check I almost always put in for safety
                                    if os.path.isfile(file):
                                        #Get the filename from the path, and remove the extension
                                        _fname = str(os.path.splitext(os.path.split(file)[1])[0])
                                        #Since I know the format will always have the number at the end of the name,
                                        #But I don't know how many numbers there will be (formats change, maybe its version 1524)
                                        #This just iterates through the reversed filename and appends each digit it finds to the 
                                        #num variable until it finds a non-number, at which point it quits
                                        filenum=''
                                        for x in reversed(_fname):
                                            if x.isdigit():
                                                filenum = x + filenum
                                            else:
                                                break
                                        #Guard against people renaming files and putting non-integers at the end
                                        #Don't even try to compute these.  If it didn't find any numbers, theres nothing
                                        #To compare
                                        if len(filenum)>0:
                                            filenum = int(filenum)
                                            #Compare what should be the file number against whatever the highest number is currently
                                            if filenum>highest_num:
                                                #If its higher, set the highest filenum to the one we just found, and the latest file to the one in this current iteration
                                                highest_num = filenum
                                                latest_file = file
                                else:
                                    if latest_file==None:
                                        #If there were files found, but it didnt properly locate a valid one, do nothing
                                        print("No working files found that match the save format")
                            else:
                                #If theres no working files found, we can't load anything
                                print("No working files found in the working directory")
                                
                    #If we made it to this point with something stored in latest_file, then we attempt to load it
                    if latest_file!=None:
                        #If there haven't been any changes to the current file, go ahead and force a load of the new one and refresh our reference UI
                        if system.dgmodified()==None:
                            system.openFile(latest_file, f = True)
                            self.refreshReferencesUI()
                            self.selectedPart = index
                            self.saveSettings()
                            self.getPreviousPartVersions()
                            self.refreshSettingsUI()
                        else:
                            #If there are changes, ask if the user is sure they want to continue
                            #If they choose yes, continue with the loading and save no changes
                            if windows.confirmDialog(title = "Unsaved Changes in Scene", message = "There are unsaved changes in the scene.  Would you like to proceed anyways?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                                system.openFile(latest_file, f = True)
                                self.refreshReferencesUI()
                                self.selectedPart = index
                                self.saveSettings()
                                self.getPreviousPartVersions()
                                self.refreshSettingsUI()
        except IndexError as E:
            print("Index Error occured while loading: %s"%(E))
    
    def loadPreviousVersionFile(self, index):
        if self.getSelectedProject()!=None and self.getSelectedPart()!=None:
            _file = self.selectedPartVersions[index]
            if system.dgmodified()==None:
                system.openFile(_file[0], f = True)
                self.refreshReferencesUI()
            else:
                if windows.confirmDialog(title = "Unsaved Changes in Scene", message = "There are unsaved changes in the scene.  Would you like to proceed anyways?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                    system.openFile(_file[0], f = True)
                    self.refreshReferencesUI()
    
    def getPartName(self):
        return os.path.split(system.sceneName())[1].split("_")[0]
    
    def findPartPIDStructure(self):
        partName = self.getPartName()
        pid_map_file = "/rendershare/LIBRARY/cg_production/00_resources/production_scripts/Modeling_Pipeline/defaultParts"
        pid_structure = ""
        #Run the check once for one directory
        if not os.path.isfile(pid_map_file):
            pid_map_file = "/Volumes/LIBRARY/cg_production/00_resources/production_scripts/Modeling_Pipeline/defaultParts"
        #Run it again for a differently mounted one.  If it still doesnt find it, it probably just doesn't exist
        if not os.path.isfile(pid_map_file):
            print("PID map not found")
            return None
        
        file = open(pid_map_file, "r")
        for line in file:
            if ":" in line.rstrip("\n"):
                if line.split(":")[0] == partName:
                    pid_structure = line.split(":")[1]
                    if pid_structure!="":
                        print("PID map found")
                        return pid_structure
        print("PID map not found")
        return None
    
    def attemptBakePID(self):
        pid_structure = self.findPartPIDStructure()
        if pid_structure!=None:
            general.select(cl = True)
            general.select(general.ls(tr = True))
            general.select(general.ls(geometry = True), add = True)
            for node in general.selected():
                general.addAttr(node, longName = "EvoxPIDMap", dt = "string")
                general.setAttr(node+".EvoxPIDMap", pid_structure)
            return True
        return None
    
    def attemptAutoPID(self):
        #Now we need to find out the PID structure for this particular part
        #This is contained in a file that maps it out.
        pid_structure = self.findPartPIDStructure()
        if pid_structure!=None:
            #Split out the group names, so that we can do a chain of group functions
            nodes=[]
            #Split the string into group names
            if "|" in pid_structure:  pid_structure=pid_structure.rstrip("\n").split("|")
            else: pid_structure = [pid_structure.rstrip("\n"),]
            print("PID Structure: %s"%(str(pid_structure)))
            #If we got any group names, which we should have at least one always
            for node in pid_structure:
                nodes.append(general.group(em=True, n = node))
            [general.parent(x, nodes[-1]) for x in general.ls(geometry = True)]
            #Perform a chain of parents for PID structures larger than one node
            if len(pid_structure)>1:
                for index, node in enumerate(nodes):
                    if index>0:
                        general.parent(node, nodes[index-1])
            return pid_structure[0]
        else:
            print("No PID Map found")
        return None
                    
    
    def saveFile(self, type=0):
        #So this function needs to look into the proper component folder (if it exists), find the Working folder (if it exists, if not make it)
        #Then save an iteration of this file.
        
        #If our project is valid
        if self.getSelectedProject()!=None:
            #If our part is valid
            if self.selectedPart!=None:
                #Get the needed information from the modeling components array for this project
                #Will need to change once parts are made into a class instead of this weird thing
                part_directory, part_name, part_numname = self.getSelectedProject().modelingComponents[self.selectedPart]
                #If the part directory exists
                if os.path.isdir(part_directory):
                    #Set some directory variables ahead of time                    
                    working_dir = os.path.join(part_directory, "Working")
                    qa_dir = os.path.join(part_directory, "QA")
                    publish_dir = os.path.join(part_directory, "Publish")
                    
                    #If those directories don't exist (they should), then make em
                    if os.path.isdir(working_dir)==False:
                        os.makedirs(working_dir)
                    if os.path.isdir(qa_dir)==False:
                        os.makedirs(qa_dir)
                    if os.path.isdir(publish_dir)==False:
                        os.makedirs(publish_dir)
                    
                    #If save type is 0 (which is a regular work file incremental save)
                    #Save format: part name_modeler_v001.mb
                    if type==0:
                        #If we have a username entered...
                        if self.username!="":
                            #If the part we're currently working on is in the scene name
                            #If this is NOT the case, somehow the user managed to load a different file while the script is running
                            if self.getSelectedPart() in system.sceneName():
                                #Get all the files in the working directory
                                #Similar to the loading function, this just attempts to find the highest version number of the working files
                                #Then saves an incremental file on top of that with a specific format
                                #See above for how this code works, its pretty much the same
                                files = glob.glob(working_dir+"/*.mb")
                                if len(files)>0:
                                    highest_num=0
                                    for file in files:
                                        if os.path.isfile(file):
                                            _fname = str(os.path.split(file)[1].split(".")[0])
                                            filenum=''
                                            
                                            for x in reversed(_fname):
                                                if x.isdigit():
                                                    filenum = x + filenum
                                                else:
                                                    break
                                            
                                            if len(filenum)>0:
                                                filenum = int(filenum)
                                                if filenum>highest_num:
                                                    highest_num = filenum
                                    else:
                                        #Once we've finished the loop, increment the highest number up one
                                        #If no other files were found, this will end up with the number one
                                        highest_num+=1
                                        #Generate the necessary amount of leading zeroes
                                        num = ("0"*max(0,5-len(str(highest_num)))+str(highest_num))
                                        print("Num: " + num)
                                else:
                                    #If no files were found, just set the number manually
                                    num = "00001"
                                
                                #If the number is 00001, show a dialogue box to inform the modeler that this is the first version of the file
                                #This shouldnt happen since the first versions of the components are generated automatically by a setup program
                                if num=="00001":
                                    if windows.confirmDialog(title = "Save Part File?", message = "Save the first version of this part? You will not be prompted when saving new versions after this.", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                                        file_name = os.path.join(working_dir , "%s_%s_v%s.mb"%(part_name, self.username, num))#part_name + "_" + self.username + "_" + "v" + num + ".mb")
                                        system.saveAs(file_name)
                                        self.getPreviousPartVersions()
                                        self.refreshSettingsUI()
                                else:
                                    #Otherwise, dont prompt the user, just save
                                    file_name = os.path.join(working_dir , "%s_%s_v%s.mb"%(part_name, self.username, num))
                                    system.saveAs(file_name)
                                    self.getPreviousPartVersions()
                                    self.refreshSettingsUI()
                            else:
                                windows.confirmDialog(title = "Scene Changed", message = "The scene has been switched from the originally loaded one.  Please re-load your scene using the heirarchy tool.", button = "Dismiss")
                        else:
                            windows.confirmDialog(title="No username entered.", message="Please enter a valid username to save with.",button="Dismiss")
                    
                    #If the save file is type 1, its a publish attempt 
                    elif type==1:
                        #Prompt the user to make sure they want to publish.  Theres no penalty for doing so, it backs up older publish files.
                        if windows.confirmDialog(title = "Publish File", message = "Publish this scene file?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                            #Generate what the final filename should be
                            file_name = os.path.join(publish_dir, part_name + "_publish.mb")
                            #If it already exists...
                            if os.path.isfile(file_name):
                                #Get the creation time of it, create a backup folder for it with the necessary time information, and move it there
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
                            #Get a list of them
                            references = general.ls(type = "reference")
                            #If theres at least one reference...
                            if len(references)>0:
                                for reference in references:
                                    #If its not the shared reference node, which is in every scene and cant be removed
                                    if "sharedReferenceNode"!=reference:
                                        reference_files.append(system.referenceQuery(reference, filename=True))
                                else:
                                    for file in reference_files:
                                        #Iterate through any references we found and remove them
                                        system.FileReference(pathOrRefNode = file).remove()
                            
                            #Clear the selection
                            general.select(clear = True)
                            #Attempt to Auto PID things
                            if self.attemptBakePID()!=None: print("Auto PID success")
                            else: print("Auto PID failed")
                            #Select all the geometry in the scene
                            general.select(general.ls(geometry = True))
                            general.select(general.ls(tr = True), add = True)
                            #Build a name for the layer that will contain this geometry
                            layerName = os.path.split(system.sceneName())[1].split("_")[0].replace(" ", "_")
                            #Create a display layer for it
                            general.createDisplayLayer(name = layerName)
                            #Save the publish file, then immediately open the working file so the filename doesn't change
                            system.saveAs(file_name)
                            system.openFile(current_filename, f = True)
                    #If its type 2, its a QA submit
                    elif type==2:
                        #Make sure the user wants to submit for QA
                        if windows.confirmDialog(title = "Submit for QA", message = "Submit this scene file for QA?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes':
                            #Get the time and build a string out of it to append to the name of the file
                            _time = time.strftime("%b%d_%Y_%H-%M-%S", time.localtime(time.time()))
                            file_name = os.path.join(qa_dir, part_name + "_%s_%s.mb"%(self.username,_time))
                            print("Saving QA file...")
                            
                            #Search for any QA files that already exist, and move them into folders if they do
                            _files = glob.glob(qa_dir+"/*.mb")
                            if len(_files)>0:
                                print("QA MB File found, needs moved")
                                found=False
                                #Iterate through the files
                                for i in _files:
                                    #If we find an exact duplicate of the current filename, show a prompt for saving over it
                                    if file_name == i:
                                        print("Found file with exact name.")
                                        found=True
                                        if windows.confirmDialog(title = "Overwrite?", message = "A QA file with this name already exists.  Overwrite it?", button = ['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')=='Yes': 
                                            print("File with exact name overwritten.")
                                            current_filename = system.sceneName()
                                            system.saveAs(file_name)
                                            system.saveAs(current_filename)
                                    else:
                                        #Otherwise, move it into a folder with the necessary info
                                        print("Moving other QA file into folder")
                                        _folder = os.path.join(qa_dir,"_old/%s"%(os.path.split(i)[1].split(".")[0]))
                                        os.makedirs(_folder)
                                        shutil.move(i, _folder)
                                else:
                                    #Once we finish the loop, if a filename with the same name wasnt found, save a QA file
                                    if found==False:
                                        print("Saving file.")
                                        current_filename = system.sceneName()
                                        system.saveAs(file_name)
                                        system.saveAs(current_filename)
                            else:
                                #Save the QA file, then immediately resave as the working file so the scene name doesnt change
                                print("No other QA files found, saving file")
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
        #if windows.optionMenu("projectOptionMenu", q = True, v = True)!="None":
        if self.getSelectedProject()!=None:
            file.write(self.getSelectedProject().name + "\n")
            #Next write the current part display name
            if self.selectedPart!=None:
                file.write(self.getSelectedProject().modelingComponents[int(self.selectedPart)][1] + "\n")
            else:
                file.write("None\n")
            #Save the current filter
        else:
            #Else, if there is no project selected somehow, just write "None" for both project and part
            file.write("None\nNone\n")
        #file.write(str(windows.optionMenu("filterMakeMenu",q = True, v = True)) + "\n")
        file.close()
    
    def getPreviousPartVersions(self):
        if self.getSelectedProject()!=None and self.getSelectedPart()!=None:
            part_dir = os.path.join(self.getSelectedProject().modelingComponents[int(self.selectedPart)][0], "Working")
            print("Finding part versions in part dir %s"%(part_dir))
            versions = glob.glob(part_dir+"/*.mb")
            print(str(versions))
            if len(versions)>0:
                versions_sorted = []
                for _file in versions:
                    
                    _fname = str(os.path.split(_file)[1].split(".")[0])
                    print("Found file version %s"%(_fname))
                    filenum=''
                    
                    for x in reversed(_fname):
                        if x.isdigit():
                            filenum = x + filenum
                        else:
                            break
                    if filenum!='':
                        filenum = int(filenum)
                        versions_sorted.append((_file, filenum, _fname))
                
                versions_sorted.sort(key=lambda x: x[1], reverse = True)
                self.selectedPartVersions = [(x[0], x[2]) for x in versions_sorted]
                print("New part versions list: %s"%(str(self.selectedPartVersions)))
                return True
                #return [x[0] for x in versions_sorted]
        print("No previous part versions found.")
        self.selectedPartVersions=[]
        return False
            
    
    def refreshSettingsUI(self):
        print(str(self.getSelectedProject()))
        print(str(self.selectedPart))
        
        if windows.window("OEMToolbar_Settings", exists = True):
            windows.textFieldGrp("usernameEntry", e = True, tx = self.username)
            #This is where we populate our drop down menu.  So its just GUI stuff
            #Get all the current menu items for the project drop down menu, if there are any
            [windows.deleteUI(item) for item in windows.optionMenu("projectOptionMenu", q = True, ill = True)]

            _filter = self.getFilters()
            if len(self.projects)>0:
                #...iterate through the projects and create a menu option for each one.
                for project in self.projects:
                    if len(_filter)>0:
                        for f in _filter:
                            if project.make == f:
                                windows.menuItem(l = project.name, p = "projectOptionMenu")
                                break
                    else:
                        windows.menuItem(l = project.name, p = "projectOptionMenu")
                
                if len(windows.optionMenu("projectOptionMenu", q = True, ill = True))==0:
                    windows.menuItem(l = "None", p = "projectOptionMenu")
            else:
                #If no projects are found, just add a None menu option.
                windows.menuItem(l = "None", p = "projectOptionMenu")
            #Set the current selection to the current project name
            if self.getSelectedProject()!=None:
                windows.optionMenu("projectOptionMenu", e = True, v = self.getSelectedProject().name)
            else:
                windows.optionMenu("projectOptionMenu", e = True, v = "None")
            
            current_buttons = windows.scrollLayout("partsScrollLayout", q = True, ca = True)
            if current_buttons!=None:
                [windows.deleteUI(x) for x in current_buttons]
            
            current_buttons = windows.scrollLayout("partVersionsScrollLayout", q = True, ca = True)
            if current_buttons!=None:
                [windows.deleteUI(x) for x in current_buttons]
            #First query whether or not we have a valid project selected.  Otherwise theres no point
            #in trying to query the parts list, since its derivative of the project directory
            #if windows.optionMenu("projectOptionMenu", q = True, v = True)=="None":
            if self.getSelectedProject()!=None and len(self.getSelectedProject().modelingComponents)>0:
                #Delete all menu items and create a "None" item if there is none
                #[windows.deleteUI(x) for x in windows.optionMenu("partOptionMenu", q = True, ill = True)]

                #windows.menuItem(l = "None", p = "partOptionMenu")
                #Delete all the menu items in the part option menu dropdown
                #[windows.deleteUI(x) for x in windows.optionMenu("partOptionMenu", q = True, ill = True)]
                for index, component in enumerate(self.getSelectedProject().modelingComponents):
                    #windows.menuItem(l = component[1], p = "partOptionMenu")
                    componentNameFixed = (component[1].replace(" ","_"))
                    labelName = "%s_label"%(componentNameFixed)
                    layoutName = "%s_layout"%(componentNameFixed)
                    buttonName = "%s_button"%(componentNameFixed)
                    fButtonName = "%s_fbutton"%(componentNameFixed)
                    
                    def buttonCommand(event, index = index):
                        self.loadFile(index)
                    
                    def fButtonCommand(event, index = index):
                        self.openPartFolder(index)
                        
                    windows.rowLayout(layoutName,p = "partsScrollLayout",nc = 3)
                    windows.button(fButtonName, l = "Finder", p = layoutName, h = 18, w = 40, command = fButtonCommand)
                    windows.button(buttonName, l = "Open", p = layoutName, w = 40, h = 18, command = buttonCommand)
                    windows.text(labelName, l = component[1], p = layoutName, w = 100, h = 18, align = "left")
                    
                for index, component in enumerate(self.selectedPartVersions):
                    #windows.menuItem(l = component[1], p = "partOptionMenu")
                    componentNameFixed = (component[1].replace(" ","_"))
                    labelName = "%s_label"%(componentNameFixed)
                    layoutName = "%s_layout"%(componentNameFixed)
                    buttonName = "%s_button"%(componentNameFixed)
                    #fButtonName = "%s_fbutton"%(componentNameFixed)
                    
                    def buttonCommand(event, index = index):
                        self.loadPreviousVersionFile(index)
                    
                    #def fButtonCommand(event, index = index):
                        #self.openPartFolder(index)
                    
                    abbreviatedName = " ".join(component[1].split("_")[1:-1])
                    if len(abbreviatedName)>10:
                        abbreviatedName = "..."+abbreviatedName[-5:]
                    
                    labelText = "%s_%s"%(abbreviatedName, component[1].split("_")[-1])
                    
                    windows.rowLayout(layoutName,p = "partVersionsScrollLayout",nc = 2)
                    #windows.button(fButtonName, l = "Finder", p = layoutName, h = 18, w = 40, command = fButtonCommand)
                    windows.button(buttonName, l = "Open", p = layoutName, w = 40, h = 18, command = buttonCommand)
                    windows.text(labelName, l = labelText, p = layoutName, w = 100, h = 18, align = "left")
                    #windows.optionMenu("partOptionMenu", e = True, v = self.getSelectedProject().modelingComponents[self.selectedPart][1])
                #else:
                    #windows.menuItem(l = "None", p = "partOptionMenu")
        
    def loadSettings(self):
        #Load the settings from the save file
        #This has to properly load the project name, part name, username, etc.
        #But also, once the info is loaded, it has to be compared against the found projects/parts
        #In case the last project you were working on is gone, or the part name changed
        if os.path.isfile(os.path.join(os.path.expanduser("~"),"Documents/maya/settings/filepublishsettings")):
            file = open(os.path.join(os.path.expanduser("~"),"Documents/maya/settings/filepublishsettings"), "r")
            self.username = file.readline().replace("\n", "")
            project_name =  file.readline().replace("\n","")
            part_name = file.readline().replace("\n","")
            if len(self.projects)>0 or project_name == "None":
                for index, project in enumerate(self.projects):
                    if project.name == project_name:
                        self.selectedProject = index
                        if len(project.modelingComponents)>0:
                            if part_name!="None":
                                for index2, part in enumerate(project.modelingComponents):
                                    if part_name == part[1]:
                                        self.selectedPart = index2
                                        if windows.confirmDialog(title = "Load previous scene?",message= "Do you want to automatically load the last scene you were working on?", button=["Yes","No"], defaultButton = "Yes", cancelButton = "No", dismissString="No")=="Yes":
                                            self.loadFile(self.selectedPart)
                                        return
                                else:
                                    self.selectedPart = 0
                                    self.saveSettings()
                                    return
                            else:
                                self.selectedPart = 0
                                self.saveSettings()
                                return
                        else:
                            self.selectedPart = None
                            self.saveSettings()
                            return
                else:
                    self.selectedProject = None
                    self.selectedPart = None
                    self.saveSettings()
                file.close()
            else:
                self.selectedProject = None
                self.selectedPart = None
                self.saveSettings()
        
        self.refreshSettingsUI()
    
    
    def openProjectFolder(self):
        #Opens a finder window of the project core directory
        if self.getSelectedProject()!=None:
            _dir = self.getSelectedProject().directory
            if (os.path.isdir(_dir)):
                call(["open", "-R", _dir])
            else:
                windows.confirmDialog(title = "Project Not Found", message = "The selected project folder cannot be found.", button=["Dismiss"])

    def openPartFolder(self, index):
        #Opens a finder window of the specified part
        if self.getSelectedProject()!=None:
            if index!=None:
                part_dir = self.getSelectedProject().modelingComponents[index][0]
                if (os.path.isdir(part_dir)):
                    call(["open", "-R", part_dir])
                else:
                    windows.confirmDialog(title = "Part Not Found", message = "The selected part folder cannot be found.", button=["Dismiss"])
    
    def getFilters(self):
        #Get all the filters that are checked
        #This function needs to be rewritten
        returnFilters = []
        for i in self.filterCheckboxes:
            if windows.checkBox(i, q = True, v = True):
                returnFilters.append(windows.checkBox(i, q = True, l = True))
                print ("Filter: " + returnFilters[-1])
        return returnFilters
#        return windows.optionMenu("filterMakeMenu", q = True, v = True)
    
    def getSelectedProject(self):
        #Returns the selected project if valid
        if len(self.projects)>0 and self.selectedProject!=None:
            return self.projects[self.selectedProject]
        return None
    
    def getSelectedPart(self):
        #Return the name of the selected part
        if self.getSelectedProject()!=None and self.selectedPart!=None:
            if len(self.getSelectedProject().modelingComponents)>0:
                return self.getSelectedProject().modelingComponents[self.selectedPart][1]
            else:
                return None
        else:
            return None
    
    def setUserName(self):
        #Set the username to the one entered in the GUI
        self.username = windows.textFieldGrp("usernameEntry", q = True, tx = True)
        self.saveSettings()
    
    def getLoadedReferences(self):
        #Return a list of references that are loaded
        reference_files = []
    
        references = general.ls(type = "reference")
        if len(references)>0:
            for reference in references:
                if "sharedReferenceNode"!=reference:
                    #reference_files.append(system.referenceQuery(reference, filename=True))
                    reference_files.append(reference)
            else:
                return reference_files
        return []
    
    def getAvailableReferences(self):
        #Get references that are available for adding to your project
        if self.getSelectedProject()!=None:
            return_list=[]
            #Get the components folder of the current project
            folder = self.getSelectedProject().componentsFolder
            #If the folder is valid
            if folder!="" and os.path.isdir(folder):
                #Get all the component folders
                for component in glob.glob(folder+"*"):
                    #Return a list of component names
                    name = component
                    print(name)
                    if component not in system.sceneName() and os.path.isdir(component) and not os.path.basename(component).startswith("_"):
                        return_list.append(component)
                else:
                    return return_list
        return []
    
    def refreshReferencesUI(self):
        #If the window exists, refresh its UI
        if windows.window("OEMToolbar_ReferencePanel", exists = True):
            #Remove all the buttons for potential references to add/remove
            if windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Available_ScrollLayout",   q=True, ca=True)!=None and len(windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Available_ScrollLayout",   q=True, ca=True))>0:
                [windows.deleteUI(x) for x in windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Available_ScrollLayout",q=True, ca=True)]
            if windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Loaded_ScrollLayout",   q=True, ca=True)!=None and len(windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Loaded_ScrollLayout",   q=True, ca=True))>0:
                [windows.deleteUI(y) for y in windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Loaded_ScrollLayout",   q=True, ca=True)]
            
            #Get a list of available and selected references from the appropriate functions
            a_refs = self.getAvailableReferences()
            s_refs = self.getLoadedReferences()
            
            #If theres any available references, iterate through them and create buttons for each
            if len(a_refs)>0:
                for index, a_ref in enumerate(a_refs):
                    #Create a name for the button and make sure there isnt already one with this name in the selected references list
                    label_name = os.path.splitext(os.path.split(a_ref)[1])[0]
                    if not "%sRN"%(label_name.replace(" ", "_")) in s_refs:
                        #Create a function mid loop to avoid late binding
                        def buttonFunction(event, a_ref=a_ref):
                            self.addReference(a_ref)
                            self.refreshReferencesUI()
                        
                        layoutName = "%s_layout"%(label_name.replace(" ", "_"))
                        #Create a button that, when clicked, will add this reference to the scene
                        windows.rowLayout(layoutName, nc = 2, p = "OEMToolbar_ReferencePanel_Frame_Available_ScrollLayout")
                        windows.button(p = layoutName, command = buttonFunction, l = "+", h = 18)
                        windows.text(p = layoutName, l = label_name, align = "left", h = 18)
            else:
                print("No references found")
            
            #Refresh loaded references.  Sane as above, but instead creates a button that removes the reference from the scene
            if len(s_refs)>0:
                for s_ref in s_refs:
                    print("Loaded Reference: %s"%(s_ref))
                    label_name = s_ref
                    
                    def buttonFunction(event, s_ref = s_ref):
                        self.deleteReference(s_ref)
                        self.refreshReferencesUI()
                    
                    layoutName = "%s_layout"%(label_name.replace(" ", "_"))
                    #Create a button that, when clicked, will add this reference to the scene
                    windows.rowLayout(layoutName, nc = 2, p = "OEMToolbar_ReferencePanel_Frame_Loaded_ScrollLayout")
                    windows.button(p = layoutName, command = buttonFunction, l = "-", h = 18)
                    windows.text(p = layoutName, l = label_name, align = "left", h = 18)
            else:
                print("No references loaded")
    
    #Adds a reference to the filepath.  Used by the buttons in the refresh reference UI command.
    def addReference(self, filePath):
        print("Attempting to add reference to component folder %s..."%(filePath))
        #a_refs = self.getAvailableReferences()
        if os.path.isdir(filePath):
            print("Part folder %s found..."%(filePath))
            part_name = os.path.splitext(os.path.split(filePath)[1])[0]
            print("Part folder %s found..."%(filePath))
            ref_path = os.path.join(filePath, "Publish/%s_publish.mb"%(part_name))
            print(ref_path)
            if os.path.isfile(ref_path):
                ref = system.createReference(ref_path, namespace = part_name)
                node = pymel.core.PyNode(system.referenceQuery(ref, referenceNode=True))
                
                ref.unload()
                node.locked.set(True)
                ref.load()
            return
    
    #Deletes a reference.  Used by the buttons in the refresh reference UI command.
    def deleteReference(self, componentName):
        s_refs = self.getLoadedReferences()
        componentName = componentName.replace(" ","_")
        if not componentName.endswith("RN"):
            componentName = "%sRN"%(componentName.replace(" ","_"))
            
        for ref in s_refs:
            if componentName == ref:
                #system.referenceQuery(ref_name, filename=True)
                system.FileReference(pathOrRefNode = system.referenceQuery(componentName, filename=True)).remove()
                return
    
    
    '''
    All the follow code is just creating GUI stuff, and is mostly separate from the logic of the program, so that if this code needs to be agnostic of Maya, it can be ported easily
    '''
    def OEM_SettingsPanel_GUI(self):
        #Create the UI
        #Define all custom commands for the buttons and dropdown menus
        def refreshButtonCommand(event):
            self.projects = findProjectDirectories(3, ["/Volumes/Client_Projects/","/Volumes/bto-secure/"], ["Modeling",])
            #self.populateProjectsList(self.getFilters())
            self.loadSettings()
            self.refreshSettingsUI()
        
        def projectOptionMenuChangeCommand(event):
            if windows.optionMenu("projectOptionMenu", q = True, v = True)!="None":
                self.selectNewProject(int(windows.optionMenu("projectOptionMenu", q = True, sl = True))-1)
                self.getPreviousPartVersions()
                self.saveSettings()
                self.refreshSettingsUI()
                self.refreshReferencesUI()
            
        def filterMakeMenuChangeCommand(event):
            self.saveSettings()
            self.refreshSettingsUI()
                
        #def partChangeCommand():
        #    if windows.optionMenu("partOptionMenu", q=True, v=True)!="None":
        #        self.selectedPart = int(windows.optionMenu("partOptionMenu", q=True, sl=True))-1
        #        self.saveSettings()
        #        self.loadFile()
        #        self.refreshSettingsUI()
        
        overall_width = 400
        
        if windows.windowPref("OEMToolbar_Settings", exists=True):
            windows.windowPref("OEMToolbar_Settings", remove=True)
        windows.window("OEMToolbar_Settings", t = "OEM Modeling",w = overall_width, h=150)
        windows.columnLayout()
        
        windows.separator(h = 5, style = "none")
        windows.rowLayout(nc = 3)
        windows.separator(w = 5, style = "none")
        windows.columnLayout()
        ###
        ###
        ###
        ''''''
        windows.frameLayout(l = "User Settings",w = overall_width, cl = False, cll = False)
        windows.textFieldGrp("usernameEntry", l = "User", cw2 = [overall_width*0.16667, 5*(overall_width*0.16667)], cc = lambda x: self.setUserName())
        windows.setParent(u = True)
        ''''''        
        windows.separator(w = overall_width, h = 20, style = "in")
        ''''''
        windows.frameLayout(l = "Projects",w = overall_width, cl = False, cll = False)
        windows.columnLayout("Project Settings")
        windows.optionMenu("projectOptionMenu", l = "Project: ", w = overall_width,cc = projectOptionMenuChangeCommand)
        windows.rowLayout(nc = 2)
        windows.button("navigateToProjectButton", l = "Open Finder Window", w = overall_width*0.5, h = 18, command = lambda event: self.openProjectFolder())
        windows.button("refreshProjectsButton", l = "Refresh List", w = overall_width*0.5, h = 18, command = refreshButtonCommand)
        windows.setParent(u = True)
        
        '''windows.text(l = "Filters:")
        self.filterCheckboxes = []
        windows.rowColumnLayout(nc = 3, columnWidth = [(1, 0.3333*overall_width), (2, 0.3333*overall_width), (3, 0.3333*overall_width)])
        for k in makes:
            self.filterCheckboxes.append(windows.checkBox(l = k, w = 100, cc = filterMakeMenuChangeCommand))
        windows.setParent(u = True)'''
        windows.setParent(u = True)
        windows.setParent(u = True)
        ''''''
        windows.separator(w = overall_width, h = 20, style = "in")
        ''''''
        windows.frameLayout(l = "Parts",w = overall_width, cl = False, cll = False)
        windows.rowColumnLayout("Part Actions", nc = 2)
        
        windows.text(l = "Parts in Project")
        windows.text(l = "Previous Versions")
        
        windows.scrollLayout("partsScrollLayout", w = overall_width / 2, h = 200)
        ''' -Part button- 
        windows.rowLayout(nc = 2)
        windows.button("testButton", l = "Test Part", w = overall_width * 0.667)
        windows.button("testButtonFinder", l = "Finder")
        windows.setParent(u = True)
         -Part button- '''
        windows.setParent(u = True)

        
        windows.scrollLayout("partVersionsScrollLayout", w = overall_width / 2, h = 200)
        ''' -Part button- 
        windows.rowLayout(nc = 2)
        windows.button("testButton", l = "Test Part", w = overall_width * 0.667)
        windows.button("testButtonFinder", l = "Finder")
        windows.setParent(u = True)
         -Part button- '''
        windows.setParent(u = True)        
        
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.setParent(u = True)
        ''''''
        windows.separator(w = 5, style = "none")
        windows.setParent(u = True)
        windows.separator(h = 5, style = "none")
        
        windows.setParent(u = True)
        
        windows.showWindow("OEMToolbar_Settings")
        self.refreshSettingsUI()
    
    def OEM_SavingPanel_GUI(self):
        if windows.windowPref("OEMToolbar_SaveGUI", exists=True):
            windows.windowPref("OEMToolbar_SaveGUI", remove=True)
        windows.window("OEMToolbar_SaveGUI", t = "Save Options", sizeable = False)
        self.addOuterPadding(5, 5)
        
        windows.frameLayout(l = "Save Options", w = 300, h = 150, cl = False, cll = False)
        windows.rowLayout(nc = 2)
        windows.button("saveQAButton", l = "Submit for QA", w = 150, h=50, c = lambda event: self.saveFile(2))
        windows.button("publishButton", l = "Publish Part", w = 150, h = 50,c = lambda event: self.saveFile(1))
        windows.setParent(u = True)
        windows.button("saveButton", l = "Save Work in Progress", w = 300, h=50, c = lambda event: self.saveFile())
        windows.setParent(u = True)
        
        self.returnOuterPadding(5, 5)
        #windows.setParent(u = True)
        windows.showWindow("OEMToolbar_SaveGUI")
        #windows.window("OEMToolbar_SaveGUI", e = True, wh = [300, 200])

    def OEM_ReferencePanel_GUI(self):
        if windows.windowPref("OEMToolbar_ReferencePanel", exists=True):
            windows.windowPref("OEMToolbar_ReferencePanel", remove=True)
        windows.window("OEMToolbar_ReferencePanel", t = "OEM Part Reference Panel", sizeable = False)
        self.addOuterPadding(5, 5)
        windows.columnLayout()
        windows.frameLayout("OEMToolbar_ReferencePanel_Frame_Available", l = "Available Parts", w = 200, h = 200)
        windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Available_ScrollLayout")
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.frameLayout("OEMToolbar_ReferencePanel_Frame_Loaded", l = "Referenced Parts", w = 200, h = 200)
        windows.scrollLayout("OEMToolbar_ReferencePanel_Frame_Loaded_ScrollLayout")
        windows.setParent(u = True)
        windows.setParent(u = True)
        windows.button(l = "Refresh", w=200, h=20, command = lambda x: self.refreshReferencesUI())
        '''windows.rowLayout(nc = 2)
        windows.button(l="Add All", w = 98, h = 20)
        windows.button(l="Remove All", w = 98, h = 20)
        windows.setParent(u = True)'''
        windows.setParent(u = True)
        self.returnOuterPadding(5, 5)
        
        windows.showWindow("OEMToolbar_ReferencePanel")
        
        self.refreshReferencesUI()
        
    def OEMToolbar_GUI(self):
        ###
        ###ADD MORE LAYOUTS HERE TO ADD THEM TO THE TAB LAYOUT
        ###
        if windows.windowPref("OEMToolbar_Toolbar", exists=True):
            windows.windowPref("OEMToolbar_Toolbar", remove=True)
        windows.window("OEMToolbar_Toolbar", t = "OEM Toolbar", sizeable=False)
        self.addOuterPadding(5, 5)
        
        windows.frameLayout(l = "OEM Toolbar")
        windows.columnLayout()
        windows.button("OEMToolbar_Settings_Button", l = "Settings", command = lambda x: self.showSettingsPanel(), w = 120, h = 40)
        windows.button("OEMToolbar_SaveGUI_Button", l = "Save GUI", command = lambda x: self.showSavingPanel(),w = 120, h = 40)
        windows.button("OEMToolbar_ReferencePanel_Button", l = "Part Referencing", command = lambda x: self.showReferencePanel(),w = 120, h = 40)
        windows.setParent(u = True)
        windows.setParent(u = True)
        
        self.returnOuterPadding(5, 5)
        
        windows.showWindow("OEMToolbar_Toolbar")
        
    def OEM_LoadingWindow_GUI(self):
            #Clear the window preference for the loading window
        if windows.windowPref("loadingWindow", exists=True):
            windows.windowPref("loadingWindow", remove=True)
            
        #Create the loading window
        windows.window("loadingWindow", w = 200, h = 20, sizeable=False, t = "Loading Projects")
        windows.columnLayout()
        windows.separator(h=20)

        windows.rowLayout(nc = 3)
        windows.separator(w=10, st = "none")
        windows.text(l = "One moment, finding projects...")
        windows.separator(w=10, st = "none")
        windows.setParent(u = True)
        windows.separator(h=20)
        windows.showWindow("loadingWindow")
    
    def addOuterPadding(self, hpadding=0, vpadding=0):
        windows.columnLayout()
        windows.separator(h = hpadding, style = "none")
        windows.rowLayout(nc=3)
        windows.separator(w = vpadding, style = "none")
    
    def returnOuterPadding(self, hpadding=0, vpadding=0):
        windows.separator(w = hpadding, style = "none")
        windows.setParent(u=True)
        windows.separator(h = vpadding, style = "none")
        windows.setParent(u=True)
        #windows.showWindow("OEMToolbar_Settings")
        #windows.showWindow("OEMToolbar_SaveGUI")