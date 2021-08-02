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
    #works by counting quotations, should probably be changed/updated to something faster
    dict = {}
    qs = 0
    tbw, tbw2 = '', ''
    for i in range(len(f)):
        if f[i] == '\"':
            qs += 1
            continue
        if qs == 1:
            tbw = tbw + f[i]
        elif qs == 3:
            tbw2 = tbw2 + f[i]
        elif qs == 4:
            dict[tbw] = tbw2
            tbw, tbw2 = '', ''
            qs = 0
    return dict

def genInfographic():
    #instructions
    if startTexts[0].get('1.0', 'end') == "Press 'Go!' for instructions.\n":
        messagebox.showinfo('Instructions',
            "1. Choose a dungeon with the drop-down menu or type it.\n2. Input a background link where prompted, or leave it blank\n    for an empty background.\n3. Type or paste the name of each item that you want\n    displayed. Spelling counts, if you can't figure out the\n    correct spelling, see the dictionaries folder for a list of all\n    valid keys.\n4. The '+' amd '-' buttons alter the amount of infographics\n    generated. You can have up to 3 at once.\n5. Once all items are inputted and all desired fields are\n    fulfilled, press 'Go!' to choose a folder to save to and\n    generate the infographic.\n6. For instructions on priority sorting and options, see the\n    readme file.")
        return

    #vars
    dungeonList, dungeonLinkList, itemLists, missingSet, notMissingSet = [], [], [], set(), set()
    length = len(dungeonChoices)
    rows, x, y = 0, 0, 0

    #reload dicts in case options have changed
    loadDicts()
    if manualSort:
        global itemDict
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
                dungeonLinkList.append('//upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png')
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
    yaxis = (length * 60) + (rows * 40) + 20

    #image start
    source = Image.new('RGBA', (xaxis, yaxis), (255, 255, 255, 0))
    draw = ImageDraw.Draw(source)

    #try bg link, ignore if invalid
    try: 
        bg = Image.open(requests.get(bgEntry.get(), stream=True).raw).resize((xaxis, yaxis), resample = Image.BOX).convert('RGBA')
        source.alpha_composite(bg, (0, 0))
    except:
        pass

    #the girth
    for i in range(length):
        #get dungeon pic, resize if needed, paste
        dungeonImage = Image.open(requests.get('https:' + dungeonLinkList[i], stream=True).raw).convert('RGBA')
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

        #manual sort option
        if manualSort == True:
            for j in range(len(itemLists[i])):
                try:
                    #open, resize, convert, paste
                    itemImage = Image.open(requests.get('https:' + itemDict[itemLists[i][j]], stream=True).raw).resize((40, 40), resample = Image.BOX).convert('RGBA')
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
                    
                    #missing handling
                    missingSet.add(itemLists[i][j])
                    continue

        #autosort
        else:
            for listIndex in range(len(itemDicts)):
                for j in range(len(itemLists[i])):
                    try:
                        #open, resize, convert, paste, add to non-missing
                        itemImage = Image.open(requests.get('https:' + itemDicts[listIndex][itemLists[i][j]], stream=True).raw).resize((40, 40), resample = Image.BOX).convert('RGBA')
                        source.alpha_composite(itemImage, (x, y))
                        notMissingSet.add(itemLists[i][j])

                        if xChangeCount != 9:
                            x+= 40
                            xChangeCount+= 1
                        else:
                            x-= 360
                            y+= 40
                            xChangeCount = 0
                    except Exception as e:
                        continue

            #missing handling
            for item in itemLists[i]:
                if item not in notMissingSet:    missingSet.add(item)

        #move xy
        x = 0
        y+= 50

    #signature
    #draw.text((297, yaxis-12), 'Made by Flaps#9562', (192, 192, 192, 255), smallFont)

    #missing handling
    if len(missingSet) > 0:
        itemErrorText = ''
        for i in missingSet:
            itemErrorText = itemErrorText + i + ', '
        messagebox.showerror("Error", 'Item(s) missing at: ' + itemErrorText + '\n\nTo see all valid item keys go to https://www.tinyurl.com/7b7bs4c')

    #save dialog
    finalPath = filedialog.asksaveasfilename(confirmoverwrite = True, initialdir = mainPath, initialfile = 'infographic.png', filetypes = [('PNG', '*.png')])
    if finalPath == '':
        messagebox.showwarning("Warning", 'File not saved.')
        return

    #save
    source.save(finalPath.rstrip('.png') + '.png', 'PNG')

def loadDicts():
    global itemDicts, itemDict
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
        try:
            itemDicts, itemDict = [], {}
            for dictFile in os.listdir(mainPath + '\\Dictionaries'):
                with open(mainPath + '\\Dictionaries\\' + dictFile, 'r', encoding = "utf-8") as f:
                    itemDict = {**itemDict, **(genDict(f.read()))}
        except Exception as e:
            messagebox.showerror('Error', 'Unknown dictionary error: ' + str(e))
            exit()
        
        messagebox.showerror('Error', 'Dictionary Error: ' + str(e) + '\n\nUsing manual sorting.')

def optionsMenu():
    #global
    global manualSort

    #options tk
    options = Toplevel()
    options.title('Options')
    options.geometry('500x360')
    options.resizable('FALSE', 'FALSE')
    options.configure(background = '#252a2d')

    optionsLabel = Label(options, text = 'Options:', style = 'options.TLabel')
    optionsLabel.pack(pady = 30)

    manualCheck = Checkbutton(options, text = 'Manual Sorting', style = 'manual.TCheckbutton', command = c.changeManual)
    if manualSort:    manualCheck.state(('selected',))
    manualCheck.pack(pady = 30)

    creditLabel = Label(options, text = 'Made by Flaps#9562', style = 'options.TLabel')
    creditLabel.pack(pady = 30)

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
        height = 25,
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

    window.geometry('{}x770'.format(length*565+50))

    for i in range(length):
        dungeonChoices[i].grid(column = i*2, row = 0, pady = 20, columnspan = 2, sticky = 'w', ipadx = 55)
        startTexts[i].grid(column = i*2, row = 1, columnspan = 2, ipady = 100)

    remButton.grid(column = 1, row = 0)
    addButton.grid(column = 3, row = 0)

    if length == 1:
        remButton.grid_remove()
    elif length == 3:
        addButton.grid_remove()

    frame.grid(row = 0, column = 0, padx = 25)
    buttonFrame.grid(row = 2, column = 0)

if __name__ == '__main__':
    #vars
    dungeons = {'Pirate Cave': '//i.imgur.com/OqzVQuc.png', 'Forest Maze': '//static.drips.pw/rotmg/wiki/Environment/Portals/Forest%20Maze%20Portal.png', 'Spider Den': '//i.imgur.com/up93OlG.png', 'Snake Pit': '//i.imgur.com/lHeUeoK.png', 'Forbidden Jungle': '//static.drips.pw/rotmg/wiki/Environment/Portals/Forbidden%20Jungle%20Portal.png', 'The Hive': '//static.drips.pw/rotmg/wiki/Environment/Portals/The%20Hive%20Portal.png', 'Magic Woods': '//i.imgur.com/mvUTUNo.png', 'Sprite World': '//i.imgur.com/LO1AmVL.png', 'Candyland Hunting Grounds': '//static.drips.pw/rotmg/wiki/Environment/Portals/Candyland%20Portal.png', 'Ancient Ruins': '//i.imgur.com/d7MSK2x.png', 'Cave of a Thousand Treasures': '//static.drips.pw/rotmg/wiki/Environment/Portals/Treasure%20Cave%20Portal.png', 'Undead Lair': '//i.imgur.com/pR8Dgth.png', 'Abyss of Demons': '//i.imgur.com/1NziBak.png', 'Manor of the Immortals': '//static.drips.pw/rotmg/wiki/Environment/Portals/Manor%20of%20the%20Immortals%20Portal.png', "Puppet Master's Theatre": '//i.imgur.com/2JZNslO.png', 'Toxic Sewers': '//i.imgur.com/4c03WNV.png', 'Cursed Library': '//i.imgur.com/Kcb7YfX.png', 'Haunted Cemetery': '//i.imgur.com/n5HqTlm.png', 'The Machine': '//i.imgur.com/eFihsCs.png', 'The Inner Workings': '//i.imgur.com/6RdEOw1.png', 'Mad Lab': '//i.imgur.com/eJNrKaO.png', 'Deadwater Docks': '//i.imgur.com/CjceJZ1.png', 'Woodland Labyrinth': '//i.imgur.com/4dn3rcG.png', 'The Crawling Depths': '//i.imgur.com/UfTq4bg.png', 'Parasite Chambers': '//i.imgur.com/xldgpdz.png', 'Beachzone': '//static.drips.pw/rotmg/wiki/Environment/Portals/Beachzone%20Portal.png', 'The Third Dimension': '//i.imgur.com/qlPofut.png', "Davy Jones' Locker": '//i.imgur.com/xpDdz03.png', 'Mountain Temple': '//i.imgur.com/SY0Jtnp.png', 'Lair of Draconis': '//static.drips.pw/rotmg/wiki/Environment/Portals/Consolation%20of%20Draconis%20Portal.png', 'Ocean Trench': '//static.drips.pw/rotmg/wiki/Environment/Portals/Ocean%20Trench%20Portal.png', 'Ice Cave': '//static.drips.pw/rotmg/wiki/Environment/Portals/Ice%20Cave%20Portal.png', 'Tomb of the Ancients': '//static.drips.pw/rotmg/wiki/Environment/Portals/Tomb%20of%20the%20Ancients%20Portal.png', 'Fungal Cavern': '//i.imgur.com/OElJTuL.png', 'Crystal Cavern': '//i.imgur.com/BHwk26f.png', 'The Nest': '//i.imgur.com/WQ95Y0j.png', 'The Shatters': '//static.drips.pw/rotmg/wiki/Environment/Portals/The%20Shatters.png', 'Lost Halls': '//i.imgur.com/uhDj0M5.png', 'Cultist Hideout': '//i.imgur.com/fg2BtCm.png', 'The Void': '//i.imgur.com/TNZ8fOw.png', 'Malogia': '//i.imgur.com/JaSkGXC.png', 'Untaris': '//i.imgur.com/rlkbOzV.png', 'Forax': '//i.imgur.com/j2CMfTA.png', 'Katalund': '//i.imgur.com/YDfY8FU.png', "Oryx's Chamber": '//i.imgur.com/8KBE64D.png', 'Wine Cellar': '//i.imgur.com/ozNWFFN.png', 'Janus the Doorwarden': '//i.imgur.com/ZfIKmgX.png', "Oryx's Sanctuary": '//i.imgur.com/NRwP3hq.png', 'Lair of Shaitan': '//static.drips.pw/rotmg/wiki/Environment/Portals/Lair%20of%20Shaitan%20Portal.png', "Puppet Master's Encore": '//static.drips.pw/rotmg/wiki/Environment/Portals/Puppet%20Encore%20Portal.png', 'Cnidarian Reef': '//i.imgur.com/qjd04By.png', 'Secluded Thicket': '//i.imgur.com/8vEAT8t.png', 'High Tech Terror': '//i.imgur.com/Y9LAhlJ.png', 'Heroic Undead Lair': '//i.imgur.com/31NX1Ld.png', 'Heroic Abyss of Demons': '//i.imgur.com/zz6D2lz.png', 'Battle for the Nexus': '//static.drips.pw/rotmg/wiki/Environment/Portals/Battle%20Nexus%20Portal.png', "Belladonna's Garden": '//i.imgur.com/VTXGPSy.png', 'Ice Tomb': '//static.drips.pw/rotmg/wiki/Environment/Portals/Ice%20Tomb%20Portal.png', 'Rainbow Road': '//static.drips.pw/rotmg/wiki/Environment/Portals/Rainbow%20Road.png', "Santa's Workshop": '//i.imgur.com/U7uy7oD.png', 'Mad God Mayhem': '//i.imgur.com/yRv9Dve.png', 'Tutorial': '//static.drips.pw/rotmg/wiki/Environment/Portals/Dungeon%20Portal.png', "Oryx's Kitchen": '//static.drips.pw/rotmg/wiki/Environment/Portals/Dungeon%20Portal.png', 'The Realm': '//static.drips.pw/rotmg/wiki/Environment/Portals/Nexus%20Portal.png', '': '//upload.wikimedia.org/wikipedia/commons/8/89/HD_transparent_picture.png'}
    dungeonNames = sorted(dungeons.keys())
    dungeonChoices, startTexts, itemDicts, itemDict = [], [], [], {}
    mainPath = os.path.dirname(os.path.realpath(__file__))

    #config getting
    try:
        c = Config()
    except Exception as e:
        messagebox.showerror('Error', 'Config load error: ' + str(e))

    manualSort = c.getManual()

    #tk and styling
    window = Tk()
    window.title('Infographic')
    window.resizable('FALSE', 'FALSE')
    window.configure(background = '#252a2d')
    window.option_add('*TCombobox*Listbox.background', '#131419')
    window.option_add('*TCombobox*Listbox.foreground', '#dddddd')
    window.option_add('*TCombobox*Listbox.selectBackground', '#4d6f8c')

    style = Style()
    style.theme_use('clam')
    
    defaultFont = font.nametofont("TkDefaultFont")
    defaultFont.configure(size = 10)
    largerDefaultFont = defaultFont.copy()
    largerDefaultFont.configure(size = 20)
    largestDefaultFont = defaultFont.copy()
    largestDefaultFont.configure(size = 30)

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
        font = largestDefaultFont,)

    style.configure('manual.TCheckbutton',
        font = largerDefaultFont,
        indicatorsize = 15)

    style.map('TScrollbar', background = [('active', '#42444e')])
    style.map('TCombobox', background = [('pressed', '#42444e')], bordercolor = [('focus', '#6c9cc4')])
    style.map('TButton', background = [('active', '#42444e')])
    style.map('TCheckbutton', foreground = [('active', '#252a2d')])

    frame = Frame(window)
    buttonFrame = Frame(window)
    startButton = Button(buttonFrame, text = 'Go!', command = genInfographic, width = 5)
    startButton.grid(column = 2, row = 0, pady = 20)
    addButton = Button(buttonFrame, text = '+', command = addGraphic, width = 3)
    remButton = Button(buttonFrame, text = '-', command = remGraphic, width = 3)
    optionsButton = Button(window, text = '⚙', width = 3, command = optionsMenu)
    optionsButton.grid(column = 0, row = 2, sticky = 'w', padx = 25)

    bgEntry = Entry(frame, font = defaultFont)
    bgEntry.insert('end', 'BG Link (empty for transparent)')
    bgEntry.grid(column = 1, row = 0, sticky = 'e', ipadx = 60)

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
