from zipfile import ZipFile, ZIP_DEFLATED
from django.template.loader import render_to_string
import os
import xml.dom.minidom

POINTS_PER_INCH = 914400

PROCESS_FILES = {
    'ppt/slides/_rels/slide2.xml.rels': 'record_slide_rels',
    'ppt/slides/slide1.xml': 'title_slide',
    'ppt/slides/slide2.xml': 'record_slide',
    'ppt/presentation.xml': 'presentation',
    'ppt/_rels/presentation.xml.rels': 'presentation_rels',
    '[Content_Types].xml': 'content_types',   
}


class PowerPointGenerator:
    
    def __init__(self, group):        
        self.group = group
        self.records = group.records.all()
        
    def get_templates(self):
        return filter(lambda f: f.endswith('.pptx'), os.listdir(os.path.join(os.path.dirname(__file__), 'pptx_templates')))
    
    def generate(self, template, outfile):
        if len(self.records) == 0:
            return False
        template = ZipFile(os.path.join(os.path.dirname(__file__), 'pptx_templates', template), mode='r')
        outfile = ZipFile(outfile, mode='w', compression=ZIP_DEFLATED)
        for name in template.namelist():
            content = template.read(name)
            if PROCESS_FILES.has_key(name):
                p = getattr(self, '_' + PROCESS_FILES[name])
                p(name, content, outfile)
            else:
                outfile.writestr(name, content)
        outfile.close()
        template.close()
        return True
                
    def _record_slide_rels(self, name, content, outfile):
        for n in range(2, len(self.records) + 2):
            x = xml.dom.minidom.parseString(content)
            record = self.records[n - 2]
            outfile.writestr('ppt/slides/_rels/slide%s.xml.rels' % n, x.toxml())     

    def _title_slide(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        for e in x.getElementsByTagName('a:t'):
            t = e.firstChild.nodeValue
            if t == 'title':
                t = self.group.title
            elif t == 'description':
                t = self.group.description
            e.firstChild.nodeValue = t        
        outfile.writestr(name, x.toxml())        
        
    def _record_slide(self, name, content, outfile):
        for n in range(2, len(self.records) + 2):
            x = xml.dom.minidom.parseString(content)
            record = self.records[n - 2]
            for e in x.getElementsByTagName('a:t'):
                t = e.firstChild.nodeValue
                if t == 'title':
                    t = record.title
                e.firstChild.nodeValue = t        
            outfile.writestr('ppt/slides/slide%s.xml' % n, x.toxml())     
    
    
    def _presentation(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        p = x.getElementsByTagName('p:sldIdLst')[0]
        maxid = max(map(lambda e: int(e.getAttribute('id')), p.getElementsByTagName('p:sldId')))
        for n in range(3, len(self.records) + 2):
            e = x.createElement('p:sldId')
            e.setAttribute('id', str(maxid + n))
            e.setAttributeNS('http://schemas.openxmlformats.org/officeDocument/2006/relationships', 'r:id', 'rooibosId%s' % n)
            p.appendChild(e)
        outfile.writestr(name, x.toxml())
    
    def _presentation_rels(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        p = x.getElementsByTagName('Relationships')[0]
        for n in range(3, len(self.records) + 2):
            e = x.createElement('Relationship')
            e.setAttribute('Id', 'rooibosId%s' % n)
            e.setAttribute('Type', 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide')
            e.setAttribute('Target', 'slides/slide%s.xml' % n)
            p.appendChild(e)
        outfile.writestr(name, x.toxml())
    
    def _content_types(self, name, content, outfile):
        x = xml.dom.minidom.parseString(content)
        for n in range(3, len(self.records) + 2):
            e = x.createElement('Override')
            e.setAttribute('PartName', '/ppt/slides/slide%s.xml' % n)
            e.setAttribute('ContentType', 'application/vnd.openxmlformats-officedocument.presentationml.slide+xml')
            x.firstChild.appendChild(e)
        outfile.writestr(name, x.toxml())
    