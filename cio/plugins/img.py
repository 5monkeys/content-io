import json
from hashlib import sha1
from os import path
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from ..plugins.base import BasePlugin


class ImagePlugin(BasePlugin):

    ext = 'img'

    def _open(self, filename):
        raise NotImplementedError

    def _save(self, filename, bytes):
        raise NotImplementedError

    def _url(self, filename):
        raise NotImplementedError

    def _create_filename(self, filename, **kwargs):
        name, ext = path.splitext(filename)
        dir, name = name.rsplit(path.sep, 1)
        name += ''.join((key + str(value) for key, value in kwargs.iteritems()))
        name = sha1(name).hexdigest()
        subdir = name[:2]
        return path.sep.join((dir, subdir, name + ext))

    def load(self, content):
        if content:
            data = json.loads(content)

            # Add image url to loaded data
            filename = data.get('filename', None)
            data['url'] = self._url(filename) if filename else None

            return data
        else:
            return {'filename': None, 'url': None}

    def save(self, data):
        from PIL import Image
        width = int(data.get('width') or 0)
        height = int(data.get('height') or 0)

        upload = data['file']
        filename = data['filename']
        file = image = None

        if upload:
            image = Image.open(upload)
            filename = path.sep.join(('content-io', 'img', upload.name))
            width, height = image.size
            filename = self._create_filename(filename, w=width, h=height)
        elif filename:
            file = self._open(filename)
            image = Image.open(file)

        if image:
            # Crop
            crop = data.get('crop')
            if crop:
                try:
                    box = tuple(int(x) for x in crop.split(','))
                    image = image.crop(box)
                except Exception as e:
                    print e
                else:
                    filename = self._create_filename(filename, crop=crop)

            # Resize
            i_width, i_height = image.size
            if (width and width != i_width) or (height and height != i_height):
                try:
                    image = image.resize((width, height), Image.ANTIALIAS)
                    pass
                except Exception as e:
                    print e
                else:
                    filename = self._create_filename(filename, w=width, h=height)
            else:
                width = i_width
                height = i_height

            if filename != data['filename']:
                # new_file = self._open(filename, 'w')
                new_file = StringIO.StringIO()
                image.save(new_file, image.format)
                filename = self._save(filename, new_file)
                # new_file.close()

        if file:
            file.close()

        content = {
            'filename': filename,
            'width': width,
            'height': height,
            'id': data['id'] or None,
            'class': data['class'] or None,
            'alt': data['alt'] or None
        }

        return json.dumps(content)

    def delete(self, data):
        raise NotImplementedError

    def render(self, data):
        attrs = {
            'src': 'http://placekitten.com/160/90',
            'width': 160,
            'height': 90
        }
        if data:
            url = data.get('url')
            alt = data.get('alt')
            width = data.get('width') or 0
            height = data.get('height') or 0
            if url:
                attrs['src'] = url
            if alt:
                attrs['alt'] = alt
            if width and height:
                attrs['width'] = width
                attrs['height'] = height

        return u'<img {0} />'.format(u' '.join(u'{0}="{1}"'.format(attr, value) for attr, value in attrs.iteritems()))
