# RotMG-InfographicMaker
RotMG Infographic Maker generates infographics from item text given in Realm of the Mad God blogposts.

# Requirements
All files in the .zip must be in the same folder as application except Infographics (it is there for easy storage of generated infographics).

An internet connection is required.

This has not been tested outside of Windows 10.

# Priority Sorting and Dictionary Modifying
Dictionary files must start with a number followed by an exclamation mark (!). The number determines the priority of the items in the dictionary file. The first items rendered by the infographic maker come from the file that starts with 1!, then 2!, then 3!, and so on. New dictionary files can be added and others can be removed, I try to keep the files in the .zip updated to contain all the items from the game.

To add or modify a dictionary entry, make sure you follow the format:

"Item Name" src="//link"

The link must not have any "https:" or "http:". The infographic maker is case-sensitive so it is recommended that you capitalize the item name as a title.

# Manual Sorting
The options button and the config.txt (use 1 or 0) contain an option for manual sorting. If it is on, the item will be sorted as given in the text box.

# Note
Python file is the source code. If you want to run it you will have to put it in place of the .exe file in the .zip or in an identical folder to the .zip.

# Instructions on using the app can be found in the app
