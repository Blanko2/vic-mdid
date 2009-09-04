# -*- coding: iso8859-1 -*-
"""
Bot for getting multiple images from an external site. It takes a URL as an
argument and finds all images (and other files specified by the extensions
in 'fileformats') that URL is referring to, asking whether to upload them.
If further arguments are given, they are considered to be the text that is
common to the descriptions.

A second use is to get a number of images that have URLs only differing in
numbers. To do this, use the command line option "-pattern", and give the URL
with the variable part replaced by '$' (if that character occurs in the URL
itself, you will have to change the bot code, my apologies).

Other options:
-shown      Choose images shown on the page as well as linked from it
-justshown  Choose _only_ images shown on the page, not those linked
"""

__version__='$Id: imageharvest.py 6571 2009-04-04 02:20:27Z nicdumz $'

import re, sys, os
import wikipedia, upload

def get_imagelinks(url):
    # Given a URL, get all images linked to by the page at that URL.
    # First, we get the location for relative links from the URL.
    relativepath = url.split("/")
    if len(relativepath) == 1:
        relativepath=relativepath[0]
    else:
        relativepath=relativepath[:len(relativepath)-1]
        relativepath="/".join(relativepath)
    links = []
    uo = wikipedia.MyURLopener()
    file = uo.open(url)
    text = file.read()
    file.close()
    text = text.lower()
    if not shown:
        R=re.compile("href\s*=\s*[\"'](.*?)[\"']")
    elif shown == "just":
        R=re.compile("src\s*=s*[\"'](.*?)[\"']")
    else:
        R=re.compile("[\"'](.*?)[\"']")
    for link in R.findall(text):
        ext = os.path.splitext(link)[1].lower().strip('.')
        if ext in fileformats:
            if re.compile("://").match(text):
                links += [link]
            else:
                links += [relativepath+"/"+link]
    return links

def main(give_url, image_url, desc):
    url = give_url

    if url == '':
        if image_url:
            url = wikipedia.input(u"What URL range should I check (use $ for the part that is changeable)")
        else:
            url = wikipedia.input(u"From what URL should I get the images?")

    if image_url:
        minimum=1
        maximum=99
        answer= wikipedia.input(u"What is the first number to check (default: 1)")
        if answer:
            minimum=int(answer)
        answer= wikipedia.input(u"What is the last number to check (default: 99)")
        if answer:
            maximum=int(answer)

    if not desc:
        basicdesc = wikipedia.input(
            u"What text should be added at the end of the description of each image from this url?")
    else:
        basicdesc = desc

    if image_url:
        ilinks = []
        i = minimum
        while i <= maximum:
            ilinks += [url.replace("$",str(i))]
            i += 1
    else:
        ilinks = get_imagelinks(url)

    for image in ilinks:
        answer = wikipedia.inputChoice(u'Include image %s?' % image, ['yes', 'no', 'stop'], ['y', 'N', 's'], 'N')
        if answer == 'y':
            desc = wikipedia.input(u"Give the description of this image:")
            desc = desc + "\r\n\n\r" + basicdesc
            uploadBot = upload.UploadRobot(image, desc)
            uploadBot.run()
        elif answer == 's':
            break
try:
    url = u''
    image_url = False
    shown = False
    desc = []

    for arg in wikipedia.handleArgs():
        if arg == "-pattern":
            image_url = True
        elif arg == "-shown":
            shown = True
        elif arg == "-justshown":
            shown = "just"
        elif url == u'':
            url = arg
        else:
            desc += [arg]
    desc = ' '.join(desc)

    fileformats = ('jpg', 'jpeg', 'png', 'gif', 'svg', 'ogg')
    mysite = wikipedia.getSite()
    main(url, image_url, desc)
finally:
    wikipedia.stopme()
