from flask import Flask, request, Response, abort
import os
import requests
import logging
import json
import dotdictify
from time import sleep
import base64
import cherrypy


app = Flask(__name__)

logger = None
format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger('cvpartner-rest-service')


# Log to stdout
stdout_handler = logging.StreamHandler()
stdout_handler.setFormatter(logging.Formatter(format_string))
logger.addHandler(stdout_handler)
logger.setLevel(logging.getLevelName(os.environ.get('log_level', 'INFO')))

headers = {}
if os.environ.get('headers') is not None:
    headers = json.loads(os.environ.get('headers').replace("'", "\""))


def encode(v):
    for key, value in v.items():
        if isinstance(value,dict):
            encode(value)
        else:
            v[key] = base64.b64encode(requests.get(value).content).decode("utf-8")

    return v


def str_to_bool(string_input):
    return str(string_input).lower() == "true"


def transform(obj):
    res = {}
    for k, v in obj.items():
        if k == "image":
            if dotdictify.dotdictify(v).large.url is not None:
                res[k] = encode(v)

            else:
                pass
        try:
            _ = json.dumps(v)
        except Exception:
            pass
        else:
            res[k] = v
    return res


class DataAccess:

    def __get_all_users(self, path):
        logger.info("Fetching data from url: %s", path)
        offset = 0
        clean = "start"
        while clean == "start" or len(clean) == 100:
            url = os.environ.get("base_url") + path + "?offset=" + str(offset)
            logger.debug("url :" + url)
            req = requests.get(url, headers=headers)
            if req.status_code != 200:
                req = self.check_error(req, url, headers, 'get')
            clean = json.loads(req.text)
            offset += len(clean)
            for entity in clean:
                yield entity

    def __post_user(self, url, entity):
        logger.debug("url: " + url)
        logger.debug('entity["payload"]:')
        logger.debug(entity["payload"])
        req = requests.post(url, headers=headers, json=entity["payload"])
        if req.status_code != 200:
            req = self.check_error(req, url, headers, 'post', 'json', entity["payload"])
        return str(req.status_code)

    def __put_user(self, url, entity):
        url = url + "/" + entity["id"]
        logger.debug("url: " + url)
        logger.debug('entity["payload"]:')
        logger.debug(entity["payload"])
        req = requests.put(url, headers=headers, json=entity["payload"])
        if req.status_code != 200:
            req = self.check_error(req, url, headers, 'put', 'json', entity["payload"])
        return str(req.status_code)

    def __get_all_cvs(self, path):
        logger.info("Fetching data from url: %s", path)
        offset = 0
        clean = "start"
        while clean == "start" or len(clean) == 100:
            url = os.environ.get("base_url") + path + "?offset=" + str(offset)
            logger.debug("url :" + url)
            req = requests.get(url, headers=headers)
            if req.status_code != 200:
                req = self.check_error(req, url, headers, 'get')

            clean = json.loads(req.text)
            offset += len(clean)
            cv_url = os.environ.get("base_url") + "v3/cvs/"
            for entity in clean:
                if entity.get('deactivated'):
                    pass
                for k, v in entity.items():
                    if k == "id":
                        cv_url += v + "/"
                for k, v in entity.items():
                    if k == "default_cv_id":
                        cv_url += v
                req = requests.get(cv_url, headers=headers)
                if req.status_code != 200:
                    req = self.check_error(req, cv_url, headers, 'get')
                cv = json.loads(req.text)
                if str_to_bool(os.environ.get('delete_company_images', "False")) == True:
                    for i in range(len(cv["project_experiences"])):
                        del cv["project_experiences"][i]["images"]
                yield transform(cv)
                cv_url = os.environ.get("base_url") + "v3/cvs/"

    def __get_all_paged_entities(self, path):
        logger.info("Fetching data from paged url: %s", path)
        url = os.environ.get("base_url") + path
        next_page = url
        page_counter = 1
        while next_page is not None:
            logger.info("Fetching data from url: %s", next_page)
            req = requests.get(next_page, headers=headers)
            if req.status_code != 200:
                req = self.check_error(req, next_page, headers, 'get')
            dict = dotdictify.dotdictify(json.loads(req.text))
            for entity in dict.get(os.environ.get("entities_path")):
                yield transform(entity)

            if dict.get(os.environ.get('next_page')) is not None:
                page_counter += 1
                next_page = dict.get(os.environ.get('next_page'))
            else:
                next_page = None
        logger.info('Returning entities from %i pages', page_counter)

    def __get_all_references(self, path):
        logger.info('Fetching data from paged url: %s', path)
        url = os.environ.get("base_url") + path
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": os.environ.get('token')
        }
        reference_data = json.loads(os.environ.get('reference_post').replace("'","\""))
        total_amount = json.loads(requests.post(url, data=json.dumps(reference_data), headers=headers).text)["total"]
        counter = 0
        size = 10
        while counter < total_amount:
            req = requests.post(url, data=json.dumps(reference_data), headers=headers)
            if req.status_code != 200:
                req = self.check_error(req, url, headers, 'post', 'data', json.dumps(reference_data))
            res = dotdictify.dotdictify(json.loads(req.text))
            counter += size
            reference_data["offset"] = counter
            entities = res.get(os.environ.get("references_path"))
            for entity in entities:
                yield(entity.get("reference"))

        logger.info("returned from all pages")

    def __get_all_categories(self, path):
        logger.info("Fetching data from url: %s", path)
        url = os.environ.get("base_url") + path
        req = requests.get(url, headers=headers)
        if req.status_code != 200:
            req = self.check_error(req, url, headers, 'get')
        clean = json.loads(req.text)
        for entity in clean:
            yield entity

    def __post_custom_tag(self, url, entity):
        logger.debug("url: " + url)
        logger.debug('entity["payload"]:')
        logger.debug(entity["payload"])
        req = requests.post(url, headers=headers, json=entity["payload"])
        if req.status_code != 200:
            req = self.check_error(req, url, headers, 'post', 'json', entity["payload"])
        return str(req.status_code)

    def __put_custom_tag(self, url, entity):
        url = url + "/" + entity["id"]
        logger.debug("url: " + url)
        logger.debug('entity["payload"]:')
        logger.debug(entity["payload"])
        req = requests.put(url, headers=headers, json=entity["payload"])
        if req.status_code != 200:
            req = self.check_error(req, cv_url, headers, 'put', 'json', entity["payload"])
        return str(req.status_code)

    def check_error(self, req, url, headers, method, json = None, data = None):
        if req.status_code == 429:
            return self.recursive_request(url, headers, req.headers.get('Retry-After'), method, json, data)                        
        else:
            logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
            raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))        

    def recursive_request(self, url, headers, retry_after, method, json = None, data = None):
        logger.info("Sleeping for %.2f seconds" % float(retry_after))
        sleep(float(retry_after))
        if method in('get', 'post', 'put'):
            req = requests.request(method=method, url=url, headers=headers, json=json, data=data)
        else:
            logger.error("Unexpected request method: request method = %s" % method)
            raise AssertionError("Unexpected request method: request method = %s" % method)

        if req.status_code != 200:
            if req.status_code == 429:
                req = self.recursive_request(url, headers, req.headers.get('Retry-After'), method, data_type, data)                        
            else:
                logger.error("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
                raise AssertionError("Unexpected response status code: %d with response text %s" % (req.status_code, req.text))
        return req

    def get_paged_entities(self, path):
        logger.info("getting all paged")
        return self.__get_all_paged_entities(path)

    def get_users(self, path):
        logger.info('getting all users')
        return self.__get_all_users(path)

    def post_or_put_users(self, path, entities):
        logger.info('posting/putting users')
        url = os.environ.get("base_url") + path
        status = ""
        for entity in entities:
            if entity["operation"] == "post":
                status = self.__post_user(url, entity)
            elif entity["operation"] == "put":
                status = self.__put_user(url, entity)
        return status

    def get_cvs(self, path):
        logger.info('getting all cvs')
        return self.__get_all_cvs(path)

    def get_references(self, path):
        logger.info('getting all references')
        return self.__get_all_references(path)

    def get_custom_tag_categories(self, path):
        logger.info('getting all categories')
        return self.__get_all_categories(path)

    def post_or_put_custom_tags(self, path, entities):
        logger.info('posting/putting custom tags')
        url = os.environ.get("base_url") + path
        status = ""
        for entity in entities:
            if entity["operation"] == "post":
                status = self.__post_custom_tag(url, entity)
            elif entity["operation"] == "put":
                status = self.__put_custom_tag(url, entity)
        return status


data_access_layer = DataAccess()


def stream_json(clean):
    first = True
    yield '['
    for i, row in enumerate(clean):
        if not first:
            yield ','
        else:
            first = False
        yield json.dumps(row)
    yield ']'


@app.route("/<path:path>", methods=["GET", "POST"])
def get(path):
    entities = data_access_layer.get_paged_entities(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/references", methods=["GET"])
def get_references():
    path = os.environ.get("reference_url")
    entities = data_access_layer.get_references(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/user", methods=["GET"])
def get_user():
    path = os.environ.get("user_url")
    entities = data_access_layer.get_users(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/user", methods=["POST"])
def post_or_put_user():
    path = os.environ.get("user_url")
    entities = json.load(request.stream)
    status_code = data_access_layer.post_or_put_users(path, entities)
    return Response(status_code)


@app.route("/cv", methods=["GET"])
def get_cv():
    path = os.environ.get("user_url")
    entities = data_access_layer.get_cvs(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/custom_tag_category", methods=["GET"])
def get_custom_tag_category():
    path = os.environ.get("custom_tag_category_url")
    entities = data_access_layer.get_custom_tag_categories(path)
    return Response(
        stream_json(entities),
        mimetype='application/json'
    )


@app.route("/custom_tag", methods=["POST"])
def post_or_put_custom_tag():
    path = os.environ.get("custom_tag_url")
    entities = json.load(request.stream)
    status_code = data_access_layer.post_or_put_custom_tags(path, entities)
    return Response(status_code)


if __name__ == '__main__':
    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5000,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()
