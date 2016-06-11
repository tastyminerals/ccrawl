#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Simple crawler for Corpora mailing list.
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
YEARS = [str(y) for y in range(1995, 2017)]
JUNK = r'|'.join(['\[ date \]', '\[ thread \]', '\[ subject \]', '\[ author \]',
                  '\[Corpora-List\]', '\n\n\n+', 'Previous message:.*\n',
                  'Next message:.*\n', 'Messages sorted by:.*\n',
                  'More information about the Corpora-archive.*'])
# http://mailman.uib.no//public/corpora/2016-June/thread.html
URLS = ['http://mailman.uib.no//public/corpora/{0}-{1}/{2}',
        'http://clu.uni.no/corpora/{0}-{1}/{2}']
SESSION = requests.session()


def show_completed(complete):
    # Display a simple progress bar
    done = 100 - complete
    if done > 100:
        done = 100
    sys.stdout.write('\rCompleted {0}%'.format(done))
    sys.stdout.flush()


def create_db(data):
    # Pickle retrived dict
    pickle.dump(data, open(".corpora_list.pickle", "wb"))
    print "\nCORPORA-list has been stored!"


def load_db():
    # Load pickled dict
    try:
        loaded_corpora = pickle.load(open(".corpora_list.pickle", "rb"))
    except IOError:
        ans = raw_input("Local CORPORA-list not found, do you want to sync? (y/n): ")
        if ans.lower()[0] == 'y':
            ans = raw_input("Perform deep sync (include emails, might take ~25 min!)? (y/n): ")
        else:
            sys.exit(1)
        if ans.lower()[0] != 'y':
            loaded_corpora = sync()
            create_db(loaded_corpora)
            return loaded_corpora
        else:
            loaded_corpora = sync(True)
    return loaded_corpora


def _include_older(corpora):
    # Retieve data from older archives
    # Start sync loop
    print 'Retrieving CORPORA data from 1995-2004 (might take ~25 min!)...'
    period = YEARS[:9]
    diff, complete = int(round(100 / len(period))), 100
    for i, year in enumerate(period):
        show_completed(complete)
        for i, _ in enumerate(MONTHS):
            link = URLS[1].format(year, i, '')
            # Get threads list
            threads = SESSION.get(link)
            threads_content = bs4.BeautifulSoup(threads.content, 'lxml')
            if threads_content.title.text == '404 Not Found':
                continue
            # Get urls per thread
            thread_hrefs = threads_content.find_all('a', href=True)
            thread_urls = [turl['href'] for turl in thread_hrefs
                           if turl['href'].endswith('.html')]
            if not thread_urls:
                continue
            thread_text = re.sub(JUNK, '',
                                 threads_content.get_text().encode('utf-8'))
            thread = (link, thread_text)
            corpora[thread] = {}
            corpora = _deep_sync(corpora, thread_urls, thread, year, i, 1)
        complete -= diff
        show_completed(complete)
    return corpora


def _deep_sync(corpora, thread_urls, thread, year, month, n=0):
    # Sync deep (retrieve email data per subject)
    # Get data per subject
    for url in thread_urls:
        email_url = URLS[n].format(year, month, url)
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
    period = [str(year) for year in range(1995, int(last_year))][9:]
    diff, complete = int(round(100 / len(period))), 100
    for i, year in enumerate(period):
        # display % completed
        show_completed(complete)
        for month in MONTHS:
            link = URLS[0].format(year, month, suffix)
            # Get threads list
            threads = SESSION.get(link)
            threads_content = bs4.BeautifulSoup(threads.content, 'lxml')
            if threads_content.title.text == '404 Not Found':
                continue
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
    return corpora_data


def search(corpora):
    # Search CORPORA for keywords
    query = args.find or args.dfind
    fresults = []
    dfresults = []
    # sort corpora data by year
    srt_corpora = sorted(corpora.items(),
                         key=lambda x: x[0][0].split('/')[-2].split('-')[0])
    for thread, subject in srt_corpora:
        header = '>>> {0}{1}{2}'.format(do.BOLD, thread[0], do.END)
        # search in a whole thread
        th_lines = [re.sub('  +|\t+', ' ', line.strip())
                    for line in unicode(thread[1], 'utf-8').split('\n')
                    if line != u'\xc2\xa0' and line.strip() != '']
        first = True
        if not args.dfind:
            for line in th_lines:
                # search for user query match
                found = re.search(query, line, flags=re.IGNORECASE)
                if found:
                    if first:
                        fresults.append('-' * len(header))
                        fresults.append(header)
                        first = False
                    thr_str = ''.join([do.BRED, r'\1', do.END])
                    thr_found = re.sub('({0})'.format(query), thr_str,
                                       found.string, flags=re.IGNORECASE)
                    fresults.append(thr_found)
        elif args.dfind:
            for subj_url, body in subject.items():
                if re.search(query, body, flags=re.IGNORECASE):
                    dfresults.append(subj_url)
    # print -f results
    for res in fresults:
        print res
    # print -df results
    for url in dfresults:
        print '>>>', url


def main():
    if args.sync:
        ans = raw_input("Perform deep sync (include emails, might take ~25 min!)? (y/n): ")
        if ans.lower()[0] == 'y':
            print 'DEEP'
            corp = sync(True)
        else:
            corp = sync()
        create_db(corp)
        sys.exit()

    if args.old:
        corp = _include_older(corp)
        create_db(corp)
        sys.exit()
    if args.find or args.dfind:
        # load local db
        corp = load_db()
    search(corp)


if __name__ == '__main__':
    prs = argparse.ArgumentParser(description="""
    Simple CORPORA mailing list crawler.""")
    prs.add_argument('-f', '--find', type=str,
                     help='specify a search keyword (search thread titles).',
                     required=False)
    prs.add_argument('-df', '--dfind', type=str,
                     help='specify a search keyword (search emails).',
                     required=False)
    prs.add_argument('-s', '--sync', action='store_true',
                     help='syncronize with CORPORA-list.',
                     required=False)
    prs.add_argument('-old', '--old', action='store_true',
                     help='include older archives dating back to 1995.',
                     required=False)
    args = prs.parse_args()
    main()
