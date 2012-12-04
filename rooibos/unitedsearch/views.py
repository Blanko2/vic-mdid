from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect, Http404
from rooibos.workers.models import JobInfo
from django.template import RequestContext
from rooibos.ui.views import select_record
from django.utils import simplejson
from rooibos.storage.models import *
from rooibos.access.models import AccessControl, ExtendedGroup, AUTHENTICATED_GROUP
from rooibos.data.models import Collection, Record, standardfield, CollectionItem, Field, FieldValue
from django.conf.urls.defaults import *
from urllib import urlencode
from common import *
from . import *
import searchers

import sys
import traceback

class usViewer():
    def __init__(self, searcher, mynamespace):
        self.urlpatterns = patterns('',
            url(r'^search/', self.search, name='search'),
            url(r'^select/', self.select, name='select'))
        self.searcher = searcher
        self.namespace = mynamespace
    
    def url_select(self):
        return reverse(self.namespace + ':select')
    
    def url_search(self):
        return reverse(self.namespace + ':search')
    
    def __url_search_(self, params={}):
        u = self.url_search()
        return u + (("&" if "?" in u else "?") + urlencode(params) if params else "")

    def htmlparams(self, defaults):
        def out(params, indent, prefix, default):
            label = params.label if params.label else " ".join(prefix)
            
            
            if isinstance(params, DefinedListParameter):
                #print "DefinedListParameter : ----------"

                options = params.options or []
                r_content = "  "*indent + (label + ": " if params.label else "") 
                #r_content += "<select name=\"i_"[0]+str( + "_".join(prefix) + "\"" + ("" or default and " value=\"" + default + "\"") + ">"
                r_content += "<select name=\"i_" + "_".join(prefix) + "\""
                if params.multipleAllowed :
                  r_content += " multiple = \"multiple\""
                r_content += ">"
                selected = options[0]
                if default:
                      selected = default
                  
                for option in options :
                    if option == selected:
                        r_content += "<option selected=\"selected\" value=" + option
                    else: 
                        r_content += "<option value=" + option
                    r_content += ">" + option + "</option>"
                r_content += "</select><br>"
                return [r_content]
            
            elif isinstance(params, MapParameter):
                r = ["  "*indent + "<div>"]
                for index in range(len(params.parammap)-1, -1, -1) :
                #for k in params.parammap:
                    k = params.parammap.keys()[index]
                    r += out(params.parammap[k], indent + 1, prefix + [k], default != None and default[k] != None and default[k])
                r += ["  "*indent + "</div>"]
                return r
            elif isinstance(params, ListParameter):
                r = ["  "*indent + "<div>"]
                index =0
                i = 0
                for v in params.paramlist :
                    #print "default ========"
                    #print default
                    r += out(v, indent+1, [str(prefix[0])+str(index)], default and default[i] or None)
                    index = index+1
                    i = i+1
                r += ["  "*indent + "</div>"]
                return r
            elif isinstance(params, ScalarParameter):
                return ["  "*indent + (label + ": " if params.label else "") + "<input type=\"text\" name=\"i_" + "_".join(prefix) + "\" value=\"" + (default or "") + "\" />"]
            elif isinstance(params, OptionalParameter):
                r = ["  "*indent + "<div>"]
                indent += 1
                r += ["  "*indent + "<input name=\"i_" + "_".join(prefix) + "\" type=\"checkbox\" class=\"param-opt-a\"" + (" checked=\"true\"" if default else "") + "> " + label]
                r += ["  "*indent + "<div class=\"param-opt\">"]
                r += out(params.subparam, indent + 1, prefix + ["opt"], default and default[0] if isinstance(default, list) else default or None)
                r += ["  "*indent + "</div>"]
                indent -= 1
                r += ["  "*indent + "</div>"]
                return r
            
            elif isinstance(params, OptionalDoubleParameter):
                r = ["  "*indent + "<div>"]
                indent += 2
                r += ["  "*indent + "<input name=\"i_" + "_".join(prefix) + "\" type=\"checkbox\" class=\"param-opt-a\"" + (" checked=\"true\"" if default else "") + "> " + "Add Field"]
                r += ["  "*indent + "<div class=\"param-opt\">"]
                r += out(params.subparam1, indent + 1, prefix + ["opt"], default and default[0] or None)
                r += out(params.subparam2, indent + 1, prefix + ["opt"], default and default[1] or None)
                r += ["  "*indent + "</div>"]
                indent -= 2
                r += ["  "*indent + "</div>"]
                return r
            elif isinstance(params, OptionalTripleParameter):
                r = ["  "*indent + "<div>"]
                indent += 2
                r += ["  "*indent + "<input name=\"i_" + "_".join(prefix) + "\" type=\"checkbox\" class=\"param-opt-a\"" + (" checked=\"true\"" if default else "") + "> " + "Add Field"]
                r += ["  "*indent + "<div class=\"param-opt\">"]
                r += out(params.subparam1, indent + 1, prefix + ["opt"], default and default[0] or None)
                r += out(params.subparam2, indent + 1, prefix + ["opt"], default and default[0] or None)
                r += out(params.subparam3, indent + 1, prefix + ["opt"], default and default[0] or None)
                r += ["  "*indent + "</div>"]
                indent -= 2
                r += ["  "*indent + "</div>"]
                return r
            
            elif isinstance(params, UserDefinedTypeParameter) :
                  options = params.type_options or []
                  r_content = "  "*indent + (label + ": " if params.label else "")
                  
                  r_content += "<div>"
                  
                  # select box for the type options
                  r_content += "<select name=\"i_" + "_".join(prefix) +"_type"+ "\">"
                  selected = options[0]
                  if default:
                      selected = default[0]
                  
                  for option in options :
                    if option == selected:
                        r_content += "<option selected=\"selected\" value=" + option
                    else: 
                        r_content += "<option value=" + option
                    r_content += ">" + option + "</option>"
                  r_content += "</select><br>"
                  
                  # textbox for value
                  if default and len(default) >0:
                    value = default[1]
                  else:
                    value = ""
                  r_content += "<input name=\"i_" + "_".join(prefix)+"_value" + "\" type=\"text\" value=\"" + value + "\" />"
                  
                  r_content += "</div>"
                  
                  return [r_content]
                
        return "\n".join(out(self.searcher.parameters, 0, [], defaults))

    
    def readargs(self, getdata):
        inputs = dict([(n[2:], getdata[n]) for n in getdata if n[:2] == "i_"])
        def read(params, prefix):
            if isinstance(params, MapParameter):
                r = {}
                for k in params.parammap:
                    if k in r :
                      r[k].append(read(params.parammap[k], prefix + [k]))
                    else :
                      r[k] = read(params.parammap[k], prefix + [k])
                return r
            if isdigitalnzinstance(params, ListParameter):

                r = []
                index = 0
                for v in params.paramlist:
                      r.append(read(v, prefix+[str(index)]))
                      index = index+1
                return r
            if isinstance(params, ScalarParameter):
                if "_".join(prefix) in inputs:
                    return inputs["_".join(prefix)]
            if isinstance(params, OptionalParameter):
                return [read(params.subparam, prefix + ["opt"])] if inputs.get("_".join(prefix), "off") == "on" else []
            if isinstance(params, DefinedListParameter):
                if "_".join(prefix) in inputs:
                    return inputs["_".join(prefix)]

            if isinstance(params, UserDefinedTypeParameter) :
                field_type = ""
                field_value = ""
                if "_".join(prefix)+"_type" in inputs:
                    field_type = inputs["_".join(prefix)+"_type"]
                if "_".join(prefix)+"_value" in inputs:
                    field_value = inputs["_".join(prefix)+"_value"]
                return field_type, field_value
                #if "_".join(prefix) in inputs:
                #   return inputs["_".join(prefix)]
        return read(self.searcher.parameters, [])
    

    
    def perform_search(self, request, resultcount):
        
        #print "request.GET:"

        
        query = request.GET.get('q', '') or request.POST.get('q', '')

        if query and "=" in query and not "params={" in query:
            kw = ""
            par = ""
            query_list = query.split(',')
            for q in query_list:
                if "=" in q:
                    key_value = q.split("=")
                    key = key_value[0]
                    value = key_value[1]
                    del key_value[0]
                    del key_value[0]
                    if len(key_value)>0 :
                        for v in key_value:
                            value += "+"+v
                    if not par=="":
                        par +=","
                    if value.startswith("+"):
                        del value[0]
                    par += "\""+key+"\":\""+value+"\""
                else:
                    if not kw=="":
                        kw += "+"
                    kw += q


            new_query = "keywords="+kw+",params={"+par+"}"
            query = new_query
            
        


        
        
        # Advanced search from sidebar
        offset = request.GET.get('from', '') or request.POST.get('from', '') or "0"
        params = {}
        #not_params = {}
        #or_params = {}
        t_str = "i_field0_type"
        #print "t_sr = =========="
        v_str = "i_field0_value"
        # new Gallica
        if t_str in request.GET and v_str in request.GET:
            key = request.GET[t_str]
            value = request.GET[v_str]
            if key and value:
                params.update({key:[[value,"and"]]})
                params.update({"first":key})
            #print "params = "
            #print params
            i=1
            while i<5:
                t_str = "i_field"+str(i)+"_opt_type"
                v_str = "i_field"+str(i)+"_opt_value"
                o_str = "i_field"+str(i)+"_opt"

                
                if t_str in request.GET and v_str in request.GET:
                    key = request.GET[t_str]
                    value = request.GET[v_str]
                    #print "value = "
                    #print value
                    opt = ""
                    if i>0:
                        opt = request.GET[o_str]
                    
                    if key and value:
                        if not key in params:
                            params.update({key:[[value,opt]]})
                        else:
                            v = params[key]
                            v.append([value,opt])
                            params.update({key:v})

                        """if opt=="or":
                            if not key in or_params:
                                or_params.update({key:[value]})
                            else:
                                List = or_params[key]
                                List.append(value)
                                or_params.update({key:List})
                        if opt=="except":
                            if not key in not_params:
                                not_params.update({key:[value]})
                            else:
                                List = not_params[key]
                                List.append(value)
                                not_params.update({key:List})"""
                i = i+1
            """
            if len(not_params)>0:
                params.update({"except":not_params})
            if len(or_params)>0:
                params.update({"or":or_params})
            """
            if "i_language" in request.GET:
                lang = request.GET["i_language"]
                params.update({"language":lang})
            if "i_copyright" in request.GET:
                cr = request.GET["i_copyright"]
                params.update({"copyright":cr})
            if "i_start date" in request.GET:
                sd = request.GET["i_start date"]
                params.update({"start date":sd})
            if "i_start date" in request.GET:
                ed = request.GET["i_end date"]
                params.update({"end date":sd})
            params.update({"adv_sidebar":True})
            #print params
        # Old Gallica
        elif "i_field_field1_type" in request.GET: 
          n=1
          while n<=5:
            key = request.GET["i_field_field"+str(n)+"_type"]
            value = request.GET["i_field_field"+str(n)+"_value"]
            if value:
              params.update({key:value})
            n=n+1
          if "i_language" in request.GET:
            lang = request.GET["i_language"]
            params.update({"language":lang})
          if "i_copyright" in request.GET:
            cr = request.GET["i_copyright"]
            params.update({"copyright":cr})
          if "i_start date" in request.GET:
            sd = request.GET["i_start date"]
            params.update({"start date":sd})
          if "i_start date" in request.GET:
            ed = request.GET["i_end date"]
            params.update({"end date":sd})
        #NGA    
        else : 
          for n in request.GET:
            """
            #print n
            #print "="
            #print request.GET[n]
            """
            if "_opt" in n:
              key = n.replace("i_","").replace("_opt",'')
              if request.GET[n]:
                params.update({key:request.GET[n]})
            

          
        """
        for n in request.GET:
            #print "n ="
            #print n
            #print "="
            #print request.GET[n]
            #print "\n\n"
            if n[:2] == "p-":
                params[n[2:]] = request.GET[n]
        """
        #args = self.readargs(request.GET)
        #query = "keyword=,title=e,artist=e"
        #print params

        result,args = self.searcher.search(query, params, offset, resultcount)
        results = result.images

        def resultpart(image):
            if isinstance(image, ResultRecord):
                return {
                    "is_record": True,
                    "thumb_url": image.record.get_thumbnail_url(),
                    "title": image.record.title,
                    "record_url": image.record.get_absolute_url(),
                    "identifier": image.record.id
                }
            else:
                return {
                    "thumb_url": image.thumb,
                    "title": image.name,
                    "record_url": image.infourl,
                    "identifier": image.identifier
                }

        prev_off = hasattr(self.searcher, "previousOffset") and self.searcher.previousOffset(offset, resultcount)
        
        
        
        prev = None
        
        if int(offset)>0 :

          prev_off =int(offset)-50
          
          if prev_off > int(result.total):
            prev_off = result.total-len(result.images)-50
          if prev_off <0:
            prev_off=0
          prev = self.__url_search_({ 'q': query, 'from': prev_off })

        nextPage = None
        
        firstPage = None
        
        lastPage = None
        
        if int(offset)>0:
          firstPage = self.__url_search_({ 'q': query, 'from': 0 })
        
        if (int(result.nextoffset)<int(result.total)):
          nextPage = self.__url_search_({ 'q': query, 'from': result.nextoffset })
          
        if (nextPage):
          num_lastPageResult = result.total%50
          if num_lastPageResult==0:
            num_lastPageResult=50
          lastOffset = result.total-num_lastPageResult
          lastPage = self.__url_search_({ 'q': query, 'from': lastOffset })
          
        query = ""
        if "simple_keywords" in args:
            query = args["simple_keywords"]

        return {
                'results': map(resultpart, results),
                'select_url': self.url_select(),
                'next_page': nextPage,
                'previous_page': prev, 
                'first_page': firstPage,
                'last_page' :lastPage,
                'hits': result.total,
                'searcher_name': self.searcher.name,
                'html_parameters': self.htmlparams(args),
                'query': query
            }
        
    def search(self, request):
        
        a = self.perform_search(request,50)
        #print "previous_page: %s" % a["previous_page"]
        return render_to_response('searcher-results.html', a, context_instance=RequestContext(request))


    def record(self, identifier):
        print "in record, identifier = "+str(identifier)
        image = self.searcher.getImage(identifier)
        if isinstance(image, ResultRecord):
            return image.record
        record = Record.objects.create(name=image.name,
                        source=image.url,
                        tmp_extthumb=image.thumb,
                        manager='unitedsearch')
        print"add_field"
        def add_field(f, v, o):
            if type(v) == list:
                for w in v:
                    add_field(f, w, o)
            elif v:
                # TODO: neaten?
                try:
                    FieldValue.objects.create(
                        record=record,
                        field=standardfield(f),
                        order=o,
                        value=v)
                except:
                    pass
        print"fields added"
        n = 0
        # go through the metadata given by the searcher; just add whatever can be added---what are not standard fields are simply skipped.
        for field, value in dict(image.meta, title=image.name).iteritems():
            add_field(field, value, n)
            n += 1
        print"done the for"
        collection = get_collection()
        CollectionItem.objects.create(collection=collection, record=record)
        job = JobInfo.objects.create(func='unitedsearch_download_media', arg=simplejson.dumps({
            'record': record.id,
            'url': image.url
        }))
        job.run()
        return record

    def select(self, request):
        print request.POST
        print request.method
        if not request.user.is_authenticated():
            raise Http404()
        
        if request.method in "POST":
            # TODO: maybe drop the unused given-records portion of this
            postid = request.POST.get('id', '[]')
            imagesjs = json.loads(postid.strip("[]"))
            print "Json:"+imagesjs
            #print self.searcher.getImage(imagesjs)
            #images = map(self.searcher.getImage, imagesjs)
            images = [self.searcher.getImage(imagesjs)]
            print "images = "+str(images)
            urlmap = {}
            for i in images:
                urlmap[i.record.get_absolute_url() if isinstance(i, ResultRecord) else i.url]=i
            print "urlmap = "+str(urlmap)
            urls = urlmap.keys()
            print "urls = "+str(urls)
            # map of relevant source URLs to record IDs that already exist
            ids = dict(Record.objects.filter(source__in=urls, manager='unitedsearch').values_list('source', 'id'))
            print "ids = "+str(ids)
            result = []
            for url in urls:
                id = ids.get(url)
                if id:
                    print "got id"
                    result.append(id)
                else:
                    print "got record"
                    i = urlmap[url].identifier
                    print i
                    record = self.record(i)
                    print record
                    result.append(record.id)
            print result
            r = request.POST.copy()
            r['id'] = simplejson.dumps(result)
            request.POST = r
        return select_record(request)

class usUnionViewer(usViewer):
    def __init__(self, searcher):
        usViewer.__init__(self, searcher, None)
    
    def url_select(self):
        return reverse("united:union-select", kwargs={"sid": self.searcher.identifier})

    def url_search(self):
        return reverse("united:union-search", kwargs={"sid": self.searcher.identifier})

searchersmap = dict([(s.identifier, s) for s in searchers.all])

def union(request, sid):
    from union import searcherUnion
    slist = map(searchersmap.get, sid.split(","))
    searcher = slist[0] if len(slist) == 1 else searcherUnion(slist)
    return usUnionViewer(searcher)

def union_select(request, sid="local"):
    return union(request, sid).select(request)

def union_search(request, sid="local"):
    return union(request, sid).search(request)
