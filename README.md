# patent_scraper_analysis

In order to gain insight into technological trends, I started investigating patents. It seemed like "smart" people had an understanding of trends in patents being filed but I couldn't figure out how they knew what they knew. To solve this issue, I built a scraper which pulls data from the USPTO and also wrote several notebooks analyzing different aspects of the patents. 

## No-Code Scraping Workflow

The initial search page can be found [here](http://patft.uspto.gov/netahtml/PTO/search-bool.html). The program will query the patent search page and pull the number of patents that should be returned for the search query entered into the functions parameters.

The URL of the page returned from a search will look like this:
```
http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r=0&f=S&l=50&TERM1=probiotic&FIELD1=&co1=AND&TERM2=&FIELD2=&d=PTXT
```

Using those numbers, the program will loop through links to individual patents. One of those links looks like this:
```
http://patft.uspto.gov/netacgi/nph-Parser?Sect1=PTO2&Sect2=HITOFF&p=1&u=%2Fnetahtml%2FPTO%2Fsearch-bool.html&r=1&f=G&l=50&co1=AND&d=PTXT&s1=probiotic&OS=probiotic&RS=probiotic
```
The url parameter `&r=1` is modified to return different patents for the search query in the `&s1=probiotic` parameter.

## Analysis Notebooks

### Meta-Data

In this notebook, the pipeline is made to analyze features like inventors, publication dates, primary examiners.

#### Publication Date Example Plot

![](https://i.imgur.com/px767ex.png)

### Abstracts

In this notebook, I created a pipeline to analyze the content of the abstracts of the patents in the input data. 

#### Example Plot of Common 3-Grams

![](https://i.imgur.com/0aAnkUf.png)

### uBiome Analysis

I specifically dove into uBiome because I knew a bit about their business from before they filed for bankrupcy and I was interested to see what their patents looked like. 

#### Inventors

![](https://i.imgur.com/37tUJz5.png)

#### Publication Dates

![](https://i.imgur.com/qTdFdIG.png)

#### Claims Topic 3-Gram Cloud

![](https://i.imgur.com/jIB6gx6.png)

## To Do

- Standardize plots
  - Both high-level style choices (grids, tick marks, font sizes) to axis labels, titles and legends.
- Do more in-depth text analysis
  - Got into claims and was able to apply N-Gram analysis and LDA Topic Modeling to both claims and abstracts
  - Next step is to find a more in depth method of analyzing text. LDA seems sufficient for unsupervised clustering but there may be more complex methods out there. 
  
## Example Input Data

https://drive.google.com/file/d/1FtqAcsA-xKhNqVqFMK0rzjQTmsxWaIz3/view?usp=sharing
