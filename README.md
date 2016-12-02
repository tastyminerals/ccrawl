# ccrawl
Simple CORPORA list crawler

The **CORPORA list** is open for information and questions about text corpora such as availability, aspects of compiling and using corpora, software, tagging, parsing, bibliography, conferences etc. The list is also open for all types of discussion with a bearing on corpora.

**CORPORA list**: http://clu.uni.no/corpora/welcome.html

- Subscription page: http://clu.uni.no/corpora/sub.html
- Archives (October 2004 - present): http://mailman.uib.no//public/corpora/
- Older archives: http://www.hit.uib.no/corpora/old.html

### Screenshots:
![searching threads](http://i.imgur.com/oD1Vjqh.png)

![searching emails](http://i.imgur.com/GwCmUDx.png) 

### Usage:
**ccrawl** is a python script and can be run simply by `python2 ccrawl.py` + some arguments.
Before using the script you need to syncronize with the CORPORA first: `python2 ccrawl --sync`.
Depending on your choice this operation might take seconds or up to 20 min. **ccrawl** will create a local copy of CORPORA `.corpora_list.pickle` which will be accessed each time you run the script. 

- To search CORPORA thread titles: 
```
python2 ccrawl.py -f corpus
```
```
python2 ccrawl.py -f "chinese corpus"
```
- To search CORPORA emails (available only if you performed deep sync):
```
python2 ccrawl.py -df corpus
``` 
```
python2 ccrawl.py -df "chinese corpus"
```

- To add older archives (1995-2004): 
```
python2 ccrawl.py -old
```
- To see help: 
```
python2 ccrawl.py -h
```

### Install:
No installation needed.
Make sure you have python2 installed on your system before running.

The script uses **requests** and **beautifulsoup4** libraries.

