import six

from string import Formatter
from .. import PY26


class ContentFormatter(Formatter):
    """
    ContentFormatter uses string formatting as a template engine,
    not raising key/index/value errors, and keeps braces and variable-like parts in place.
    """

    def get_value(self, key, args, kwargs):
        try:
            return super(ContentFormatter, self).get_value(key, args, kwargs)
        except (IndexError, KeyError):
            if (PY26 or six.PY3) and key == u'\0':
                # PY26: Handle of non-indexed variable -> Turn null byte into {}
                return type(key)(u'{}')
            else:
                # PY27: Not a context variable -> Keep braces
                return self._brace_key(key)

    def convert_field(self, value, conversion):
        if conversion and isinstance(value, six.string_types) and value[0] == u'{' and value[-1] == u'}':
            # Value is wrapped with braces and therefore not a context variable -> Keep conversion as value
            return self._inject_conversion(value, conversion)
        else:
            return super(ContentFormatter, self).convert_field(value, conversion)

    def format_field(self, value, format_spec):
        try:
            return super(ContentFormatter, self).format_field(value, format_spec)
        except ValueError:
            # Unable to format value and therefore not a context variable -> Keep format_spec as value
            return self._inject_format_spec(value, format_spec)

    def parse(self, format_string):
        if PY26 or six.PY3:
            # PY26 does not support non-indexed variables -> Place null byte for later removal
            # PY3 does not like mixing non-indexed and indexed variables to we disable them here too.
            format_string = format_string.replace('{}', '{\0}')

        parsed_bits = super(ContentFormatter, self).parse(format_string)

        # Double braces are treated as escaped -> re-duplicate when parsed
        return self._escape(parsed_bits)

    def get_field(self, field_name, args, kwargs):
        return super(ContentFormatter, self).get_field(field_name, args, kwargs)

    def _brace_key(self, key):
        """
        key: 'x' -> '{x}'
        """
        if isinstance(key, six.integer_types):
            t = str
            key = t(key)
        else:
            t = type(key)
        return t(u'{') + key + t(u'}')

    def _inject_conversion(self, value, conversion):
        """
        value: '{x}', conversion: 's' -> '{x!s}'
        """
        t = type(value)
        return value[:-1] + t(u'!') + conversion + t(u'}')

    def _inject_format_spec(self, value, format_spec):
        """
        value: '{x}', format_spec: 'f' -> '{x:f}'
        """
        t = type(value)
        return value[:-1] + t(u':') + format_spec + t(u'}')

    def _escape(self, bits):
        """
        value: 'foobar {' -> 'foobar {{'
        value: 'x}' -> 'x}}'
        """
        # for value, field_name, format_spec, conversion in bits:
        while True:
            try:
                value, field_name, format_spec, conversion = next(bits)
                if value:
                    end = value[-1]
                    if end in (u'{', u'}'):
                        value += end
                yield value, field_name, format_spec, conversion
            except StopIteration:
                break
