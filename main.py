import csv
import sys, os
import logging
import datetime
from engine.posta import Posta
from datetime import date



def start():
    # configure logging
    d = date.today()

    log_file = d.isoformat()
    log_path = os.getcwd() + "\\logs"
    print(log_path)
    logging.basicConfig(
    format="%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    datefmt="'%m/%d/%Y %I:%M:%S %p",
    handlers=[
        logging.FileHandler("{0}/{1}.log".format(log_path, log_file)),
        logging.StreamHandler()
    ],
    level = logging.DEBUG)

    logger = logging.getLogger(__name__)

    # get posta object
    logger.info("...Starting Application...")
    # get settings from csv file
    settings = {}
    sites =[]
    with open('1_settings.csv') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            single_setting = {}
            single_setting['site'] = row['site']
            single_setting['posts'] = row['posts']
            single_setting['category'] = row['category']
            single_setting['table'] = row['table']
            #single_setting['year'] = row['year']
            sites.append(single_setting)
    settings ['workload'] = sites
    posta = Posta(settings, logger)
    posta.main()
    logger.info("Execution finished")


if __name__ == '__main__':
    start()