from django import template
from django.utils.html import escape
from django.template.loader import get_template
from django.template import Context, Variable

register = template.Library()


class MetaDataNode(template.Node):
    
    def __init__(self, record, fieldset):
        self.record = Variable(record)
        self.fieldset = Variable(fieldset)
    
    def render(self, context):
        record = self.record.resolve(context)
        fieldvalues = list(record.get_fieldvalues(owner=context['request'].user,
                                                  fieldset=self.fieldset.resolve(context)))        
        if fieldvalues:
            fieldvalues[0]._subitem = False
        for i in range(1, len(fieldvalues)):
            fieldvalues[i]._subitem = (fieldvalues[i].field == fieldvalues[i - 1].field and
                                      fieldvalues[i].group == fieldvalues[i - 1].group)
            
        result = []
        for value in fieldvalues:
            result.append('<div class="metadata-%sitem"><div class="label">%s</div><div class="value">%s</div></div>\n' %
                          (value._subitem and 'sub' or '', value.resolved_label, value.value or '&nbsp;'))
        
        return '<div class="metadata">%s</div>' % ''.join(result)
        
    
@register.tag
def metadata(parser, token):
    try:
        tag_name, record, fieldset = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    return MetaDataNode(record, fieldset)
    