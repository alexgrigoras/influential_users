# Influential users

## Description
Determining the most influential users from the multimedia social network YouTube by creating a graph with the most important users / channels.

Image taken from: <i>Fan, Yujie & Zhang, Yiming & Ye, Yanfang & Zheng, Wanhong. (2017). Social Media for
Opioid Addiction Epidemiology: Automatic Detection of Opioid Addicts from Twitter and
Case Studies, 1259-1267</i>

## Architecture
The main components of the application are

1. <b>Information Gathering</b> - YouTube

1. <b>Data Storage</b> - MongoDB

1. <b>Analysis</b>
    1. ranking algorithms
    1. sentiment detection

## Application structure
```
influential_users
├── youtube_sentiment_analysis
|   ├── data
|   ├── modules
|   |   ├── __init__.py
|   |   ├── crawler.py
|   |   ├── analysis.py
|   |   └── storage.py
|   ├── __init__.py
|   └── __main__.py
├── LICENSE
├── README.md
├── requirements.txt
└── setup.py
```

## Resources

1. <b>Academic papers</b>

1. <b>Web content</b>
