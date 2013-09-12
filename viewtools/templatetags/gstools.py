from django import template
from gitshell.gsuser.utils import UrlRouter

register = template.Library()

@register.filter
def keyvalue(dict, key):
    return dict[key]

@register.filter
def route(urlRouter, url):
    return urlRouter.route(url)


