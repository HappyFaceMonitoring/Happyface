import json
import requests
import pycurl
from io import BytesIO


def get_data_from_elasticsearch(base_url, header, query_head, query_body, logger):
    logger.debug("Starting data extraction from elastic API")
    # next build the http data string from the query_header and the query_body
    # important: There has to be a newline between header and body
    # see here for more information: https://www.elastic.co/guide/en/elasticsearch/reference/master/search-multi-search.html
    request = "\n" + json.dumps(query_head) + "\n" + json.dumps(query_body) + "\n"
    logger.debug(f"using query:\n{request}")
    # get the data with pycurl (http://pycurl.io/docs/latest/quickstart.html)
    # pycurl needs a function to write the http response to, we use BytesIO
    # the correspondig curl command is: curl -X POST -H 'Content-Type: application/json' -H "Authorization: Bearer $CERN_BEARER_TOKEN" "https://monit-grafana.cern.ch/api/datasources/proxy/9582/_msearch" --data $request
    response_body = BytesIO()
    response_header = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, base_url)
    c.setopt(c.POSTFIELDS, request)
    c.setopt(c.HTTPHEADER, header)
    c.setopt(c.WRITEDATA, response_body)
    c.setopt(c.WRITEHEADER, response_header)
    c.perform()
    c.close()
    logger.debug(f"recieved haeder:\n{response_header.getvalue()}\n")
    logger.debug(f"recieved data:\n{response_body.getvalue()}\n")
    # check if the http code is 200 else raise an error
    if "200" not in response_header.getvalue().decode("utf8").split("\n")[0]:
        logger.error(f"recieved haeder:\n{response_header.getvalue().decode('utf8')}\n")
        logger.error(f"recieved data:\n{response_body.getvalue().decode('utf8')}\n")
        raise Exception(
            f"Server retourned an error code:\n{response_header.getvalue().decode('utf8')}"
        )

    # try to interpret the resieved data as json
    try:
        result = json.loads(response_body.getvalue().decode("utf8"))
    except Exception as e:
        logger.error(e)
        logger.error("The HTTP response didn't contain the expected JSON.")
        raise
    return result


def get_data_from_grafana(url, db_name, query, token=None, **other_params):
    """Simple helper function to get the resource data from a grafana service in JSON format.

    Args:
        url (str): Url to the grafana instance. Should look like `https://grafana_instance.com/api/dataresources/3/query`.
        db_name (str): Name of the db you want to fetch data from.
        query (triple quoted raw string): The query to execute on the db to get the data wanted.
                                          Should be in a triple quoted raw string format `r\"\"\"SELECT... \"\"\"`,
                                          so that single quoted strings are possible in the query.
        token (str, optional): The identification token to for the grafana instance if necessary. Defaults to None.
        **other_params: Additional parameters for the grafana api, e.g. `epoch="s"`.

    Returns:
        json like dict or list: The http response json.
    """
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    if token:
        headers["Authorization"] = "Bearer " + token

    params = {
        "db": db_name,
        "q": query,
    }
    if other_params:
        params.update(**other_params)

    r = requests.get(url, headers=headers, params=params)
    return r.json()
