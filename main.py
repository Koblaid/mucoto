import os
import re
from collections import Counter

from path import path
from mutagenx import mp3, oggvorbis, apev2, musepack


AUDIO_FILES = ('.mp3', '.mpc', '.ape', '.ogg')
META_FILES = ('.tif', '.jpg', '.gif', '.bmp', '.nfo', '.txt', '.htm', '.doc', '.sfv')


def parse_track_filename(track_path):
    file_name = track_path.basename()
    file_ext = track_path.ext
    track_name = None
    track_no = 0
    track_artist = None

    match = re.match('(.+)\ -\ ([\d]{1,3})\ -\ (.+)(\..{1,5})', file_name)
    if match:
        track_artist, track_no, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext.lower()}

    match = re.match('([\d]{1,3})\ (.+)\ -\ (.+)(\..{1,5})', file_name)
    if match:
        track_no, track_artist, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext.lower()}

    match = re.match('(.+)\ -\ (.+)(\..{1,5})', file_name)
    if match:
        track_artist, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext.lower()}

    if not track_name:
        print('unknown audio file pattern: ', file_name)
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext.lower()}




def read_cd(cd_path):
    tracks = []
    meta_files = []
    for file_path in sorted(cd_path.files()):
        if file_path.ext.lower() in AUDIO_FILES:
            track_dict = parse_track_filename(file_path)

            if track_dict['file_ext'] == '.mp3':
                track_obj = mp3.MP3(file_path)
            elif track_dict['file_ext'] == '.ogg':
                track_obj = oggvorbis.OggVorbis(file_path)
            elif track_dict['file_ext'] == '.ape':
                track_obj = apev2.APEv2File(file_path)
            elif track_dict['file_ext'] == '.mpc':
                track_obj = musepack.Musepack(file_path)
            else:
                print('no duration', repr(track_dict['file_ext']), file_path)
                track_obj = None

            track_dict['length'] = 0 if track_obj is None else track_obj.info.length
            if track_dict['length'] == 0:
                print('no track length', file_path)

            tracks.append(track_dict)
        elif file_path.ext.lower() in META_FILES:
            meta_files.append(file_path)
        else:
            print('unknown filetype', file_path.ext, file_path)
    return tracks, meta_files


def x():
    basepath = path('/home/ben/music')


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

    length = {
        'total': 0,
        'min': 9999,
        'max': 0,
        'avg': 9,
    }
    all_length = []
    for artist in artists.values():
        for album in artist['albums']:
            for cd in album['cds']:
                for track in cd['tracks']:
                    if track['length'] > 0:
                        all_length.append(track['length'])
    stats['length'] = dict(
        total_in_h=round(sum(all_length) / 60. / 60, 2),
        min_in_sec=round(min(all_length), 2),
        max_in_min=round(max(all_length) / 60. , 2),
        avg_in_min=round(sum(all_length) / float(len(all_length)) / 60., 2),
    )
    return stats


