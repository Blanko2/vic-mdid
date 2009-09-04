# -*- coding: utf-8 -*-
"""
Add or change categories on a number of pages. Usage:
catall.py name - goes through pages, starting at 'name'. Provides
the categories on the page and asks whether to change them. If no
starting name is provided, the bot starts at 'A'.

Options:
-onlynew : Only run on pages that do not yet have a category.
"""
#
# (C) Rob W.W. Hooft, Andre Engels, 2004
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: catall.py 6686 2009-04-23 20:25:23Z cosoleto $'
#

import wikipedia, sys

msg={
    'ar':u'بوت: تغيير التصنيفات',
    'de':u'Bot: Wechsele Kategorien',
    'en':u'Bot: Changing categories',
    'he':u'Bot: משנה קטגוריות',
    'fr':u'Bot: Change categories',
    'he':u'בוט: משנה קטגוריות',
    'ia':u'Bot: Alteration de categorias',
    'it':u'Bot: Cambio categorie',
    'ja':u'ロボットによる: カテゴリ変更',
    'lt':u'robotas: Keičiamos kategorijos',
    'ksh':u'Bot: Saachjruppe tuusche of dobei donn',
    'nl':u'Bot: wijziging van categorieën',
    'pl':u'Bot: Zmiana kategorii',
    'pt':u'Bot: Categorizando',
    'sr':u'Bot: Ð˜Ð·Ð¼ÐµÐ½Ð° ÐºÐ°Ñ‚ÐµÐ³Ð¾Ñ€Ð¸Ñ˜Ð°',
    'sv':u'Bot: Ändrar kategori',
    'zh':u'機器人: 更改分類',
    }

def choosecats(pagetext):
    chosen=[]
    flag=False
    length=1000
    print ("Give the new categories, one per line.")
    print ("Empty line: if the first, don't change. Otherwise: Ready.")
    print ("-: I made a mistake, let me start over.")
    print ("?: Give the text of the page with GUI.")
    print ("??: Give the text of the page in console.")
    print ("xx: if the first, remove all categories and add no new.")
    print ("q: quit.")
    while flag == False:
        choice=wikipedia.input(u"?")
        if choice=="":
            flag=True
        elif choice=="-":
            chosen=choosecats(pagetext)
            flag=True
        elif choice=="?":
            import editarticle
            editor = editarticle.TextEditor()
            newtext = editor.edit(pagetext)
        elif choice =="??":
            wikipedia.output(pagetext[0:length])
            length = length+500
        elif choice=="xx" and chosen==[]:
            chosen = None
            flag=True
        elif choice=="q":
            print "quit..."
            sys.exit()
        else:
            chosen.append(choice)
    return chosen

def make_categories(page, list, site = None):
    if site is None:
        site = wikipedia.getSite()
    pllist=[]
    for p in list:
        cattitle="%s:%s" % (site.category_namespace(), p)
        pllist.append(wikipedia.Page(site,cattitle))
    page.put_async(wikipedia.replaceCategoryLinks(page.get(), pllist),
                   comment=wikipedia.translate(site.lang, msg))

docorrections=True
start=[]

for arg in wikipedia.handleArgs():
    if arg == '-onlynew':
        docorrections=False
    else:
        start.append(arg)

if start == []:
    start='A'
else:
    start=' '.join(start)

mysite = wikipedia.getSite()

try:
    for p in mysite.allpages(start = start):
        try:
            text=p.get()
            cats=p.categories()
            if cats == []:
                wikipedia.output(u"========== %s ==========" % p.title())
                print "No categories"
                print "----------------------------------------"
                newcats=choosecats(text)
                if newcats != [] and newcats is not None:
                    make_categories(p, newcats, mysite)
            else:
                if docorrections:
                    wikipedia.output(u"========== %s ==========" % p.title())
                    for c in cats:
                        wikipedia.output(c.title())
                    print "----------------------------------------"
                    newcats=choosecats(text)
                    if newcats is None:
                        make_categories(p, [], mysite)
                    elif newcats != []:
                        make_categories(p, newcats, mysite)
        except wikipedia.IsRedirectPage:
            wikipedia.output(u'%s is a redirect' % p.title())
finally:
    wikipedia.stopme()
