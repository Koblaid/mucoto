import os
import re

from path import path


AUDIO_FILES = ('.mp3', '.mpc', '.ape', '.ogg')
META_FILES = ('.tif', '.jpg', '.gif', '.bmp', '.nfo', '.txt', '.htm', '.doc')


def parse_track_filename(track_path):
    file_name = track_path.basename()
    file_ext = track_path.ext
    track_name = None
    track_no = 0
    track_artist = None

    match = re.match('(.+)\ -\ ([\d]{1,3})\ -\ (.+)\.(.{1,5})', file_name)
    if match:
        track_artist, track_no, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext}

    match = re.match('([\d]{1,3})\ (.+)\ -\ (.+)\.(.{1,5})', file_name)
    if match:
        track_no, track_artist, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext}

    match = re.match('(.+)\ -\ (.+)\.(.{1,5})', file_name)
    if match:
        track_artist, track_name, file_ext = match.groups()
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext}

    if not track_name:
        print('unknown audio file pattern: ', file_name)
        return {'track_no': int(track_no), 'artist': track_artist, 'name': track_name, 'file_ext': file_ext}



def x():
    basepath = path('/home/ben/music')


    artists = {}
    for letterpath in basepath.dirs():

        for artistpath in letterpath.dirs():
            if artistpath.basename() == '.AppleDouble':
                continue

            albums = []
            for albumpath in artistpath.dirs():
                for unknownfile in albumpath.dirs():
                    print('TODO %s' % unknownfile)


                tracks = []
                meta_files = []
                for file_path in sorted(albumpath.files()):
                    if file_path.ext.lower() in AUDIO_FILES:
                        tracks.append(parse_track_filename(file_path))
                    elif file_path.ext.lower() in META_FILES:
                        meta_files.append(file_path)
                    else:
                        print('unknown filetype', file_path.ext, file_path)

                albumname = albumpath.basename()
                albumyear = None

                match = re.match('([\d]{4})\ -\ (.+)', albumname)
                if match:
                    albumyear, albumname = match.groups()

                albums.append({'name': albumname, 'tracks': tracks, 'meta_files': meta_files, 'year': albumyear})

            artists[str(artistpath.basename())] = albums



            for unknownfile in artistpath.files():
                print('TODO %s' % unknownfile)


        for unknownfile in letterpath.files():
            print('TODO %s' % unknownfile)


    for unknownfile in basepath.files():
        print('TODO %s' % unknownfile)

    return artists



def stats(artists):
    stats = {}

    stats['no_artists'] = len(artists)

    stats['no_albums'] = sum((len(albums) for albums in artists.values()))

    stats['no_files_by_type'] = {}
    for albums in artists.values():
        for album in albums:
            for track in album['tracks']:
                ext = track['file_ext']
                stats['no_files_by_type'].setdefault(ext, 0)
                stats['no_files_by_type'][ext] += 1

            for filename in album['meta_files']:
                ext = path(filename).ext
                stats['no_files_by_type'].setdefault(ext, 0)
                stats['no_files_by_type'][ext] += 1

    return stats


