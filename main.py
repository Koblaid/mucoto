import os
import re
from collections import Counter

from path import path
from mutagenx import mp3, oggvorbis, apev2, musepack


AUDIO_FILES = ('.mp3', '.mpc', '.ape', '.ogg', 'wma')
META_FILES = ('.tif', '.jpg', '.gif', '.bmp', '.nfo', '.txt', '.htm', '.doc', '.sfv', '.m3u')

RE_PARTS = dict(
    artist='(?P<artist>.+)',
    track_name='(?P<track_name>.+)',
    track_no='(?P<track_no>[\d]{1,3})',
    ext='(?P<ext>\..{1,5})',
)

FORMATS = (
    '<artist> - <track_no> - <track_name><ext>',
    '<track_no>  - <artist> - <track_name><ext>',
    '<track_no> <artist> - <track_name><ext>',
    '<artist> - <track_name><ext>'
)


def parse_track_filename(track_path):
    file_name = track_path.basename()
    track_dict = dict(
        file_name=file_name,
        file_ext=track_path.ext,
        artist=None,
        track_name=None,
        track_no=0,
        track_artist=None,
        file_path=track_path,
        length=0,
        bitrate=0,
    )

    for format_str in FORMATS:
        re_str = format_str.replace(' ', '\ ')
        for part in RE_PARTS:
            re_str = re_str.replace('<'+part+'>', RE_PARTS[part])
        re_str = '^' + re_str + '$'
        match = re.match(re_str, file_name)
        if match:
            track_dict.update(match.groupdict())
            break
    else:
        print('unknown audio file pattern: ', file_name)

    track_dict['track_no'] = int(track_dict['track_no'])
    return track_dict


def read_cd(cd_path):
    tracks = []
    meta_files = []
    artists = set()

    for file_path in sorted(cd_path.files()):
        if file_path.ext.lower() in AUDIO_FILES:
            track_dict = parse_track_filename(file_path)
            track_dict['size'] = file_path.getsize()
            artists.add(track_dict['artist'])
            tracks.append(track_dict)
        elif file_path.ext.lower() in META_FILES:
            meta_files.append(file_path)
        else:
            print('unknown filetype', file_path.ext, file_path)

    if len(artists) > 1:
        print('more than one artist in one cd', cd_path, artists)

    return tracks, meta_files


def read_audio_file_tags(track_dict):
    file_path = track_dict['file_path']
    try:
        if track_dict['file_ext'] == '.mp3':
            track_obj = mp3.MP3(file_path)
        elif track_dict['file_ext'] == '.ogg':
            track_obj = oggvorbis.OggVorbis(file_path)
        elif track_dict['file_ext'] == '.ape':
            track_obj = apev2.APEv2File(file_path)
        elif track_dict['file_ext'] == '.mpc':
            track_obj = musepack.Musepack(file_path)
        else:
            raise Exception('Unknown file format')
    except Exception as e:
        print('error while reading tag of %s: %s' % (file_path, e))
        track_obj = None

    if track_obj is not None:
        track_dict['length'] = track_obj.info.length
        track_dict['bitrate'] = track_obj.info.bitrate
    else:
        track_dict['length'] = 0
        track_dict['bitrate'] = 0

    if track_dict['length'] == 0 or track_dict['bitrate'] == 0:
        print('missing track info', file_path)


def parse_directory(basepath):
    basepath = path(basepath)
    artists = {}
    for letterpath in basepath.dirs():

        for artistpath in letterpath.dirs():
            if artistpath.basename() == '.AppleDouble':
                continue

            albums = []
            for albumpath in artistpath.dirs():

                found_audio = False
                found_dir = False
                for el in albumpath.listdir():
                    if el.isfile() and el.ext in AUDIO_FILES:
                        found_audio = True
                    elif el.isdir():
                        found_dir = True

                if not found_audio and not found_dir:
                    print('wrong dir, contains no audio or dir', albumpath)
                if found_audio and found_dir:
                    print('wrong dir, contains audio _and_ dir', albumpath)

                cds = []
                if found_dir:
                    album_meta_files = []
                    for el in albumpath.listdir():
                        if el.isdir():
                            match = re.match('cd\ ?([\d]{1})', el.basename(), re.IGNORECASE)
                            cd_no = 0
                            if match:
                                (cd_no,) = match.groups()
                            else:
                                print('Wrong cd name', el)

                            tracks, cd_meta_files = read_cd(el)
                            cds.append({'cd_no': cd_no, 'tracks': tracks, 'meta_files': cd_meta_files})
                        else:
                            if el.ext in META_FILES:
                                album_meta_files.append(el)
                            else:
                                print('unknown meta file', el)

                else:
                    tracks, album_meta_files = read_cd(albumpath)
                    cds.append({'tracks': tracks, 'meta_files': [], 'cd_no': 0})

                albumname = albumpath.basename()
                albumyear = None

                match = re.match('([\d]{4})\ -\ (.+)', albumname)
                if match:
                    albumyear, albumname = match.groups()

                albums.append({'name': albumname, 'cds': cds, 'meta_files': album_meta_files, 'year': albumyear})


            artist_meta_files = []
            for filepath in artistpath.files():
                if filepath.ext in META_FILES:
                    artist_meta_files.append(str(filepath.basename()))
                else:
                    print('TODO %s' % filepath)


            artists[str(artistpath.basename())] = {'albums': albums, 'meta_files': artist_meta_files}




        for unknownfile in letterpath.files():
            print('TODO %s' % unknownfile)


    for unknownfile in basepath.files():
        print('TODO %s' % unknownfile)

    return artists


def read_tags(artists):
    for track_dict in get_all_tracks(artists):
        read_audio_file_tags(track_dict)


def get_all_tracks(artists):
    for artist in artists.values():
        for album in artist['albums']:
            for cd in album['cds']:
                for track in cd['tracks']:
                    yield track


def stats(artists):
    stats = {}

    stats['no_artists'] = len(artists)

    stats['no_albums'] = sum((len(artist['albums']) for artist in artists.values()))

    stats['no_files_by_type'] = Counter()
    for artist in artists.values():
        for meta_file in artist['meta_files']:
            stats['no_files_by_type'][path(meta_file).ext] += 1

        for album in artist['albums']:
            for cd in album['cds']:
                for track in cd['tracks']:
                    stats['no_files_by_type'][track['file_ext']] += 1

            for filename in album['meta_files']:
                stats['no_files_by_type'][path(filename).ext] += 1
                for cd in album['cds']:
                    for filename in cd['meta_files']:
                        stats['no_files_by_type'][path(filename).ext] += 1

    stats['no_of_cds'] = Counter()
    for artist in artists.values():
        for album in artist['albums']:
            stats['no_of_cds'][len(album['cds'])] += 1

    all_length = []
    for track in get_all_tracks(artists):
        if track['length'] > 0:
            all_length.append(track['length'])

    if all_length:
        stats['length'] = dict(
            total_in_h=round(sum(all_length) / 60. / 60, 2),
            min_in_sec=round(min(all_length), 2),
            max_in_min=round(max(all_length) / 60. , 2),
            avg_in_min=round(sum(all_length) / float(len(all_length)) / 60., 2),
        )

    all_size = []
    for track in get_all_tracks(artists):
        all_size.append(track['size'])
    stats['size'] = dict(
        total_in_gb=round(sum(all_size) / 1000 / 1000 / 1000, 3),
        min_in_mb=round(min(all_size) / 1000 / 1000, 3),
        max_in_mb=round(max(all_size) / 1000 / 1000, 3),
        avg_in_mb=round(sum(all_size) / float(len(all_size)) / 1000 / 1000, 3),
    )

    stats['bitrates_by_tracks'] = Counter()
    for track in get_all_tracks(artists):
        if track['bitrate'] % 1000 == 0 and track['bitrate'] > 0:
            stats['bitrates_by_tracks'][track['bitrate']/1000] += 1

    stats['albums_with_heterogenous_bitrates'] = 0
    stats['albums_with_homogenous_bitrates'] = Counter()
    for artist in artists.values():
        for album in artist['albums']:
            bitrates = set()
            for cd in album['cds']:
                for track in cd['tracks']:
                    if track['bitrate'] > 0:
                        bitrates.add(track['bitrate'])
            if len(bitrates) == 1:
                stats['albums_with_homogenous_bitrates'][bitrates.pop()] += 1
            else:
                stats['albums_with_heterogenous_bitrates'] += 1

    return stats


