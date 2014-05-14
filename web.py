import time

from flask import Flask, render_template

import main

app = Flask(__name__)

@app.route('/')
def hello_world():
    artists = main.parse_directory(dir_path)
    start = time.time()
    duration = time.time() - start
    stats = main.stats(artists)
    return render_template('index.html', artists=artists, stats=stats, duration=duration)

if __name__ == '__main__':
    app.run(debug=True)
