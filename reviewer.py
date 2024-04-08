from pywebio import start_server, config
from pywebio.input import *
from pywebio.output import *
from pywebio.pin import put_file_upload, put_input, put_checkbox, put_select, pin, pin_update
from os import path
import bibProcesser
import pickle
import re

#####################################################################################
# Data Variables
#####################################################################################
entries = []
merged_entries = []

sort_key = "citation-per-year"
sort_asc = False
displaying_keys = ["citation-per-year", "year", "times-cited", "title"]
entries_keys = []

#####################################################################################
# Procedures
#####################################################################################
def saveData(variable, name):
    with open(path.join(path.dirname(__file__),f"data/{name}"), "wb") as file:
        pickle.dump(variable, file)

def loadData(name):
    if not path.isfile(path.join(path.dirname(__file__),f"data/{name}")): 
        return
    
    with open(path.join(path.dirname(__file__),f"data/{name}"), "rb") as file:
        variable = pickle.load(file)
    return variable

def addfile_Procedure():
    file = pin.bibFile
    if file == None:
        return
    global entries
    popup("Loading", "Loading bib file...",closable=False)
    newEntry = bibProcesser.getEntries(file)
    entries.append((newEntry, file["filename"]))
    LoadBibliography_Screen(info=lambda:put_info(f"Loaded {len(newEntry)} entries"))
    close_popup()

def removeFile_Procedure(i):
    global entries
    entry,_ = entries.pop(i)
    LoadBibliography_Screen(info=lambda:put_warning(f"Removed {len(entry)} entries"))

def importCitations():
    global entries
    popup("Loading", ["Importing citations...", put_loading()])
    bibProcesser.importCitations(entries)
    close_popup()
    mergeBibliography_Procedure()

def checkCitations_Procedure():
    amountWithoutTimesCited = bibProcesser.lacksTimeCited(entries)
    if amountWithoutTimesCited > 0:
        popup(f"Found {amountWithoutTimesCited} articles without citation count",[
            put_text("Do you want to import this information? This may take some time"),
            put_buttons(["Accept","Cancel"], onclick=[importCitations, mergeBibliography_Procedure])
        ], closable=False)
    else:
        mergeBibliography_Procedure()


def mergeBibliography_Procedure():
    global merged_entries, entries_keys
    
    merged_entries, repeated = bibProcesser.mergeEntries(entries)

    popup(f"Generated bibliography with {len(merged_entries)} entries", content=[
        f"Removed {repeated} repeated entries(by doi)",
        put_button("OK", onclick=main_screen)
        ], closable=False)
    
    saveData(merged_entries, "merged_entries")

def sortBibliographies_Procedure():
    global merged_entries, sort_key, sort_asc
    sort_key = ""+pin.sort_key
    sort_asc = len(pin.sort_asc) > 0
    merged_entries = bibProcesser.sortEntries(merged_entries, sort_key, sort_asc)
    viewBibliographies_Screen()

def addDisplayingKey_Procedure():
    global displaying_keys
    if not pin.displaying_keys in displaying_keys:
        displaying_keys.append(pin.displaying_keys)
        viewBibliographies_Screen()
    else:
        toast("Already displaying field")

def removeDisplayingKey_Procedure():
    global displaying_keys
    if pin.displaying_keys in displaying_keys:
        displaying_keys.remove(pin.displaying_keys)
        viewBibliographies_Screen()
    else:
        toast("Not displaying field")

def createNewField_Procedure():
    global merged_entries, entries_keys, displaying_keys

    fields = re.findall(r'"(.*?)"', pin.create_field_func)
    expression = pin.create_field_func
    protect_expression = pin.create_field_func
    for field in fields:
        if not (field in entries_keys):
            toast(f'Illegal field "{field}"', color="danger")
            return
        expression = expression.replace(f'"{field}"', f'float(e["{field}"])')
        protect_expression = protect_expression.replace(f'"{field}"',"")
    
    if re.match(r'^[0-9()+\-*/\s]+$', protect_expression) is None:
        toast("Invalid expression", color="danger")
        return
    
    success = bibProcesser.createNewKey(pin.create_field_name,expression, merged_entries)

    if not success:
        toast("Failed for all entries, are you sure the fields selected are numbers?")
        return
    
    entries_keys.append(pin.create_field_name)
    entries_keys.sort()
    displaying_keys.append(pin.create_field_name)
    saveData(merged_entries, "merged_entries")
    saveData(displaying_keys, "displaying_keys")
    viewBibliographies_Screen()

def selectAllArticles_Procedure():
    val = [] if all([len(pin[f"selected_article_{i}"]) != 0 for i in range(len(merged_entries))]) else ""
    for i in range(len(merged_entries)):
        pin_update(f"selected_article_{i}", value=val)

#####################################################################################
# Screens
#####################################################################################
def helpCreateField_Popup():
    popup("How to create a new field:",[
        put_text("Define the name of the new field (if an existing name is given, it may be overwritten)."),
        put_text("The expression is defined as fields toghether with mathematical expressions"),
        put_text("Fields are defined between quotes, and need to be one of the fields that areadly exist in the elements"),
        put_text("The field does not need to be present in all entries, but must exist in at least one"),
        put_text('Ex: "times-cited"/(2024-"year")')
    ])

def LoadBibliography_Screen(info=lambda:None):
    clear() 
    put_button('Go back', onclick=main_screen)
    put_text("Add your references(.bib)",)
    put_file_upload('bibFile',label='Upload a file:', accept='.bib')
    put_button("add", onclick=addfile_Procedure)
    if len(entries) > 0:
        put_text(f"Entries loaded: {sum(len(e[0]) for e in entries)}")
        for i, (entry, name) in enumerate(entries):
            put_row([
                put_text(f"     > ({len(entry)}) {name}"),
                put_button("remove", onclick=lambda i=i:removeFile_Procedure(i), color="danger")
            ])

    info()
    if len(entries) > 0:
        put_button("Merge", onclick=checkCitations_Procedure, color="success")

def viewBibliographies_Screen():
    global entries_keys
    if len(entries_keys) == 0:
        entries_keys = bibProcesser.getEntriesKeys(merged_entries)

    clear()
    put_button('Go back', onclick=main_screen)
    put_row([
        put_text("Order: "),
        put_select("sort_key",entries_keys,value=sort_key),
        put_button("sort",onclick=sortBibliographies_Procedure),
        put_checkbox("sort_asc",["descending"],value=[sort_asc])
    ])

    put_row([
        put_text("Edit displaying fields:"),
        put_select("displaying_keys", entries_keys),
        put_buttons(["Add", "Remove"], onclick=[addDisplayingKey_Procedure, removeDisplayingKey_Procedure])
    ])

    put_row([
        put_text("Create field:"),
        put_input("create_field_name", placeholder="Name"),
        put_input("create_field_func", placeholder='Expression'),
        put_button("Create", onclick=createNewField_Procedure),
        put_button("Help", onclick=helpCreateField_Popup)
    ])

    put_row([
        put_text("Add to list:"),
        put_select("available_lists", []),
        put_buttons(["Add", "New list"], onclick=[lambda:None, lambda:None])
    ])

    doi = lambda e: put_link("https://doi.org/"+e["doi"],"https://doi.org/"+e["doi"]) if "doi" in e else "-" 

    table_row = lambda e: [e[key] if key in e else "-" for key in displaying_keys]

    table = [[put_checkbox(f"selected_article_{i}",[""]),i+1]+table_row(e)+[doi(e)] for i,e in enumerate(merged_entries)]

    put_table(table, header=[put_button("☑",onclick=selectAllArticles_Procedure)," "]+displaying_keys+["doi"])

def main_screen():
    close_popup()
    clear()
    buttons_labels = ['Load bibliography']
    buttons_actions =  [LoadBibliography_Screen]
    
    if len(merged_entries) > 0:
        buttons_labels.append("View bibliography")
        buttons_actions.append(viewBibliographies_Screen)
    
    put_buttons(buttons_labels, onclick=buttons_actions)

#####################################################################################
# Main
#####################################################################################

def loadAll():
    global merged_entries, displaying_keys
    temp = loadData("merged_entries")
    if temp: merged_entries = temp
    temp = loadData("displaying_keys")
    if temp: displaying_keys = temp


def main():
    config(css_style=".container{max-width: 90%};")
    loadAll()
    start_server(main_screen,host="127.0.0.1", port=8080, auto_open_webbrowser=True)

if __name__ == '__main__':
    main()