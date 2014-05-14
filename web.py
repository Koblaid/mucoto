import time

from flask import Flask, render_template

import main

app = Flask(__name__)

@app.route('/')
def hello_world():
    dir_path = '/run/media/ben/6187082c-cf9e-4f8d-829c-6d71ba19f11f/d2/d/music/'

    start = time.time()
    artists = main.parse_directory(dir_path)
    dir_duration = time.time() - start

    start = time.time()
    main.read_tags(artists)
    tag_duration = time.time() - start

    start = time.time()
    stats = main.stats(artists)
    stats_duration = time.time() - start

    return render_template('index.html', artists=artists, stats=stats, dir_duration=dir_duration, tag_duration=tag_duration, stats_duration=stats_duration)

if __name__ == '__main__':
    app.run(debug=True)
