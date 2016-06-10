#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Simple crawler for Corpora and BioNLP mailing lists.
Searches the mailing list for keywords.
"""
from __future__ import division
import argparse
import re
import pickle
import subprocess as sb
import sys


try:
    import requests
    import bs4
except ImportError:
    print "Installing missing python libs..."
    sb.call(['sudo', 'pip2', 'install', 'requests'])
    sb.call(['sudo', 'pip2', 'install', 'beautifulsoup4'])
    import requests
    import bs4


# colors for fun
class do:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    BBLUE = '\033[1;94m'
    GREEN = '\033[92m'
    BGREEN = '\033[1;92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BRED = '\033[1;91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
          'August', 'September', 'October', 'November', 'December']
YEARS = [str(year) for year in range(1995, 2017)]
JUNK = r'\[ date \]|\[ thread \]|\[ subject \]|\[ author \]|\[Corpora-List\]|\n\n\n+'
# http://mailman.uib.no//public/corpora/2016-June/thread.html
URLS = ['http://mailman.uib.no//public/corpora/{0}-{1}/{2}',
        'http://mail.bionlp.org/pipermail/bionlp_bionlp.org/{0}-{1}/{2}']
SESSION = requests.session()


def show_completed(complete):
    # Display a simple progress bar
    sys.stdout.write('\rCompleted {0}%'.format(100 - complete))
    sys.stdout.flush()


def create_db(data):
    # Pickle retrived dict
    pickle.dump(data, open( ".corpora_list.pickle", "wb" ))
    print "CORPORA-list has been stored!"


def load_db():
    # Load pickled dict
    try:
        loaded_corpora = pickle.load(open(".corpora_list.pickle", "rb" ))
    except IOError:
        ans = raw_input("Local CORPORA-list not found, do you want to sync? (y/n): ")
        if ans.lower()[0] == 'y':
            ans = raw_input("Perform deep sync (include emails, might take ~25 min!)? (y/n): ")
        else:
            sys.exit(1)
        if ans.lower()[0] != 'y':
            loaded_corpora = sync()
            return loaded_corpora
        else:
            loaded_corpora = sync(True)
    return loaded_corpora


def _deep_sync(corpora, thread_urls, thread, year, month):
    # Sync deep (retrieve email data per subject)
    # Get data per subject
    for url in thread_urls:
        email_url = MLIST.format(year, month, url)
        email = SESSION.get(email_url)
        email_cont = bs4.BeautifulSoup(email.content, 'lxml')
        email_data = email_cont.get_text().encode('utf-8')
        # Remove some junk from email body
        corpora[thread][email_url] = re.sub(JUNK, '', email_data)
    return corpora


def sync(deep=False):
    # Sync with the current CORPORA
    suffix = 'thread.html'
    # Get the last dates
    up = SESSION.get('http://mailman.uib.no//public/corpora/')
    up_cont = bs4.BeautifulSoup(up.content, 'lxml')
    last_month, last_year = up_cont.find_all('td')[3].text.strip(':').split()
    # Start sync loop
    corpora_data = {}
    period = YEARS[9:]  # FIXIT
    diff, complete = int(round(100 / len(period))), 100
    for i, year in enumerate(period):
        # display % completed
        show_completed(complete)
        for month in MONTHS:
            link = MLIST.format(year, month, suffix)
            # Get threads list
            threads = SESSION.get(link)
            threads_content = bs4.BeautifulSoup(threads.content, 'lxml')
            # Get urls per thread
            thread_hrefs = threads_content.find_all('a', href=True)
            thread_urls = [turl['href'] for turl in thread_hrefs
                           if turl['href'].endswith('.html')]
            if not thread_urls:
                continue
            thread_text = re.sub(JUNK, '',
                                 threads_content.get_text().encode('utf-8'))
            thread = (link, thread_text)
            corpora_data[thread] = {}
            if deep:
                corpora_data = _deep_sync(corpora_data, thread_urls,
                                          thread, year, month)
        complete -= diff
        show_completed(complete)
    create_db(corpora_data)
    return corpora_data


def search(corpora, query):
    # Search CORPORA for keywords
    results = []
    for thread, subject in corpora.items():
        header = '>>> {0}{1}{2}'.format(do.BOLD, thread[0], do.END)
        # search in a whole thread
        th_lines = [re.sub('  +|\t+', ' ', line.strip())
                    for line in unicode(thread[1], 'utf-8').split('\n')
                    if line != u'\xc2\xa0' and line.strip() != '']
        first = True
        for line in th_lines:
            # search for user query match
            found = re.search(query, line, flags=re.IGNORECASE)
            if found:
                if first:
                    print '-' * len(header)
                    print header
                    first = False
                thr_str = ''.join([do.BRED, r'\1', do.END])
                thr_found = re.sub('({0})'.format(query), thr_str,
                                   found.string, flags=re.IGNORECASE)
                print thr_found


def main():
    corp = load_db()
    search(corp, args.find)


if __name__ == '__main__':
    prs = argparse.ArgumentParser(description="""
    Simple CORPORA and BioNLP mailing list crawler.""")
    prs.add_argument('-f', '--find', type=str,
                     help='specify a search keyword.',
                     required=True)
    prs.add_argument('-s', '--sync', action='store_true',
                     help='syncronize with CORPORA-list.',
                     required=False)
    prs.add_argument('-old', '--old', action='store_true',
                     help='include older archives dating back to 1995.',
                     required=False)
    prs.add_argument('-m', '--mlist', type=int,
                     help='specify a mailing list: 1 -> CORPORA, 2 -> BIONLP,'+
                     'default 1.', default=1,
                     required=False)
    args = prs.parse_args()
    MLIST = args.mlist
    if args.mlist == 1:
        MLIST = URLS[0]
    elif args.mlist == 2:
        MLIST = URLS[1]
    else:
        print 'ERROR! Incorrect mailing list.'
        sys.exit(1)
    main()


