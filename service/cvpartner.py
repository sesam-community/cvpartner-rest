from flask import Flask, request, Response
import os
import requests
import logging
import json
import dotdictify

app = Flask(__name__)
logger = None
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger('cvpartner-rest-service')

# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)
logger.setLevel(logging.DEBUG)

@app.route("/<path:path>", methods=["GET"])
def get(path):
    origin_path = os.environ.get("base_url") + path

    headers = {}
    if os.environ.get('headers') is not None:
        headers = json.loads(os.environ.get('headers').replace("'","\""))

    next_page = origin_path

    entities = []
    page_counter = 1
    while next_page is not None:
        logger.info("Fetching data from url: %s", next_page)
        req = requests.get(next_page, headers=headers)
        dict = dotdictify.dotdictify(json.loads(req.text))
        entities.extend(dict.get(os.environ.get("entities_path")))
        if dict.get(os.environ.get('next_page')) is not None:
            page_counter+=1
            next_page = dict.get(os.environ.get('next_page'))
        else:
            next_page = None
    logger.info('Returning entities from %i pages', page_counter)
    return Response(response=json.dumps(entities), mimetype='application/json')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=os.environ.get('port',5000))
