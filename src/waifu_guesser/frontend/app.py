from base64 import b64encode
import json
from Shimarin.plugins.flask_api import ShimaApp, CONTEXT_PATH
from Shimarin.server.events import EventEmitter, Event

from flask import Flask, render_template, request

app = Flask(__name__)
emitter = EventEmitter()
app.register_blueprint(ShimaApp(emitter))
app.config["JSON_SORT_KEYS"] = False
app.config["JSON_PRETTYPRINT_REGULAR"] = True

EVENTS: dict[str, Event] = {}


@app.route(CONTEXT_PATH + "/", methods=["GET"])
async def index():
    return render_template("index.html", CONTEXT_PATH=CONTEXT_PATH)


@app.route(CONTEXT_PATH + "/upload", methods=["POST"])
async def evaluate():
    files = request.files.getlist("file")
    if len(files) > 1:
        return {
            "message": "expected only one image"
        }, 400
    file = files[0]
    threshold = float(request.values.get("threshold", 0.1))
    limit = int(request.values.get("limit", 50))
    file.seek(0)

    json_data = json.dumps({
        "threshold": threshold,
        "format": "json",
        "limit": limit,
        "image": b64encode(file.read()).decode(),
        "content-type": request.content_type.lower()
    })

    event = Event.new("danbooru_new_image", json_data, json.loads)
    EVENTS[event.identifier] = event
    await emitter.send(event)
    return f'Uploaded! Go to <a href="{CONTEXT_PATH}/result?id={event.identifier}">the results page</a> to see if the result is ready!'


@app.route(CONTEXT_PATH + "/result", methods=["GET"])
async def get_result():
    _id = request.args.get("id")
    if not _id: return {"message":"Invalid Event ID! Please try again!"}, 400
    event = EVENTS.get(_id)
    if event is None: return {"message":"Invalid Event ID! Please try again!"}, 400
    if event.answered:
        EVENTS.pop(_id)
        answer = event.answer
        if answer['ok']: # type: ignore
            if answer['content-type'] == "application/json": # type: ignore
                return answer
            return render_template("evaluate.html", base64data=answer['image'], tags=answer['tags'], CONTEXT_PATH=CONTEXT_PATH) # type: ignore
        return {"message": answer['message']}, 500 # type: ignore
    return {"message": "Waiting for server, please, reload the page..."}, 200
