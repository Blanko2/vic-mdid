#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This is a bot that uses external filtering programs to munge the
article text, for example:

    python piper.py -filter:'tr A-Z a-z' Wikipedia:Sandbox

Would lower case the article with tr(1).

Muliple -filter commands can be specified:

    python piper.py -filter:cat -filter:'tr A-Z a-z' -filter:'tr a-z A-Z' Wikipedia:Sandbox


Would pipe the article text through cat(1) (NOOP) and then lower case
it with tr(1) and upper case it again with tr(1)

The following parameters are supported:

&params;

    -debug         If given, doesn't do any real changes, but only shows
                   what would have been changed.

    -always        Always commit changes without asking you to accept them

    -filter:       Filter the article text through this program, can be
                   given multiple times to filter through multiple programs in
                   the order which they are given

In addition all command-line parameters are passed to
genFactory.handleArg() which means pagegenerators.py arguments are
supported.

"""
__version__ = '$Id: piper.py 6285 2009-01-23 14:32:00Z siebrand $'
import wikipedia
import pagegenerators

import os
import pipes
import tempfile

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class PiperBot:
    # Edit summary message that should be used.
    # NOTE: Put a good description here, and add translations, if possible!
    msg = {
        'en': u'Robot: Piping the article text through %s',
        'ar': u'روبوت: استبدال نص المقال من خلال %s',
        'is': u'Vélmenni: Pípa texta síðunnar í gegnum %s',
        'nl': u'Bot: paginatekst door %s geleid'
    }

    def __init__(self, generator, debug, filters, always):
        """
        Constructor. Parameters:
            * generator - The page generator that determines on which pages
                          to work on.
            * debug     - If True, doesn't do any real changes, but only shows
                          what would have been changed.
            * always    - If True, don't prompt for changes
        """
        self.generator = generator
        self.debug = debug
        self.always = always
        self.filters = filters

    def run(self):
        # Set the edit summary message
        pipes = ', '.join(self.filters)
        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), self.msg) % pipes)
        for page in self.generator:
            self.treat(page)

    def pipe(self, program, text):
        """
        Pipes a given text through a given program and returns it
        """

        text = text.encode('utf-8')

        pipe = pipes.Template()
        pipe.append(program.encode("ascii"), '--')

        # Create a temporary filename to save the piped stuff to
        tempFilename = '%s.%s' % (tempfile.mktemp(), 'txt')
        file = pipe.open(tempFilename, 'w')
        file.write(text)
        file.close()

        # Now retrieve the munged text
        mungedText = open(tempFilename, 'r').read()
        # clean up
        os.unlink(tempFilename)

        unicode_text = unicode(mungedText, 'utf-8')

        return unicode_text

    # debug
    #def savePage(self, name, text):
    #    mungedName = name.replace(":", "_").replace("/", "_").replace(" ", "_")
    #
    #    saveName = "/tmp/piper/%s" % mungedName
    #    file = open(saveName, 'w')
    #    file.write(text.encode("utf-8"))
    #    file.close()
    #    print "Wrote to %s" % saveName

    def treat(self, page):
        """
        Loads the given page, does some changes, and saves it.
        """
        try:
            # Load the page
            text = page.get()
        except wikipedia.NoPage:
            wikipedia.output(u"Page %s does not exist; skipping." % page.aslink())
            return
        except wikipedia.IsRedirectPage:
            wikipedia.output(u"Page %s is a redirect; skipping." % page.aslink())
            return

        # debug
        # self.savePage(page.title(), text)

        # Munge!
        for program in self.filters:
            text = self.pipe(program, text);

        # only save if something was changed
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            wikipedia.output(u"\n\n>>> %s <<<" % page.title())
            # show what was changed
            wikipedia.showDiff(page.get(), text)
            if not self.debug:
                if not self.always:
                    choice = wikipedia.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
                else:
                    choice = 'y'
                if choice == 'y':
                    try:
                        # Save the page
                        page.put(text)
                    except wikipedia.LockedPage:
                        wikipedia.output(u"Page %s is locked; skipping." % page.aslink())
                    except wikipedia.EditConflict:
                        wikipedia.output(u'Skipping %s because of edit conflict' % (page.title()))
                    except wikipedia.SpamfilterError, error:
                        wikipedia.output(u'Cannot change %s because of spam blacklist entry %s' % (page.title(), error.url))


def main():
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()
    # The generator gives the pages that should be worked upon.
    gen = None
    # This temporary array is used to read the page title if one single
    # page to work on is specified by the arguments.
    pageTitleParts = []
    # If debug is True, doesn't do any real changes, but only show
    # what would have been changed.
    debug = False
    # will become True when the user uses the -always flag.
    always = False
    # The program to pipe stuff through
    filters = []

    # Parse command line arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith("-debug"):
            debug = True
        elif arg.startswith("-filter:"):
            prog = arg[8:]
            filters.append(prog)
        elif arg.startswith("-always"):
            always = True
        else:
            # check if a standard argument like
            # -start:XYZ or -ref:Asdf was given.
            if not genFactory.handleArg(arg):
                pageTitleParts.append(arg)

    if pageTitleParts != []:
        # We will only work on a single page.
        pageTitle = ' '.join(pageTitleParts)
        page = wikipedia.Page(wikipedia.getSite(), pageTitle)
        gen = iter([page])

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        # The preloading generator is responsible for downloading multiple
        # pages from the wiki simultaneously.
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = PiperBot(gen, debug, filters, always)
        bot.run()
    else:
        wikipedia.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
