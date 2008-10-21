
# Source: http://www.djangosnippets.org/snippets/512/
# Modified by Andreas Knab, 10/14/2008
def unique_slug(item,slug_source,slug_field):
  """Ensures a unique slug field by appending an integer counter to duplicate slugs.
  
  The item's slug field is first prepopulated by slugify-ing the source field. If that value already exists, a counter is appended to the slug, and the counter incremented upward until the value is unique.
  
  For instance, if you save an object titled Daily Roundup, and the slug daily-roundup is already taken, this function will try daily-roundup-2, daily-roundup-3, daily-roundup-4, etc, until a unique value is found.
  
  Call from within a model's custom save() method like so:
  unique_slug(item, slug_source='field1', slug_field='field2')
  where the value of field slug_source will be used to prepopulate the value of slug_field.
  """
  if not getattr(item, slug_field): # if it's already got a slug, do nothing.
      from django.template.defaultfilters import slugify
      itemModel = item.__class__
      max_length = itemModel._meta.get_field(slug_field).max_length
      slug = slugify(getattr(item,slug_source))
      allSlugs = [getattr(i, slug_field) for i in itemModel.objects.complex_filter({'%s__startswith' % slug_field: slug[:10]})]
      if slug in allSlugs:
          counter = 2
          while slug in allSlugs:
              slug = "%s-%i" % (slug[:max_length - 1 - len(str(counter))], counter)
              counter += 1
      setattr(item,slug_field,slug)


def safe_int(value, default):
    try:
        return int(value)
    except ValueError:
        return default
