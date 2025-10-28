from wordcloud import WordCloud
from operator import itemgetter
from random import Random
from PIL import Image, ImageDraw, ImageFont
import numpy as np
from wordcloud.wordcloud import IntegralOccupancyMap
import re

class EmojiWordCloud(WordCloud):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generateEmojiWordCloud(self, frequencies, max_font_size=None):
        """Create a word_cloud from words and frequencies.

        Parameters
        ----------
        frequencies : dict from string to float
            A contains words and associated frequency.

        max_font_size : int
            Use this font-size instead of self.max_font_size

        Returns
        -------
        self

        """
        # make sure frequencies are sorted and normalized
        frequencies = sorted(frequencies.items(), key=itemgetter(1), reverse=True)
        if len(frequencies) <= 0:
            raise ValueError("We need at least 1 word to plot a word cloud, "
                             "got %d." % len(frequencies))
        frequencies = frequencies[:self.max_words]

        # largest entry will be 1
        max_frequency = float(frequencies[0][1])

        frequencies = [(word, freq / max_frequency)
                       for word, freq in frequencies]

        if self.random_state is not None:
            random_state = self.random_state
        else:
            random_state = Random()

        if self.mask is not None:
            boolean_mask = self._get_bolean_mask(self.mask)
            width = self.mask.shape[1]
            height = self.mask.shape[0]
        else:
            boolean_mask = None
            height, width = self.height, self.width
        occupancy = IntegralOccupancyMap(height, width, boolean_mask)

        # create image
        img_grey = Image.new("L", (width, height))
        draw = ImageDraw.Draw(img_grey)
        img_array = np.asarray(img_grey)
        font_sizes, positions, orientations, colors = [], [], [], []

        last_freq = 1.

        if max_font_size is None:
            # if not provided use default font_size
            max_font_size = self.max_font_size

        if max_font_size is None:
            # figure out a good font size by trying to draw with
            # just the first two words
            if len(frequencies) == 1:
                # we only have one word. We make it big!
                font_size = self.height
            else:
                self.generate_from_frequencies(dict(frequencies[:2]),
                                               max_font_size=self.height)
                # find font sizes
                sizes = [x[1] for x in self.layout_]
                try:
                    font_size = int(2 * sizes[0] * sizes[1]
                                    / (sizes[0] + sizes[1]))
                # quick fix for if self.layout_ contains less than 2 values
                # on very small images it can be empty
                except IndexError:
                    try:
                        font_size = sizes[0]
                    except IndexError:
                        raise ValueError(
                            "Couldn't find space to draw. Either the Canvas size"
                            " is too small or too much of the image is masked "
                            "out.")
        else:
            font_size = max_font_size

        # we set self.words_ here because we called generate_from_frequencies
        # above... hurray for good design?
        self.words_ = dict(frequencies)

        if self.repeat and len(frequencies) < self.max_words:
            # pad frequencies with repeating words.
            times_extend = int(np.ceil(self.max_words / len(frequencies))) - 1
            # get smallest frequency
            frequencies_org = list(frequencies)
            downweight = frequencies[-1][1]
            for i in range(times_extend):
                frequencies.extend([(word, freq * downweight ** (i + 1))
                                    for word, freq in frequencies_org])

        emojiPattern=re.compile(r':(\w+):')
        # start drawing grey image
        for word, freq in frequencies:
            result=None
            transposed_font=None
            x,y=0,0
            # select the font size
            rs = self.relative_scaling
            if rs != 0:
                font_size = int(round((rs * (freq / float(last_freq))
                                       + (1 - float(rs))) * font_size))
            if emojiPattern.match(word):
                orientation=None
                newHeight,newWidth=0,0
                try:
                    emojiImg=Image.open(f"emoji/{word[1:-1]}.png").convert("RGBA")
                except FileNotFoundError:
                    x,y=0,0
                else:
                    while True:
                        if font_size < self.min_font_size:
                            # font-size went too small
                            break

                        newWidth=font_size
                        wpercent = (newWidth/float(emojiImg.size[0]))
                        newHeight = int((float(emojiImg.size[1])*float(wpercent)))
                        emojiImg=emojiImg.resize((int(newWidth),int(newHeight)),Image.LANCZOS)
                        result = occupancy.sample_position(
                            newHeight + self.margin,  # 高度 + 边距
                            newWidth + self.margin,  # 宽度 + 边距  
                            random_state
                        )
                        if result is not None:
                            break  # 找到位置，退出循环

                        font_size -= self.font_step
                    

                    x, y = np.array(result) + self.margin // 2
                    img_grey.paste(Image.new("L",(newWidth,newHeight),"white"),(y,x),emojiImg)#type:ignore
            else:
                if random_state.random() < self.prefer_horizontal:
                    orientation = None
                else:
                    orientation = Image.ROTATE_90
                tried_other_orientation = False
                while True:
                    if font_size < self.min_font_size:
                        # font-size went too small
                        break
                    # try to find a position
                    font = ImageFont.truetype(self.font_path, font_size)
                    # transpose font optionally
                    transposed_font = ImageFont.TransposedFont(
                        font, orientation=orientation)
                    # get size of resulting text
                    box_size = draw.textbbox((0, 0), word, font=transposed_font, anchor="lt")
                    # find possible places using integral image:
                    result = occupancy.sample_position(box_size[3] + self.margin,
                                                    box_size[2] + self.margin,
                                                    random_state)
                    if result is not None:
                        # Found a place
                        break
                    # if we didn't find a place, make font smaller
                    # but first try to rotate!
                    if not tried_other_orientation and self.prefer_horizontal < 1:
                        orientation = (Image.ROTATE_90 if orientation is None else
                                    Image.ROTATE_90)
                        tried_other_orientation = True
                    else:
                        font_size -= self.font_step
                        orientation = None

                if font_size < self.min_font_size:
                    # we were unable to draw any more
                    break

                x, y = np.array(result) + self.margin // 2
                # actually draw the text
                draw.text((y, x), word, fill="white", font=transposed_font)
            positions.append((x, y))
            orientations.append(orientation)
            font_sizes.append(font_size)
            colors.append(self.color_func(word, font_size=font_size,
                                        position=(x, y),
                                        orientation=orientation,
                                        random_state=random_state,
                                        font_path=self.font_path))
                # recompute integral image
            if self.mask is None:
                img_array = np.asarray(img_grey)
            else:
                img_array = np.asarray(img_grey) + boolean_mask
            # recompute bottom right
            # the order of the cumsum's is important for speed ?!
            occupancy.update(img_array, x, y)
            last_freq = freq

        self.layout_ = list(zip(frequencies, font_sizes, positions,
                                    orientations, colors))
        #img_grey.save("debug_grey.png")
        return self

    def to_image(self):
        self._check_generated()
        if self.mask is not None:
            width = self.mask.shape[1]
            height = self.mask.shape[0]
        else:
            height, width = self.height, self.width
        
        img = Image.new(self.mode, (int(width * self.scale),
                                    int(height * self.scale)),
                        self.background_color) # type: ignore
        draw = ImageDraw.Draw(img)
        
        emojiPattern=re.compile(r':(\w+):')
        for (word, count), font_size, position, orientation, color in self.layout_:
            if emojiPattern.match(word):
                try:
                    emojiImg=Image.open(f"emoji/{word[1:-1]}.png").convert("RGBA")
                except FileNotFoundError:
                    continue
                else:
                    newWidth=font_size*self.scale
                    wpercent = (newWidth/float(emojiImg.size[0]))
                    newHeight = int((float(emojiImg.size[1])*float(wpercent)))
                    emojiImg=emojiImg.resize((int(newWidth),int(newHeight)),Image.LANCZOS)
                    pos = (int(position[1] * self.scale),
                        int(position[0] * self.scale))
                    img.paste(emojiImg,pos,emojiImg)
            else:
                font = ImageFont.truetype(self.font_path,
                                        int(font_size * self.scale))
                transposed_font = ImageFont.TransposedFont(
                    font, orientation=orientation)
                pos = (int(position[1] * self.scale),
                    int(position[0] * self.scale))
                draw.text(pos, word, fill=color, font=transposed_font)

        return self._draw_contour(img=img)


if __name__ == "__main__":
    ew=EmojiWordCloud(width=1080,height=720,font_path="msyh.ttc",background_color="white",max_font_size=150)
    freqs={':ocean:':5, ':heart:':3, '测试':10, '词云':7}
    ew.generateEmojiWordCloud(freqs)
    ew.to_file("wordcloud.png")