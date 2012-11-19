import sublime, sublime_plugin, os, stat

#p4 makes files read only which causes an annoying pop up on save.
#This removes read-only from a file before saving
class PreSaveCommand(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        myFile = view.file_name()
        fileAtt = os.stat(view.file_name())[0]
        if (not fileAtt & stat.S_IWRITE):
            os.chmod(myFile, stat.S_IWRITE)