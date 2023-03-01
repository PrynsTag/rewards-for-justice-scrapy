# Crimebot

<!--- Add badge with scrapy version used --->
[![Scrapy version](https://img.shields.io/badge/scrapy-2.8.0-green.svg)](https://scrapy.org)

Scrapy, a fast high-level web crawling & scraping framework for Python.

## Description

This is a Scrapy spider that crawls the [Rewards for Justice website](https://rewardsforjustice.net).

## Installation

Install all the dependency packages using pip:

    pip install -r requirements.txt

## Quick start

### Run the spider
    
    scrapy crawl rewardsforjustice

By default, this will crawl the Rewards for Justice website and 
save the results to a json and xlxs file in the current directory.
