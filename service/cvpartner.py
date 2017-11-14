from flask import Flask, request, Response
import os
import requests
import logging
import json
import dotdictify
from time import sleep

app = Flask(__name__)
logger = None
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger('cvpartner-rest-service')

# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

headers = {}
if os.environ.get('headers') is not None:
    headers = json.loads(os.environ.get('headers').replace("'","\""))

@app.route("/<path:path>", methods=["GET"])
def get(path):
    origin_path = os.environ.get("base_url") + path

    next_page = origin_path

    entities = []
    page_counter = 1
    while next_page is not None:
        if os.environ.get('sleep') is not None:
            logger.info("sleeping for %s milliseconds", os.environ.get('sleep') )
            sleep(float(os.environ.get('sleep')))

        logger.info("Fetching data from url: %s", next_page)
        req = requests.get(next_page, headers=headers)
        if req.status_code != 200:
            logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            raise AssertionError ("Unexpected response status code: %d with response text %s"%(req.status_code, req.text))
        dict = dotdictify.dotdictify(json.loads(req.text))
        entities.extend(dict.get(os.environ.get("entities_path")))
        if dict.get(os.environ.get('next_page')) is not None:
            page_counter+=1
            next_page = dict.get(os.environ.get('next_page'))
        else:
            next_page = None
    logger.info('Returning entities from %i pages', page_counter)
    return Response(response=json.dumps(entities), mimetype='application/json')


@app.route("/post", methods=["POST"])
def post():
    logger.info('Receiving entities on /post')

    entities = request.get_json()
    logger.info(str(entities))
    result = []
    counter = 0
    if not isinstance(entities, list):
        entities = [entities]
    for entity in entities:
        url = os.environ.get("base_url") + entity[os.environ.get("post_url")]
        req = requests.get(url, headers=headers)
        result.extend(req.text)
        counter += 1

    logger.info('Returning %s entities')

    return Response(response=result, mimetype='application/json')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('port',5000))
