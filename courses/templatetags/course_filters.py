from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def get_index(lst, index):
    try:
        return lst[int(index)]
    except (IndexError, TypeError, ValueError):
        return None
