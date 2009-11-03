from django.conf import settings
import os
import tempfile
import wave
import struct
import re
from django.utils import simplejson
from StringIO import StringIO
from subprocess import Popen, PIPE
from PIL import Image

def _seconds_to_timestamp(seconds):
    hours = seconds / 3600
    minutes = seconds / 60
    seconds = seconds % 60
    return '%02d:%02d:%02d' % (hours, minutes, seconds)

def _run_ffmpeg(parameters, infile, outfile_ext):
    if not settings.FFMPEG_EXECUTABLE:
        return None
    handle, filename = tempfile.mkstemp(outfile_ext)
    os.close(handle)
    try:
        cmd = 'ffmpeg -i "%s" %s -y "%s"' % (infile, parameters, filename)
        ffmpeg = Popen(cmd, executable=settings.FFMPEG_EXECUTABLE, stdout=PIPE, stderr=PIPE)
        ffmpeg.wait()
        file = open(filename, 'rb')
        result = StringIO(file.read())
        file.close()
        return result
    except:
        return None
    finally:
        os.remove(filename)

def capture_video_frame(videofile, offset=5):
    params = '-r 1 -ss %s -t 00:00:01 -vframes 1 -f image2' % _seconds_to_timestamp(offset)
    return _run_ffmpeg(params, videofile, '.jpg')

def render_audio_waveform(audiofile, basecolor=(255, 255, 255), background=None):
    wave_file = _run_ffmpeg('-t 00:00:30 -ar 8192 -ac 1', audiofile, '.wav')
    if not wave_file:
        return None
    file = wave.open(wave_file, 'rb')
    data = file.readframes(30 * 8192)
    frames = struct.unpack('%sh' % (len(data) / 2), data)
    if background:
        image = Image.open(background)
        if image.size != (600, 400):
            image = image.transform((600, 400), Image.EXTENT, (0, 0, image.size[0], image.size[1]))
    else:
        image = Image.new("RGBA", (600, 400), (0, 0, 0))
    pix = image.load()
    lf = len(frames)
    lows, highs = [], []
    for x in range(600):
        f, t = (x * lf) / 600, ((x + 1) * lf) / 600
        lows.append(min(frames[f:t]))
        highs.append(max(frames[f:t]))
    low, high = abs(min(lows)), abs(max(highs))
    lows = map(lambda v: v * 150 / low, lows)
    highs = map(lambda v: v * 150 / high, highs)
    for x in range(600):
        high = 225 - highs[x]
        low = 225 - lows[x]
        for y in range(high, 225):
            color = (225 - y) * 255 / (225 - high)
            pix[x, y] = (color * basecolor[0] / 255, color * basecolor[1] / 255, color * basecolor[2] / 255)
        for y in range(225, low):
            color = (y - 225) * 255 / (low - 225)
            pix[x, y] = (color * basecolor[0] / 255, color * basecolor[1] / 255, color * basecolor[2] / 255)
    output = StringIO()
    image.save(output, 'JPEG', quality=85, optimize=True)
    output.seek(0)
    return output

def render_audio_waveform_by_mimetype(audiofile, mimetype):
    path = os.path.join(settings.STATIC_DIR, 'images', 'audiothumbs')
    mimetype = mimetype.split('/')[1]
    background = os.path.join(path, mimetype + '.png')
    if not os.path.isfile(background):
        background = os.path.join(path, 'general.png')
        if not os.path.isfile(background):
            background = None
    colorfile = os.path.join(path, mimetype + '.json')
    if not os.path.isfile(colorfile):
        colorfile = os.path.join(path, 'general.json')
        if not os.path.isfile(colorfile):
            colorfile = None
    if colorfile:
        color = simplejson.load(open(colorfile, 'r'))
    else:
        color = (255, 255, 255)
    return render_audio_waveform(audiofile, color, background)

def get_image(media):
    if media.mimetype.startswith('image/'):
        return media.load_file()
    if media.mimetype.startswith('video/'):
        return capture_video_frame(media.get_absolute_file_path())
    if media.mimetype.startswith('audio/'):
        return render_audio_waveform_by_mimetype(media.get_absolute_file_path(), media.mimetype)
    return None
