import sublime_plugin
import re

syntax_list = {
    "PHP": True
}


class PhpdoxCommand(sublime_plugin.TextCommand):

    settings = {}

    templates = {

# Class template
        'class': """
/**
* ${{1:{0}}}
* @uses {1}
* @category ${{2:Category}}
* @package  ${{3:Package}}
*/""",

# Interface template
        'interface': """
/**
* ${{1:{0}}}
* @uses {1}
* @category ${{2:Category}}
* @package  ${{3:Package}}
*/""",

# Function template
        'function': """
    /**
     * ${{1:{name}}}{params}
     * @return ${{{tabstop1}:mixed}} ${{{tabstop2}:Value}}
     */""",

# Variable template
        'variable': """
    /**
     * ${{1:\\{name}}}
     * @var {type}
     * @access {access}{static}
     */"""
    }

    def run(self, edit, **args):
        """Entry point"""
        v = self.view
        self.settings = v.settings()
        line = v.line(v.sel()[0])
        snippet = self.process_line(v.substr(line))
        if (snippet != None):
            v.run_command('move', {'by': 'lines', 'forward': False})
            v.run_command('move_to', {'to': 'hardeol'})
            v.run_command('insert_snippet', {'contents': "\n"})
            v.run_command('move_to', {'to': 'hardbol', 'extend': True})
            v.run_command('left_delete')
            v.run_command('insert_snippet', {'contents': snippet})

    def process_line(self, line):
        """Resolves current line type and calls respective parse method"""
        for p_name, p_string in self.settings.get('phpdox')['patterns'].items():
            pattern = re.compile(p_string, re.VERBOSE)
            match = pattern.search(line)
            if (match != None):
                method = getattr(self, 'dox_' + p_name)
                return method(match)
        return None

    def dox_class(self, match):
        """Resolves class's PHPDoc by given match"""
        return self.templates['class'].format(*match.group('name_class', 'name_parent'))

    def dox_interface(self, match):
        """Resolves interface's PHPDoc by given match"""
        return self.templates['interface'].format(*match.group('name_interface', 'name_parent'))

    def dox_function(self, match):
        """Resolves function's PHPDoc by given match"""
        params, tabstop_index = self.resolve_params(match.group('params'))
        tokens = {
            'access': self.resolve_access(match.group('access')),
            'name': match.group('name'),
            'params': params,
            'static': self.resolve_static(match.group('static')),
            'tabstop1': tabstop_index,
            'tabstop2': tabstop_index + 1,
        }
        print self.templates['function'].format(**tokens)
        return self.templates['function'].format(**tokens)

    def dox_variable(self, match):
        """Resolves variable's PHPDoc by given match"""
        tokens = {
            'access': self.resolve_access(match.group('access')),
            'name': match.group('name'),
            'static': self.resolve_static(match.group('static')),
            'type': self.resolve_var_type(match.group('value')),
        }
        return self.templates['variable'].format(**tokens)

    def resolve_access(self, val):
        """Resolves access modifier value"""
        if (val != ''):
            return val
        return 'public'

    def resolve_static(self, val):
        """Resolves static modifier value"""
        if (val == 'static'):
            return '\n     * @static'
        return ''

    def resolve_params(self, val):
        """Resolves method's parameters description"""
        if (val == ''):
            return [val, 2]
        params = []
        lines = []
        tabstop_index = 2

        for param in val.replace(' ', '').split(','):
            name, assign, value = param.partition('=')
            v_type = self.resolve_var_type(value)
            params.append([v_type, name])
        for count, pair in enumerate(params):
            v_type, v_name = pair
            lines.append('     * @param ${{{0}:{1}}} \\{2} ${{{3}:Description}}'.format(count + (count + 2), v_type, v_name, count + (count + 3)))
            tabstop_index = count + (count + 4)
        return ['\n' + '\n'.join(lines), tabstop_index]

    def resolve_var_type(self, val):
        """Resolves variable's type by given value"""
        type = 'mixed'
        if (val == 'array()'):
            type = 'array'
        elif (val.isdigit()):
            type = 'int'
        elif (val.startswith(('\'', '"'))):
            type = 'string'
        return type
