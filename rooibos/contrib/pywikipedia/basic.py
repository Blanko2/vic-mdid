#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This is not a complete bot; rather, it is a template from which simple
bots can be made. You can rename it to mybot.py, then edit it in
whatever way you want.

The following parameters are supported:

&params;

    -debug         If given, doesn't do any real changes, but only shows
                   what would have been changed.

All other parameters will be regarded as part of the title of a single page,
and the bot will only work on that single page.
"""
__version__ = '$Id: basic.py 7015 2009-07-03 20:28:49Z alexsh $'
import wikipedia
import pagegenerators

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

class BasicBot:
    # Edit summary message that should be used.
    # NOTE: Put a good description here, and add translations, if possible!
    msg = {
        'ar': u'روبوت: تغيير ...',
        'cs': u'Robot změnil ...',
        'de': u'Bot: Ändere ...',
        'en': u'Robot: Changing ...',
        'fr': u'Robot: Changé ...',
        'ja':u'ロボットによる：編集',
        'ksh': u'Bot: Ännern ...',
        'nds': u'Bot: Änderung ...',
        'nl': u'Bot: wijziging ...',
        'pt': u'Bot: alterando...',
        'sv': u'Bot: Ändrar ...',
        'zh': u'機器人：編輯.....',
    }

    def __init__(self, generator, debug):
        """
        Constructor. Parameters:
            * generator - The page generator that determines on which pages
                          to work on.
            * debug     - If True, doesn't do any real changes, but only shows
                          what would have been changed.
        """
        self.generator = generator
        self.debug = debug

    def run(self):
        # Set the edit summary message
        wikipedia.setAction(wikipedia.translate(wikipedia.getSite(), self.msg))
        for page in self.generator:
            self.treat(page)

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

        ################################################################
        # NOTE: Here you can modify the text in whatever way you want. #
        ################################################################

        # If you find out that you do not want to edit this page, just return.
        # Example: This puts the text 'Test' at the beginning of the page.
        text = 'Test ' + text

        # only save if something was changed
        if text != page.get():
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            wikipedia.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<" % page.title())
            # show what was changed
            wikipedia.showDiff(page.get(), text)
            if not self.debug:
                choice = wikipedia.inputChoice(u'Do you want to accept these changes?', ['Yes', 'No'], ['y', 'N'], 'N')
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

    # Parse command line arguments
    for arg in wikipedia.handleArgs():
        if arg.startswith("-debug"):
            debug = True
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
        bot = BasicBot(gen, debug)
        bot.run()
    else:
        wikipedia.showHelp()

if __name__ == "__main__":
    try:
        main()
    finally:
        wikipedia.stopme()
