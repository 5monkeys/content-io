ENVIRONMENT = {
    'default': {
        'i18n': 'en-us',
        'l10n': 'local',
        'g11n': 'global'
    }
}

CACHE = 'locmem://'
STORAGE = 'sqlite://:memory:'

PIPELINE = [
    'cio.pipeline.pipes.cache.CachePipe',
    'cio.pipeline.pipes.meta.MetaPipe',
    'cio.pipeline.pipes.plugin.PluginPipe',
    'cio.pipeline.pipes.storage.StoragePipe',
    'cio.pipeline.pipes.storage.NamespaceFallbackPipe'
]

PLUGINS = [
    'cio.plugins.txt.TextPlugin',
    'cio.plugins.md.MarkdownPlugin'
]

URI_SCHEME_SEPARATOR = '://'
URI_NAMESPACE_SEPARATOR = '@'
URI_PATH_SEPARATOR = '/'
URI_EXT_SEPARATOR = '.'
URI_VERSION_SEPARATOR = '#'
URI_DEFAULT_EXT = 'txt'
