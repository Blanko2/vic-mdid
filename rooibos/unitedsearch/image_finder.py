import re  

def get_thumble(url):
    if "sunsite.utk.edu/bessie/sculpture/" in url:
        s = url.split("/")
        s.pop()
        folder = s.pop()
        return url+folder+".jpg"  
    else:
        return url

def get_image_url(url,thumble_url):
    if "artsearch.nga.gov.au" in url:
        return thumble_url.replace("/SML/", "/LRG/")
    if "static.flickr.com" in url:
        return thumble_url.replace("_t.", ".")
    if "quod.lib.umich.edu" in url:
        #if it's part of a smaller collection, i think, entryid will change to x-<something>, can't guess what
        arts = re.findall("[^_]+", re.findall("[^jpg]+", re.findall("[^/]*.jpg", thumble_url)[0])[0].strip('.'))
        col = re.findall("[^/]+/thumb", thumble_url)[0].split("/")[0]
        if len(arts) is 2:
            return "http://quod.lib.umich.edu/cgi/i/image/getimage-idx?c="+col+"&cc="+col+"&entryid=" +arts[0]+"-"+arts[1]+ "&viewid=" +arts[0]+"_"+arts[1]+ "&width=10000&height=10000&res=3"
        elif len(arts) is 1:
            return "http://quod.lib.umich.edu/cgi/i/image/getimage-idx?c="+col+"&cc="+col+"&entryid=" +arts[0]+ "&viewid=" +arts[0]+ "&width=10000&height=10000&res=3"
        else:
            return url
    if "artsearch.nga.gov.au" in url:
        #Assuming they comply with aus copyright act 1968
        return thumble_url.replace("/SML/", "/LRG/")
    if "http://acms.sl.nsw.gov.au" in url:
        #not sure if we're allowed these,
        #http://www.sl.nsw.gov.au/using/copies/imaging.html
        return thumble_url.replace("_DAMt", "_DAMl").replace("t.jpg", "r.jpg")
    if "territorystories" in url:
        #Assuming they comply with aus copyright act 1968
        return thumble_url.replace(".JPG.jpg", ".JPG")
    #url = url.replace("/thum/", "/full/").replace("s.jpg", ".jpg")
    if "images.slsa.sa.gov.au" in url:
        #PictureNT "All images from PictureNT may be reproduced or saved for research or educational purposes"
        return thumble_url.replace("/mpcimgt/", "/mpcimg/")
    if "recordsearch.naa.gov.au" in url:
        #Comply with Australian Copyright Act 1968 - research
        num = re.findall("Number=([0-9]*)", thumble_url)[0]
        return "http://recordsearch.naa.gov.au/NAAMedia/ShowImage.asp?T=P&S=1&B="+num
    if "lib.uwm.edu" in url:
        #The low-resolution images available from the UWM Libraries Digital Collections
        #website may be copied by individuals or libraries for personal use, research, 
        #teaching or any "fair use" as defined by copyright law.
        return thumble_url.replace("thumbnail.exe", "getimage.exe") + "&DMSCALE=0&DMWIDTH=0"
    #url = url.replace("/thumbnail/", "/reference/")
    if "sunsite.utk.edu/bessie/sculpture/" in url:
        #University of Tennessee, Knoxville
        #Presumably comply with US Copyright law
        s = url.split("/")
        s.pop()
        folder = s.pop()
        return url+folder+".jpg"  
    if "nla.gov.au" in url:
        #Assuming they comply with aus copyright act 1968
        return thumble_url.replace("-t", "-v")
    if "www.leodis.net" in url:
        #Leeds city council, support the Open Archives Initiative
        #Presumably fair use applies for copyrith law
        return url
    if "slv.vic.gov.au" in url: #sometimes digital.slv, sometimes www.slv
        #don't know how to get full size image, sorry
        return url
    if "digitallibrary.usc.edu" in url: #don't know how to get full image
        return url
    if "slwa.wa.gov.au" in url:
        #Assuming they comply with aus copyright act 1968
        return thumble_url.replace(".png", ".jpg")
    if "salemhistory.net" in url:
        #Oregon Historic Photograph Collections
        #Assuming Fair Use provision in US Copyright law
        col = re.findall("CISOROOT=/[^&]+", thumble_url)[0].split("=/")[1]
        image = re.findall("CISOPTR=[^&]+", thumble_url)[0].split("=")[1]
        return "http://photos.salemhistory.net/utils/getprintimage/collection/"+col+"/id/"+image+"/scale/100/width/10000/height/10000"
        #return thumble_url.replace("", "")
    if "localhost:8000/static/images/thumbnail_unavailable.png" in thumble_url:
        return url
    
    return url   
   
