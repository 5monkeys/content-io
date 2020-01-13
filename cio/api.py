# coding=utf-8
from __future__ import unicode_literals

from .conf import settings
from .environment import env
from .node import Node, empty
from .pipeline import pipeline
from .plugins import plugins
from .backends import storage
from .backends.exceptions import NodeDoesNotExist
from .utils.uri import URI

__all__ = ['get', 'set', 'delete', 'publish', 'revisions', 'load']


def get(uri, default=None, lazy=True):

    node = Node(uri, default)

    # Set URI namespace to current environment scheme, if not set
    uri = node.uri
    if not uri.namespace:
        namespace = getattr(env, node.uri.scheme)[0]
        uri = uri.clone(namespace=namespace)
    node.uri = uri

    # Send/Buffer node through pipeline
    if lazy:
        node = pipeline.buffer('get', node)
    else:
        # TODO: Return node from pipeline
        pipeline.send('get', node)

    return node


def set(uri, data, publish=True, **meta):
    node = Node(uri, data, **meta)

    # Extend uri with missing extension and version
    uri = node.uri
    if not uri.ext:
        uri = uri.clone(ext=settings.URI_DEFAULT_EXT)
    if not uri.version:
        uri = uri.clone(version='draft')
    node.uri = uri

    # Send node through pipeline
    pipeline.send('set', node)

    # Auto publish
    if publish:
        pipeline.send('publish', node)

    return node


def delete(*uris):
    # Initialize nodes with "empty" content
    def init_node(uri):
        node = Node(uri, empty)

        # Default version to draft
        if not node.uri.version:
            node.uri = node.uri.clone(version='draft')
        return node
    nodes = (init_node(uri) for uri in uris)

    # Send nodes through pipeline
    response = pipeline.send('delete', *nodes)

    # Return requested uris for successfully deleted nodes (content set to None)
    return [node.initial_uri for node in response.values() if node.content is None]


def publish(uri):
    node = Node(uri)

    # Publish draft if no specific version specified
    if not node.uri.version:
        uri = node.uri = node.uri.clone(version='draft')

    response = pipeline.send('publish', node)
    return response.get(uri)


def revisions(uri):
    return storage.get_revisions(uri)


def load(uri):
    uri = URI(uri)
    node = None
    data = None

    def uri_chain(uri):
        uri = uri.clone(query=None)
        if uri.version:
            yield uri
        if uri.version != 'draft':
            yield uri.clone(version='draft')
        yield uri.clone(version=None)

    # Try to get node from storage in order: given version, draft, published
    for _uri in uri_chain(uri):
        try:
            stored_node = storage.get(_uri)
        except NodeDoesNotExist:
            continue
        else:
            # Add potential query params for plugin resolve
            meta = stored_node.get('meta') or {}
            node = Node(URI(stored_node['uri']).clone(query=uri.query), content=stored_node['content'], **meta)
            break

    if node:
        # Load node data with related plugin
        plugin = plugins.resolve(node.uri)  # May raise UnknownPlugin and should be handled outside api
        data = plugin._load(node)
        node.content = plugin._render(node, data)

    else:
        # Initialize non-existing node without version
        uri = uri.clone(version=None)

        # Set default extension
        if not uri.ext:
            uri = uri.clone(ext=settings.URI_DEFAULT_EXT)

        # Validate plugin existence
        plugins.resolve(uri)

        node = Node(uri)

    return {
        'uri': node.uri,
        'data': data,
        'content': node.content,
        'meta': node.meta
    }


def search(uri=None):
    return storage.search(uri=uri)
