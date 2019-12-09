#!/usr/bin/python
"""
A flask server to handle webhooks from the digests plugin.
"""

from flask import Flask, request
import logging
from process import ProcessDigest

logger = logging.getLogger('digest_webhook')
file_handler = logging.FileHandler('digest_webhook.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

logger.info('running digest webhook.py')

app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d4jjf2b6176a' # ?


@app.route('/', methods=['GET', 'POST'])
def digest_event():
    print 'digest_event'
    if request.method == 'POST':
        data = request.json
        try:
            # Process in a thread, as this server uses Flask and may not
            # handle a large number of requests.
            t = ProcessDigest(data)
            t.start()
        except Exception, exc:
            print exc
            logger.error(str(exc))

        return '', 200
    else:
        return '', 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081, debug=True, threaded=True)
