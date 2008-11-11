from django.contrib.sites.models import Site
from django.db.models import Q
import sys

def unique_slug(item, slug_source=None, slug_literal=None, slug_field='name', check_current_slug=False):
    """Ensures a unique slug field by appending an integer counter to duplicate slugs.
    
    Source: http://www.djangosnippets.org/snippets/512/
    Modified by Andreas Knab, 10/14/2008
    
    The item's slug field is first prepopulated by slugify-ing the source field.
    If that value already exists, a counter is appended to the slug, and the
    counter incremented upward until the value is unique.
    
    For instance, if you save an object titled Daily Roundup, and the slug
    daily-roundup is already taken, this function will try daily-roundup-2,
    daily-roundup-3, daily-roundup-4, etc, until a unique value is found.
    
    Call from within a model's custom save() method like so:
    unique_slug(item, slug_source='field1', slug_field='field2')
    where the value of field slug_source will be used to prepopulate the value of slug_field.
    
    If slug_source does not exist, it will be used as a literal string.
    """      
    if check_current_slug or not getattr(item, slug_field): # if it's already got a slug, do nothing.
        from django.template.defaultfilters import slugify
        itemModel = item.__class__
        max_length = itemModel._meta.get_field(slug_field).max_length      
        if check_current_slug and getattr(item, slug_field):
            slug = slugify(getattr(item, slug_field))
        else:
            slug = slugify(slug_source and getattr(item, slug_source, slug_literal) or slug_literal)
        slug = slug[:max_length]
        slug_check = slug[:min(len(slug), max_length-len(str(sys.maxint)))]
        
        query = itemModel.objects.complex_filter({'%s__startswith' % slug_field: slug_check})
        
        # check to see if slug needs to be unique together with another field only
        unique_together = filter(lambda f: slug_field in f, itemModel._meta.unique_together)
        # only handle simple case of one unique_together with one additional field
        if len(unique_together) == 1 and len(unique_together[0]) == 2:
            l = list(unique_together[0])
            l.remove(slug_field)
            unique_with = l[0]
            query = query & itemModel.objects.complex_filter({unique_with: getattr(item, unique_with)})
        
        allSlugs = [getattr(i, slug_field) for i in query]
        
        if slug in allSlugs:
            counter = 2
            uniqueslug = slug
            while uniqueslug in allSlugs:
                uniqueslug = "%s-%i" % (slug[:max_length - 1 - len(str(counter))], counter)
                counter += 1
            slug = uniqueslug
        setattr(item, slug_field, slug)


def safe_int(value, default):
    try:
        return int(value)
    except ValueError:
        return default


def get_full_url(absolute_url):
    # todo: support SSL
    return 'http://%s%s' % (Site.objects.get_current().domain, absolute_url)
