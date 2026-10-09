"""Mars Mission Control: a small JSON API plus a same-origin browser dashboard."""
import os
import psycopg
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from database import connect

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024
CATEGORIES = ('Exploration', 'Engineering', 'Science')


@app.get('/')
def dashboard():
    return render_template('index.html', app_name=os.environ.get('APP_NAME', 'Mars Mission Control'))


@app.get('/api/health')
def health():
    with connect() as conn:
        conn.execute('SELECT 1')
    return jsonify(status='ok', database='connected')


@app.get('/api/missions')
def list_missions():
    with connect() as conn:
        missions = conn.execute('SELECT * FROM missions ORDER BY id DESC').fetchall()
    return jsonify(missions)


@app.post('/api/missions')
def create_mission():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Send a JSON object.'), 400
    title, sector = data.get('title'), data.get('sector')
    category, reward = data.get('category'), data.get('reward')
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
        return jsonify(error='Title must contain 1–100 characters.'), 400
    if not isinstance(sector, str) or not 1 <= len(sector.strip()) <= 40:
        return jsonify(error='Sector must contain 1–40 characters.'), 400
    if category not in CATEGORIES:
        return jsonify(error='Choose Exploration, Engineering, or Science.'), 400
    if type(reward) is not int or not 10 <= reward <= 500:
        return jsonify(error='Reward must be a whole number from 10 to 500.'), 400
    with connect() as conn:
        mission = conn.execute(
            'INSERT INTO missions (title, sector, category, reward) '
            'VALUES (%s, %s, %s, %s) RETURNING *',
            (title.strip(), sector.strip(), category, reward),
        ).fetchone()
    return jsonify(mission), 201


@app.patch('/api/missions/<int:mission_id>/complete')
def complete_mission(mission_id):
    # The conditional UPDATE is atomic: two requests cannot complete a mission twice.
    with connect() as conn:
        mission = conn.execute(
            "UPDATE missions SET status = 'completed', completed_at = NOW() "
            "WHERE id = %s AND status = 'available' RETURNING *", (mission_id,),
        ).fetchone()
        if not mission:
            exists = conn.execute('SELECT id FROM missions WHERE id = %s', (mission_id,)).fetchone()
            if exists:
                return jsonify(error='This mission is already completed.'), 409
            return jsonify(error='Mission not found.'), 404
    return jsonify(mission)


@app.delete('/api/missions/<int:mission_id>')
def delete_mission(mission_id):
    # Keep completed missions as the colony's permanent achievement history.
    with connect() as conn:
        deleted = conn.execute(
            "DELETE FROM missions WHERE id = %s AND status = 'available' RETURNING id",
            (mission_id,),
        ).fetchone()
        if not deleted:
            exists = conn.execute('SELECT id FROM missions WHERE id = %s', (mission_id,)).fetchone()
            if exists:
                return jsonify(error='Completed missions stay in the colony history.'), 409
            return jsonify(error='Mission not found.'), 404
    return '', 204


@app.get('/api/stats')
def stats():
    with connect() as conn:
        summary = conn.execute("""
            SELECT COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'available') AS available,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                COALESCE(SUM(reward) FILTER (WHERE status = 'completed'), 0) AS credits
            FROM missions
        """).fetchone()
    # Derived from stored missions; never kept in volatile Python variables.
    summary['rank'] = ('Pioneer' if summary['credits'] >= 1000 else
                       'Explorer' if summary['credits'] >= 400 else 'Cadet')
    return jsonify(summary)


@app.errorhandler(psycopg.Error)
def database_error(error):
    # Do not send connection strings, credentials, or database errors to the browser.
    app.logger.error('Database operation failed: %s', type(error).__name__)
    return jsonify(error='Database temporarily unavailable. Try again shortly.'), 503


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error=error.description), error.code
