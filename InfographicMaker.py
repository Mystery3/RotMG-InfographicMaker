#encoding:utf-8
import asyncio
import httpx
import os
import re
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog, tkinter.font, tkinter.messagebox, ttkwidgets.autocomplete
from io import BytesIO
from math import ceil
from PIL import Image, ImageDraw, ImageFont

MAIN_PATH = os.path.dirname(os.path.realpath(__file__)).replace('\\', '/')
FONT = ImageFont.truetype(f'{MAIN_PATH}/calibrib.ttf', 26)

#for managing text boxes, comboboxes, item lists, dungeon lists, and for calling infographic commands
class Graphic:
    def __init__(self, root: tk.Tk, frame: tk.Frame, dungeons: list, manual: ttk.Checkbutton, dungeon_dict: dict, items_dict: dict):
        self._root = root
        self._frame = frame
        self._dungeons = dungeons
        self._manual = manual
        self._dungeon_dict = dungeon_dict
        self._items_dict = items_dict
        self.dungeon_boxes = []
        self.text_boxes = []

    def infographic(self):
        asyncio.run(stitch_infographics(self._dungeon_dict, self._items_dict, [box.get() for box in self.dungeon_boxes], [items.get('0.0', 'end').splitlines() for items in self.text_boxes], ('selected' in self._manual.state())))

    def update_window(self):
        for box in enumerate(self.dungeon_boxes):
            box[1].grid(row=0, column=box[0], padx=5, pady=5)
        for box in enumerate(self.text_boxes):
            box[1].grid(row=1, column=box[0], padx=5, pady=5)

    def add_graphic(self):
        if len(self.dungeon_boxes) == 4:
            return
        self.dungeon_boxes.append(ttkwidgets.autocomplete.AutocompleteCombobox(self._frame, self._dungeons))
        self.text_boxes.append(tk.Text(self._frame, width=35, height=25, font=TK_FONT, borderwidth=1, relief='flat', highlightthickness=2, highlightbackground='#252a2d', background='#36393e', foreground='#dddddd', highlightcolor='#6c9cc4', selectbackground = '#4d6f8c', insertbackground = '#dddddd'))
        self.update_window()

    def rem_graphic(self):
        if len(self.dungeon_boxes) == 1:
            return
        self.dungeon_boxes.pop().destroy()
        self.text_boxes.pop().destroy()
        self.update_window()

    def update_dicts(self):
        self.dungeons, self._dungeon_dict = load_dungeons()
        self._items_dict = load_dictionaries()

def load_dungeons() -> tuple[list, dict]:
    try:
        base_dungeon_dict = {}
        final_dungeon_dict = {}

        #get lines from dungeon file
        with open(MAIN_PATH + '/dungeons.txt', 'r', encoding = 'utf-8') as dungeons:
            dungeon_lines = dungeons.readlines()

        #put names and links into dictionary
        for line in dungeon_lines:
            match = re.match(r'(.+)\s\|\s(.+)', line) #split at " | "
            base_dungeon_dict[match.group(1)] = match.group(2)

        dungeon_names = sorted(base_dungeon_dict)

        #sort dictionary (hopefully for intra-dictionary sorting?)
        for dungeon in dungeon_names:
            final_dungeon_dict[dungeon] = base_dungeon_dict[dungeon]

        return (dungeon_names, final_dungeon_dict)
        
    except Exception as e:
        tkinter.messagebox.showerror('Error', f'Dungeons load error: {e}')
        exit()

def load_dictionaries() -> dict:
    try:
        files = []
        items_dict = {}

        #get dictionary files
        base_files = os.listdir(f'{MAIN_PATH}/Dictionaries')

        #sort by int before "!"
        for filename in base_files:
            match = re.match(r'([0-9]+)!(.+)', filename) #split at "!"
            files.insert(int(match.group(1)) - 1, match.group(0))

        #create dictionary for items
        for filename in files:
            with open(f'{MAIN_PATH}/Dictionaries/{filename}', 'r', encoding='utf-8') as items:
                for line in items.readlines():
                    match = re.match(r'(.+)\s\|\s(.+)', line) #split at " | "
                    items_dict[match.group(1)] = match.group(2)

        return items_dict

    except Exception as e:
        tkinter.messagebox.showerror('Error', f'Dictionary load error: {e}')
        exit()

async def get_image(url: str, count: str=None) -> Image:
    async with httpx.AsyncClient() as client:
        content = await client.get(url)
        
    image = Image.open(BytesIO(content.content)).convert('RGBA').resize((40, 40), resample=Image.BOX)

    #draw count with black outline
    if count != None:
        image_draw = ImageDraw.Draw(image)
        image_draw.text((1, 1), count, (0, 0, 0, 255))
        image_draw.text((3, 1), count, (0, 0, 0, 255))
        image_draw.text((3, 3), count, (0, 0, 0, 255))
        image_draw.text((1, 3), count, (0, 0, 0, 255))
        image_draw.text((2, 2), count, (255, 255, 255, 255))

    return image

async def generate_infographic(dungeon_dict: dict, items_dict: dict, dungeon: str, items: list[str], manual: bool) -> Image:
    #dungeon image
    try:
        if dungeon in dungeon_dict.keys():
            dungeon_image = Image.open(BytesIO(httpx.get(dungeon_dict[dungeon]).content)).convert('RGBA')
        else:
            dungeon_image = Image.new('RGBA', (56, 56), (0, 0, 0, 0))
    except Exception as e:
        tkinter.messagebox.showerror('Dungeon Image Error', f'Dungeon Image Error: {e}')
        return

    #resize if too big to 56x56
    if dungeon_image.size[0] > 60 or dungeon_image.size[1] > 60:
        dungeon_image = dungeon_image.resize((56, 56), resample=Image.BOX)

    #manage missing items
    missing_items = [item for item in items if item not in items_dict.keys()]
    items = [item for item in items if item not in missing_items]
    if len(missing_items) != 0:
        tkinter.messagebox.showwarning('Missing Items', f'Missing Items: {str(missing_items)}\nMissing items will be ignored.')

    #sort by dictionary order if not manual
    used_items = []
    if not manual:
        for item1 in items_dict.keys():
            for item2 in items:
                if item1 == item2:
                    used_items.append(item1)
    else:
        used_items = items

    #create list of tasks for asyncio
    get_image_funcs = []
    for item in used_items:
        #detect "x##" for token numbers
        count = None
        match = re.match(r'[^0-9]+x ?([0-9]+)', item) #detect not digits until "x##"
        if match != None:
            count = match.group(1)

        get_image_funcs.append(asyncio.create_task(get_image(items_dict[item], count)))

    #grab all item images
    try:
        images = await asyncio.gather(*get_image_funcs)
    except Exception as e:
        tkinter.messagebox.showerror('Image Load Error', f'Image Load Error: {e}')
        return

    #resize all images
    for image in images:
        image.resize((40, 40), resample=Image.BOX)

    #image base and draw dungeon header
    image_base = Image.new('RGBA', (400, (ceil(len(items) / 10) * 40 + 70)))
    image_base_draw = ImageDraw.Draw(image_base)

    image_base.alpha_composite(dungeon_image, (0, 0))
    image_base_draw.text((60, 17), dungeon, (192, 192, 192, 255), FONT)
    
    #draw items
    current_item = 0
    for y in range(ceil(len(items) / 10)):
        for x in range(10):
            image_base.alpha_composite(images[current_item], (x * 40, 60 + y * 40))
            current_item+= 1
            if current_item == len(images):    break
        else:    continue #continue if previous loop wasn't broken out of
        break #break if previous loop was broken out of

    return image_base

async def stitch_infographics(dungeon_dict: dict, items_dict: dict, dungeons: list[str], items: list[list[str]], manual: bool) -> None:
    #prompt for save path, return if cancelled
    save_path = tkinter.filedialog.asksaveasfilename(confirmoverwrite = True, initialdir = MAIN_PATH, initialfile = 'infographic.png', filetypes = [('PNG', '*.png')])
    print(save_path)
    if save_path == '':
        tkinter.messagebox.showwarning('Warning', 'File not saved.')
        return

    #create tasks for each infographic (length is based on amount of dungeons)
    infographic_funcs = []
    for i in range(len(dungeons)):
        infographic_funcs.append(asyncio.create_task(generate_infographic(dungeon_dict, items_dict, dungeons[i], items[i], manual)))

    #grab all infographics (at once!)
    infographics = await asyncio.gather(*infographic_funcs)

    #grab total height and create new base
    total_height = sum([image.size[1] for image in infographics]) - 10
    image_base = Image.new('RGBA', (400, total_height), (0, 0, 0, 0))

    #stitch images
    current_height = 0
    for image in infographics:
        image_base.alpha_composite(image, (0, current_height))
        current_height+= image.size[1]

    #save image
    image_base.save(save_path.removesuffix('.png') + '.png', 'PNG')
    tkinter.messagebox.showinfo('Saved', 'Infographic saved successfully.')

def main():
    global TK_FONT
    dungeons, dungeon_dict = load_dungeons()
    items_dict = load_dictionaries()

    ##################################################################################################################
    #window setup
    root = tk.Tk()
    root.title('Infographic')
    icon = tk.PhotoImage(data=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00 \x00\x00\x00 \x08\x06\x00\x00\x00szz\xf4\x00\x00\x00\x01sRGB\x01\xd9\xc9,\x7f\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\nOIDATx\x9c\x85Wk\x8c\\e\x19~\xce\xf9\xbes\x9b\xdb\xee\xec.\xbdm\xafK\xdb\xa5\xdbV\x84B\xb9T\xa0\xa2\x82)\xdaX \x11\rB\x0c$h\xd0\xf8\xc3\x10\xc0\x18\x7f\x88F\xfda\x8c\x18\x82\x08\x04bH@\xa3\xe0%\x98R\xa9\xa4)\xb6\x14\xb6\xdb\xb2Ko\x0b\xdb\xebnw\xb6\xdb\xee\xec\xee\\\xcf\x9c\x9b\xcfw\xe6\xcc\xb6\x10\x8d\xb3\xf9vf\xbe\xf9.\xef\xfb\xbc\xcf\xfb\xbe\xcf\x91W\xcf_\x10\x01\x11"M\x83\x1e\x04\xb3z\x88\x1c\'\x10h\x11\xb4H\x83\xe0|\xa8\x03\xa1\xa6\x83\x1f\x11E\x9c\xe7_k\x0f\xd4b\xfek\xfe\x86\xf87n\x83\x1e\x86\xcd\xdf8B\xfe\xe9|\xd7\xd5RM\x9b\r\xa4\xc8\xb5\xce\x91F\xf3\x04\xae\x8a\x90\xf6\xc2\\\x18\x050yy\xd6\x8cx\xb1\xc4\x94\xa7\xc3\ry(-k]\x8dK\xf6\xe0\xa2\r-\xb3\xa0\x85\xcd\xdfu\xbe\xb7\xf3\xe6\xb4\xf4\xe0\xba\x11*\x812N\xe4*B\x9f;G\x9aa\x98\x1c\xa7\xa1=p\xf1\xe9%\x12\xd7\xdc\xb8\x12k\xb7\xdc\x86\xd7\x9f\x7f\r\xbf\xdf3\x01\xa1\x8b\x18\x8d(\xf1\xe4\xa2\t4(\xf9>g\x14\xe7B\x85\x00=\x0cyvJ\xf8x\xfc\xf1;`\xfa\x1a\xf6\xffk/\xfe\xbd\xaf\x80\xc3\x91\x98;G:A8k\x06\xc8Y\xbe\x8b\xcf\xad\x16\xf8\xda\x93?\xc6\x8e\xf1\x85\xa8/\xb6Q\x99x\x0e\x99 \x8c\x0fU\x90\xa9w=\xb9h\xee\xde\x96!-\xefU\xf8\xd4\xba(\x8c\x8d\xf3\xeaD\xb4\x16bt\xf3#X\xd5w\x14\xd7]\xfb\x12\x9e\xfc\xd5[(\x84\x0e\xaaB+K\x871w|\x0f\xeb\xda\x1b\xb8\xef\xa7\x8f\xe3\x99\xf7$\xc6\x1a\xe7\xb0\xf6\xd4\xbb8yl\x16\xb9\xd0F\xa0Pb\x905\r\x9f\xb8\xf6\xa2\xef\xda%F\xcd\x85\x84F\x9bA\x84\x81\xbf\xefF\xbe\xe7\x16<\xb3\xfd8\x1e\xfe\xfa\x03\xb8wl\x1c/\xbe4\x8c\xf3\xb02\xd2\xa2\x87\xcb\xe0\xe2\xfeG\xef\xc4[\xfe\x958~t\x17n\xdfz\x03\xa6^9\x84\xb0\x1e\xa2K\xaf\x13\xcff\xcc$\xfe\xcf+\xb1$&1\x9a\x84\r\xc8\x83\xb1\xc3\xe7\xf0\xd9\xca)\x1cX\xbb\x1c\xdbw\x1f\xc7C\x0f>\x86/\x1ez\x18\x7f9X\x87l\'\xf4w\xdf\xb3\x1a\xc5\x8d\xf7b\xdfk\xef\xa2c\xf1\x02\\^=\x8b\xf7v\x1d\xc1\xa6U]\xe8\xbb\xeb3\xbc\xb8N\xef\t+3!\x86!\x1e\t\x06\x1f\x83\xe5"EU\xe6D\x8e\x83\xd2\xf0\x04\xf6\xbd\xf0&\xa6v\xedA\xef\xd6\xef\x90\x07\x1f\xe2\xd5\x03]x\xe0g?\xc4\xc8W\x1f\x83\xbcn\xa5\x8de\xdf~\x0c\xcf\xbey\x0cQc\x16\x9d+\x97\xc0y\x7f\x17f\xc6j\xd8\xf6\xc4\xdd8w\xd3\x16\x8c\x1f\x1cB*\xe3\x80h\xc2\'\x19\xa5eA\xe7pI\x0f_7\xa0rI3L\x94k.*\x1c\xa6i\xc6\xc6\x86N\x06\x1bn\x95X\xf6\xe6^\x9c\xd8s\x10K\xb7L\xe2\x00\xf7\x9d94\x847\x16\xde\x82\xad\xdf\xbb\x0br\xf37\xb7a\xd7\xf9.\x04\xd3\x83h\xf8\x01\x96\xda\x1e&\xf7\x0e\xb2\x18D\x10\xbc\xf1\x9d\x97\xff\x8a\xe2\xc9\x13\xb0yI\xbd\xe11\x0f4X)\x07\x910P\xf6#xLU\xcd\xb2\x11I\x0bg\xa7\xa61>U\x84e\x181\xfc\xd5Z\x03\xf7\x7f\xe5z\xac^\xb1\x1c\x1f\xed\x1c\xc2\xfa\xa3\x83\xb0:W\xc0,\x151\xf4\xceA\xf4~\x9e\x06`\xfd\xad\x18\xddw\x10\xd9\x8c\x8d\xaaf\xe2\xaa`\x0cg?\x1c\xc4\xc2\xbc\x86\x86)1\xc1C\xb3\xb96d\xd2\x0e\x0c/\x80\xeb\x87pUq\x11\xbc\xd8\x960\xe9\xb9BC\xd5\x8cv\x86C8\x16LI\xb60\x0b\xa6g\xcb\x98\x85\x85\xae6\x03\x05\xee1O\xeeG\xdf\xe6\r\xf8`\xff\x04:;S\x18\x18<\x01\xf9a\x81\xf1\xf5\xaa\x90RGGZ\xa2\xc4\x94Y\xbf\xed6x\xb5\xf3\x18\xa9\x06\x18\x1d\x9b@\xef\x92.X\xe94"\x1aP\xae\xd4Q(\xce\x12r\x8b\xd0\x93\xe5DB\x92q\x9e\xe7!\xd058\\\'\xf8\x8e  \x01g0zf\x12\xdd=\x97\xa1\xe3Kk \xd7\\\x0bQ\x9cA\x8a\x08fl\x1b\xb3U\x17\xf2\xcc\x99\xb3p\xb2iHZ\xdfn\x19x\xaf\x12\xe2X\xdf6Tg&152\x0c[\x04\x08\x89@\x9d\xf1\xd4\x0cU\xb5\to\x83\xf9n\xd2\x00\xa2\xa0\xf3B\xd3I7\x0bK\xa3\x81\xd0\xf7c\x03\xdc0@\xba=\x07Q*\xe1\xc5t\x0f\xacM\x1b\x91Iu\xa3\xe1\x96\xb1x\xe1<\xd4]\x97\x05\x8b\x95\xb00=\x83l[\x0e6\xe3h\xa8z\xcf\x0bG.L\xe1\xc4\xb9i\xa4x\x91_\xaa\xa0\xfc\xcf}(\xb9i\x9c\xb5B\x04\xd2%\xf3|f\xa6\xaax\x1aJB@\x12\x05\x95\x0c\x1e\xebE\xcd#w\xaa\x12\x8b\x88\x80l\x8b\xd0\xe8\xbb\x1c\xfd\x17*p"\x07\x1b\xb3\x8dx\x9f"\xb3\xe2[\xb9\\\x86\xec\xb9\xa2\x0f\xc3G\x0f\xc30j\xc8\x87\xed0\x18\nF\x14\x1d"D\xfb\x82.\xbc\xbfW\xc7\x9d\xc7G\xd0\xd3\t\xec\x1c\x03\xf6\x90\x84\xfb\x99hg\xe9p[\x92r\r\x8e*G/\xc7&\x8e\x9b8n\xe0\x8f\xbb\n\x02o\xf4,E\xfe2A\xc8\r\x18\xac\'3\xb5z\\#&&\xc8\x83\x8eN\xc8\xa1\xd3\xa3\xb8\xf9\xe6[p~|\x1c\x85B\x01\x8efc\xb40\x81(\xf0agr({\x02\x16\xbd[\xfd(\x07\x0f}h\xa7\x81\xfe\x03\x02\xdb?\x02\x9e\x89|Li\x01V\x93\xcb\xdf5\x05n\xea\xa3\x11W{\xc0\x17|ZK\xa3\x9e\xb5P\xaf\xd4`\xb0\xf9\x14\xa7\xa7q>\x97\x8b\xfb\x83 I\xaf\xbdq\x13\xce\x11}9\xf4\xa7?\xe0\xe0\xc8il\xd9t\r\xd6\xac[\x87I\x1aQw\x1bL%\x81\xf2L\tn0\x8d\'\xe8\xe6U/\x90\xe5\x0f\x13\xfa{\x1a\xd8\x98\x01\xdaG\xd2x\x9aM%\xa2\x01\x99P\xe2A\x9b~mex\xae\xa4{\x03\xc0\xde?\n\xfc\x96\xb8\xf4\x14\'\xd1\xf0V\x80\xd0\xb2F\xd4\xd0\xdbK\x9c\x989\xbb\x0f\x1fE\xff[\xbb!\x7f\x94\x9f\xc4\xdf\x8e\xec\xc6o\xde\x1f\xc2\x9a\r\xeb\xb1y\xdd\x15\xe8]\xbd\n\'O\x1c\xc7\xc8\xe930H\xa6\x01\xe6\xf5CG2\xf8\xc6\xf7#t/\x02\x8eM\x01\xbf\x8e\x08\xa5\xee\xa1\x8b!\x19\xd6]\xdcUr\xf0\xad\xa7S\xe8t"\x1c:\xa5\xe3)\x02}\xc1\xaa\xe1z\x92t~6E"\xcfC>\x9f\xc7;\x87\x0ec\xe7\xc0\x07h\xe3\xf9\x8f,$\x07\xfeq\xa8\x82;Vq,\xd1\xf1\x93\xfe~\xfc|\xff \xae\xb9\xbc\x1b\xcbr\x19\x8cML\x02\x8b\x97`\xc3\x82E(0~\xbf(kh\xb3\xda!:*\x98\xdc\xff6\xc9\xa4\n\x91\x0e\x9f\xb0\x9e\xea\xb0\xf0\xdc\x9a\x1b\xe1\x96}\xb8K},2}\xaceVuud\xd1\xcd\xf8\xbf;z\x06\xbf{}\x07\xf4\x8a\x8b\x07\xf2!\xee[1\x85\x1dG\x8b\x90\x17\x1a\x06^=\x12\xa0\xafk\x04O\xad\xec\xc4\xab\xf5y\xf8\xc1\xdb\x03\xb8\xfeS+\x19{\x1dU\x16\x14\x9f\x83z\x04\x81\x15`\x86]s~\xd5\x8b\xdb\xb2"\x9e\x9d\x10\xd0P\n\xc8i\xa0D\xf1\xc1\xba\x18\x1bW!z%\xc2\xee\xd7*\xd8\xde?\x04\xed\xd4)\xfc\xf9\xd6\x85\xa8\x9c\x1e\xc1+\x03\x01\xc6\xaa&K\x89\xd0XR\x05\xfa\xc7I\xbe\x99i\xdc\xdc=\x85\x97\xaf\\\x8e\'\x19\xf7qV2Sk\xa6\x8cjF\xaa-K\xe6\xbeU\xad\xb0\x7f*\xa9uqT\xd8\xd2\x8b\xc5"J\xec~\xccp\x18*;\xd8\x90l\xcf\xc2G\x96\x89\xfb\x97gq\xbbV\xc6\xe0\x81a\x0cN\n\xd6\tU\xc8\xd8W4\xe6\xa5\xc6\xca\xe9S.\x8dW\r\xec\x18\xf6\xf0\xe5yE,1:14]Aw\x96\xa5\x95\x1c\x08\xc3(6"\xa2\x11~\xa3\x11w==\x11"J\xebE\xf4\xd6\xa5\xb7\x82\x1d\xd0\x16&\xd1\x8b`0KT)/\xb1\x9e\xfc\xb2\xd7%\n>\x8e\x9c\xb7\xe12\xd5\xd5\xe5\xaa`\xc9\xb8j\xeaMM\x13RKU\xd9Gk\x84\xa6`4`R\x1fr\xb2\xa9\xf1\xa2\xd6P\xdf\xc3\xf8b\x82\x07\x81\xe6Pk""E\x98\xe2b\xc3^\x08\xc9u\xaa8\xa12\x8bI\xd7fJ;\xe4\x8c\xb2\x98\xb7\t%pt\x1a\x00->H\xc9\xa9HG\xbc\xb9n\x02\xe7f\x18K=9\x98Um\xce\x00\xf5\x99CO\x04\x8aL\x0cP\x1aP\xe3|\xc4PD\xf4<V\x9aZH\'\xa8\x89\xeb$fd\xc3I\x11\xc1rS\xbd\xc6\x0e(Q\x1a\xcb\x085\xa7\xe0\xe5\x9f\xc1\x06\xe3\xd2\x88j\xcdG\x8a\x0c\xb7\xb4D\x9a+\x91\x99\xa8\x1cE8#!\xa0\x91\xa8\x1f\x83\x17\xa9yUhL\x8aX\x93\xab\x1d\x1e\x1cr\xdem\xb8l\xe5!\xd2\x0e\xc5-\xbcD8i\x89\xcaj\xc9j\x15c~\xb2\r\xb5D\x83\xc9\x9a\xde&Y\xe7\xd5<k\xbf\xbaX\x19\xa1\xbcu8R\xad\x8b\x13\x14R<$\xab<S\xc6\xb1kZ\xca\x19\xbd\x19\x06\xc9\xcf\r\xca\xbb\xac\xad\'\x17\xb7\xe4\xbd\x96 \xd0\x92\xd7\x1c)\xa9\x0e\x14\xe8\xd0\x04\xf2\xa6\x11\xc7Uy\x15K-\xbe[,\xa3\x19"\x93\xbb$\x04T\x8d\xc8rs\'E\x8b\xea\xaa\x96*\xe3\x8cQ\x9a\xc6\xdb\xaai\x19:e9\r\xb1\x05O\x8e\x1fS\xe6\x04\xadlj\xb8(~\x9aQF\xa4\xe9\x92\xe5S\x1b\xa8\xf6\x1c?\xe2\xe8q\xecc\xfb8g\xf2{\x8a\x86\x94\x12$\xd4\x01*%\xf3\\\xd3\xc6L\xd0\x89\x9a\xcdu\xaa\x16\xa4\xb8\xd5R\xb4Qde&\xa4M]\x91\x9f\x087SW\xb5\xf0\x8f\t]\x15\x82\xac\x92x\xa4j\x9e\x9b\xf3\xc9\xe3\x16b~4_\x86:\\\x15\x19\x95\xe7J\xa8&\xdd\xb0\x9d\xde*\x19\xa7. \x87\xe3\x91\xe6P\xa1\xf0\xc9\xf2\x88\x9c\xca\x91\x84l1\x94\x14\x82\xc5\x8dU4\x08?a\x00\x0f\xccr&\x0c\x04\xda\xb8)\xa7.\xd6\xf5\x8b\x0b\x14\x01\xf9\xdd\xe0\xbb\n\x81\x97\xd4\x00/\tA&\xce(=\xe6\x85\xc9\xbd\xa9\xd8\x18\r\xbe\xe2\x0bI\x98\xc90<\xa2ip\xeb\xf51\x03\x04\xd3&c\xe9\xa8\x07\x92\x0cV\xf0\x91xA\xb3\n\xb6\x0c\x94\xcaK\x86\xc0N6\xb7\xd2QA-\x99\x82\xd2\x97\x94h\x81Rk\xf1\x83\t\xebg\x9cnU\xf6\x00+O\tghM\xf6\xfe7\x03\x18>\xcc\xcfH\x1ck\xd8\x14\x96\xec\xdb\x8a\xfd\xca\x00\xf5`\x92\x18!\xd4\xa1QR\x88\x80\xa4\x12j\xf1e\x11ua\xa8\x14q\x9c\x8e\xaa\xc0\xb1j\x92X\x94\x03\xa8R\x06\xa5\x14\xaa$\xce\x85\xf2\xff0 \x10Z\xa9\x12\x88l-P\xaa\xc8\x8f\x9f\xef\x04w\xc7\x0f$\xc9\xb3\xb6\xb8\xa4\x12\xb6\x82#\x12\x02\xabb\xa4\'\xe4\xd2\xb5\xe6s\xa22L=%+\x196E\xbdIwJq\xc4\x92\xd7\x7f\x00\x10\x18\xcd\x84;k\x95\xc5\x00\x00\x00\x00IEND\xaeB`\x82')
    root.wm_iconphoto(True, icon)
    root.configure(background = '#36393e')

    style = ttk.Style()
    style.theme_use('clam')

    TK_FONT = tkinter.font.nametofont("TkDefaultFont")
    TK_FONT.configure(size=10)

    root.option_add('*TCombobox*Listbox.background', '#36393e')
    root.option_add('*TCombobox*Listbox.foreground', '#dddddd')
    root.option_add('*TCombobox*Listbox.selectBackground', '#4d6f8c')

    style.configure('.',
        background = '#36393e',
        foreground = '#dddddd',
        fieldbackground = '#36393e',
        bordercolor = '#292b2f',
        darkcolor = '#292b2f',
        lightcolor = '#292b2f',
        insertcolor = '#dddddd',
        borderwidth = 1,
        arrowcolor = '#dddddd',
        troughcolor = '#36393e')

    style.configure('TButton',
        background = '#36393e',
        width=3)
    
    style.configure('go.TButton',
        background = '#36393e',
        width=6)

    style.map('TButton', background=[('active', '#292b2f')])
    style.map('TCheckbutton', background=[('active', '#292b2f')])

    style.map('TCombobox', background = [('pressed', '#292b2f'), ('active', '#292b2f')], bordercolor = [('focus', '#6c9cc4')])
    style.map('TScrollbar', background = [('active', '#292b2f')])

    ##################################################################################################################
    #util frame
    util_frame = ttk.Frame(root)

    help_button = ttk.Button(util_frame, text='?', command=lambda: tkinter.messagebox.showinfo('Instructions', '1. Choose a dungeon with the dropdown menu or type it in\n    for a custom name.\n\n2. In the larger field, type the names of all the items you want\n    to render, with each one on a separate line.\n\n3. Press "Go!" and select the file destination of your choosing.\nMultiple Infographics: To make multiple infographics, use the\n    plus and minus buttons to add or remove an infographic.\n\nAdditional Notes: If you changed the contents of the\n    dictionary files while the app is open, you can reload them\n    with the reload button.\n\nManual Sorting: Turning on the manual sort toggle will sort\n    the items as given, not by dictionary order.\n\nMade by Flaps#9562'))
    help_button.grid(row=0, column=0)

    reload_button = ttk.Button(util_frame, text='⟳', command=lambda: graphic.update_dicts)
    reload_button.grid(row=0, column=1, padx=5)

    manual_check = ttk.Checkbutton(util_frame, text='Manual Sort')
    manual_check.grid(row=0, column=2)

    util_frame.grid(row=0, column=0, sticky=tk.NW, padx=5, pady=5)

    ##################################################################################################################
    #graphic frame
    graphic_frame = ttk.Frame(root)
    graphic = Graphic(root, graphic_frame, dungeons, manual_check, dungeon_dict, items_dict)
    graphic_frame.grid(row=1, column=0)

    ##################################################################################################################
    #button frame
    button_frame = ttk.Frame(root)

    rem_button = ttk.Button(button_frame, text='-', command=graphic.rem_graphic)
    rem_button.grid(row=0, column=0)

    go_button = ttk.Button(button_frame, text='Go!', command=graphic.infographic, style='go.TButton')
    go_button.grid(row=0, column=1)

    add_button = ttk.Button(button_frame, text='+', command=graphic.add_graphic)
    add_button.grid(row=0, column=2)

    button_frame.grid(row=2, column=0, padx=5, pady=5)
    ##################################################################################################################

    graphic.add_graphic()

    root.mainloop()

if __name__ == '__main__':
    main()
