"""
Log info and errors to digest.log.

I also considered emailing errors but am using Kibana for monitoring instead.
"""

import logging
from logging.handlers import SMTPHandler

logger = logging.getLogger('digest')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

"""
mail_handler = SMTPHandler(('localhost', 25),
                           'markschmucker@yahoo.com',
                           ['markschmucker@yahoo.com'],
                           'Digest Error'
                           )
mail_handler.setFormatter(formatter)
mail_handler.setLevel(logging.ERROR)
"""

file_handler = logging.FileHandler('digest.log')
file_handler.setFormatter(formatter)
file_handler.setLevel(logging.INFO)

#logger.addHandler(mail_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
logger.info('Starting...')
