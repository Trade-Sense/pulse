from enum import Enum


class SentimentSource(str, Enum):
    reddit = "reddit"
    twitter = "twitter"
