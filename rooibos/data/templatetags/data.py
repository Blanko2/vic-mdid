from django import template
from django.template.loader import render_to_string
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
            fieldvalues[0].subitem = False
        for i in range(1, len(fieldvalues)):
            fieldvalues[i].subitem = (fieldvalues[i].field == fieldvalues[i - 1].field and
                                      fieldvalues[i].group == fieldvalues[i - 1].group)
        
        return render_to_string('data_metadata.html',
                                dict(values=fieldvalues),
                                context_instance=context)


@register.tag
def metadata(parser, token):
    try:
        tag_name, record, fieldset = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two arguments" % token.contents.split()[0]
    return MetaDataNode(record, fieldset)
