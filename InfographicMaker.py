# encoding: utf-8
from tkinter import *
from tkinter.ttk import *
import os, requests
from ttkwidgets import autocomplete
from tkinter import filedialog, messagebox, font
from PIL import Image, ImageFont, ImageDraw
from math import ceil

'''
Author = Flaps#9562
Year = 2021
Function = RotMG Infographic Maker. HAS ONLY BEEN TESTED ON WINDOWS 10.
'''

class Config:
    #class for managing config/options
    def __init__(self):
        self.file = os.path.dirname(os.path.realpath(__file__)) + '\\config.txt'

    #extra, might use later
    def getFullConfig(self):
        with open(self.file, 'r') as configFile:
            lines = configFile.read().splitlines()
            dictionary = {}
            for i in lines:
                dictionary = {**dictionary, i.partition(':')[0] : i.partition(':')[2]}
        return dictionary

    #get state of manual
    def getManual(self):
        with open(self.file, 'r') as configFile:
            lines = configFile.read().splitlines()
            if lines[0].partition(':')[2] == '0':    manual = False
            else:    manual = True
        return manual

    #swap state of manual
    def changeManual(self):
        global manualSort
        with open(self.file, 'r+') as configFile:
            lines = configFile.read().splitlines(True)
            if self.getManual():
                lines[0] = lines[0].partition(':')[0] + lines[0].partition(':')[1] + '0'
                manual = False
            else:
                lines[0] = lines[0].partition(':')[0] + lines[0].partition(':')[1] + '1'
                manual = True
            configFile.truncate(0)
            configFile.seek(0)
            for i in lines:
                configFile.write(i)
        manualSort = manual     

def genDict(f):
    #generate dict from formatted txt file
    dict = {}
    lines = f.splitlines()
    for line in lines:
        linePart = line.partition(' | ')
        dict[linePart[0]] = linePart[2]
    return dict

def loadDungeons():
    global dungeons, dungeonNames
    try:
        with open(mainPath + '\\dungeons.txt', 'r', encoding = 'utf-8') as f:
            dungeons = genDict(f.read())
        dungeonNames = sorted(dungeons.keys())
    except Exception as e:
        messagebox.showerror('Error', 'Dungeons load error: ' + str(e))
        exit() 

def loadDicts():
    global itemDicts, itemDict, manualSort
    try:
        if manualSort == True:    raise Exception('Manual sort is on.')
        for dictFile in os.listdir(mainPath + '\\Dictionaries'):
            #index finding
            index = ''
            if '!' not in dictFile:    raise ValueError('{} is missing \"!\" indicator for priority sorting.'.format(dictFile))
            for char in dictFile:
                if char == '!':    break
                index = index + char
            if not index.isdigit():    raise ValueError('{} has invalid characters before \"!\" indicator.'.format(dictFile))
            index = int(index) - 1

            #dict defining
            itemDict = {}
            with open(mainPath + '\\Dictionaries\\' + dictFile, 'r', encoding = "utf-8") as f:
                itemDict = genDict(f.read())
                itemDicts[index] = itemDict
    except Exception as e:
        manualSort = True
        messagebox.showerror('Error', 'Dictionary Error: ' + str(e) + '\n\nUsing manual sorting.')

def genInfographic():
    #instructions
    if startTexts[0].get('1.0', 'end') == "Press 'Go!' for instructions.\n":
        messagebox.showinfo('Instructions',
            "1. Choose a dungeon with the drop-down menu or type it.\n2. Input a background link where prompted, or leave it blank\n    for an empty background.\n3. Type or paste the name of each item that you want\n    displayed. Spelling counts, if you can't figure out the\n    correct spelling, see the dictionaries folder for a list of all\n    valid keys.\n4. The '+' amd '-' buttons alter the amount of infographics\n    generated. You can have up to 4 at once.\n5. Once all items are inputted and all desired fields are\n    fulfilled, press 'Go!' to choose a folder to save to and\n    generate the infographic.\n6. For instructions on priority sorting and options, see the\n    readme file.")
        return

    #vars
    dungeonList, dungeonLinkList, itemLists, missingSet, notMissingSet = [], [], [], set(), set()
    length = len(dungeonChoices)
    rows, x, y = 0, 0, 0

    #reload dicts in case options have changed
    loadDicts()
    
    #rebuild dict if manual mode is on
    if manualSort:
        global itemDict
        itemDict = {}
        for dictFile in os.listdir(mainPath + '\\Dictionaries'):
            with open(mainPath + '\\Dictionaries\\' + dictFile, 'r', encoding = "utf-8") as f:
                itemDict = {**itemDict, **(genDict(f.read()))}
    
    #get dungeons and items
    try:
        for i in range(length):
            try:
                dungeonList.append(dungeonChoices[i].get())
                dungeonLinkList.append(dungeons[dungeonChoices[i].get()])
            except:
                dungeonList.append(dungeonChoices[i].get())
                dungeonLinkList.append('https://upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png')
                messagebox.showwarning('Warning', 'Unexpected dungeon.')
            
            #split text by line, add stripped list to lists
            itemList = startTexts[i].get('0.0', 'end').splitlines()
            itemLists.append([x.strip(' –') for x in itemList])

        #get rows for yaxis
        for i in itemLists:
            rows = rows + ceil(len(i) / 10)
    except Exception as e:
        messagebox.showerror("Error", 'Unknown Error: ' + str(e))
        exit()

    #geometry
    xaxis = 400
    yaxis = (length * 60) + ((length - 1) * 10) + (rows * 40)# + 20 (was for signature)

    #image start
    source = Image.new('RGBA', (xaxis, yaxis), (255, 255, 255, 0))
    draw = ImageDraw.Draw(source)

    #bg is currently disabled
    #try bg link, ignore if invalid
    #try: 
    #    bg = Image.open(requests.get(bgEntry.get(), stream=True).raw).resize((xaxis, yaxis), resample = Image.BOX).convert('RGBA')
    #    source.alpha_composite(bg, (0, 0))
    #except:
    #    pass

    #the girth
    for i in range(length):
        #get dungeon pic, resize if needed, paste
        dungeonImage = Image.open(requests.get(dungeonLinkList[i], stream=True).raw).convert('RGBA')
        if dungeonImage.size[0] > 60 or dungeonImage.size[1] > 60:
            dungeonImage = dungeonImage.resize((56, 56), resample = Image.BOX)
        source.alpha_composite(dungeonImage, (x, y))

        #move xy
        x+= 60
        y+= 17
        
        #dungeon text
        draw.text((x, y), dungeonList[i], (192, 192, 192, 255), normalFont)

        #move xy
        x-= 60
        y+= 43

        #var for counting columns
        xChangeCount = 0

        #missing handling
        #manualsort
        if manualSort == True:
            for j in range(len(itemLists[i])):
                try:
                    itemDict[itemLists[i][j]]
                except Exception as e:
                    missingSet.add(itemLists[i][j])
                    continue

        #autosort
        else:
            for listIndex in range(len(itemDicts)):
                for j in range(len(itemLists[i])):
                    try:
                        itemDicts[listIndex][itemLists[i][j]]
                        notMissingSet.add(itemLists[i][j])
                    except Exception as e:
                        continue
            for item in itemLists[i]:
                if item not in notMissingSet:    missingSet.add(item)

        #missing handling
        if len(missingSet) > 0:
            itemErrorText = ''
            for i in missingSet:
                itemErrorText = itemErrorText + i + ', '
            messagebox.showerror("Error", 'Item(s) missing at: ' + itemErrorText + '\n\nTo see all valid item keys see the Dictionaries folder.')

        #save dialog
        try:
            finalPath = filedialog.asksaveasfilename(confirmoverwrite = True, initialdir = mainPath + '\\Infographics', initialfile = 'infographic.png', filetypes = [('PNG', '*.png')])
            if finalPath == '':
                messagebox.showwarning("Warning", 'File not saved.')
                return
        except Exception:
            finalPath = filedialog.asksaveasfilename(confirmoverwrite = True, initialdir = mainPath, initialfile = 'infographic.png', filetypes = [('PNG', '*.png')])
            if finalPath == '':
                messagebox.showwarning("Warning", 'File not saved.')
                return

        #manual sort option
        if manualSort == True:
            for j in range(len(itemLists[i])):
                try:
                    #open, resize, convert, paste
                    itemImage = Image.open(requests.get(itemDict[itemLists[i][j]], stream=True).raw).resize((40, 40), resample = Image.BOX).convert('RGBA')
                    source.alpha_composite(itemImage, (x, y))

                    #column/row handling
                    if xChangeCount != 9:
                        x+= 40
                        xChangeCount+= 1
                    else:
                        x-= 360
                        y+= 40
                        xChangeCount = 0
                except Exception as e:
                    if xChangeCount != 9:
                        x+= 40
                        xChangeCount+= 1
                    else:
                        x-= 360
                        y+= 40
                        xChangeCount = 0
                    continue

        #autosort
        else:
            for listIndex in range(len(itemDicts)):
                for j in range(len(itemLists[int(i)])): #not sure why i had to convert this to int
                    try:
                        #open, resize, convert, paste, add to non-missing
                        itemImage = Image.open(requests.get(itemDicts[listIndex][itemLists[i][j]], stream=True).raw).resize((40, 40), resample = Image.BOX).convert('RGBA')
                        source.alpha_composite(itemImage, (x, y))

                        if xChangeCount != 9:
                            x+= 40
                            xChangeCount+= 1
                        else:
                            x-= 360
                            y+= 40
                            xChangeCount = 0
                    except Exception as e:
                        continue

        #move xy
        x = 0
        y+= 50

    #signature
    #draw.text((297, yaxis-12), 'Made by Flaps#9562', (192, 192, 192, 255), smallFont) (RIP signamature)

    #save
    source.save(finalPath.rstrip('.png') + '.png', 'PNG')
    messagebox.showinfo('Saved', 'Infographic saved successfully.')

def optionsMenu():
    #global
    global manualSort

    #options tk
    options = Toplevel()
    options.title('Options')
    options.geometry('{}x{}'.format(int(maxX/3.84), int(maxY/2.571))) #500, 420 on 1080p
    options.resizable('FALSE', 'FALSE')
    options.configure(background = '#252a2d')

    optionsLabel = Label(options, text = 'Options:', style = 'options.TLabel')
    optionsLabel.pack(pady = int(maxY/36)) #30 on 1080p

    manualCheck = Checkbutton(options, text = 'Manual Sorting', style = 'manual.TCheckbutton', command = c.changeManual)
    if manualSort:    manualCheck.state(('selected',))
    manualCheck.pack(pady = int(maxY/64)) #15 on 1080p

    reloadDungeons = Button(options, text = 'Reload Dungeons', style = 'dungeons.TButton', command = loadDungeons)
    reloadDungeons.pack(pady = int(maxY/64)) #15 on 1080p

    creditLabel = Label(options, text = 'Made by Flaps#9562', style = 'options.TLabel')
    creditLabel.pack(pady = int(maxY/36)) #30 on 1080p

    options.mainloop()

def remGraphic():
    #removes 1 item from each list of widgets and repacks
    index = len(dungeonChoices) - 1

    dungeonChoices[index].destroy()
    dungeonChoices.pop()

    startTexts[index].destroy()
    startTexts.pop()

    manageWindow()

def addGraphic():
    #adds 1 item to each list of widgets and repacks, sets defaults
    dungeonChoice = autocomplete.AutocompleteCombobox(frame, completevalues = dungeonNames, font = defaultFont)
    dungeonChoice.set('Choose a Dungeon')
    dungeonChoices.append(dungeonChoice)

    startText = Text(frame,
        font = defaultFont,
        height = 20,
        width = 60,
        borderwidth = 1,
        relief = 'flat',
        highlightthickness = 1,
        highlightbackground = '#252a2d',
        background = '#131419',
        foreground = '#dddddd',
        highlightcolor = '#6c9cc4',
        selectbackground = '#4d6f8c',
        insertbackground = '#dddddd',
        insertborderwidth = 1)
    startTexts.append(startText)

    manageWindow()

def manageWindow():
    #resize window, pack/repack widgets, button handling
    length = len(dungeonChoices)

    #fit to monitor
    window.geometry('{}x{}'.format(length*int(maxX/4.5)+int(maxX/38.4), int(maxY/1.5766))) #len * ~427 + 50, 685 on 1080p

    for i in range(length):
        dungeonChoices[i].grid(column = i*2, row = 0, pady = int(maxY/54), columnspan = 2, sticky = 'we') #pady 20, ipadx 55 on 1080p
        startTexts[i].grid(column = i*2, row = 1, columnspan = 2, ipady = int(maxY/10.8)) #ipady 100 on 1080p

    remButton.grid(column = 1, row = 0)
    addButton.grid(column = 3, row = 0)

    if length == 1:
        remButton.grid_remove()
    elif length == 4:
        addButton.grid_remove()

    frame.grid(row = 0, column = 0, padx = int(maxX/76.8)) #padx 25 on 1080p
    buttonFrame.grid(row = 2, column = 0)

if __name__ == '__main__':
    #vars
    dungeonChoices, dungeonNames, startTexts, itemDicts, itemDict, dungeons = [], [], [], [], {}, {}
    mainPath = os.path.dirname(os.path.realpath(__file__))

    #load dungeon dict
    loadDungeons()

    #config getting
    try:
        c = Config()
    except Exception as e:
        messagebox.showerror('Error', 'Config load error: ' + str(e))
        exit()

    manualSort = c.getManual()

    #tk and styling
    window = Tk()
    window.title('Infographic')
    window.resizable('FALSE', 'FALSE')
    window.configure(background = '#252a2d')
    window.option_add('*TCombobox*Listbox.background', '#131419')
    window.option_add('*TCombobox*Listbox.foreground', '#dddddd')
    window.option_add('*TCombobox*Listbox.selectBackground', '#4d6f8c')

    #geometry managing
    maxX = window.wm_maxsize()[0]
    maxY = window.wm_maxsize()[1]

    style = Style()
    style.theme_use('clam')
    
    defaultFont = font.nametofont("TkDefaultFont")
    defaultFont.configure(size = int(maxX/192)) #10 on 1080p
    largerDefaultFont = defaultFont.copy()
    largerDefaultFont.configure(size = int(maxX/96)) #20 on 1080p
    largestDefaultFont = defaultFont.copy()
    largestDefaultFont.configure(size = int(maxX/64)) #30 on 1080p

    style.configure('.',
        background = '#252a2d',
        foreground = '#dddddd',
        fieldbackground = '#131419',
        bordercolor = '#252a2d',
        darkcolor = '#131419',
        lightcolor = '#252a2d',
        insertcolor = '#dddddd',
        borderwidth = 1,
        arrowcolor = '#dddddd',
        troughcolor = '#42444e')

    style.configure('TButton',
        background = '#131419',
        relief = 'flat')

    style.configure('TScrollbar',
        background = '#252a2d',
        gripcount = 0)

    style.configure('options.TLabel',
        font = largestDefaultFont)

    style.configure('manual.TCheckbutton',
        font = largerDefaultFont,
        background = '#131419',
        padding = 5,
        indicatorsize = int(maxX/128)) #15 on 1080p

    style.configure('dungeons.TButton',
        font = largerDefaultFont)

    style.map('TScrollbar', background = [('active', '#42444e')])
    style.map('TCombobox', background = [('pressed', '#42444e')], bordercolor = [('focus', '#6c9cc4')])
    style.map('TButton', background = [('active', '#42444e')], foreground = [('disabled', '#131419')])
    style.map('dungeons.TButton', background = [('active', '#eeebe7')], foreground = [('active', '#252a2d')])
    style.map('TCheckbutton', foreground = [('active', '#252a2d')])

    frame = Frame(window)
    buttonFrame = Frame(window)
    startButton = Button(buttonFrame, text = 'Go!', command = genInfographic, width = 5)
    startButton.grid(column = 2, row = 0, pady = int(maxY/54)) #20 on 1080p
    addButton = Button(buttonFrame, text = '+', command = addGraphic, width = 3)
    remButton = Button(buttonFrame, text = '-', command = remGraphic, width = 3)
    optionsButton = Button(window, text = '⚙', width = 3, command = optionsMenu)
    optionsButton.grid(column = 0, row = 2, sticky = 'w', padx = int(maxX/76.8)) #25 on 1080p

    #bg is currently disabled
    #bgEntry = Entry(frame, font = defaultFont)
    #bgEntry.insert('end', 'BG Link (empty for transparent)')
    #bgEntry.grid(column = 1, row = 0, sticky = 'e', ipadx = int(maxX/32)) #60 on 1080p

    #initiate
    addGraphic()
    startTexts[0].insert('1.0', "Press 'Go!' for instructions." )

    #dictionary reading
    try:
        itemDicts = [None] * len(os.listdir(mainPath + '\\Dictionaries'))
    except Exception:
        messagebox.showerror('Error', '\"Dictionaries\" folder not found.')
        exit()

    #font loading
    try:
        normalFont = ImageFont.truetype(mainPath + '\calibrib.ttf', 26)
        #smallFont = ImageFont.truetype(mainPath + '\calibrib.ttf', 12)
    except:
        messagebox.showerror('Error', 'Font load error.')

    window.mainloop()