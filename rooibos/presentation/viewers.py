from django import forms
from django.http import Http404, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response
from django.conf import settings
from django.template import RequestContext
from django.core.urlresolvers import reverse
from rooibos.access import get_effective_permissions_and_restrictions, filter_by_access
from rooibos.viewers import register_viewer, Viewer
from rooibos.storage import get_image_for_record
from rooibos.data.models import Record, Collection
from models import Presentation
from reportlab.pdfgen import canvas
from reportlab.lib import pagesizes
from reportlab.lib.units import inch
from reportlab.lib.styles import StyleSheet1, ParagraphStyle
from reportlab.lib.colors import white, black
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus.frames import Frame
import Image
import re
import math


def _get_presentation(obj, request, objid):
    if obj:
        if not isinstance(obj, Presentation):
            return None
    else:
        obj = Presentation.get_by_id_for_request(objid, request)
        if not obj:
            return None
    return obj


class PresentationViewer(Viewer):

    title = "View"
    weight = 100

    def view(self, request):
        return_url = request.GET.get('next', reverse('presentation-browse'))
        return render_to_response('presentation_viewer.html',
                                  {'presentation': self.obj,
                                   'return_url': return_url,
                                },
                            context_instance=RequestContext(request))


@register_viewer('presentationviewer', PresentationViewer)
def presentationviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return PresentationViewer(presentation, request.user) if presentation else None



class FlashCardViewer(Viewer):

    title = "Flash Cards"
    weight = 18

    def view(self, request):
        presentation = self.obj

        passwords = request.session.get('passwords', dict())

        response = HttpResponse(mimetype='application/pdf')

        pagesize = getattr(pagesizes, settings.PDF_PAGESIZE)
        width, height = pagesize

        p = canvas.Canvas(response, pagesize=pagesize)

        def getStyleSheet():
            stylesheet = StyleSheet1()
            stylesheet.add(ParagraphStyle(name='Normal',
                                          fontName='Times-Roman',
                                          fontSize=8,
                                          leading=10))
            stylesheet.add(ParagraphStyle(name='SlideNumber',
                                          parent=stylesheet['Normal'],
                                          alignment=TA_RIGHT,
                                          fontSize=6,
                                          leading=8))
            stylesheet.add(ParagraphStyle(name='Data',
                                          parent=stylesheet['Normal'],
                                          leftIndent=18,
                                          firstLineIndent=-18,
                                          ))
            return stylesheet

        styles = getStyleSheet()

        items = presentation.items.filter(hidden=False)

        def decoratePage():
            p.saveState()
            p.setDash(2, 2)
            p.setStrokeColorRGB(0.8, 0.8, 0.8)
            p.line(width / 2, inch / 2, width / 2, height - inch / 2)
            p.line(inch / 2, height / 3, width - inch / 2, height / 3)
            p.line(inch / 2, height / 3 * 2, width - inch / 2, height / 3 * 2)
            p.setFont('Helvetica', 8)
            p.setFillColorRGB(0.8, 0.8, 0.8)
            p.drawString(inch, height / 3 - 3 * inch / 72, 'Cut here')
            p.drawString(inch, height / 3 * 2 - 3 * inch / 72, 'Cut here')
            p.translate(width / 2 - 3 * inch / 72, height - inch)
            p.rotate(270)
            p.drawString(0, 0, 'Fold here')
            p.restoreState()

        def getParagraph(*args, **kwargs):
            try:
                return Paragraph(*args, **kwargs)
            except (AttributeError, IndexError):
                return None

        def drawCard(index, item):
            p.saveState()
            p.translate(0, height / 3 * (2 - index % 3))

            # retrieve record while making sure it's accessible to presentation owner
            record = Record.filter_one_by_access(presentation.owner, item.record.id)

            if record:
                image = get_image_for_record(record, presentation.owner, 800, 800, passwords)
                if image:
                    p.drawImage(image, inch / 2, inch / 2, width=width / 2 - inch, height=height / 3 - inch,
                                preserveAspectRatio=True)
                f = Frame(width / 2 + inch / 2, inch / 2,
                          width=width / 2 - inch, height = height / 3 - inch,
                          leftPadding=0, bottomPadding=0, rightPadding=0, topPadding=0)
                data = []
                data.append(getParagraph('%s/%s' % (index + 1, len(items)), styles['SlideNumber']))
                values = item.get_fieldvalues(owner=request.user)
                for value in values:
                    v = value.value if len(value.value) < 100 else value.value[:100] + '...'
                    data.append(getParagraph('<b>%s:</b> %s' % (value.resolved_label, v), styles['Data']))
                annotation = item.annotation
                if annotation:
                    data.append(getParagraph('<b>%s:</b> %s' % ('Annotation', annotation), styles['Data']))
                data = filter(None, data)
                f.addFromList(data, p)
                if data:
                    p.setFont('Helvetica', 8)
                    p.setFillColorRGB(0, 0, 0)
                    p.drawRightString(width - inch / 2, inch / 2, '...')

            p.restoreState()

        for index, item in enumerate(items):
            if index % 3 == 0:
                if index > 0:
                    p.showPage()
                decoratePage()
            drawCard(index, item)

        p.showPage()
        p.save()
        return response


@register_viewer('flashcardviewer', FlashCardViewer)
def flashcardviewer(obj, request, objid=None):
    presentation = _get_presentation(obj, request, objid)
    return FlashCardViewer(presentation, request.user) if presentation else None
