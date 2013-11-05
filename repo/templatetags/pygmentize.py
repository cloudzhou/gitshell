from django import template
from pygments import highlight 
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter 
 
register = template.Library()
@register.filter(name='pygmentize') 
def pygmentize(code, lang):
    lexer = get_lexer_by_name(lang, encoding='utf-8')
    formatter = HtmlFormatter(linenos=True,
                              encoding='utf-8',
                              cssclass='%s highlight' % lang
                              )
    result = highlight(code, lexer, formatter)
    return result
